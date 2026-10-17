import logging

from django import forms
from django.contrib.auth.forms import SetPasswordForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.connection import ConnectionDoesNotExist
from django.utils.translation import gettext_lazy as _

from dusken.apps.neuf_auth.models import AuthProfile
from dusken.apps.neuf_auth.validators import USERNAME_HELP_TEXT, validate_new_username
from dusken.apps.neuf_ldap.utils import ldap_username_exists, set_ldap_password

logger = logging.getLogger(__name__)


class NeufSetPasswordForm(SetPasswordForm):
    """Saves a hashed user password in each of the following places:
    - Local DB on DuskenUser
    - Local DB on AuthProfile as LDAP salted SHA1
    - LDAP (if user exists in LDAP)
    """

    def save(self, commit=True):
        self.user = super().save(commit=commit)

        username = self.user.username
        raw_password = self.cleaned_data["new_password1"]

        try:
            if ldap_username_exists(username):
                set_ldap_password(username, raw_password)
            self.user.set_ldap_hash(raw_password)
        except ConnectionDoesNotExist:
            logger.warning(f"Skipping password update of user {username}, since the LDAP connection does not exist")

        return self.user


class SetUsernameForm(forms.Form):
    username = forms.CharField(
        label=_("Username"),
        initial="",
        help_text=USERNAME_HELP_TEXT,
    )

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop("instance")
        # TODO: If there is no authprofile, then show password field
        super().__init__(*args, **kwargs)

    def clean(self):
        if self.instance.has_set_username:
            raise ValidationError(_("Username can only be set once"))

    def save(self):
        self.instance.username = self.cleaned_data["username"]

        ap, _ = AuthProfile.objects.get_or_create(user=self.instance)
        ap.username_updated = timezone.now()
        ap.save()

        return self.instance.save()

    def clean_username(self):
        username = self.cleaned_data["username"].lower()
        validate_new_username(username, self.instance)
        return username
