import datetime

from django.contrib.auth.models import AbstractUser
from django.db import models
from base_model import AbstractBaseModel


class User(AbstractBaseModel, AbstractUser):
    def __unicode__(self):
        if len(self.first_name) + len(self.last_name) > 0:
            return u'{first} {last} ({username})'.format(
                first=self.first_name,
                last=self.last_name,
                username=self.username)
        return u"{username}".format(username=self.username)

    phone_number = models.CharField(max_length=30, null=True, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    legacy_id = models.IntegerField(null=True, blank=True)
    address = models.OneToOneField('dusken_api.Address', null=True, blank=True)
    place_of_study = models.ManyToManyField('dusken_api.PlaceOfStudy', null=True, blank=True)

    def owner(self):
        return self
    
    def has_valid_membership(self):
        # FIXME more than one membership?
        # FIXME membership_type?
        membership = self.membership_set.filter(end_date__gt=datetime.datetime.now())
        return len(membership) == 1 and membership[0].is_valid()

    class Meta:
        app_label = "dusken_api"


class UserMeta(AbstractBaseModel):
    key = models.CharField(max_length=255)
    value = models.TextField(blank=True)
    user = models.ForeignKey('dusken_api.User')

    class Meta:
        app_label = "dusken_api"


