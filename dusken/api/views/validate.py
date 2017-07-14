from phonenumber_field.phonenumber import to_python

from django.http import JsonResponse
from django.utils.translation import ugettext as _
from dusken.utils import validate_email, validate_phone_number


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
