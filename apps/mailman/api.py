from urllib.parse import urljoin

import requests
from django.conf import settings


def _get_auth():
    return settings.MAILMAN_API_USERNAME, settings.MAILMAN_API_PASSWORD


def get_lists_by_email(email):
    params = {'address': email}
    r = requests.get(settings.MAILMAN_API_URL, params=params, auth=_get_auth())

    if r.status_code == 404:
        return None

    r.raise_for_status()  # requests.exceptions.HTTPError

    return r.json()['lists']

# TODO: Add subscribe function
# TODO: Add unsubscribe function
