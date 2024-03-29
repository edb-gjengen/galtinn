# encoding: utf-8

import datetime

from django.contrib.auth.models import Permission
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from dusken.models import DuskenUser, MemberCard, Membership, MembershipType, Order


class MembershipTest(APITestCase):
    """Membership/order functionality for regular users."""

    def setUp(self):
        self.user = DuskenUser.objects.create_user(
            "olanord", email="olanord@example.com", password="mypassword", phone_number="+4794430002"
        )
        self.client.force_login(self.user)
        self.membership_type = MembershipType.objects.create(
            name="Cool Club Membership", slug="standard", duration=datetime.timedelta(days=365), is_default=True
        )

    def test_stripe_create_charge(self):
        url = reverse("membership-charge")
        payload = {
            "membership_type": self.membership_type.slug,
            "stripe_token": {"id": "asdf", "email": "asdf@example.com"},
        }
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Order.objects.first().payment_method, Order.BY_CARD)
        self.assertEqual(Membership.objects.count(), 1)

    def test_stripe_renewing_valid_membership_gives_proper_start_date(self):
        today = datetime.date.today()
        old_membership_ends = today + datetime.timedelta(days=10)
        new_membership_starts = old_membership_ends + datetime.timedelta(days=1)
        Membership.objects.create(
            start_date=today, end_date=old_membership_ends, membership_type=self.membership_type, user=self.user
        )
        url = reverse("membership-charge")
        payload = {
            "membership_type": self.membership_type.slug,
            "stripe_token": {"id": "asdf", "email": "asdf@example.com"},
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(self.user.last_membership.start_date, new_membership_starts)

    def test_cannot_create_membership_directly(self):
        membership_data = {
            "start_date": datetime.date.today().isoformat(),
            "end_date": (datetime.date.today() + self.membership_type.duration).isoformat(),
            "user": self.user.pk,
            "membership_type": self.membership_type.slug,
            "order": Order.objects.create(price_nok=self.membership_type.price, user=self.user).pk,
        }

        url = reverse("membership-api-list")
        response = self.client.post(url, membership_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    def test_cannot_use_kassa_endpoint(self):
        url = reverse("kassa-membership")
        payload = {
            "membership_type": self.membership_type.slug,
            "user": self.user.pk,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    def test_confirming_phone_number_claims_orders(self):
        today = datetime.datetime.now().date()
        membership = Membership.objects.create(
            start_date=today - datetime.timedelta(days=10),
            end_date=today + datetime.timedelta(days=10),
            membership_type=self.membership_type,
        )
        Order.objects.create(payment_method=Order.BY_SMS, product=membership, price_nok=0, phone_number="+4794430002")
        self.assertFalse(self.user.is_member)
        self.assertTrue(self.user.unclaimed_orders.exists())
        self.user.phone_number_confirmed = True
        self.user.save()
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_member)
        self.assertFalse(self.user.unclaimed_orders.exists())

    def test_disallow_claiming_orders_from_deleted_users(self):
        today = datetime.datetime.now().date()
        membership_from_deleted_user = Membership.objects.create(
            start_date=today - datetime.timedelta(days=10),
            end_date=today + datetime.timedelta(days=10),
            membership_type=self.membership_type,
        )
        Order.objects.create(
            payment_method=Order.BY_APP, product=membership_from_deleted_user, price_nok=0, phone_number=None
        )

        self.assertEqual(Order.objects.filter(phone_number__isnull=True).count(), 1)
        self.assertFalse(self.user.unclaimed_orders.exists())

        self.user.phone_number = ""
        self.user.save()

        self.assertFalse(self.user.unclaimed_orders.exists())


class KassaMembershipTest(APITestCase):
    """Membership/order functionality for privileged user."""

    def setUp(self):
        self.user = DuskenUser.objects.create_user("apiuser", email="apiuser@example.com", password="mypassword")
        self.user.user_permissions.add(Permission.objects.get(codename="add_membership"))
        self.client.force_login(self.user)
        self.membership_type = MembershipType.objects.create(
            name="Cool Club Membership", slug="standard", duration=datetime.timedelta(days=365), is_default=True
        )
        self.member_card = MemberCard.objects.create(card_number=123456789)

    def test_create(self):
        membership_data = {
            "start_date": datetime.date.today().isoformat(),
            "end_date": (datetime.date.today() + self.membership_type.duration).isoformat(),
            "user": self.user.pk,
            "membership_type": self.membership_type.slug,
            "order": Order.objects.create(price_nok=self.membership_type.price, user=self.user).pk,
        }

        url = reverse("membership-api-list")
        response = self.client.post(url, membership_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    def test_kassa_create_for_user(self):
        url = reverse("kassa-membership")
        payload = {
            "membership_type": self.membership_type.slug,
            "user": self.user.pk,
        }
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data.get("user"), self.user.pk)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Order.objects.first().payment_method, Order.BY_CASH_REGISTER)
        self.assertEqual(Membership.objects.count(), 1)

    def test_kassa_create_for_non_user(self):
        url = reverse("kassa-membership")
        payload = {
            "membership_type": self.membership_type.slug,
            "user": None,
            "phone_number": "+4794430002",
            "member_card": 123456789,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data.get("phone_number"), payload.get("phone_number"))
        self.assertEqual(response.data.get("member_card"), self.member_card.card_number)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Membership.objects.count(), 1)

    def test_kassa_create_for_non_user_without_card(self):
        url = reverse("kassa-membership")
        payload = {
            "membership_type": self.membership_type.slug,
            "user": None,
            "phone_number": "+4794430002",
            "member_card": None,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data.get("phone_number"), payload.get("phone_number"))
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Membership.objects.count(), 1)

    def test_kassa_renew_for_non_user_without_card(self):
        today = datetime.datetime.now().date()
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

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data.get("phone_number"), payload.get("phone_number"))
        self.assertEqual(Order.objects.count(), 2)
        self.assertEqual(Membership.objects.count(), 2)
        new_membership = Order.objects.get(pk=response.data.get("id")).product
        self.assertEqual(Membership.objects.get(pk=new_membership.pk).start_date, expected_start_date)
        self.assertEqual(Membership.objects.get(pk=new_membership.pk).end_date, expected_end_date)

    def test_kassa_cannot_renew_lifelong(self):
        lifelong_type = MembershipType.objects.create(
            name="Forever Cool Club Membership", slug="lifelong", expiry_type="never"
        )
        Membership.objects.create(
            start_date=datetime.date.today(), end_date=None, membership_type=lifelong_type, user=self.user
        )
        url = reverse("kassa-membership")
        payload = {
            "membership_type": self.membership_type.slug,
            "user": self.user.pk,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

    def test_kassa_cannot_renew_if_expires_in_more_than_one_year(self):
        Membership.objects.create(
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(days=370),
            membership_type=self.membership_type,
            user=self.user,
        )
        url = reverse("kassa-membership")
        payload = {
            "membership_type": self.membership_type.slug,
            "user": self.user.pk,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

    def test_kassa_renewing_valid_membership_gives_proper_start_date(self):
        today = datetime.date.today()
        old_membership_ends = today + datetime.timedelta(days=10)
        new_membership_starts = old_membership_ends + datetime.timedelta(days=1)
        Membership.objects.create(
            start_date=today, end_date=old_membership_ends, membership_type=self.membership_type, user=self.user
        )
        url = reverse("kassa-membership")
        payload = {
            "membership_type": self.membership_type.slug,
            "user": self.user.pk,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(self.user.last_membership.start_date, new_membership_starts)

    def test_kassa_create_needs_identifier(self):
        url = reverse("kassa-membership")
        payload = {
            "membership_type": self.membership_type.slug,
            "user": None,
            "phone_number": None,
            "member_card": None,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

    def test_kassa_new_member_card_associates_with_user(self):
        url = reverse("kassa-membership")
        payload = {
            "membership_type": self.membership_type.slug,
            "user": self.user.pk,
            "phone_number": None,
            "member_card": self.member_card.card_number,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(self.user.member_cards.filter(pk=self.member_card.pk).exists())
        self.assertTrue(MemberCard.objects.get(pk=self.member_card.pk).registered is not None)
        self.assertTrue(MemberCard.objects.get(pk=self.member_card.pk).is_active)

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
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertFalse(MemberCard.objects.get(pk=old_card.pk).is_active)

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
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

    def test_kassa_new_member_card_associates_with_order(self):
        url = reverse("kassa-membership")
        payload = {
            "membership_type": self.membership_type.slug,
            "user": None,
            "phone_number": "+4794430002",
            "member_card": self.member_card.card_number,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Order.objects.filter(member_card=self.member_card).count(), 1)
        self.assertTrue(MemberCard.objects.get(pk=self.member_card.pk).is_active)
        self.assertTrue(MemberCard.objects.get(pk=self.member_card.pk).registered is not None)
