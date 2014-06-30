from base_model import AbstractBaseModel
from django.db import models

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


