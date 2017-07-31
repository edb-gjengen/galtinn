import logging
import requests

from django.conf import settings
from urllib.parse import urljoin

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


def get_last_campaign_archive_url(list_id):
    if not list_id:
        list_id = settings.MAILCHIMP_LIST_ID

    validate_mailchimp_settings(list_id)

    url = urljoin(settings.MAILCHIMP_API_URL, '/3.0/campaigns/')

    params = {
        'list_id': list_id,
        'status': 'sent',
        'count': 1
    }

    res = requests.get(url, params, auth=_get_auth())
    campaigns = res.json().get('campaigns')

    return campaigns[0].get('archive_url') if campaigns else None


def update_list_subscription(email, status, merge_data=None, list_id=None):
    from apps.mailchimp.models import MailChimpSubscription
    assert status in dict(MailChimpSubscription.STATUS_CHOICES).keys()

    if not list_id:
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
