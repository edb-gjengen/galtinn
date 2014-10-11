from django.apps import AppConfig


class DuskenAppConfig(AppConfig):
    name = 'dusken_api'

    def ready(self):
        import dusken_api.signals