from django.core import validators
from django.core.exceptions import ValidationError
from phonenumber_field.validators import validate_international_phonenumber
from phonenumber_field.phonenumber import to_python

from dusken.models import DuskenUser
from django.http import JsonResponse
from django.utils.translation import ugettext as _


def validate_email(request):
    email = request.GET.get('email', None)
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
    data = {
        'message': message
    }
    return JsonResponse(data)


def validate_phone_number(request):
    number = to_python(request.GET.get('phone_number', None))
    valid = True
    try:
        validate_international_phonenumber(number)
    except ValidationError:
        valid = False

    message = ''
    if not valid:
        message += _('Phone number is invalid')
    elif DuskenUser.objects.filter(phone_number=number).exists():
        message = _('Phone number is already in use.')
    data = {
        'message': message
    }
    return JsonResponse(data)
