from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from django.test import TestCase

from dusken.models import DuskenUser, Membership, MembershipType


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
