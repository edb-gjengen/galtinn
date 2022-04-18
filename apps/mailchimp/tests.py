import json

import requests_mock
from django.conf import settings
from django.test import TestCase, override_settings
from rest_framework.reverse import reverse

from apps.mailchimp.models import MailChimpSubscription
from apps.mailchimp.utils import get_list_member_url
from dusken.models import DuskenUser

MAILCHIMP_TEST_LIST_ID = "889d23ac1a"


class IncomingWebhook(TestCase):
    """Test webhooks"""

    fixtures = ["mailchimp"]

    @override_settings(MAILCHIMP_LIST_ID=MAILCHIMP_TEST_LIST_ID)
    def test_unsubscribe(self):
        data = {
            "data[action]": "unsub",
            "data[email]": "espen@example.com",
            "data[email_type]": "html",
            "data[id]": "cd1adcdac0",
            "data[ip_opt]": "178.74.21.27",
            "data[list_id]": "889d23ac1a",
            "data[merges][EMAIL]": "espen@example.com",
            "data[merges][FNAME]": "Espen",
            "data[merges][LNAME]": "Espensen",
            "data[reason]": "manual",
            "data[web_id]": "336983365",
            "fired_at": "2016-12-20 16:10:15",
            "type": "unsubscribe",
        }

        url = "{}?secret={}".format(reverse("mailchimp:incoming"), settings.MAILCHIMP_WEBHOOK_SECRET)
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(MailChimpSubscription.objects.first().status, MailChimpSubscription.STATUS_UNSUBSCRIBED)

    @override_settings(MAILCHIMP_LIST_ID=MAILCHIMP_TEST_LIST_ID)
    def test_subscribe(self):
        data = {
            "type": "subscribe",
            "fired_at": "2016-12-20 21:35:57",
            "data[id]": "8a25ff1d98",
            "data[list_id]": "889d23ac1a",
            "data[email]": "espen@example.com",
            "data[email_type]": "html",
            "data[merges][EMAIL]": "espen@example.com",
            "data[merges][FNAME]": "Espen",
            "data[merges][LNAME]": "Espensen",
            "data[ip_opt]": "10.20.10.30",
            "data[ip_signup]": "10.20.10.30",
        }

        url = "{}?secret={}".format(reverse("mailchimp:incoming"), settings.MAILCHIMP_WEBHOOK_SECRET)
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(MailChimpSubscription.objects.first().status, MailChimpSubscription.STATUS_SUBSCRIBED)


@override_settings(MAILCHIMP_LIST_ID=MAILCHIMP_TEST_LIST_ID)
class MailchimpAPI(TestCase):
    fixtures = ["mailchimp"]

    def test_subscribe(self):
        email = "yolo@example.com"
        self._user = DuskenUser.objects.create(email=email, username="yolo")
        self.client.force_login(self._user)

        url = reverse("mailchimp:subscription-list")
        list_id = MAILCHIMP_TEST_LIST_ID
        status = MailChimpSubscription.STATUS_SUBSCRIBED

        data = {"email": email, "status": status}

        with requests_mock.mock() as m:
            m.put(get_list_member_url(list_id, email), json={"status": status})
            res = self.client.post(url, content_type="application/json", data=json.dumps(data), format="json")

        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()["status"], status)

    def test_unsubscribe(self):
        email = "espen@example.com"
        self._user = DuskenUser.objects.create(email=email, username="yolo2")
        self.client.force_login(self._user)

        subscription = MailChimpSubscription.objects.get(pk=1)
        url = reverse("mailchimp:subscription-detail", args=[subscription.pk])
        list_id = MAILCHIMP_TEST_LIST_ID
        status = MailChimpSubscription.STATUS_UNSUBSCRIBED

        data = {"status": status}

        self.assertNotEqual(subscription.status, status)

        with requests_mock.mock() as m:
            m.put(get_list_member_url(list_id, email), json={"status": status})
            res = self.client.patch(url, content_type="application/json", data=json.dumps(data), format="json")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], status)
