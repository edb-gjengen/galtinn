from dusken_api.models import Member
from rest_framework.test import APITestCase

class UserTest(APITestCase):
    def setUp(self):
        member = Member.objects.create_user('robert', email='robert.kolner@gmail.com', password='test')
        member.save()

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