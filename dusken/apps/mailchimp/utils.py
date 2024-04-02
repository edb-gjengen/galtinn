import hashlib
from urllib.parse import urljoin

from django.conf import settings


def subscriber_hash(email):
    m = hashlib.md5()  # noqa: S324
    m.update(email.lower().encode())
    return m.hexdigest()


def get_list_member_url(list_id, email):
    return urljoin(settings.MAILCHIMP_API_URL, f"/3.0/lists/{list_id}/members/{subscriber_hash(email)}")
