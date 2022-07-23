from django.apps import AppConfig


class MailchimpConfig(AppConfig):
    name = "dusken.apps.mailchimp"
    label = "mailchimp"

    def ready(self):
        import dusken.apps.mailchimp.signals  # noqa
