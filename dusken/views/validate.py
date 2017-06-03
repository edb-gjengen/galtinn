from django.core import validators
from django.core.exceptions import ValidationError
from phonenumber_field.validators import validate_international_phonenumber
from phonenumber_field.phonenumber import to_python

from dusken.models import DuskenUser
from django.http import JsonResponse
from django.utils.translation import ugettext as _


def validate(request):
    email = request.GET.get('email', None)
    number = to_python(request.GET.get('number', None))
    email_message = validate_email(email)
    number_message = validate_phone_number(number)
    data = {
        'email_message': email_message,
        'number_message': number_message,
        'missing_first_name': _('You need to enter your first name.'),
        'missing_last_name': _('You need to enter your last name.')
    }
    return JsonResponse(data)


def validate_email(email):
    if email == '':
        return _('You need to enter an email.')

    try:
        validators.validate_email(email)
    except ValidationError:
        return _('Email is invalid.')

    if DuskenUser.objects.filter(email=email).exists():
        return _('Email is already in use.')


def validate_phone_number(number):
    if number == '':
        return _('You need to enter a phone number.')

    try:
        validate_international_phonenumber(number)
    except ValidationError:
        return _('Phone number is invalid')

    if DuskenUser.objects.filter(phone_number=number).exists():
        return _('Phone number is already in use.')
