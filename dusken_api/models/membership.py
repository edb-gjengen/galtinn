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
    user = models.ForeignKey('dusken_api.User')

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


