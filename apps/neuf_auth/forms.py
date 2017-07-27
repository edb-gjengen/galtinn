from django.contrib.auth.forms import SetPasswordForm
from django.core.validators import MinLengthValidator


from apps.neuf_ldap.utils import set_ldap_password, ldap_username_exists
from apps.neuf_auth.validators import validate_password


class NeufAuthSetPasswordForm(SetPasswordForm):
    """ Saves a user password in each of the following services:
        - Local db
        - LDAP
    """

    def save(self, commit=True):
        self.user = super().save(commit=commit)

        username = self.user.username
        password = self.cleaned_data['new_password1']

        if ldap_username_exists(username):
            set_ldap_password(username, password)

        return self.user  # Local Django User

    def clean_new_password1(self):
        raw_password = self.cleaned_data.get('new_password1')

        MinLengthValidator(8)(raw_password)
        validate_password(raw_password)

        return raw_password
