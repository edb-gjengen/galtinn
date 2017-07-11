from django import forms
from django.core.exceptions import ValidationError
from django.forms import fields
from django.utils.translation import ugettext as _

from dusken.models import DuskenUser
from phonenumber_field.formfields import PhoneNumberField
from captcha.fields import ReCaptchaField


from dusken.utils import email_exist, phone_number_exist


class DuskenUserForm(forms.ModelForm):
    first_name = fields.CharField()
    last_name = fields.CharField()
    email = fields.EmailField()
    phone_number = PhoneNumberField()
    captcha = ReCaptchaField()

    def clean_email(self):
        email = self.cleaned_data['email']
        if email_exist(email):
            raise forms.ValidationError(_('Email already in use'))
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']
        if phone_number_exist(phone_number):
            raise forms.ValidationError(_('Phone number already in use'))
        return phone_number

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
