from django.db import models
from django.utils.translation import gettext_lazy as _

from dusken.apps.common.mixins import BaseModel


class UserLogMessage(BaseModel):
    user = models.ForeignKey("dusken.DuskenUser", models.CASCADE, related_name="log_messages")
    message = models.CharField(max_length=500)
    changed_by = models.ForeignKey(
        "dusken.DuskenUser",
        on_delete=models.SET_NULL,
        related_name="user_changes",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message} ({self.user_id})"

    class Meta:
        verbose_name = _("User log message")
        verbose_name_plural = _("User log messages")


class OrgUnitLogMessage(BaseModel):
    org_unit = models.ForeignKey("dusken.OrgUnit", models.CASCADE, related_name="log_messages")
    message = models.CharField(max_length=500)
    changed_by = models.ForeignKey(
        "dusken.DuskenUser",
        on_delete=models.SET_NULL,
        related_name="org_unit_changes",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message} ({self.org_unit_id})"

    class Meta:
        verbose_name = _("Org unit log message")
        verbose_name_plural = _("Org unit log messages")
