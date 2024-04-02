from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from phonenumber_field.validators import validate_international_phonenumber


def phone_number_validator(phone_number):
    if phone_number == "":
        raise ValidationError(_("You need to enter a phone number."))

    try:
        validate_international_phonenumber(phone_number)
    except ValidationError as err:
        raise ValidationError(_("Phone number is invalid")) from err


def email_validator(email):
    if email.strip() == "":
        raise ValidationError(_("You need to enter an email."))

    try:
        validators.validate_email(email)
    except ValidationError as err:
        raise ValidationError(_("Email is invalid.")) from err
