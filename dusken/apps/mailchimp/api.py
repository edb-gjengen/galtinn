import logging
from http import HTTPStatus

import requests
from django.conf import settings

from dusken.apps.mailchimp.utils import get_list_member_url

logger = logging.getLogger(__name__)


class MailchimpAPIException(requests.exceptions.HTTPError):
    """General MailChimp API Error"""


def _get_auth():
    return "anystring", settings.MAILCHIMP_API_KEY


def validate_mailchimp_settings(list_id):
    if not settings.MAILCHIMP_API_KEY or not list_id:
        raise ValueError(f"API_KEY ({settings.MAILCHIMP_API_KEY}) or LIST_ID ({list_id}) not set. Check settings.py")


def update_list_subscription(email, status, merge_data=None):
    from dusken.apps.mailchimp.models import MailChimpSubscription

    if status not in dict(MailChimpSubscription.STATUS_CHOICES):
        raise ValueError(f"Invalid mailchimp status {status}")

    list_id = settings.MAILCHIMP_LIST_ID
    validate_mailchimp_settings(list_id)

    data = {
        "email_address": email,
        "status": status,
        "status_if_new": status,
    }
    if merge_data:
        data["merge_fields"] = merge_data

    logger.info("Update subscription %s on list %s", email, list_id)

    # Create or update (with PUT)
    r = requests.put(get_list_member_url(list_id, email), auth=_get_auth(), json=data, timeout=10)

    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise MailchimpAPIException(e) from e

    return r.json()


def get_list_subscription(email):
    list_id = settings.MAILCHIMP_LIST_ID
    validate_mailchimp_settings(list_id)

    # Get subscription status
    r = requests.get(get_list_member_url(list_id, email), auth=_get_auth(), timeout=10)

    if r.status_code == HTTPStatus.NOT_FOUND:
        return None

    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise MailchimpAPIException(e) from e

    return r.json()
