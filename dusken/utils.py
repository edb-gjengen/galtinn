import logging
import random
import re
import unicodedata

from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.translation import gettext as _

from dusken.tasks import send_mail_task

logger = logging.getLogger(__name__)


# Letters NFKD doesn't split into a base letter and an accent
TRANSLITERATIONS = str.maketrans({"æ": "ae", "ø": "o", "ß": "ss", "ð": "d", "þ": "th", "ł": "l", "đ": "d"})


def username_part(name, length):
    """Lowercase ASCII letters from a name: "Øystein" -> "oystein", "Anne-Lise" -> "annelise"."""
    name = unicodedata.normalize("NFKD", name.lower().translate(TRANSLITERATIONS))
    return re.sub(r"[^a-z]", "", name)[:length]


def generate_username(first_name, last_name):
    """Generate a unique username based on first and last name.
    Example: nikolakr1234
    """
    from dusken.models import DuskenUser  # noqa: PLC0415

    prefix = username_part(first_name, 6) + username_part(last_name, 2) or "user"
    # Four digits until a prefix gets crowded, then longer suffixes
    for digits in (4, 4, 4, 6, 6, 6, 8):
        username = f"{prefix}{random.randint(1, 10**digits - 1):0{digits}d}"  # noqa: S311
        if not DuskenUser.objects.filter(username=username).exists():
            return username
    msg = f"No free username for prefix {prefix}"
    raise RuntimeError(msg)


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
