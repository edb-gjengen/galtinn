import django
import datetime

from base_model import AbstractBaseModel
from django.db import models

   
class Membership(AbstractBaseModel):
    def __unicode__(self):
        return u"{0}: {1} - {2}".format(
            self.member,
            self.start_date,
            self.end_date)

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    membership_type = models.ForeignKey('dusken_api.MembershipType')
    payment = models.ForeignKey('dusken_api.Payment', unique=True, null=True, blank=True)
    member = models.ForeignKey('dusken_api.Member')

    def expires(self):
        return self.end_date

    def is_valid(self):
        return self.payment is not None

    def owner(self):
        return self.member

    class Meta:
        app_label = "dusken_api"

class MembershipType(AbstractBaseModel):
    def __unicode__(self):
        return u"{}".format(self.name)

    name = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    does_not_expire = models.BooleanField(default=False)

    class Meta:
        app_label = "dusken_api"

class PaymentType(models.Model):
    def __unicode__(self):
        return u"{}".format(self.name)

    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "dusken_api"

class Payment(AbstractBaseModel):
    def __unicode__(self):
        return "{},- via {}".format(self.value, self.payment_type.name)

    # Note: More like tokens?
    payment_type = models.ForeignKey('dusken_api.PaymentType')
    value = models.IntegerField()
    transaction_id = models.IntegerField(unique=True, null=True, blank=True)

    class Meta:
        app_label = "dusken_api"

class Address(AbstractBaseModel):
    class Meta:
        verbose_name_plural = "Addresses"
        app_label = "dusken_api"

    def __unicode__(self):
        return u"{street}, {code} {city}, {country}".format(
            street=self.street_address,
            code=self.postal_code,
            city=self.city,
            country=self.country)

    street_address = models.CharField(max_length=255)
    street_address_two = models.CharField(max_length=255, null=True, blank=True)
    postal_code = models.CharField(max_length=10)
    city = models.CharField(max_length=100)
    country = models.ForeignKey('dusken_api.Country', null=True, blank=True)

    @property
    def full(self):
        return self.__unicode__()

class Country(AbstractBaseModel):
    class Meta:
        verbose_name_plural = "Countries"
        app_label = "dusken_api"

    def __unicode__(self):
        return self.name

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=3, unique=True) #ISO 3166-1 alpha 2


class PlaceOfStudy(AbstractBaseModel):
    class Meta:
        app_label = "dusken_api"

    def __unicode__(self):
        return u"{institution}, {year}".format(
            institution=self.institution,
            year=self.from_date.year)

    from_date = models.DateField()
    institution = models.ForeignKey('dusken_api.Institution')


class Institution(AbstractBaseModel):
    class Meta:
        app_label = "dusken_api"

    def __unicode__(self):
        return u'%s - %s' % (self.short_name, self.name)

    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=16)

class MemberMeta(AbstractBaseModel):
    class Meta:
        app_label = "dusken_api"

    key = models.CharField(max_length=255)
    value = models.TextField(blank=True)
    member = models.ForeignKey('dusken_api.Member')

class GroupProfile(AbstractBaseModel):
    """
    django.contrib.auth.model.Group extended with additional fields.
    """
    class Meta:
        app_label = "dusken_api"

    def __unicode__(self):
        return u"{}".format(self.posix_name)

    posix_name = models.CharField(max_length=255, unique=True)
    group = models.OneToOneField(django.contrib.auth.models.Group)

class OrgUnit(AbstractBaseModel):
    """
    Associations, comittee or similar
    """
    class Meta:
        app_label = "dusken_api"

    def __unicode__(self):
        return u"{}".format(self.name)

    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    members = models.ManyToManyField('dusken_api.Member', null=True, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')
    groups = models.ManyToManyField(django.contrib.auth.models.Group, null=True, blank=True) # permissions # TODO remove this?

class ServiceHook(AbstractBaseModel):
    """
    Events with callback_urls
    """
    class Meta:
        app_label = "dusken_api"

    def __unicode__(self):
        return u"{}".format(self.name)

    event = models.CharField(max_length=255)
    member = models.ForeignKey('dusken_api.Member')
    is_active = models.BooleanField(default=True)
    callback_url = models.TextField()


