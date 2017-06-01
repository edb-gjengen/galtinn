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
    valid = True
    try:
        validators.validate_email(email)
    except ValidationError:
        valid = False

    message = ''
    if not valid:
        message = _('Email is invalid.')
    elif DuskenUser.objects.filter(email=email).exists():
        message = _('Email is already in use.')
    return message


def validate_phone_number(number):
    valid = True
    if number == '':
        valid = False
    try:
        validate_international_phonenumber(number)
    except ValidationError:
        valid = False

    message = ''
    if not valid:
        message += _('Phone number is invalid')
    elif DuskenUser.objects.filter(phone_number=number).exists():
        message = _('Phone number is already in use.')
    return message
