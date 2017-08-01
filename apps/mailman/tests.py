import requests_mock
from django.test import TestCase
from django.urls import reverse

from dusken.models import DuskenUser


class MailmanAPI(TestCase):
    def test_subscribe(self):
        address = 'yolo@example.com'
        list_name = 'ninjatest'
        self._user = DuskenUser.objects.create(email=address, username='yolo')
        self.client.force_login(self._user)

        url = reverse('mailman:memberships', args=[list_name, address])

        # with requests_mock.mock() as m:
        res = self.client.post(url, content_type='application/json', format='json')

        self.assertEqual(res.status_code, 201)
        # self.assertEqual(res.json()['status'], )

    def test_unsubscribe(self):
        pass