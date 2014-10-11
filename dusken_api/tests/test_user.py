import json
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED
from rest_framework.test import APITestCase

from dusken_api.models import User


class UserTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('robert', email='robert.kolner@gmail.com', password='pass')
        self.user.save()
        self.token = Token.objects.get(user=self.user).key

    def __set_login(self, user_is_logged_in=True):
        if user_is_logged_in:
            self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        else:
            self.client.credentials()

    def test_user_login(self):
        user_data = {
            'username': self.user.username,
            'password': 'pass',
        }

        url = reverse('user-login')
        response = self.client.post(url, user_data, format='json')

        # Check if the response even makes sense:
        self.assertEqual(response.status_code, HTTP_200_OK, 'Got wrong response code {}'.format(response.status_code))

        data = json.loads(response.content)
        token = data.get('token', None)

        # Check if the returned login token is correct:
        self.assertIsNotNone(token, 'No token was returned in response')
        self.assertEqual(token, self.token, "Token from login and real token are not the same!")

    def test_get(self):
        """
        Tests that GET /api/v1/users returns correct data.
        """
        pass

    def test_create(self):
        """
        Tests that POST /api/v1/users in fact creates user with correct data.
        """
        pass

    def test_update(self):
        """
        Tests that PUT /api/v1/users/1 and PUT /api/v1/users/2 in fact creates user with correct data.
        """
        pass

    def test_delete(self):
        """
        Tests that DELETE /api/v1/users/1 deletes the user
        """
        pass