from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from dusken.models import DuskenUser
from phonenumber_field.formfields import PhoneNumberField


class DuskenUserForm(forms.ModelForm):
    class Meta:
        model = DuskenUser
        fields = ['first_name', 'last_name', 'email', 'phone_number']


class MembershipActivateForm(forms.Form):
    card_number = forms.IntegerField(widget=forms.NumberInput(attrs={'autofocus': True}))
    phone_number = PhoneNumberField(widget=forms.TextInput(attrs={'type': 'tel'}))
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()
    user_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)


class MembershipRenewForm(forms.Form):
    email = forms.EmailField(widget=forms.HiddenInput())


class UserEmailValidateForm(forms.Form):
    email_key = forms.CharField(required=True)
    slug = forms.CharField(required=True)

    def clean(self):
        user_uuid = self.cleaned_data.get('slug')
        try:
            user = DuskenUser.objects.get(uuid=user_uuid)
        except DuskenUser.DoesNotExist:
            raise ValidationError(_('User does not exist'))

        if user.email_key != self.cleaned_data.get('email_key'):
            raise ValidationError(_('Invalid email key for user'))

        if user.email_is_confirmed:
            raise ValidationError(_('Email already confirmed'))

        self.cleaned_data['user'] = user
