from django.apps import AppConfig


class DuskenAppConfig(AppConfig):
    name = 'dusken'

    def ready(self):
        import dusken.signals
