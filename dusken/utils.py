import logging
import random
import re

import requests
from django.conf import settings
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.translation import gettext as _

from dusken.tasks import send_mail_task

logger = logging.getLogger(__name__)


def generate_username(first_name, last_name):
    """Generate a fairly unique username based on first and last name.
    Example: nikolakr1234
    """
    whitespace_re = re.compile(r"\s")
    first_name = first_name.encode("ascii", "ignore").lower()[:6].decode("utf-8")
    last_name = last_name.encode("ascii", "ignore").lower()[:2].decode("utf-8")
    random_number = random.randint(1, 9999)
    username = f"{first_name}{last_name}{random_number:04d}"
    username = whitespace_re.sub("", username)
    return username


class InlineClass:
    def __init__(self, dictionary):
        self.__dict__ = dictionary


def send_validation_email(user):
    if user.email_is_confirmed:
        # Bail
        return

    site = Site.objects.get(pk=settings.SITE_ID)
    url_kwargs = {"slug": str(user.uuid), "email_key": user.email_key}

    context = {
        "user": user,
        "validation_url": "https://{}{}".format(site.domain, reverse("user-email-validate", kwargs=url_kwargs)),
        "site_name": site.name,
    }

    message = render_to_string("dusken/emails/validation_email.txt", context)
    html_message = render_to_string("dusken/emails/validation_email.html", context)

    from_email = settings.DEFAULT_FROM_EMAIL

    send_mail_task.delay(
        _("Confirm your email address at Chateau Neuf"),
        from_email,
        message,
        [user.email],
        html_message=html_message,
    )


def create_email_key(length=12):
    return get_random_string(length=length)


def send_sms(to, message):
    if settings.TESTING:
        return True
    url = f"{settings.TEKSTMELDING_API_URL}send"
    payload = {"to": str(to), "message": message}
    headers = {"Authorization": "Token " + settings.TEKSTMELDING_API_KEY}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        logger.warning(f"Failed to send SMS, status_code={response.status_code} payload={payload}")
        return None

    return response.json().get("outgoing_id")


def send_validation_sms(user):
    if user.phone_number_confirmed:
        # Bail
        return None

    # Create a key if needed
    if not user.phone_number_key:
        user.phone_number_key = create_phone_key()
        user.save()

    message = _("Confirm your phone number at Chateau Neuf with this code:")
    message = message + " " + user.phone_number_key

    return send_sms(to=user.phone_number, message=message)


def create_phone_key(length=6):
    return "".join([random.choice("0123456789") for i in range(length)])


def email_exists(email):
    from dusken.models import DuskenUser

    return DuskenUser.objects.filter(email=email).exists()


def phone_number_exist(phone_number):
    from dusken.models import DuskenUser

    return DuskenUser.objects.filter(phone_number=phone_number).exists()
