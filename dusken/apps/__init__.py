# Django reads an app's config from <app>.apps, and for dusken that is this package, which shadows
# a dusken/apps.py module, so the config lives here.
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DuskenAppConfig(AppConfig):
    name = "dusken"
    verbose_name = _("Dusken")

    def ready(self):
        import dusken.signals  # noqa: F401, PLC0415
