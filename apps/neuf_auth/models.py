from django.db import models

from apps.common.mixins import BaseModel


class AuthProfile(BaseModel):
    """ Used for syncing authentication with internal systems """
    user = models.OneToOneField('dusken.DuskenUser')
    ldap_password = models.CharField(max_length=254, blank=True, default='')
    username_updated = models.DateTimeField(default=None, blank=True, null=True)
