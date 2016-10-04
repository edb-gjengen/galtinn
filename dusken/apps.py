from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class DuskenAppConfig(AppConfig):
    name = 'dusken'
    verbose_name = _('Dusken')

    def ready(self):
        import dusken.signals
