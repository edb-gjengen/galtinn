from urllib.parse import urljoin

import requests_mock
from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlencode
from rest_framework import status

from apps.mailman.api import get_list_url
from dusken.models import DuskenUser


class MailmanAPI(TestCase):
    def test_subscribe(self):
        address = "yolo@example.com"
        list_name = "ninjatest"
        params = {"full_name": "Yo Lo"}
        self._user = DuskenUser.objects.create(email=address, username="yolo")
        self.client.force_login(self._user)

        url = reverse("mailman:memberships", args=[list_name, address])
        url = urljoin(url, f"?{urlencode(params)}")

        with requests_mock.mock() as m:
            m.put(get_list_url(list_name), json=True)
            res = self.client.put(url, params, content_type="application/json", format="json")

        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json(), {"success": True})

    def test_unsubscribe(self):
        address = "yolo@example.com"
        list_name = "ninjatest"
        self._user = DuskenUser.objects.create(email=address, username="yolo")
        self.client.force_login(self._user)

        url = reverse("mailman:memberships", args=[list_name, address])

        with requests_mock.mock() as m:
            m.delete(get_list_url(list_name), status_code=status.HTTP_204_NO_CONTENT)
            res = self.client.delete(url, content_type="application/json", format="json")

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
