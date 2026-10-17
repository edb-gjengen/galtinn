from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase

from dusken.admin import DuskenUserChangeForm, DuskenUserCreationForm
from dusken.apps.neuf_auth.forms import SetUsernameForm
from dusken.apps.neuf_auth.validators import LDAPUsernameValidator, blacklist_validator
from dusken.models import DuskenUser


@pytest.mark.parametrize("username", ["abc", "jonas", "jonas2", "a" * 32])
def test_valid_usernames(username):
    LDAPUsernameValidator(username)


@pytest.mark.parametrize(
    "username",
    ["ab", "a" * 33, "jo_nas", "jo-nas", "_jonas", "Jonas", "2jonas", "jonas\n", "jonås", "jo nas"],
)
def test_invalid_usernames(username):
    with pytest.raises(ValidationError):
        LDAPUsernameValidator(username)


@pytest.mark.parametrize("username", ["root", "admin", "sshd", "daemon", "postgres"])
def test_blacklisted_usernames(username):
    with pytest.raises(ValidationError):
        blacklist_validator(username)


ldap_group_exists = patch("dusken.apps.neuf_auth.validators.ldap_user_group_exists", return_value=False)
ldap_user_exists = patch("dusken.apps.neuf_auth.validators.ldap_username_exists", return_value=False)


@ldap_user_exists
@ldap_group_exists
class SetUsernameFormTests(TestCase):
    def setUp(self):
        self.user = DuskenUser.objects.create_user("olano1234", email="ola@example.com")

    def form(self, username):
        return SetUsernameForm({"username": username}, instance=self.user)

    def test_lowercases(self, *_mocks):
        form = self.form("OlaNord")
        assert form.is_valid(), form.errors
        assert form.cleaned_data["username"] == "olanord"

    def test_rejects_old_characters(self, *_mocks):
        assert not self.form("ola_nord").is_valid()
        assert not self.form("ola-nord").is_valid()

    def test_rejects_taken(self, *_mocks):
        DuskenUser.objects.create_user("olanord", email="other@example.com")
        form = self.form("OLANORD")
        assert not form.is_valid()
        assert form.errors["username"] == ["Username olanord is taken"]

    def test_rejects_ldap_group(self, group_exists, *_mocks):
        group_exists.side_effect = lambda name: name == "styret"
        assert not self.form("styret").is_valid()
        assert self.form("styre").is_valid()


@ldap_user_exists
@ldap_group_exists
class AdminUsernameTests(TestCase):
    def form(self, user, username):
        unbound = DuskenUserChangeForm(instance=user)
        data = {name: unbound[name].value() for name in unbound.fields if unbound[name].value() is not None}
        data["username"] = username
        return DuskenUserChangeForm(data, instance=user)

    def test_keeps_old_name(self, *_mocks):
        user = DuskenUser.objects.create_user("ola_nord", email="ola@example.com")
        form = self.form(user, "ola_nord")
        assert form.is_valid(), form.errors

    def test_new_name_follows_rules(self, *_mocks):
        user = DuskenUser.objects.create_user("ola_nord", email="ola@example.com")
        assert not self.form(user, "kari_nord").is_valid()
        assert not self.form(user, "root").is_valid()
        form = self.form(user, "KariNord")
        assert form.is_valid(), form.errors
        assert form.cleaned_data["username"] == "karinord"

    def test_rename_to_ldap_group(self, group_exists, *_mocks):
        group_exists.side_effect = lambda name: name == "styret"
        user = DuskenUser.objects.create_user("olanord", email="ola@example.com")
        assert not self.form(user, "styret").is_valid()

    def test_add_user(self, *_mocks):
        DuskenUser.objects.create_user("karinord", email="kari@example.com")

        def form(username):
            data = {"username": username, "email": "ola@example.com", "usable_password": "false"}
            return DuskenUserCreationForm(data)

        assert not form("ola_nord").is_valid()
        assert not form("root").is_valid()
        assert not form("KariNord").is_valid()
        valid = form("OlaNord")
        assert valid.is_valid(), valid.errors
        assert valid.save().username == "olanord"


@pytest.mark.django_db
def test_admin_add_page_renders(client):
    client.force_login(DuskenUser.objects.create_superuser("root", "root@example.com", "hunter2hunter2"))
    response = client.get("/admin/dusken/duskenuser/add/")
    assert response.status_code == 200
    assert b'name="email"' in response.content
