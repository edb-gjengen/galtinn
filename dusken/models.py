# coding: utf-8
import uuid

from django.contrib.auth.models import AbstractUser
from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import Group as DjangoGroup
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from jsonfield import JSONField
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel


class AbstractBaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class DuskenUser(AbstractBaseModel, AbstractUser):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    phone_number = models.CharField(max_length=30, null=True, blank=True)
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
    payment = models.ForeignKey('dusken.Payment', null=True, blank=True)
    user = models.ForeignKey('dusken.DuskenUser', null=True, blank=True, related_name='memberships')
    # from django.contrib.postgres.fields import JSONField
    extra_data = JSONField(blank=True, default=dict)

    def expires(self):
        return self.end_date

    def is_valid(self):
        return self.payment is not None

    def __str__(self):
        return "{}: {} - {}".format(self.user, self.start_date, self.end_date)


class MembershipType(AbstractBaseModel):
    name = models.CharField(max_length=254)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    does_not_expire = models.BooleanField(default=False)
    price = models.IntegerField(default=0, help_text=_('Price in øre'))

    def __str__(self):
        return "{}".format(self.name)


class MemberCard(AbstractBaseModel):
    card_number = models.IntegerField()
    registered_datetime = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    user = models.ForeignKey('dusken.DuskenUser', null=True, blank=True, related_name='membercards')


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
    short_name = models.CharField(max_length=128, blank=True)
    is_active = models.BooleanField(default=True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    groups = models.ManyToManyField(DjangoGroup, blank=True)

    def __str__(self):
        if self.short_name:
            return "{} ({})".format(self.name, self.short_name)

        return "{}".format(self.name)

    class MPTTMeta:
        order_insertion_by = ['name']


class Payment(AbstractBaseModel):
    BY_CARD = 'card'
    BY_SMS = 'sms'
    BY_APP = 'app'
    PAYMENT_METHOD_OTHER = 'other'
    PAYMENT_METHODS = (
        (BY_APP, _('Mobile app')),
        (BY_SMS, _('SMS')),
        (BY_CARD, _('Credit card')),
        (PAYMENT_METHOD_OTHER, _('Other (cash register, bar, ...)')),
    )

    payment_method = models.CharField(max_length=254, choices=PAYMENT_METHODS, default=PAYMENT_METHOD_OTHER)
    value = models.IntegerField(help_text=_('In øre'))
    transaction_id = models.CharField(
        max_length=254,
        null=True,
        blank=True,
        help_text=_('Stripe charge ID, Kassa event ID, SMS event ID or App event ID')
    )

    def value_in_kr(self):
        return int(self.value / 100)

    def __str__(self):
        return "{} by {}".format(self.value_in_kr(), self.payment_method)


class PlaceOfStudy(AbstractBaseModel):
    from_date = models.DateField()
    institution = models.ForeignKey('dusken.Institution')

    def __str__(self):
        return "{institution}, {year}".format(institution=self.institution, year=self.from_date.year)


class Institution(AbstractBaseModel):
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=16)

    def __str__(self):
        return '{} - {}'.format(self.short_name, self.name)
