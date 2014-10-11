from base_model import AbstractBaseModel
from django.db import models


class Payment(AbstractBaseModel):
    def __unicode__(self):
        return "{},- via {}".format(self.value, self.payment_type.name)

    # Note: More like tokens?
    payment_type = models.ForeignKey('dusken_api.PaymentType')
    value = models.IntegerField()
    transaction_id = models.IntegerField(unique=True, null=True, blank=True)

    class Meta:
        app_label = "dusken_api"

   
class PaymentType(models.Model):
    def __unicode__(self):
        return u"{}".format(self.name)

    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "dusken_api"


