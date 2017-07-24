from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.test import APITestCase

from dusken.models import DuskenUser, MemberCard, Order


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


class KassaCardUpdateTestCase(APITestCase):
    def setUp(self):
        self.user = DuskenUser.objects.create_user(
            'olanord', email='olanord@example.com', password='mypassword')
        self.user.user_permissions.add(
            Permission.objects.get(content_type=ContentType.objects.get_for_model(MemberCard),
                                   codename='change_membercard'))
        self.client.force_login(self.user)
        self.user_card = MemberCard.objects.create(
            card_number=111111111, registered=timezone.now(), user=self.user)
        self.order_card = MemberCard.objects.create(
            card_number=222222222, registered=timezone.now())
        self.blank_card = MemberCard.objects.create(
            card_number=333333333)

    def test_kassa_can_set_blank_card_on_order(self):
        order = Order.objects.create(price_nok=0,
                                     phone_number='+4794430002')
        url = reverse('card-update-kassa')
        payload = {
            'user': None,
            'order': order.uuid,
            'member_card': self.blank_card.card_number,
        }
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(Order.objects.get(pk=order.pk).member_card.pk, self.blank_card.pk)
        self.assertTrue(MemberCard.objects.get(pk=self.blank_card.pk).is_active)
        self.assertTrue(MemberCard.objects.get(pk=self.blank_card.pk).registered is not None)

    def test_kassa_cannot_set_card_owned_by_user_on_order(self):
        order = Order.objects.create(price_nok=0,
                                     phone_number='+4794430002')
        url = reverse('card-update-kassa')
        payload = {
            'user': None,
            'order': order.uuid,
            'member_card': self.user_card.card_number,
        }
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

    def test_kassa_can_set_blank_card_on_user(self):
        url = reverse('card-update-kassa')
        payload = {
            'user': self.user.pk,
            'order': None,
            'member_card': self.blank_card.card_number,
        }
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(MemberCard.objects.get(pk=self.blank_card.pk).is_active)
        self.assertTrue(MemberCard.objects.get(pk=self.blank_card.pk).registered is not None)
        self.assertFalse(MemberCard.objects.get(pk=self.user_card.pk).is_active)

    def test_kassa_cannot_set_card_associated_with_order_on_user(self):
        Order.objects.create(price_nok=0,
                             phone_number='+4794430002',
                             member_card=self.order_card)
        url = reverse('card-update-kassa')
        payload = {
            'user': self.user.pk,
            'order': None,
            'member_card': self.order_card.card_number,
        }
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
