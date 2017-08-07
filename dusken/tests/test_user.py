import os
from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from django.test import TestCase

from dusken.models import DuskenUser, Order, Membership, MembershipType


class DuskenUserAPITestCase(APITestCase):
    def setUp(self):
        self.user = DuskenUser.objects.create_user(
            'olanord', email='olanord@example.com', password='mypassword')
        self.user.save()
        self.other_user = DuskenUser.objects.create_user(
            'karinord', email='karinord@example.com', password='mypassword')
        self.other_user.save()
        self.token = Token.objects.create(user=self.user).key

    def __set_login(self, user_is_logged_in=True):
        if user_is_logged_in:
            self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        else:
            self.client.credentials()

    def test_user_can_obtain_token(self):
        data = {
            'username': self.user.email,
            'password': 'mypassword',
        }
        url = reverse('obtain-auth-token')
        response = self.client.post(url, data, format='json')

        # Check if the response even makes sense:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data.get('token', None)

        # Check if the returned login token is correct:
        self.assertIsNotNone(token, 'No token was returned in response')
        self.assertEqual(token, self.token, "Token from login and real token are not the same!")

    def test_user_can_only_view_self(self):
        self.assertEqual(DuskenUser.objects.count(), 2)
        self.client.force_login(self.user)
        url = reverse('user-api-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.user.pk)


class DuskenUserPhoneValidationTestCase(TestCase):
    def setUp(self):
        self.user = DuskenUser.objects.create_user(
            'olanord', email='olanord@example.com', password='mypassword',
            phone_number='+4794430002')
        self.user.save()
        from dusken.utils import send_validation_sms
        send_validation_sms(self.user)

    def test_user_phone_number_confirmation_valid_key(self):
        self.client.force_login(self.user)
        self.assertFalse(self.user.phone_number_confirmed)
        self.assertTrue(self.user.phone_number_key.isdigit())
        url = reverse('user-phone-validate')
        data = {
            'phone_key': self.user.phone_number_key
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, reverse('user-phone-validate-success'))
        self.assertTrue(DuskenUser.objects.get(pk=self.user.pk).phone_number_confirmed)

    def test_user_phone_number_confirmation_invalid_key(self):
        self.client.force_login(self.user)
        url = reverse('user-phone-validate')
        data = {
            'phone_key': 'hello'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(DuskenUser.objects.get(pk=self.user.pk).phone_number_confirmed)


class DuskenUserActivateTestCase(TestCase):
    def setUp(self):
        self.membership_type = MembershipType.objects.create(
            name='Cool Club Membership',
            slug='standard',
            duration=timedelta(days=365),
            is_default=True)
        today = timezone.now().date()
        self.membership = Membership.objects.create(
            start_date=today - timedelta(days=10),
            end_date=today + timedelta(days=10),
            membership_type=self.membership_type)
        self.order = Order.objects.create(
            payment_method=Order.BY_CASH_REGISTER,
            product=self.membership,
            price_nok=0,
            phone_number='+4794430002',
            transaction_id='14bf6820-3aca-42c8-8a32-61d1b4c44781')
        self.user_data = {
            'first_name': 'Ola',
            'last_name': 'Nordmann',
            'email': 'olanord@example.com',
            'g-recaptcha-response': 'PASSED',
            'code': self.order.transaction_id[:8],
        }
        os.environ['RECAPTCHA_TESTING'] = 'True'

    def tearDown(self):
        os.environ['RECAPTCHA_TESTING'] = 'False'

    def test_invalid_url_does_not_render_form(self):
        kwargs = {
            'phone': '4712345678',
            'code': '12345678'
        }
        url = reverse('user-activate', kwargs=kwargs)
        response = self.client.post(url)
        # Very clever.
        self.assertTrue(b'the link is invalid' in response.content)

    def test_invalid_post_data_does_not_render_form(self):
        kwargs = {
            'phone': '4712345678',
            'code': '12345678'
        }
        url = reverse('user-activate', kwargs=kwargs)
        response = self.client.post(url, self.user_data)
        # Very clever.
        self.assertTrue(b'the link is invalid' in response.content)

    def test_right_combination_confirms_phone_number_and_claims_order(self):
        kwargs = {
            'phone': str(self.order.phone_number).replace('+', ''),
            'code': self.order.transaction_id[:8]
        }
        url = reverse('user-activate', kwargs=kwargs)
        response = self.client.post(url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)  # redirect to home
        user = DuskenUser.objects.get(email=self.user_data.get('email'))
        self.assertTrue(user.phone_number_confirmed)
        self.assertTrue(user.is_member)


class DuskenUserMembershipTestCase(TestCase):
    def setUp(self):
        self.user = DuskenUser.objects.create_user('olanord', email='olanord@example.com')
        self.now = timezone.now().date()
        self.membership_type = MembershipType.objects.create(
            name='Cool Club Membership',
            slug='standard',
            duration=timedelta(days=365),
            is_default=True)

    def test_has_membership(self):
        self.assertEqual(DuskenUser.objects.with_valid_membership().count(), 0)
        self.assertFalse(self.user.is_member)

        m = Membership.objects.create(
            user=self.user, start_date=self.now, end_date=self.now + timedelta(days=365),
            membership_type=MembershipType.objects.first())
        self.assertTrue(self.user.is_member)
        self.assertEqual(DuskenUser.objects.with_valid_membership().count(), 1)

        m.end_date = None
        m.save()
        self.assertEqual(DuskenUser.objects.with_valid_membership().count(), 1)

        m.delete()
        self.assertEqual(DuskenUser.objects.with_valid_membership().count(), 0)
