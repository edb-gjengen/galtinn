# encoding: utf-8
from __future__ import unicode_literals

import datetime
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_201_CREATED
from rest_framework.test import APITestCase

from dusken.models import DuskenUser, Membership, MembershipType


class MembershipTest(APITestCase):
    def setUp(self):
        self.user = DuskenUser.objects.create_user('robert', email='robert.kolner@gmail.com', password='pass')
        self.user.save()
        self.token = Token.objects.get(user=self.user).key
        membership_type = MembershipType.objects.create(name='Medlemskap DNS (årlig')

        self.membership = Membership.objects.create(
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(days=365),
            membership_type=membership_type,
            user=self.user
        )

    def __set_login(self, user_is_logged_in=True):
        if user_is_logged_in:
            self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        else:
            self.client.credentials()

    def test_get(self):
        """
        Tests that GET /api/v1/memberships returns correct data.
        """

    def test_create(self):
        """
        Tests that POST /api/v1/memberships in fact creates membership with correct data.
        """
        self.__set_login()
        membership_data = {
            'start_date': self.membership.start_date.isoformat(),
            'end_date': self.membership.end_date.isoformat(),
            'user': self.user.pk,
            'membership_type': self.membership.membership_type.pk
        }

        url = reverse('membership-list')
        response = self.client.post(url, membership_data, format='json')

        # Check if the response even makes sense:
        self.assertEqual(response.status_code, HTTP_201_CREATED)

    def test_update(self):
        """
        Tests that PUT /api/v1/memberships/1 and PUT /api/v1/memberships/2 in fact creates membership with correct data.
        """
        pass

    def test_delete(self):
        """
        Tests that DELETE /api/v1/memberships/1 deletes the membership
        """
        pass
