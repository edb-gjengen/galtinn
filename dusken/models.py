# coding: utf-8
from __future__ import unicode_literals
import datetime

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import Group as DjangoGroup
from django.utils.encoding import python_2_unicode_compatible
from django_countries.fields import CountryField
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel


class AbstractBaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


@python_2_unicode_compatible
class DuskenUser(AbstractBaseModel, AbstractUser):
    phone_number = models.CharField(max_length=30, null=True, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    legacy_id = models.IntegerField(null=True, blank=True)
    place_of_study = models.ManyToManyField('dusken.PlaceOfStudy', blank=True)

    street_address = models.CharField(max_length=255, null=True, blank=True)
    street_address_two = models.CharField(max_length=255, null=True, blank=True)
    postal_code = models.CharField(max_length=10, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    country = CountryField(null=True, blank=True)

    def has_valid_membership(self):
        memberships = self.membership_set.filter(end_date__gt=datetime.datetime.now())
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


@python_2_unicode_compatible
class Membership(AbstractBaseModel):
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    membership_type = models.ForeignKey('dusken.MembershipType')
    payment = models.ForeignKey('dusken.Payment', null=True, blank=True)
    user = models.ForeignKey('dusken.DuskenUser', null=True, blank=True)

    def expires(self):
        return self.end_date

    def is_valid(self):
        return self.payment is not None

    def __str__(self):
        return "{}: {} - {}".format(self.member, self.start_date, self.end_date)


@python_2_unicode_compatible
class MembershipType(AbstractBaseModel):
    name = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    does_not_expire = models.BooleanField(default=False)

    def __str__(self):
        return "{}".format(self.name)


@python_2_unicode_compatible
class GroupProfile(AbstractBaseModel):
    """
    django.contrib.auth.model.Group extended with additional fields.
    """

    posix_name = models.CharField(max_length=255, unique=True)
    group = models.OneToOneField(DjangoGroup)

    def __str__(self):
        return "{}".format(self.posix_name)


@python_2_unicode_compatible
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


@python_2_unicode_compatible
class Payment(AbstractBaseModel):
    # Note: More like tokens?
    payment_type = models.ForeignKey('dusken.PaymentType')
    value = models.IntegerField()
    transaction_id = models.IntegerField(unique=True, null=True, blank=True)

    def __str__(self):
        return "{},- via {}".format(self.value, self.payment_type.name)


@python_2_unicode_compatible
class PaymentType(models.Model):
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return "{}".format(self.name)


@python_2_unicode_compatible
class PlaceOfStudy(AbstractBaseModel):
    from_date = models.DateField()
    institution = models.ForeignKey('dusken.Institution')

    def __str__(self):
        return "{institution}, {year}".format(institution=self.institution, year=self.from_date.year)


@python_2_unicode_compatible
class Institution(AbstractBaseModel):
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=16)

    def __str__(self):
        return '{} - {}'.format(self.short_name, self.name)
