from django import forms
from django.contrib.auth.forms import SetPasswordForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from apps.neuf_auth.models import AuthProfile
from apps.neuf_auth.validators import LDAPUsernameValidator, blacklist_validator
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


class SetUsernameForm(forms.Form):
    username = forms.CharField(
        label=_('Username'),
        initial='',
        help_text=_('Between 3 and 32 characters. Small letters, digits and - or _ only. It must start with a letter.'),
        validators=[LDAPUsernameValidator, blacklist_validator])

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance')
        super().__init__(*args, **kwargs)

    def clean(self):
        ap = AuthProfile.objects.filter(user=self.instance).first()
        if ap is not None and ap.username_updated is not None:
            raise ValidationError(_('Username can only be set once'))

    def save(self):
        self.instance.username = self.cleaned_data['username']

        ap, created = AuthProfile.objects.get_or_create(user=self.instance)
        ap.username_updated = timezone.now()
        ap.save()

        return self.instance.save()

    def clean_username(self):
        username = self.cleaned_data['username'].lower()
        if self.instance.__class__.objects.exclude(pk=self.instance.pk).filter(username__iexact=username).exists():
            raise ValidationError(_('Username {value} is taken', params={'value': username}))

        if ldap_username_exists(username):
            raise ValidationError(_('Username {value} is taken', params={'value': username}))

        return username
