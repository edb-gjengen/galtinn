from django.contrib.auth.forms import SetPasswordForm
from django.core.validators import MinLengthValidator

from apps.neuf_auth.models import AuthProfile
from apps.neuf_ldap.utils import set_ldap_password, ldap_username_exists, ldap_create
from apps.neuf_auth.validators import validate_password


class NeufAuthSetPasswordForm(SetPasswordForm):
    """ Saves a user password in each of the following services:
        - Local db (in dusken_duskenuser and neuf_auth_authprofile)
        - LDAP
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
        ap.ldap_password = ldap_create(raw_password)
        ap.save()

    def clean_new_password1(self):
        raw_password = self.cleaned_data.get('new_password1')

        MinLengthValidator(8)(raw_password)
        validate_password(raw_password)

        return raw_password
