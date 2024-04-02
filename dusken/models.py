import logging
import uuid
from datetime import timedelta
from itertools import chain

from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group
from django.contrib.auth.models import Group as DjangoGroup
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel
from phonenumber_field.modelfields import PhoneNumberField

from dusken.apps.common.mixins import BaseModel
from dusken.apps.neuf_ldap.utils import delete_ldap_user, ldap_create_password
from dusken.managers import DuskenUserManager, MembershipManager, OrderManager
from dusken.utils import create_email_key, send_validation_email

logger = logging.getLogger(__name__)


# FIXME: We can't seem use the django-stubs type plugin to infer types from OrgUnit, since MPTTModel is untyped/any
class DuskenUser(AbstractUser):  # type: ignore
    updated = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    first_name = models.CharField(_("first name"), max_length=254, blank=True)
    last_name = models.CharField(_("last name"), max_length=254, blank=True)
    email = models.EmailField(_("email address"), unique=True)
    email_confirmed_at = models.DateTimeField(blank=True, null=True)
    email_key = models.CharField(max_length=40, default=create_email_key)
    phone_number = PhoneNumberField(_("phone number"), blank=True, default="")
    phone_number_key = models.CharField(max_length=40, blank=True, null=True)  # noqa: DJ001
    phone_number_confirmed = models.BooleanField(default=False)
    phone_number_confirmed_at = models.DateTimeField(blank=True, null=True)
    date_of_birth = models.DateField(_("date of birth"), null=True, blank=True)

    # Address
    street_address = models.CharField(_("street address"), max_length=255, null=True, blank=True)  # noqa: DJ001
    street_address_two = models.CharField(_("street address 2"), max_length=255, null=True, blank=True)  # noqa: DJ001
    postal_code = models.CharField(_("postal code"), max_length=10, null=True, blank=True)  # noqa: DJ001
    city = models.CharField(_("city"), max_length=100, null=True, blank=True)  # noqa: DJ001
    country = CountryField(_("country"), default="NO", blank=True)

    place_of_study = models.ForeignKey(
        "dusken.PlaceOfStudy",
        models.SET_NULL,
        verbose_name=_("place of study"),
        blank=True,
        null=True,
    )
    legacy_id = models.IntegerField(_("legacy id"), null=True, blank=True)

    stripe_customer_id = models.CharField(_("stripe customer id"), max_length=254, null=True, blank=True)  # noqa: DJ001

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = DuskenUserManager()

    @property
    def email_is_confirmed(self):
        return self.email_confirmed_at is not None

    def confirm_email(self, save=True):
        if not self.email_is_confirmed:
            self.email_confirmed_at = timezone.now()
            if save:
                self.save()

    def confirm_phone_number(self, save=True):
        if not self.phone_number_confirmed:
            self.phone_number_confirmed = True
            self.phone_number_confirmed_at = timezone.now()
            if save:
                self.save()

    def get_absolute_url(self):
        return reverse("user-detail", kwargs={"slug": self.uuid})

    @property
    def active_member_card(self):
        return self.member_cards.filter(is_active=True).first()

    @property
    def is_volunteer(self):
        return self.groups.filter(profile__type=GroupProfile.TYPE_VOLUNTEERS).exists()

    @property
    def has_set_username(self):
        from dusken.apps.neuf_auth.models import AuthProfile

        return AuthProfile.objects.filter(user=self, username_updated__isnull=False).exists()

    @property
    def is_member(self):
        return bool(self.last_membership and self.last_membership.is_valid)

    @property
    def is_lifelong_member(self):
        return bool(self.last_membership and self.last_membership.membership_type.expiry_type == "never")

    def has_group(self, group):
        if type(group) is not Group:
            raise TypeError("Must of type Group")
        return self.groups.filter(id=group.id).exists()

    @property
    def last_membership(self):
        return self.memberships.order_by("-start_date").first()

    @property
    def unclaimed_orders(self):
        return Order.objects.unclaimed(phone_number=self.phone_number)

    def update_volunteer_status(self):
        # FIXME: What if user is part of a group not tied to an org unit? Should check that
        if self.groups.count() <= 1 and self.is_volunteer:
            Group.objects.filter(profile__type=GroupProfile.TYPE_VOLUNTEERS).first().user_set.remove(self)
        else:
            Group.objects.filter(profile__type=GroupProfile.TYPE_VOLUNTEERS).first().user_set.add(self)

    def log(self, message, changed_by=None):
        if changed_by is None:
            changed_by = self
        UserLogMessage(user=self, message=message, changed_by=changed_by).save()

    def save(self, **kwargs):
        # If email or phone number has changed, invalidate confirmation state
        self.invalidate_confirmation_state()

        # If phone number is confirmed, claim orders
        self.claim_orders()

        super().save(**kwargs)

    def delete(self, **kwargs):
        logger.info(f"Deleting user with username {self.username}")
        # Before deleting, remove phone number from user orders to prevent leaking related user data
        # with a recycled phone number (ie. membership and order data).
        self.orders.update(phone_number=None)

        # Delete all the LDAP related user data if LDAP is configured
        delete_ldap_user(self.username)

        super().delete(**kwargs)

    def set_ldap_hash(self, raw_password):
        from dusken.apps.neuf_auth.models import AuthProfile

        ap, _ = AuthProfile.objects.get_or_create(user=self)
        ap.ldap_password = ldap_create_password(raw_password)
        ap.save()

    def invalidate_confirmation_state(self):
        if self.pk is not None:
            orig = DuskenUser.objects.get(pk=self.pk)

            if orig.email != self.email:
                self.email_confirmed_at = None
                self.email_key = create_email_key()
                send_validation_email(self)

            if orig.phone_number != self.phone_number:
                self.phone_number_confirmed = False
                self.phone_number_confirmed_at = None

    def claim_orders(self, ignore_confirmed_state=False):
        if self.phone_number_confirmed or (ignore_confirmed_state and self.phone_number):
            for order in self.unclaimed_orders:
                order.user = self
                order.product.user = self
                order.product.save()
                order.save()

                if order.member_card:
                    order.member_card.user = self
                    order.member_card.save()

    def get_full_address(self):
        address_part = [str(self.street_address), str(self.street_address_two)]
        address_part = " ".join(x for x in address_part if x != "None")
        zip_code_part = [str(self.postal_code), str(self.city)]
        zip_code_part = " ".join(x for x in zip_code_part if x != "None")
        country = self.country.name if self.country else ""

        return "{}{}, {}".format(address_part + ", " if address_part else "", zip_code_part, country)

    def have_address(self):
        return any((self.street_address, self.street_address_two, self.postal_code, self.city))

    def __str__(self):
        if len(self.first_name) + len(self.last_name) > 0:
            return f"{self.first_name} {self.last_name} ({self.username})"
        return f"{self.username}"

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        default_permissions = ("add", "change", "delete", "view")


class Membership(BaseModel):
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    membership_type = models.ForeignKey("dusken.MembershipType", models.CASCADE)
    user = models.ForeignKey("dusken.DuskenUser", models.SET_NULL, null=True, blank=True, related_name="memberships")

    objects = MembershipManager()

    @property
    def is_valid(self):
        # FIXME: update for trial membership and life long memberships
        is_lifelong = self.membership_type.expiry_type = MembershipType.EXPIRY_NEVER and self.end_date is None
        return is_lifelong or self.end_date >= timezone.now().date()

    @property
    def expires_in_less_than_one_month(self):
        if not self.end_date:
            return False
        return self.end_date < (timezone.now().date() + timedelta(days=30))

    @property
    def expires_in_less_than_one_year(self):
        if not self.end_date:
            return False
        return self.end_date < (timezone.now().date() + timedelta(days=365))

    def __str__(self):
        name = self.__class__.__name__
        if self.end_date is None:
            return f"{name}: Life long"
        end_date = f" - {self.end_date}" if self.end_date is not None else "N/A"
        return f"{name}: {self.start_date}{end_date}"

    class Meta:
        verbose_name = _("Membership")
        verbose_name_plural = _("Memberships")
        default_permissions = ("add", "change", "delete", "view")


class MembershipType(BaseModel):
    """Type of membership

    A membership expires in different ways
     - EXPIRY_DURATION: Expires after n time has past, specified by the duration field
     - EXPIRY_NEVER: Never expires
     - EXPIRY_END_OF_YEAR: Expiry is set to the first day of the year after the current year
    """

    EXPIRY_DURATION = "duration"
    EXPIRY_NEVER = "never"
    EXPIRY_END_OF_YEAR = "end_of_year"
    EXPIRY_TYPES = (
        (EXPIRY_DURATION, _("Duration")),
        (EXPIRY_NEVER, _("Never")),
        (EXPIRY_END_OF_YEAR, _("End of year")),
    )

    name = models.CharField(max_length=254)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    price = models.IntegerField(default=0, help_text=_("Price in øre"))
    is_default = models.BooleanField(default=False)
    duration = models.DurationField(default=timedelta(days=365), null=True, blank=True)
    expiry_type = models.CharField(max_length=254, choices=EXPIRY_TYPES, default=EXPIRY_DURATION)

    @property
    def price_nok_kr(self):
        return int(self.price / 100)

    def __str__(self):
        return f"{self.name}"

    def save(self, **kwargs):
        # Only one can be default
        if self.is_default:
            MembershipType.objects.all().update(is_default=False)
        super().save(**kwargs)

    def get_expiry_date(self):
        """Get the correct end date for this membership type."""
        now = timezone.now()
        if self.expiry_type == self.EXPIRY_DURATION:
            return (now + self.duration).date()
        elif self.expiry_type == self.EXPIRY_END_OF_YEAR:
            return now.date().replace(year=now.year + 1, month=1, day=1)
        elif self.expiry_type == self.EXPIRY_NEVER:
            return None

        raise ImproperlyConfigured(f"MembershipType object {self.__str__()} is configured incorrectly")

    @classmethod
    def get_default(cls):
        try:
            return cls.objects.get(is_default=True)
        except cls.DoesNotExist as err:
            raise ImproperlyConfigured("Error: At least one MembershipType must have is_default set") from err
        except cls.MultipleObjectsReturned as err:
            raise ImproperlyConfigured("Error: Only one MembershipType can have is_default set") from err

    class Meta:
        verbose_name = _("Membership type")
        verbose_name_plural = _("Membership types")


class MemberCard(BaseModel):
    card_number = models.IntegerField(_("card number"), unique=True)
    registered = models.DateTimeField(_("registered"), null=True, blank=True)
    is_active = models.BooleanField(_("is active"), default=True)
    user = models.ForeignKey(
        "dusken.DuskenUser",
        models.SET_NULL,
        verbose_name=_("user"),
        null=True,
        blank=True,
        related_name="member_cards",
    )

    def register(self, user=None, order=None):
        assert not (user and order)
        if user or (order and not self.registered):
            self.registered = timezone.now()
            self.is_active = True
        if user:
            user.member_cards.filter(is_active=True).update(is_active=False)
            self.user = user
        if order:
            assert not order.member_card
            order.member_card = self
            order.save()
        self.save()

    def __str__(self):
        return f"{self.card_number}"

    class Meta:
        verbose_name = _("Member card")
        verbose_name_plural = _("Member cards")
        default_permissions = ("add", "change", "delete", "view")


class GroupProfile(BaseModel):
    """django.contrib.auth.model.Group extended with additional fields."""

    TYPE_VOLUNTEERS = "volunteers"
    TYPE_STANDARD = ""

    TYPES = ((TYPE_VOLUNTEERS, _("Volunteers")), (TYPE_STANDARD, _("Standard")))
    type = models.CharField(max_length=255, choices=TYPES, default=TYPE_STANDARD, blank=True)

    posix_name = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    group = models.OneToOneField(DjangoGroup, models.CASCADE, related_name="profile")

    def validate_unique(self, exclude=None):
        super().validate_unique(exclude=exclude)
        if (
            self.posix_name != ""
            and self.__class__.objects.filter(posix_name=self.posix_name).exclude(id=self.id).exists()
        ):
            raise ValidationError(_("Posix name must be unique or empty"))

    def save(self, **kwargs):
        # Only one can be the volunteer group
        if self.type == self.TYPE_VOLUNTEERS:
            GroupProfile.objects.all().update(type=self.TYPE_STANDARD)

        super().save(**kwargs)

    def __str__(self):
        return f"{self.posix_name}"

    class Meta:
        verbose_name = _("Group profile")
        verbose_name_plural = _("Group profiles")


# FIXME: We can't seem use the django-stubs type plugin to infer types from BaseModel, since MPTTModel is untyped/any
class OrgUnit(MPTTModel, BaseModel):  # type: ignore
    """Association, comittee or similar"""

    name = models.CharField(_("name"), max_length=255)
    slug = models.SlugField(_("slug"), unique=True, max_length=255, blank=True)
    short_name = models.CharField(_("short name"), max_length=128, blank=True)
    is_active = models.BooleanField(_("is active"), default=True)
    description = models.TextField(_("description"), blank=True, default="")

    # Contact
    email = models.EmailField(_("email"), blank=True, default="")
    contact_person = models.ForeignKey(
        "dusken.DuskenUser",
        models.SET_NULL,
        verbose_name=_("contact person"),
        blank=True,
        null=True,
    )
    website = models.URLField(_("website"), blank=True, default="")

    # Member and permission groups
    group = models.ForeignKey(
        DjangoGroup,
        models.SET_NULL,
        verbose_name=_("group"),
        blank=True,
        null=True,
        related_name="member_orgunits",
    )
    admin_group = models.ForeignKey(
        DjangoGroup,
        models.SET_NULL,
        verbose_name=_("admin group"),
        blank=True,
        null=True,
        related_name="admin_orgunits",
    )

    # Hierarchical :-)
    parent = TreeForeignKey(
        "self",
        models.SET_NULL,
        verbose_name=_("parent"),
        null=True,
        blank=True,
        related_name="children",
        db_index=True,
    )

    @property
    def users(self):
        order_fields = ["first_name", "last_name", "username"]
        admins = self.admin_group.user_set.order_by(*order_fields)
        users = self.group.user_set.order_by(*order_fields).exclude(pk__in=admins)
        return chain(admins, users)

    def add_user(self, user_obj, changed_by):
        self.group.user_set.add(user_obj)
        self.log(f"Added user {user_obj}", changed_by)
        user_obj.log(f"Added to {self} OrgUnit", changed_by)
        user_obj.update_volunteer_status()

    def add_admin(self, user_obj, changed_by):
        self.group.user_set.add(user_obj)
        self.admin_group.user_set.add(user_obj)
        self.log(f"Added admin {user_obj}", changed_by)
        user_obj.log(f"Added to {self} OrgUnit as admin", changed_by)
        user_obj.update_volunteer_status()

    def remove_user(self, user_obj, changed_by):
        self.group.user_set.remove(user_obj)
        self.admin_group.user_set.remove(user_obj)
        self.log(f"Removed user {user_obj}", changed_by)
        user_obj.log(f"Removed from {self} OrgUnit", changed_by)
        user_obj.update_volunteer_status()

    def remove_admin(self, user_obj, changed_by):
        if self.admin_group == self.group:
            return
        self.admin_group.user_set.remove(user_obj)
        self.log(f"Removed {user_obj} from admin", changed_by)
        user_obj.log(f"No longer admin in {self} OrgUnit", changed_by)

    def log(self, message, changed_by):
        OrgUnitLogMessage(org_unit=self, message=message, changed_by=changed_by).save()

    def __str__(self):
        if self.short_name:
            return f"{self.name} ({self.short_name})"

        return f"{self.name}"

    class MPTTMeta:
        order_insertion_by = ["name"]

    class Meta:
        verbose_name = _("Org unit")
        verbose_name_plural = _("Org units")


class Order(BaseModel):
    """Simple order model which only supports one product per order"""

    BY_CARD = "card"
    BY_SMS = "sms"
    BY_APP = "app"
    BY_CASH_REGISTER = "cash_register"
    PAYMENT_METHOD_OTHER = "other"
    PAYMENT_METHODS = (
        (BY_APP, _("Mobile app")),
        (BY_SMS, _("SMS")),
        (BY_CARD, _("Credit card")),
        (BY_CASH_REGISTER, _("Cash register")),
        (PAYMENT_METHOD_OTHER, _("Other")),
    )

    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    price_nok = models.IntegerField(help_text=_("Price in øre"))

    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.SET_NULL, related_name="orders", null=True, blank=True)
    product = models.OneToOneField("dusken.Membership", models.SET_NULL, null=True, blank=True)

    # Payment
    payment_method = models.CharField(max_length=254, choices=PAYMENT_METHODS, default=PAYMENT_METHOD_OTHER)
    transaction_id = models.CharField(  # noqa: DJ001
        max_length=254,
        null=True,
        blank=True,
        help_text=_("Stripe charge ID, Kassa event ID, SMS event ID or App event ID"),
    )

    phone_number = PhoneNumberField(blank=True, null=True)
    member_card = models.ForeignKey("dusken.MemberCard", models.SET_NULL, related_name="orders", null=True, blank=True)

    objects = OrderManager()

    def price_nok_kr(self):
        return int(self.price_nok / 100)

    def __str__(self):
        return f"{self.uuid}"

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        default_permissions = ("add", "change", "delete", "view")


class PlaceOfStudy(BaseModel):
    name = models.CharField(_("name"), max_length=255)
    short_name = models.CharField(_("short name"), max_length=16, default="", blank=True)

    def __str__(self):
        if not self.short_name:
            return self.name

        return f"{self.name} ({self.short_name})"

    class Meta:
        verbose_name = _("Place of study")
        verbose_name_plural = _("Places of study")


class UserLogMessage(BaseModel):
    user = models.ForeignKey("dusken.DuskenUser", models.CASCADE, related_name="log_messages")
    message = models.CharField(max_length=500)
    changed_by = models.ForeignKey(
        "dusken.DuskenUser",
        on_delete=models.SET_NULL,
        related_name="user_changes",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message} ({self.user_id})"

    class Meta:
        verbose_name = _("User log message")
        verbose_name_plural = _("User log messages")


class OrgUnitLogMessage(BaseModel):
    org_unit = models.ForeignKey("dusken.OrgUnit", models.CASCADE, related_name="log_messages")
    message = models.CharField(max_length=500)
    changed_by = models.ForeignKey(
        "dusken.DuskenUser",
        on_delete=models.SET_NULL,
        related_name="org_unit_changes",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message} ({self.org_unit_id})"

    class Meta:
        verbose_name = _("Org unit log message")
        verbose_name_plural = _("Org unit log messages")
