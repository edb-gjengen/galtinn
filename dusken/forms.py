from django import forms
from django.forms import fields
from dusken.models import DuskenUser


class DuskenUserForm(forms.ModelForm):
    email = fields.EmailField()

    class Meta:
        model = DuskenUser
        fields = ['first_name', 'last_name', 'email', 'phone_number']
