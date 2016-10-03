# coding: utf-8
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import Group as DjangoGroup
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from jsonfield import JSONField
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel
from phonenumber_field.modelfields import PhoneNumberField


class AbstractBaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class DuskenUser(AbstractBaseModel, AbstractUser):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    phone_number = PhoneNumberField(blank=True)
    phone_number_validated = models.BooleanField(default=False)
    date_of_birth = models.DateField(null=True, blank=True)

    street_address = models.CharField(max_length=255, null=True, blank=True)
    street_address_two = models.CharField(max_length=255, null=True, blank=True)
    postal_code = models.CharField(max_length=10, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    country = CountryField(null=True, blank=True)

    place_of_study = models.ManyToManyField('dusken.PlaceOfStudy', blank=True)
    legacy_id = models.IntegerField(null=True, blank=True)

    stripe_customer_id = models.CharField(max_length=254, null=True, blank=True)

    def get_absolute_url(self):
        return reverse('user-detail', kwargs={'slug': self.uuid})

    def has_valid_membership(self):
        memberships = self.memberships.filter(end_date__gt=timezone.now())
        for m in memberships:
            if m.is_valid():
                return True

        return False

    def get_last_valid_membership(self):
        return self.memberships.filter(end_date__gt=timezone.now()).order_by('-start_date').first()

    def __str__(self):
        if len(self.first_name) + len(self.last_name) > 0:
            return '{first} {last} ({username})'.format(
                first=self.first_name,
                last=self.last_name,
                username=self.username)
        return "{username}".format(username=self.username)


class Membership(AbstractBaseModel):
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    membership_type = models.ForeignKey('dusken.MembershipType')
    user = models.ForeignKey('dusken.DuskenUser', null=True, blank=True, related_name='memberships')
    # from django.contrib.postgres.fields import JSONField
    extra_data = JSONField(blank=True, default=dict)

    def expires(self):
        return self.end_date

    def is_valid(self):
        return self.order is not None

    def __str__(self):
        end_date = self.end_date if self.end_date is not None else 'N/A'
        return "{} - {} ({})".format(self.start_date, end_date, self.user_id)


class MembershipType(AbstractBaseModel):
    name = models.CharField(max_length=254)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    does_not_expire = models.BooleanField(default=False)
    price = models.IntegerField(default=0, help_text=_('Price in øre'))
    is_default = models.BooleanField(default=False)
    duration = models.DurationField(default=timedelta(days=365), null=True, blank=True)

    def __str__(self):
        return "{}".format(self.name)

    def save(self, **kwargs):
        # Only one can be default
        if self.is_default:
            MembershipType.objects.all().update(is_default=False)
        super().save(**kwargs)

    @staticmethod
    def get_default():
        try:
            return MembershipType.objects.get(is_default=True)
        except MembershipType.DoesNotExist:
            raise ImproperlyConfigured('Error: At least one MembershipType must have is_default set')
        except MembershipType.MultipleObjectsReturned:
            raise ImproperlyConfigured('Error: Only one MembershipType can have is_default set')


class MemberCard(AbstractBaseModel):
    card_number = models.IntegerField(unique=True)
    registered_datetime = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    user = models.ForeignKey('dusken.DuskenUser', null=True, blank=True, related_name='membercards')

    def __str__(self):
        return "{}".format(self.card_number)


class GroupProfile(AbstractBaseModel):
    """
    django.contrib.auth.model.Group extended with additional fields.
    """

    posix_name = models.CharField(max_length=255, unique=True)
    group = models.OneToOneField(DjangoGroup)

    def __str__(self):
        return "{}".format(self.posix_name)


class OrgUnit(MPTTModel, AbstractBaseModel):
    """
    Association, comittee or similar
    """

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255, blank=True)
    short_name = models.CharField(max_length=128, blank=True)
    is_active = models.BooleanField(default=True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    groups = models.ManyToManyField(DjangoGroup, blank=True, related_name='member_orgunits')
    admin_groups = models.ManyToManyField(DjangoGroup, blank=True, related_name='admin_orgunits')

    def __str__(self):
        if self.short_name:
            return "{} ({})".format(self.name, self.short_name)

        return "{}".format(self.name)

    class MPTTMeta:
        order_insertion_by = ['name']


class Order(AbstractBaseModel):
    """ Simple order model which only supports one product per order """
    BY_CARD = 'card'
    BY_SMS = 'sms'
    BY_APP = 'app'
    PAYMENT_METHOD_OTHER = 'other'
    PAYMENT_METHODS = (
        (BY_APP, _('Mobile app')),
        (BY_SMS, _('SMS')),
        (BY_CARD, _('Credit card')),
        (PAYMENT_METHOD_OTHER, _('Other')),
    )

    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    price_nok = models.IntegerField(help_text=_('In øre'))

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='orders')
    product = models.OneToOneField('dusken.Membership', null=True, blank=True)

    # Payment
    payment_method = models.CharField(max_length=254, choices=PAYMENT_METHODS, default=PAYMENT_METHOD_OTHER)
    transaction_id = models.CharField(
        max_length=254,
        null=True,
        blank=True,
        help_text=_('Stripe charge ID, Kassa event ID, SMS event ID or App event ID')
    )

    def price_nok_kr(self):
        return int(self.price_nok / 100)

    def __str__(self):
        return "{}".format(self.uuid)


class PlaceOfStudy(AbstractBaseModel):
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=16)

    def __str__(self):
        return '{} - {}'.format(self.short_name, self.name)
