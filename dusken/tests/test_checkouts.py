import datetime
import json
import time
from http import HTTPStatus
from types import SimpleNamespace
from unittest import mock

import pytest
from django.test import Client
from django.urls import reverse
from stripe import WebhookSignature

from dusken.models.orders import MembershipType, StripePayment
from dusken.models.users import DuskenUser


@pytest.fixture()
def user():
    return DuskenUser.objects.create_user(
        "olanord",
        email="olanord@example.com",
        password="mypassword",
        phone_number="+4794430002",
    )


@pytest.fixture()
def membership_type():
    return MembershipType.objects.create(
        name="Cool Club Membership",
        slug="standard",
        duration=datetime.timedelta(days=365),
        is_default=True,
        stripe_price_id="price_asdf",
    )


@pytest.fixture(
    params=[
        {"id": "cs_1234", "model": StripePayment.StripeModel.PAYMENT_INTENT},
        {"id": "pi_4321", "model": StripePayment.StripeModel.CHECKOUT_SESSION},
    ],
    ids=lambda param: param["model"],
)
def stripe_payment(user, membership_type, request):
    return StripePayment.objects.create(
        user=user, membership_type=membership_type, stripe_id=request.param["id"], stripe_model=request.param["model"]
    )


@pytest.fixture()
def _use_fake_signing_secret(settings):
    settings.STRIPE_WEBHOOK_SIGNING_SECRET = "yolo"  # noqa: S105


@pytest.mark.django_db()
def test_stripe_create_checkout_session(user, membership_type, client):
    client.force_login(user)
    url = reverse("stripe-checkout-session")
    payload = {
        "membership_type": membership_type.slug,
    }
    stripe_id = "yolo"

    with mock.patch("stripe.Customer.create") as customer_create, mock.patch(
        "stripe.checkout.Session.create"
    ) as session_create:
        customer_create.return_value = SimpleNamespace(id="someid")
        session_create.return_value = SimpleNamespace(id=stripe_id, url="http://example.com/payment-url-123")
        response = client.post(url, payload, format="json")

    assert response.status_code == HTTPStatus.SEE_OTHER, getattr(response, "data", response.status_code)
    assert StripePayment.objects.count() == 1
    sp = StripePayment.objects.get()
    assert sp.stripe_id == stripe_id
    assert sp.membership_type.id == membership_type.id
    assert sp.user.id == user.id
    assert sp.status == StripePayment.Status.OPEN


@pytest.mark.django_db()
def test_stripe_create_payment_sheet(user, membership_type, client):
    client.force_login(user)
    url = reverse("stripe-payment-sheet")
    payload = {
        "membership_type": membership_type.slug,
    }
    stripe_id = "yolo"

    with mock.patch("stripe.Customer.create") as customer_create, mock.patch(
        "stripe.PaymentIntent.create"
    ) as payment_intent, mock.patch("stripe.EphemeralKey.create") as ephemeral_key:
        customer_create.return_value = SimpleNamespace(id="someid")
        ephemeral_key.return_value = SimpleNamespace(secret="somesecret")
        payment_intent.return_value = SimpleNamespace(id=stripe_id, client_secret="someclientsecret")
        response = client.post(url, payload, format="json")

    assert response.status_code == HTTPStatus.OK, getattr(response, "data", response.status_code)
    assert StripePayment.objects.count() == 1
    sp = StripePayment.objects.get()
    assert sp.stripe_id == stripe_id
    assert sp.membership_type.id == membership_type.id
    assert sp.user.id == user.id
    assert sp.status == StripePayment.Status.OPEN
    assert sp.source == "app"
    assert sp.stripe_model == StripePayment.StripeModel.PAYMENT_INTENT


@pytest.mark.django_db()
def test_stripe_webhook_invalid_signature(client):
    url = reverse("stripe-webhook")
    response = client.post(url, format="json")

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == ["Invalid stripe webhook signature"]


@pytest.mark.django_db()
@pytest.mark.usefixtures("_use_fake_signing_secret")
def test_stripe_webhook_unhandled_event(client: Client):
    url = reverse("stripe-webhook")

    payload = {"type": "finished-showering"}
    response = client.post(url, payload, headers=_stripe_signature_header(payload), content_type="application/json")

    assert response.status_code == HTTPStatus.OK, response.json()
    assert not response.json()["handled"]


@pytest.mark.django_db()
@pytest.mark.usefixtures("_use_fake_signing_secret")
def test_stripe_webhook_checkout_session_complete(client: Client, stripe_payment: StripePayment):
    url = reverse("stripe-webhook")
    event_name = (
        "checkout.session.completed"
        if stripe_payment.stripe_model == StripePayment.StripeModel.CHECKOUT_SESSION
        else "payment_intent.succeeded"
    )
    payload = {"type": event_name, "data": {"object": {"id": stripe_payment.stripe_id}}}

    assert not stripe_payment.user.is_member

    response = client.post(url, payload, headers=_stripe_signature_header(payload), content_type="application/json")

    assert response.status_code == HTTPStatus.OK, response.json()
    assert response.json()["handled"]

    stripe_payment.refresh_from_db()
    assert stripe_payment.status == StripePayment.Status.COMPLETE
    assert stripe_payment.user.is_member


def _stripe_signature_header(payload: dict):
    ts = int(time.time())
    signed_payload = f"{ts}.{json.dumps(payload)}"
    signature = WebhookSignature._compute_signature(signed_payload, "yolo")  # noqa: SLF001
    return {"stripe-signature": f"t={ts },v1={signature}"}
