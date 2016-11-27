from unittest import skip
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APITestCase

from dusken.models import DuskenUser


class DuskenUserTest(APITestCase):
    def setUp(self):
        self.user = DuskenUser.objects.create_user('robert', email='robert.kolner@gmail.com', password='pass')
        self.user.save()
        self.token = Token.objects.create(user=self.user).key

    def __set_login(self, user_is_logged_in=True):
        if user_is_logged_in:
            self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        else:
            self.client.credentials()

    @skip("Not implemented")
    def test_user_login(self):
        user_data = {
            'username': self.user.username,
            'password': 'pass',
        }

        url = reverse('api-login')
        response = self.client.post(url, user_data, format='json')

        # Check if the response even makes sense:
        self.assertEqual(response.status_code, HTTP_200_OK, 'Got wrong response code {}'.format(response.status_code))
        token = response.data.get('token', None)

        # Check if the returned login token is correct:
        self.assertIsNotNone(token, 'No token was returned in response')
        self.assertEqual(token, self.token, "Token from login and real token are not the same!")
