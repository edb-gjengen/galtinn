# encoding: utf-8

import datetime

from django.contrib.auth.models import Permission
from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from dusken.models import DuskenUser, Membership, MembershipType, MemberCard, Order


class MembershipTest(APITestCase):
    def setUp(self):
        self.user = DuskenUser.objects.create_user(
            'olanord', email='olanord@example.com', password='mypassword')
        self.user.user_permissions.add(Permission.objects.get(codename='add_membership'))
        self.client.force_login(self.user)
        self.membership_type = MembershipType.objects.create(
            name='Cool Club Membership',
            slug='membership',
            duration=datetime.timedelta(days=365),
            is_default=True)

        self.member_card = MemberCard.objects.create(card_number=123456789)

    def test_create(self):
        """
        Tests that POST /api/v1/memberships in fact creates membership with correct data.
        """
        membership_data = {
            'start_date': datetime.date.today().isoformat(),
            'end_date': (datetime.date.today() + self.membership_type.duration).isoformat(),
            'user': self.user.pk,
            'membership_type': self.membership_type.slug,
            'order': Order.objects.create(price_nok=self.membership_type.price,
                                          user=self.user).pk
        }

        url = reverse('membership-api-list')
        response = self.client.post(url, membership_data, format='json')

        # Check if the response even makes sense
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    def test_stripe_create_charge(self):
        url = reverse('membership-charge')
        raw_data = {
            'membership_type': self.membership_type.slug,
            'stripe_token': {
                'id': 'asdf',
                'email': 'asdf@example.com'
            }
        }
        response = self.client.post(url, raw_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Membership.objects.count(), 1)

    def test_stripe_create_renew_charge(self):
        url = reverse('membership-charge-renew')
        raw_data = {
            'membership_type': self.membership_type.slug,
            'stripe_token': {
                'id': 'asdf',
                'email': 'asdf@example.com'
            }
        }
        response = self.client.post(url, raw_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Membership.objects.count(), 1)

    def test_kassa_create_for_user(self):
        url = reverse('membership-kassa')
        raw_data = {
            'membership_type': self.membership_type.slug,
            'user': self.user.pk,
        }
        response = self.client.post(url, raw_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data.get('user'), self.user.pk)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Membership.objects.count(), 1)

    def test_kassa_create_for_non_user(self):
        url = reverse('membership-kassa')
        raw_data = {
            'membership_type': self.membership_type.slug,
            'user': None,
            'phone_number': '+4745480454',
            'member_card': 123456789
        }
        response = self.client.post(url, raw_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data.get('phone_number'), raw_data.get('phone_number'))
        self.assertEqual(response.data.get('member_card'), self.member_card.card_number)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Membership.objects.count(), 1)

    def test_kassa_create_for_non_user_without_card(self):
        url = reverse('membership-kassa')
        raw_data = {
            'membership_type': self.membership_type.slug,
            'user': None,
            'phone_number': '+4745480454',
            'member_card': None
        }
        response = self.client.post(url, raw_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data.get('phone_number'), raw_data.get('phone_number'))
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Membership.objects.count(), 1)

    def test_kassa_cannot_renew_lifelong(self):
        lifelong_type = MembershipType.objects.create(
            name='Forever Cool Club Membership',
            slug='lifelong',
            expiry_type='never')
        Membership.objects.create(
            start_date=datetime.date.today(),
            end_date=None,
            membership_type=lifelong_type,
            user=self.user)
        url = reverse('membership-kassa')
        raw_data = {
            'membership_type': self.membership_type.slug,
            'user': self.user.pk,
        }
        response = self.client.post(url, raw_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

    def test_kassa_cannot_renew_if_expires_in_more_than_one_month(self):
        Membership.objects.create(
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(days=31),
            membership_type=self.membership_type,
            user=self.user)
        url = reverse('membership-kassa')
        raw_data = {
            'membership_type': self.membership_type.slug,
            'user': self.user.pk,
        }
        response = self.client.post(url, raw_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

    def test_kassa_renewing_valid_membership_gives_proper_start_date(self):
        today = datetime.date.today()
        old_membership_ends = today + datetime.timedelta(days=10)
        new_membership_starts = old_membership_ends + datetime.timedelta(days=1)
        Membership.objects.create(
            start_date=today,
            end_date=old_membership_ends,
            membership_type=self.membership_type,
            user=self.user)
        url = reverse('membership-kassa')
        raw_data = {
            'membership_type': self.membership_type.slug,
            'user': self.user.pk,
        }
        response = self.client.post(url, raw_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(self.user.last_membership.start_date, new_membership_starts)
