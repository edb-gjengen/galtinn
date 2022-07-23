from django.apps import AppConfig


class MailchimpConfig(AppConfig):
    name = "apps.mailchimp"
    label = "mailchimp"

    def ready(self):
        import apps.mailchimp.signals  # noqa
