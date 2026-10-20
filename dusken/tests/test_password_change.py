from unittest.mock import patch

from django.contrib.auth.tokens import default_token_generator
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from dusken.apps.neuf_auth.models import AuthProfile
from dusken.models import DuskenUser

NEW = "a-new-Passw0rd-for-ola"

ldap_user_exists = patch("dusken.apps.neuf_auth.forms.ldap_username_exists", return_value=False)


@ldap_user_exists
class PasswordChangeTests(TestCase):
    def setUp(self):
        self.user = DuskenUser.objects.create_user("olanord", email="ola@example.com", password="mypassword")
        self.client.force_login(self.user)
        self.url = reverse("password_change")

    def post(self, old_password):
        return self.client.post(self.url, {"old_password": old_password, "new_password1": NEW, "new_password2": NEW})

    def test_requires_current_password(self, *_mocks):
        response = self.post("wrong-password")
        assert response.status_code == 200
        assert "old_password" in response.context["form"].errors
        self.user.refresh_from_db()
        assert self.user.check_password("mypassword")

    def test_changes_password_and_ldap_hash(self, *_mocks):
        response = self.post("mypassword")
        assert response.status_code == 302
        self.user.refresh_from_db()
        assert self.user.check_password(NEW)
        assert AuthProfile.objects.get(user=self.user).ldap_password


@ldap_user_exists
class PasswordResetTests(TestCase):
    def test_reset_needs_no_current_password(self, *_mocks):
        user = DuskenUser.objects.create_user("olanord", email="ola@example.com", password="mypassword")
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        # The first request swaps the token for a session and redirects to the set-password URL
        response = self.client.get(reverse("password_reset_confirm", args=[uidb64, token]))
        response = self.client.post(response.url, {"new_password1": NEW, "new_password2": NEW})
        assert response.status_code == 302
        user.refresh_from_db()
        assert user.check_password(NEW)
        assert AuthProfile.objects.get(user=user).ldap_password
