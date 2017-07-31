import logging
import requests

from django.conf import settings

from apps.mailchimp.utils import get_list_member_url

logger = logging.getLogger(__name__)


class MailchimpAPIException(requests.exceptions.HTTPError):
    """ General MailChimp API Error """


def _get_auth():
    return 'anystring', settings.MAILCHIMP_API_KEY


def validate_mailchimp_settings(list_id):
    if not settings.MAILCHIMP_API_KEY or not list_id:
        raise ValueError('API_KEY ({}) or LIST_ID ({}) not set. Check settings.py'.format(
            settings.MAILCHIMP_API_KEY,
            list_id
        ))


def update_list_subscription(email, status, merge_data=None):
    from apps.mailchimp.models import MailChimpSubscription
    assert status in dict(MailChimpSubscription.STATUS_CHOICES).keys()

    list_id = settings.MAILCHIMP_LIST_ID

    validate_mailchimp_settings(list_id)

    data = {
        "email_address": email,
        "status": status,
        "status_if_new": status,
    }
    if merge_data:
        data["merge_fields"] = merge_data

    logger.info('Update subscription %s on list %s', email, list_id)

    # Create or update (with PUT)
    r = requests.put(get_list_member_url(list_id, email), auth=_get_auth(), json=data)

    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise MailchimpAPIException(e)

    return r.json()


def get_list_subscription(email):
    list_id = settings.MAILCHIMP_LIST_ID

    # Get subscription status
    r = requests.get(get_list_member_url(list_id, email), auth=_get_auth())

    if r.status_code == 404:
        return None

    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise MailchimpAPIException(e)

    return r.json()
