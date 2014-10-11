import django

from base_model import AbstractBaseModel
from django.db import models


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
    members = models.ManyToManyField('dusken_api.User', null=True, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')
    groups = models.ManyToManyField(django.contrib.auth.models.Group, null=True, blank=True)  # permissions # TODO remove this?


