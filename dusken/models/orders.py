import logging
import uuid
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from dusken.apps.common.mixins import BaseModel
from dusken.managers import MembershipManager, OrderManager

logger = logging.getLogger(__name__)


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

    @staticmethod
    def start_date_for_user(user):
        if user and user.is_member:
            return user.last_membership.end_date + timezone.timedelta(days=1)
        return timezone.now().date()

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
    stripe_price_id = models.CharField(max_length=254, blank=True, default="")

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

        if self.expiry_type == self.EXPIRY_END_OF_YEAR:
            return now.date().replace(year=now.year + 1, month=1, day=1)

        if self.expiry_type == self.EXPIRY_NEVER:
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
        if user is None and order is None:
            raise ValueError("Cannot register without neither user nor order")
        if user or (order and not self.registered):
            self.registered = timezone.now()
            self.is_active = True
        if user:
            user.member_cards.filter(is_active=True).update(is_active=False)
            self.user = user
        if order:
            if order.member_card:
                raise ValueError("Member card already registered to order")
            order.member_card = self
            order.save()
        self.save()

    def __str__(self):
        return f"{self.card_number}"

    class Meta:
        verbose_name = _("Member card")
        verbose_name_plural = _("Member cards")
        default_permissions = ("add", "change", "delete", "view")


class Order(BaseModel):
    """Simple order model which only supports one product/orderline per order"""

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

    class PaymentSource(models.TextChoices):
        APP = "app"
        WEB = "web"

    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    price_nok = models.IntegerField(help_text=_("Price in øre"))

    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.SET_NULL, related_name="orders", null=True, blank=True)
    product = models.OneToOneField("dusken.Membership", models.SET_NULL, null=True, blank=True)

    # Payment
    payment_method = models.CharField(max_length=254, choices=PAYMENT_METHODS, default=PAYMENT_METHOD_OTHER)
    payment_source = models.CharField(max_length=3, choices=PaymentSource.choices, default=PaymentSource.WEB)
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


class StripePayment(BaseModel):
    """
    Mirrors a stripe checkout session or payment intent with a bit of extra metadata (user, membership_type)
    Ref: https://docs.stripe.com/api/checkout/sessions/object
    """

    class Status(models.TextChoices):
        OPEN = "open"
        COMPLETE = "complete"
        EXPIRED = "expired"

    class StripeModel(models.TextChoices):
        CHECKOUT_SESSION = "checkout_session"
        PAYMENT_INTENT = "payment_intent"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE, related_name="stripe_payments")
    stripe_id = models.CharField(max_length=500, db_index=True)
    stripe_model = models.CharField(max_length=16, choices=StripeModel.choices, default=StripeModel.CHECKOUT_SESSION)
    membership_type = models.ForeignKey("dusken.MembershipType", models.CASCADE)
    source = models.CharField(max_length=3, choices=Order.PaymentSource.choices, default=Order.PaymentSource.WEB)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.OPEN)
