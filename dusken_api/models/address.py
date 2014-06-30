from base_model import AbstractBaseModel
from django.db import models

class Address(AbstractBaseModel):
    street_address = models.CharField(max_length=255)
    street_address_two = models.CharField(max_length=255, null=True, blank=True)
    postal_code = models.CharField(max_length=10)
    city = models.CharField(max_length=100)
    country = models.ForeignKey('dusken_api.Country', null=True, blank=True)

    class Meta:
        verbose_name_plural = "Addresses"
        app_label = "dusken_api"

    @property
    def full(self):
        return self.__unicode__()
    
    def __unicode__(self):
        return u"{street}, {code} {city}, {country}".format(
            street=self.street_address,
            code=self.postal_code,
            city=self.city,
            country=self.country)


class Country(AbstractBaseModel):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=3, unique=True) #ISO 3166-1 alpha 2

    class Meta:
        verbose_name_plural = "Countries"
        app_label = "dusken_api"

    def __unicode__(self):
        return self.name



