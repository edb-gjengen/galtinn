from django.core import mail
from django.test import TestCase
from django_ox.testing import run_tasks

from dusken.models import DuskenUser


class NewUserTests(TestCase):
    def test_gets_validation_email(self):
        user = DuskenUser.objects.create_user("olanord", email="ola@example.com", password="mypassword")
        run_tasks(raise_failures=True)

        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["ola@example.com"]
        assert f"/users/{user.uuid}/validate_email/{user.email_key}" in mail.outbox[0].body
