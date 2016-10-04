import random

from django.conf import settings
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext as _


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
