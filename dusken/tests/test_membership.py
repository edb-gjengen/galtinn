# encoding: utf-8

import datetime

from django.contrib.auth.models import Permission
from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from dusken.models import DuskenUser, Membership, MembershipType, Order


class MembershipTest(APITestCase):
    def setUp(self):
        self.user = DuskenUser.objects.create_user('robert', email='robert.kolner@gmail.com', password='pass')
        self.user.user_permissions.add(Permission.objects.get(codename='add_membership'))
        self.client.force_login(self.user)
        self.membership_type = MembershipType.objects.create(
            name='Medlemskap DNS (årlig',
            duration=datetime.timedelta(days=365),
            is_default=True)

        self.membership = Membership.objects.create(
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + self.membership_type.duration,
            membership_type=self.membership_type,
            user=self.user
        )

    def test_create(self):
        """
        Tests that POST /api/v1/memberships in fact creates membership with correct data.
        """
        membership_data = {
            'start_date': self.membership.start_date.isoformat(),
            'end_date': self.membership.end_date.isoformat(),
            'user': self.user.pk,
            'membership_type': self.membership.membership_type.pk,
            'order': Order.objects.create(price_nok=self.membership.membership_type.price, user=self.user).pk
        }

        url = reverse('membership-api-list')
        response = self.client.post(url, membership_data, format='json')

        # Check if the response even makes sense
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    def test_create_charge(self):
        url = reverse('membership-charge')
        raw_data = {
            'product': self.membership_type.pk,
            'user': {
                'first_name': 'jan',
                'last_name': 'johansen',
                'email': 'asdf@example.com',
                'phone_number': '+4748105885',
            },
            'stripe_token': {
                'id': 'asdf',
                'email': 'asdf@example.com'
            }
        }
        response = self.client.post(url, raw_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Order.objects.count(), 1)

    def test_create_renew_charge(self):
        url = reverse('membership-charge-renew')
        raw_data = {
            'product': self.membership_type.pk,
            'stripe_token': {
                'id': 'asdf',
                'email': 'asdf@example.com'
            }
        }
        response = self.client.post(url, raw_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Order.objects.count(), 1)
