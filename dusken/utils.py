import random

from django.conf import settings
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext as _

from django.core import validators
from django.core.exceptions import ValidationError
from phonenumber_field.validators import validate_international_phonenumber

import dusken


def generate_username(first_name, last_name):
    """ Generate a fairly unique username based on first and last name.
        Example: nikolakr1234
    """
    first_name = first_name.encode('ascii', 'ignore').lower()[:6].decode('utf-8')
    last_name = last_name.encode('ascii', 'ignore').lower()[:2].decode('utf-8')
    random_number = random.randint(1, 9999)
    username = '{}{}{:04d}'.format(first_name, last_name, random_number)

    return username


class InlineClass(object):
    def __init__(self, dictionary):
        self.__dict__ = dictionary


def send_validation_email(user):
    if user.email_is_confirmed:
        # Bail
        return

    site = Site.objects.get(pk=settings.SITE_ID)
    url_kwargs = {'slug': str(user.uuid), 'email_key': user.email_key}

    context = {
        'user': user,
        'validation_url': 'https://{}{}'.format(site.domain, reverse('user-email-validate', kwargs=url_kwargs)),
        'site_name': site.name
    }

    message = render_to_string('dusken/emails/validation_email.txt', context)
    html_message = render_to_string('dusken/emails/validation_email.html', context)

    user.email_user(_('Confirm your email address at Chateau Neuf'), message, html_message=html_message)


def create_email_key():
    return get_random_string()


def email_exist(email):
    return dusken.models.DuskenUser.objects.filter(email=email).exists()


def validate_email(email):
    if email == '':
        return _('You need to enter an email.')

    try:
        validators.validate_email(email)
    except ValidationError:
        return _('Email is invalid.')

    if email_exist(email):
        return _('Email is already in use.')


def phone_number_exist(phone_number):
    return dusken.models.DuskenUser.objects.filter(phone_number=phone_number).exists()


def validate_phone_number(phone_number):
    if phone_number == '':
        return _('You need to enter a phone number.')

    try:
        validate_international_phonenumber(phone_number)
    except ValidationError:
        return _('Phone number is invalid')

    if phone_number_exist(phone_number):
        return _('Phone number is already in use.')