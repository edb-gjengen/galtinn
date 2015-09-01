from django.db import models
from dusken.models import AbstractBaseModel


class ServiceHook(AbstractBaseModel):
    """
    Events with callback_urls
    """

    event = models.CharField(max_length=255)
    user = models.ForeignKey('dusken.DuskenUser')
    is_active = models.BooleanField(default=True)
    callback_url = models.TextField()

    def __unicode__(self):
        return "{}".format(self.name)
