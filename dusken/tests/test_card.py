from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from dusken.models import DuskenUser, MemberCard


class CardTestCase(APITestCase):
    def setUp(self):
        self.user = DuskenUser.objects.create_user(
            'olanord', email='olanord@example.com', password='mypassword')
        self.client.force_login(self.user)
        self.card = MemberCard.objects.create(card_number=111111111, user=self.user)

    def test_find_by_card(self):
        url = reverse('membercard-api-list')
        data = {
            'card_number': self.card.card_number
        }
        res = self.client.get(url, data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['results'][0]['card_number'], self.card.card_number)
        self.assertEqual(res.data['results'][0]['user'], self.user.pk)

    def test_find_by_user(self):
        url = reverse('membercard-api-list')
        data = {
            'user': self.user.pk
        }
        res = self.client.get(url, data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['results'][0]['card_number'], self.card.card_number)
        self.assertEqual(res.data['results'][0]['user'], self.user.pk)
