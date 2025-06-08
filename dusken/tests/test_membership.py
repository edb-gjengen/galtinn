import datetime
from types import SimpleNamespace
from unittest import mock

from django.contrib.auth.models import Permission
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from dusken.models import DuskenUser, MemberCard, Membership, MembershipType, Order

today = datetime.datetime.now(tz=datetime.UTC).date()


class MembershipTest(APITestCase):
    """Membership/order functionality for regular users."""

    def setUp(self):
        self.user = DuskenUser.objects.create_user(
            "olanord",
            email="olanord@example.com",
            password="mypassword",
            phone_number="+4794430002",
        )
        self.client.force_login(self.user)
        self.membership_type = MembershipType.objects.create(
            name="Cool Club Membership",
            slug="standard",
            duration=datetime.timedelta(days=365),
            is_default=True,
        )

    def test_stripe_create_charge(self):
        url = reverse("membership-charge")
        payload = {
            "membership_type": self.membership_type.slug,
            "stripe_token": {"id": "asdf", "email": "asdf@example.com"},
        }

        with (
            mock.patch("stripe.Customer.create") as customer_create,
            mock.patch("stripe.Charge.create") as charge_create,
        ):
            customer_create.return_value = SimpleNamespace(id="someid")
            charge_create.return_value = SimpleNamespace(id="someid", status="succeeded")
            response = self.client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert Order.objects.count() == 1
        assert Order.objects.first().payment_method == Order.BY_CARD
        assert Membership.objects.count() == 1

    def test_stripe_renewing_valid_membership_gives_proper_start_date(self):
        old_membership_ends = today + datetime.timedelta(days=10)
        new_membership_starts = old_membership_ends + datetime.timedelta(days=1)
        Membership.objects.create(
            start_date=today,
            end_date=old_membership_ends,
            membership_type=self.membership_type,
            user=self.user,
        )
        url = reverse("membership-charge")
        payload = {
            "membership_type": self.membership_type.slug,
            "stripe_token": {"id": "asdf", "email": "asdf@example.com"},
        }
        with (
            mock.patch("stripe.Customer.create") as customer_crate,
            mock.patch("stripe.Charge.create") as charge_create,
        ):
            customer_crate.return_value = SimpleNamespace(id="someid")
            charge_create.return_value = SimpleNamespace(id="someid", status="succeeded")
            response = self.client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert self.user.last_membership.start_date == new_membership_starts

    def test_cannot_use_kassa_endpoint(self):
        url = reverse("kassa-membership")
        payload = {
            "membership_type": self.membership_type.slug,
            "user": self.user.pk,
        }
        response = self.client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data

    def test_confirming_phone_number_claims_orders(self):
        membership = Membership.objects.create(
            start_date=today - datetime.timedelta(days=10),
            end_date=today + datetime.timedelta(days=10),
            membership_type=self.membership_type,
        )
        Order.objects.create(payment_method=Order.BY_SMS, product=membership, price_nok=0, phone_number="+4794430002")
        assert not self.user.is_member
        assert self.user.unclaimed_orders.exists()
        self.user.phone_number_confirmed = True
        self.user.save()
        self.user.refresh_from_db()
        assert self.user.is_member
        assert not self.user.unclaimed_orders.exists()

    def test_disallow_claiming_orders_from_deleted_users(self):
        membership_from_deleted_user = Membership.objects.create(
            start_date=today - datetime.timedelta(days=10),
            end_date=today + datetime.timedelta(days=10),
            membership_type=self.membership_type,
        )
        Order.objects.create(
            payment_method=Order.BY_APP,
            product=membership_from_deleted_user,
            price_nok=0,
            phone_number=None,
        )

        assert Order.objects.filter(phone_number__isnull=True).count() == 1
        assert not self.user.unclaimed_orders.exists()

        self.user.phone_number = ""
        self.user.save()

        assert not self.user.unclaimed_orders.exists()


class KassaMembershipTest(APITestCase):
    """Membership/order functionality for privileged user."""

    def setUp(self):
        self.user = DuskenUser.objects.create_user("apiuser", email="apiuser@example.com", password="mypassword")
        self.user.user_permissions.add(Permission.objects.get(codename="add_membership"))
        self.client.force_login(self.user)
        self.membership_type = MembershipType.objects.create(
            name="Cool Club Membership",
            slug="standard",
            duration=datetime.timedelta(days=365),
            is_default=True,
        )
        self.member_card = MemberCard.objects.create(card_number=123456789)

    def test_kassa_create_for_user(self):
        url = reverse("kassa-membership")
        payload = {
            "membership_type": self.membership_type.slug,
            "user": self.user.pk,
        }
        response = self.client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data.get("user") == self.user.pk
        assert Order.objects.count() == 1
        assert Order.objects.first().payment_method == Order.BY_CASH_REGISTER
        assert Membership.objects.count() == 1

    def test_kassa_create_for_non_user(self):
        url = reverse("kassa-membership")
        payload = {
            "membership_type": self.membership_type.slug,
            "user": None,
            "phone_number": "+4794430002",
            "member_card": 123456789,
        }
        response = self.client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data.get("phone_number") == payload.get("phone_number")
        assert response.data.get("member_card") == self.member_card.card_number
        assert Order.objects.count() == 1
        assert Membership.objects.count() == 1

    def test_kassa_create_for_non_user_without_card(self):
        url = reverse("kassa-membership")
        payload = {
            "membership_type": self.membership_type.slug,
            "user": None,
            "phone_number": "+4794430002",
            "member_card": None,
        }
        response = self.client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data.get("phone_number") == payload.get("phone_number")
        assert Order.objects.count() == 1
        assert Membership.objects.count() == 1

    def test_kassa_renew_for_non_user_without_card(self):
        membership = Membership.objects.create(
            start_date=today - datetime.timedelta(days=10),
            end_date=today + datetime.timedelta(days=10),
            membership_type=self.membership_type,
        )
        Order.objects.create(payment_method=Order.BY_SMS, product=membership, price_nok=0, phone_number="+4794430002")
        url = reverse("kassa-membership")
        payload = {
            "membership_type": self.membership_type.slug,
            "user": None,
            "phone_number": "+4794430002",
            "member_card": None,
        }
        response = self.client.post(url, payload, format="json")

        expected_start_date = today + datetime.timedelta(days=10 + 1)
        expected_end_date = expected_start_date + self.membership_type.duration

        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data.get("phone_number") == payload.get("phone_number")
        assert Order.objects.count() == 2
        assert Membership.objects.count() == 2
        new_membership = Order.objects.get(pk=response.data.get("id")).product
        assert Membership.objects.get(pk=new_membership.pk).start_date == expected_start_date
        assert Membership.objects.get(pk=new_membership.pk).end_date == expected_end_date

    def test_kassa_cannot_renew_lifelong(self):
        lifelong_type = MembershipType.objects.create(
            name="Forever Cool Club Membership",
            slug="lifelong",
            expiry_type="never",
        )
        Membership.objects.create(
            start_date=today,
            end_date=None,
            membership_type=lifelong_type,
            user=self.user,
        )
        url = reverse("kassa-membership")
        payload = {
            "membership_type": self.membership_type.slug,
            "user": self.user.pk,
        }
        response = self.client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data

    def test_kassa_cannot_renew_if_expires_in_more_than_one_year(self):
        Membership.objects.create(
            start_date=today,
            end_date=today + datetime.timedelta(days=370),
            membership_type=self.membership_type,
            user=self.user,
        )
        url = reverse("kassa-membership")
        payload = {
            "membership_type": self.membership_type.slug,
            "user": self.user.pk,
        }
        response = self.client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data

    def test_kassa_renewing_valid_membership_gives_proper_start_date(self):
        old_membership_ends = today + datetime.timedelta(days=10)
        new_membership_starts = old_membership_ends + datetime.timedelta(days=1)
        Membership.objects.create(
            start_date=today,
            end_date=old_membership_ends,
            membership_type=self.membership_type,
            user=self.user,
        )
        url = reverse("kassa-membership")
        payload = {
            "membership_type": self.membership_type.slug,
            "user": self.user.pk,
        }
        response = self.client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert self.user.last_membership.start_date == new_membership_starts

    def test_kassa_create_needs_identifier(self):
        url = reverse("kassa-membership")
        payload = {
            "membership_type": self.membership_type.slug,
            "user": None,
            "phone_number": None,
            "member_card": None,
        }
        response = self.client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data

    def test_kassa_new_member_card_associates_with_user(self):
        url = reverse("kassa-membership")
        payload = {
            "membership_type": self.membership_type.slug,
            "user": self.user.pk,
            "phone_number": None,
            "member_card": self.member_card.card_number,
        }
        response = self.client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert self.user.member_cards.filter(pk=self.member_card.pk).exists()
        assert MemberCard.objects.get(pk=self.member_card.pk).registered is not None
        assert MemberCard.objects.get(pk=self.member_card.pk).is_active

    def test_kassa_new_member_card_for_user_deactivates_old_cards(self):
        old_card = MemberCard.objects.create(card_number=222222222)
        old_card.register(user=self.user)
        url = reverse("kassa-membership")
        payload = {
            "membership_type": self.membership_type.slug,
            "user": self.user.pk,
            "phone_number": None,
            "member_card": self.member_card.card_number,
        }
        response = self.client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert not MemberCard.objects.get(pk=old_card.pk).is_active

    def test_kassa_cannot_set_new_user_on_member_card(self):
        other_user = DuskenUser.objects.create_user("karinord", email="karinord@example.com", password="mypassword")
        other_card = MemberCard.objects.create(card_number=222222222)
        other_card.register(user=other_user)
        url = reverse("kassa-membership")
        payload = {
            "membership_type": self.membership_type.slug,
            "user": self.user.pk,
            "phone_number": None,
            "member_card": other_card.card_number,
        }
        response = self.client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data

    def test_kassa_new_member_card_associates_with_order(self):
        url = reverse("kassa-membership")
        payload = {
            "membership_type": self.membership_type.slug,
            "user": None,
            "phone_number": "+4794430002",
            "member_card": self.member_card.card_number,
        }
        response = self.client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert Order.objects.filter(member_card=self.member_card).count() == 1
        assert MemberCard.objects.get(pk=self.member_card.pk).is_active
        assert MemberCard.objects.get(pk=self.member_card.pk).registered is not None
