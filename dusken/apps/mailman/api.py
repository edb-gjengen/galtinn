from http import HTTPStatus
from urllib.parse import urljoin

import requests
from django.conf import settings


def _get_auth():
    return settings.MAILMAN_API_USERNAME, settings.MAILMAN_API_PASSWORD


def get_list_url(list_name):
    return urljoin(settings.MAILMAN_API_URL, f"/{list_name}")


def get_lists_by_email(email):
    params = {"address": email}
    r = requests.get(settings.MAILMAN_API_URL, params=params, auth=_get_auth(), timeout=10)

    if r.status_code == HTTPStatus.NOT_FOUND:
        return None

    r.raise_for_status()  # requests.exceptions.HTTPError

    return r.json()["lists"]


def subscribe(list_name, email, full_name, digest=False):
    params = {"address": email, "fullname": full_name, "digest": digest}
    r = requests.put(get_list_url(list_name), params=params, auth=_get_auth(), timeout=10)

    r.raise_for_status()  # requests.exceptions.HTTPError

    return {"success": r.json()}


def unsubscribe(list_name, email):
    r = requests.delete(get_list_url(list_name), params={"address": email}, auth=_get_auth(), timeout=10)

    r.raise_for_status()  # requests.exceptions.HTTPError
