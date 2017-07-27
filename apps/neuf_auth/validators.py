from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import re


def validate_password(value):
    # Passwords should not contain " and '
    blacklist = ['"', '\'']
    for c in blacklist:
        if c in value:
            raise ValidationError(u'Enter a valid password.', code='invalid')

username_re = re.compile(r'^[a-z][a-z0-9]{2,31}$')  # From 3-32 alphanum chars (man useradd), starting with a char
UsernameValidator = RegexValidator(username_re, u'Enter a valid username.')
