# encoding: utf-8

import datetime

from django.contrib.auth.models import Permission
from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from dusken.models import DuskenUser, Membership, MembershipType, MemberCard, Order


class RegularUserMembershipTest(APITestCase):
    def setUp(self):
        self.user = DuskenUser.objects.create_user(
            'olanord', email='olanord@example.com', password='mypassword')
        self.client.force_login(self.user)
        self.membership_type = MembershipType.objects.create(
            name='Cool Club Membership',
            slug='standard',
            duration=datetime.timedelta(days=365),
            is_default=True)

    def test_stripe_create_charge(self):
        url = reverse('membership-charge')
        payload = {
            'membership_type': self.membership_type.slug,
            'stripe_token': {
                'id': 'asdf',
                'email': 'asdf@example.com'
            }
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Membership.objects.count(), 1)

    def test_stripe_renewing_valid_membership_gives_proper_start_date(self):
        today = datetime.date.today()
        old_membership_ends = today + datetime.timedelta(days=10)
        new_membership_starts = old_membership_ends + datetime.timedelta(days=1)
        Membership.objects.create(
            start_date=today,
            end_date=old_membership_ends,
            membership_type=self.membership_type,
            user=self.user)
        url = reverse('membership-charge')
        payload = {
            'membership_type': self.membership_type.slug,
            'stripe_token': {
                'id': 'asdf',
                'email': 'asdf@example.com'
            }
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(self.user.last_membership.start_date, new_membership_starts)

    def test_cannot_create_membership_directly(self):
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
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    def test_cannot_use_kassa_endpoint(self):
        url = reverse('membership-kassa')
        payload = {
            'membership_type': self.membership_type.slug,
            'user': self.user.pk,
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)


class SystemUserMembershipTest(APITestCase):
    def setUp(self):
        self.user = DuskenUser.objects.create_user(
            'apiuser', email='apiuser@example.com', password='mypassword')
        self.user.user_permissions.add(Permission.objects.get(codename='add_membership'))
        self.client.force_login(self.user)
        self.membership_type = MembershipType.objects.create(
            name='Cool Club Membership',
            slug='standard',
            duration=datetime.timedelta(days=365),
            is_default=True)
        self.member_card = MemberCard.objects.create(card_number=123456789)

    def test_create(self):
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
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    def test_kassa_create_for_user(self):
        url = reverse('membership-kassa')
        payload = {
            'membership_type': self.membership_type.slug,
            'user': self.user.pk,
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data.get('user'), self.user.pk)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Membership.objects.count(), 1)

    def test_kassa_create_for_non_user(self):
        url = reverse('membership-kassa')
        payload = {
            'membership_type': self.membership_type.slug,
            'user': None,
            'phone_number': '+4794430002',
            'member_card': 123456789
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data.get('phone_number'), payload.get('phone_number'))
        self.assertEqual(response.data.get('member_card'), self.member_card.card_number)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Membership.objects.count(), 1)

    def test_kassa_create_for_non_user_without_card(self):
        url = reverse('membership-kassa')
        payload = {
            'membership_type': self.membership_type.slug,
            'user': None,
            'phone_number': '+4794430002',
            'member_card': None
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data.get('phone_number'), payload.get('phone_number'))
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Membership.objects.count(), 1)

    def test_kassa_renew_for_non_user_without_card(self):
        today = datetime.datetime.now().date()
        membership = Membership.objects.create(
            start_date=today - datetime.timedelta(days=10),
            end_date=today + datetime.timedelta(days=10),
            membership_type=self.membership_type)
        Order.objects.create(
            payment_method=Order.BY_PHYSICAL_CARD,
            product=membership,
            price_nok=0,
            phone_number='+4794430002')
        url = reverse('membership-kassa')
        payload = {
            'membership_type': self.membership_type.slug,
            'user': None,
            'phone_number': '+4794430002',
            'member_card': None
        }
        response = self.client.post(url, payload, format='json')
        expected_start_date = today + datetime.timedelta(days=10+1)
        expected_end_date = expected_start_date + self.membership_type.duration
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data.get('phone_number'), payload.get('phone_number'))
        self.assertEqual(Order.objects.count(), 2)
        self.assertEqual(Membership.objects.count(), 2)
        self.assertEqual(Membership.objects.get(pk=2).start_date, expected_start_date)
        self.assertEqual(Membership.objects.get(pk=2).end_date, expected_end_date)

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
        payload = {
            'membership_type': self.membership_type.slug,
            'user': self.user.pk,
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

    def test_kassa_cannot_renew_if_expires_in_more_than_one_month(self):
        Membership.objects.create(
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(days=31),
            membership_type=self.membership_type,
            user=self.user)
        url = reverse('membership-kassa')
        payload = {
            'membership_type': self.membership_type.slug,
            'user': self.user.pk,
        }
        response = self.client.post(url, payload, format='json')
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
        payload = {
            'membership_type': self.membership_type.slug,
            'user': self.user.pk,
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(self.user.last_membership.start_date, new_membership_starts)

    def test_kassa_create_needs_identifier(self):
        url = reverse('membership-kassa')
        payload = {
            'membership_type': self.membership_type.slug,
            'user': None,
            'phone_number': None,
            'member_card': None,
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
