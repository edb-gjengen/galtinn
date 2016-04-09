from django import forms
from django.forms import fields
from dusken.models import DuskenUser
from phonenumber_field.formfields import PhoneNumberField


class DuskenUserForm(forms.ModelForm):
    email = fields.EmailField()

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
