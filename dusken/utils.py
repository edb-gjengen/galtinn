import logging
import random
import re

from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
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
    random_number = random.randint(1, 9999)  # noqa: S311
    username = f"{first_name}{last_name}{random_number:04d}"
    return whitespace_re.sub("", username)


class InlineClass:
    def __init__(self, dictionary):
        self.__dict__ = dictionary


def send_validation_email(user):
    if user.email_is_confirmed:
        # Bail
        return

    path_and_params = reverse("user-email-validate", kwargs={"slug": str(user.uuid), "email_key": user.email_key})
    context = {
        "user": user,
        "validation_url": f"{settings.SITE_URL}{path_and_params}",
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


def email_exists(email):
    from dusken.models import DuskenUser  # noqa: PLC0415

    return DuskenUser.objects.filter(email=email.lower()).exists()


def phone_number_exist(phone_number):
    from dusken.models import DuskenUser  # noqa: PLC0415

    return DuskenUser.objects.filter(phone_number=phone_number).exists()


class HttpResponseSeeOther(HttpResponseRedirect):
    status_code = 303


def redirect_see_other(to, *args, **kwargs):
    """
    Return an HttpResponseSeeOther to the appropriate URL for the arguments
    passed.

    Adaptation of django.shortcuts.redirect to allow HTTP 303 status code
    """
    return HttpResponseSeeOther(resolve_url(to, *args, **kwargs))
