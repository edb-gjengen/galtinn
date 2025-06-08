from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import django_recaptcha.client
from django.test import TestCase
from django_recaptcha.client import RecaptchaResponse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from dusken.models import DuskenUser, Membership, MembershipType, Order
from dusken.utils import generate_username


class DuskenUserAPITestCase(APITestCase):
    def setUp(self):
        self.user = DuskenUser.objects.create_user("olanord", email="olanord@example.com", password="mypassword")
        self.other_user = DuskenUser.objects.create_user(
            "karinord",
            email="karinord@example.com",
            password="mypassword",
        )
        self.token = Token.objects.create(user=self.user).key

    def __set_login(self, user_is_logged_in=True):
        if user_is_logged_in:
            self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token)
        else:
            self.client.credentials()

    def test_user_can_obtain_token(self):
        data = {
            "username": self.user.email,
            "password": "mypassword",
        }
        url = reverse("obtain-auth-token")
        response = self.client.post(url, data, format="json")

        # Check if the response even makes sense:
        assert response.status_code == status.HTTP_200_OK
        token = response.data.get("token", None)

        # Check if the returned login token is correct:
        assert token is not None, "No token was returned in response"
        assert token == self.token, "Token from login and real token are not the same!"

    def test_user_can_only_view_self(self):
        assert DuskenUser.objects.count() == 2
        self.client.force_login(self.user)
        url = reverse("user-api-list")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == self.user.pk
        assert response.data.get("password", None) is None

    def test_user_can_register(self):
        data = {
            "email": "appuser@example.com",
            "password": "myuncommonpassword",
            "first_name": "yo",
            "last_name": "lo",
            "phone_number": "48105885",
        }
        url = reverse("user-api-register")
        response = self.client.post(url, data, format="json")

        # Check if the response even makes sense:
        assert response.status_code == status.HTTP_201_CREATED, response.data
        # Do not return a password:
        assert response.data.get("password", None) is None
        # Check if the returned login token is correct:
        assert response.data.get("auth_token") is not None, "No token was returned in response"


class DuskenUserPhoneValidationTestCase(TestCase):
    def setUp(self):
        from dusken.utils import send_validation_sms

        self.user = DuskenUser.objects.create_user(
            "olanord",
            email="olanord@example.com",
            password="mypassword",
            phone_number="+4794430002",
        )
        send_validation_sms(self.user)

    def test_user_phone_number_confirmation_valid_key(self):
        self.client.force_login(self.user)
        assert not self.user.phone_number_confirmed
        assert self.user.phone_number_key.isdigit()
        url = reverse("user-phone-validate")
        data = {"phone_key": self.user.phone_number_key}
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_302_FOUND
        assert response.url == reverse("home")
        assert DuskenUser.objects.get(pk=self.user.pk).phone_number_confirmed

    def test_user_phone_number_confirmation_invalid_key(self):
        self.client.force_login(self.user)
        url = reverse("user-phone-validate")
        data = {"phone_key": "hello"}
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert not DuskenUser.objects.get(pk=self.user.pk).phone_number_confirmed


class DuskenUserActivateTestCase(TestCase):
    def setUp(self):
        self.membership_type = MembershipType.objects.create(
            name="Cool Club Membership",
            slug="standard",
            duration=timedelta(days=365),
            is_default=True,
        )
        today = datetime.now(tz=UTC).date()
        self.membership = Membership.objects.create(
            start_date=today - timedelta(days=10),
            end_date=today + timedelta(days=10),
            membership_type=self.membership_type,
        )
        self.membership_two = Membership.objects.create(
            start_date=today - timedelta(days=10),
            end_date=today + timedelta(days=10),
            membership_type=self.membership_type,
        )
        self.order = Order.objects.create(
            payment_method=Order.BY_CASH_REGISTER,
            product=self.membership,
            price_nok=0,
            phone_number="+4794430002",
            transaction_id="14bf6820-3aca-42c8-8a32-61d1b4c44781",
        )
        self.order_foreign = Order.objects.create(
            payment_method=Order.BY_CASH_REGISTER,
            product=self.membership_two,
            price_nok=0,
            phone_number="+46771793336",
            transaction_id="79c2bf64-5b37-43a1-917a-85512eee4bbd",
        )
        self.user_data = {
            "first_name": "Ola",
            "last_name": "Nordmann",
            "email": "olanord@example.com",
            "password": "irifjckekemvjfgsdfshdf",
            "code": self.order.transaction_id[:8],
            "captcha": "not-empty",
        }

    def test_invalid_url_does_not_render_form(self):
        kwargs = {"phone": "4712345678", "code": "12345678"}
        url = reverse("user-activate", kwargs=kwargs)
        response = self.client.post(url)
        # Very clever.
        assert b"the link is invalid" in response.content

    @patch.object(django_recaptcha.client, "submit")
    def test_invalid_post_data_does_not_render_form(self, mocked_submit):
        mocked_submit.return_value = RecaptchaResponse(is_valid=True, action="form")
        kwargs = {"phone": "4712345678", "code": "12345678"}
        url = reverse("user-activate", kwargs=kwargs)

        response = self.client.post(url, self.user_data)
        # Very clever.
        assert b"the link is invalid" in response.content

    @patch.object(django_recaptcha.client, "submit")
    def test_right_combination_confirms_phone_number_and_claims_order(self, mocked_submit):
        mocked_submit.return_value = RecaptchaResponse(is_valid=True, action="form")
        kwargs = {"phone": str(self.order.phone_number).replace("+", ""), "code": self.order.transaction_id[:8]}
        url = reverse("user-activate", kwargs=kwargs)
        response = self.client.post(url, self.user_data)

        assert response.status_code == status.HTTP_302_FOUND  # redirect to home

        user = DuskenUser.objects.get(email=self.user_data.get("email"))
        assert user.phone_number_confirmed
        assert user.is_member

    @patch.object(django_recaptcha.client, "submit")
    def test_right_combination_works_for_foreign_phone(self, mocked_submit):
        mocked_submit.return_value = RecaptchaResponse(is_valid=True, action="form")
        kwargs = {
            "phone": str(self.order_foreign.phone_number).replace("+", ""),
            "code": self.order_foreign.transaction_id[:8],
        }
        self.user_data["code"] = self.order_foreign.transaction_id[:8]
        url = reverse("user-activate", kwargs=kwargs)
        response = self.client.post(url, self.user_data)

        assert response.status_code == status.HTTP_302_FOUND  # redirect to home

        user = DuskenUser.objects.get(email=self.user_data.get("email"))
        assert user.phone_number_confirmed
        assert user.is_member


class DuskenUserMembershipTestCase(TestCase):
    def setUp(self):
        self.user = DuskenUser.objects.create_user("olanord", email="olanord@example.com")
        self.now = datetime.now(tz=UTC).date()
        self.membership_type = MembershipType.objects.create(
            name="Cool Club Membership",
            slug="standard",
            duration=timedelta(days=365),
            is_default=True,
        )

    def test_has_membership(self):
        assert DuskenUser.objects.with_valid_membership().count() == 0
        assert not self.user.is_member

        m = Membership.objects.create(
            user=self.user,
            start_date=self.now,
            end_date=self.now + timedelta(days=365),
            membership_type=MembershipType.objects.first(),
        )
        assert self.user.is_member
        assert DuskenUser.objects.with_valid_membership().count() == 1

        m.end_date = None
        m.save()
        assert DuskenUser.objects.with_valid_membership().count() == 1

        m.delete()
        assert DuskenUser.objects.with_valid_membership().count() == 0


class DuskenUtilTests(TestCase):
    def test_generate_username_without_blanks(self):
        first_name = "ole remi"
        last_name = "nordmann"
        generated = generate_username(first_name, last_name)
        assert len(generated) > 0
        assert " " not in generated


class DuskenUserDelete(TestCase):
    fixtures = ["testdata"]

    def setUp(self):
        self.user = DuskenUser.objects.create_user("mrclean", email="mrclean@example.com", password="mypassword")

        mt = MembershipType.objects.first()
        self.membership = Membership.objects.create(
            start_date=datetime.now(tz=UTC),
            membership_type=mt,
            user=self.user,
        )
        self.order = Order.objects.create(
            user=self.user,
            product=self.membership,
            phone_number="48105885",
            price_nok=mt.price,
        )

        self.user_2 = DuskenUser.objects.create_user("mrclean1", email="mrclean1@example.com", password="mypassword")
        self.user_3 = DuskenUser.objects.create_user("mrclean2", email="mrclean2@example.com", password="mypassword")

    def test_delete_user(self):
        url = reverse("user-delete")
        self.client.force_login(self.user)
        response = self.client.post(url, {"confirm_username": "wrong_username"})
        self.assertFormError(
            response.context_data["form"], "confirm_username", "The username entered is not equal to your own."
        )

        response = self.client.post(url, {"confirm_username": self.user.username})

        self.assertRedirects(response, reverse("index"))

        assert not DuskenUser.objects.filter(pk=self.user.pk).exists()
        assert DuskenUser.objects.filter(username__in=["mrclean1", "mrclean2"]).count() == 2

        assert Order.objects.filter(pk=self.order.pk).exists()
        self.order.refresh_from_db()
        assert self.order.phone_number is None

        self.membership.refresh_from_db()  # Will trigger DoesNotExists if was deleted
