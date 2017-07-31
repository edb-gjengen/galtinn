from django.contrib.auth.forms import SetPasswordForm

from apps.neuf_auth.models import AuthProfile
from apps.neuf_ldap.utils import set_ldap_password, ldap_username_exists, ldap_create_password


class NeufSetPasswordForm(SetPasswordForm):
    """ Saves a hashed user password in each of the following places:
        - Local DB on DuskenUser
        - Local DB on AuthProfile as LDAP salted SHA1
        - LDAP (if user exists in LDAP)
    """

    def save(self, commit=True):
        self.user = super().save(commit=commit)

        username = self.user.username
        raw_password = self.cleaned_data['new_password1']

        if ldap_username_exists(username):
            set_ldap_password(username, raw_password)

        self._set_ldap_hash(raw_password)

        return self.user

    def _set_ldap_hash(self, raw_password):
        ap, _ = AuthProfile.objects.get_or_create(user=self.user)
        # FIXME: Switch to {CRYPT} and salted SHA-512
        ap.ldap_password = ldap_create_password(raw_password)
        ap.save()
