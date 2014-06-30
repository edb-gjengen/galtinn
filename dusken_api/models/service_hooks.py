from base_model import AbstractBaseModel
from django.db import models

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

