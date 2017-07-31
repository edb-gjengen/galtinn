import re
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _

username_re = re.compile(r'^[a-z][a-z0-9]{2,31}$')  # From 3-32 alphanum chars (man useradd), starting with a char
UsernameValidator = RegexValidator(username_re, _('Enter a valid username.'))
