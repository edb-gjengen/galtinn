from django.core import mail
from django.test import TestCase
from django.utils import translation
from django_ox.testing import run_tasks

from dusken.models import DuskenUser


class NewUserTests(TestCase):
    def test_gets_validation_email(self):
        user = DuskenUser.objects.create_user("olanord", email="ola@example.com", password="mypassword")
        run_tasks(raise_failures=True)

        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["ola@example.com"]
        assert f"/users/{user.uuid}/validate_email/{user.email_key}" in mail.outbox[0].body

    def test_validation_email_asks_nothing(self):
        # A question makes Gmail suggest replies such as "Yes, I confirm!"
        for language in ("en", "nb"):
            mail.outbox = []
            with translation.override(language):
                user = DuskenUser.objects.create_user(f"ola{language}", email=f"ola{language}@example.com")
            run_tasks(raise_failures=True)

            message = mail.outbox[0]
            html, _mimetype = message.alternatives[0]
            assert "?" not in message.body
            assert "?" not in html
            assert f"/validate_email/{user.email_key}" in message.body
            assert f"/validate_email/{user.email_key}" in html
