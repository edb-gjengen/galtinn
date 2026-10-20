import json
import time
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from django.conf import settings
from django.urls import reverse
from stripe import WebhookSignature

from dusken.models.orders import Order, StripePayment

if TYPE_CHECKING:
    from django.test import Client

CUSTOMER = {"id": "cus_new", "object": "customer", "email": "olanord@example.com"}
EXISTING_CUSTOMER = {"id": "cus_existing", "object": "customer", "email": "old@example.com"}
CHECKOUT_SESSION = {
    "id": "cs_test_123",
    "object": "checkout.session",
    "url": "https://checkout.stripe.com/c/pay/cs_test_123",
}
EPHEMERAL_KEY = {"id": "ephkey_123", "object": "ephemeral_key", "secret": "ek_test_secret"}
PAYMENT_INTENT = {"id": "pi_123", "object": "payment_intent", "client_secret": "pi_123_secret_abc"}


@pytest.fixture(
    params=[
        {"id": "pi_1234", "model": StripePayment.StripeModel.PAYMENT_INTENT, "source": Order.PaymentSource.APP},
        {"id": "cs_4321", "model": StripePayment.StripeModel.CHECKOUT_SESSION, "source": Order.PaymentSource.WEB},
    ],
    ids=lambda param: param["model"],
)
def stripe_payment(user, membership_type, request):
    return StripePayment.objects.create(
        user=user,
        membership_type=membership_type,
        stripe_id=request.param["id"],
        stripe_model=request.param["model"],
        source=request.param["source"],
    )


@pytest.fixture
def _use_fake_signing_secret(settings):
    settings.STRIPE_WEBHOOK_SIGNING_SECRET = "yolo"  # noqa: S105


def _home_url(query: str) -> str:
    return f"{settings.SITE_URL}{reverse('home')}?{query}"


@pytest.mark.django_db
def test_stripe_create_checkout_session(user, membership_type, client, stripe_api):
    client.force_login(user)
    stripe_api.respond("POST", "/v1/customers", CUSTOMER)
    stripe_api.respond("POST", "/v1/checkout/sessions", CHECKOUT_SESSION)

    response = client.post(reverse("stripe-checkout-session"), {"membership_type": membership_type.slug})

    assert response.status_code == HTTPStatus.SEE_OTHER, getattr(response, "data", response.status_code)
    assert response["Location"] == CHECKOUT_SESSION["url"]
    assert stripe_api.calls() == [
        ("POST", "/v1/customers", {"email": user.email}),
        (
            "POST",
            "/v1/checkout/sessions",
            {
                "line_items[0][price]": membership_type.stripe_price_id,
                "line_items[0][quantity]": "1",
                "mode": "payment",
                "success_url": _home_url("payment_success=1"),
                "cancel_url": _home_url("payment_canceled=1"),
                "customer": CUSTOMER["id"],
            },
        ),
    ]
    user.refresh_from_db()
    assert user.stripe_customer_id == CUSTOMER["id"]
    sp = StripePayment.objects.get()
    assert sp.stripe_id == CHECKOUT_SESSION["id"]
    assert sp.stripe_model == StripePayment.StripeModel.CHECKOUT_SESSION
    assert sp.membership_type.id == membership_type.id
    assert sp.user.id == user.id
    assert sp.status == StripePayment.Status.OPEN
    assert sp.source == Order.PaymentSource.WEB


@pytest.mark.django_db
def test_stripe_checkout_session_updates_existing_customer(user, membership_type, client, stripe_api):
    user.stripe_customer_id = EXISTING_CUSTOMER["id"]
    user.save()
    client.force_login(user)
    stripe_api.respond("GET", "/v1/customers/cus_existing", EXISTING_CUSTOMER)
    stripe_api.respond("POST", "/v1/customers/cus_existing", {**EXISTING_CUSTOMER, "email": user.email})
    stripe_api.respond("POST", "/v1/checkout/sessions", CHECKOUT_SESSION)

    response = client.post(reverse("stripe-checkout-session"), {"membership_type": membership_type.slug})

    assert response.status_code == HTTPStatus.SEE_OTHER, getattr(response, "data", response.status_code)
    calls = stripe_api.calls()
    assert calls[:2] == [
        ("GET", "/v1/customers/cus_existing", {}),
        ("POST", "/v1/customers/cus_existing", {"email": user.email}),
    ]
    assert calls[2][2]["customer"] == EXISTING_CUSTOMER["id"]
    assert StripePayment.objects.get().stripe_id == CHECKOUT_SESSION["id"]


@pytest.mark.django_db
@pytest.mark.parametrize("url_name", ["stripe-checkout-session", "stripe-payment-sheet"])
def test_stripe_customer_error_fails_payment(user, membership_type, client, stripe_api, url_name):
    user.stripe_customer_id = "cus_deleted"
    user.save()
    client.force_login(user)
    stripe_api.fail("GET", "/v1/customers/cus_deleted", "invalid_request_error", "resource_missing")

    response = client.post(reverse(url_name), {"membership_type": membership_type.slug})

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Payment failed with a Stripe API error"}
    assert not StripePayment.objects.exists()


@pytest.mark.django_db
def test_stripe_checkout_session_error_redirects_home(user, membership_type, client, stripe_api):
    client.force_login(user)
    stripe_api.respond("POST", "/v1/customers", CUSTOMER)
    stripe_api.fail("POST", "/v1/checkout/sessions", "invalid_request_error", "resource_missing")

    response = client.post(reverse("stripe-checkout-session"), {"membership_type": membership_type.slug})

    assert response.status_code == HTTPStatus.SEE_OTHER
    assert response["Location"] == _home_url("payment_failed=1&error=tryagainlater")
    assert not StripePayment.objects.exists()


@pytest.mark.django_db
def test_stripe_checkout_session_requires_login(membership_type, client, stripe_api):
    response = client.post(reverse("stripe-checkout-session"), {"membership_type": membership_type.slug})

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert stripe_api.calls() == []


@pytest.mark.django_db
def test_stripe_checkout_session_rejects_inactive_membership_type(user, membership_type, client, stripe_api):
    membership_type.is_active = False
    membership_type.save()
    client.force_login(user)

    response = client.post(reverse("stripe-checkout-session"), {"membership_type": membership_type.slug})

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert stripe_api.calls() == []


@pytest.mark.django_db
def test_stripe_create_payment_sheet(user, membership_type, client, stripe_api):
    client.force_login(user)
    stripe_api.respond("POST", "/v1/customers", CUSTOMER)
    stripe_api.respond("POST", "/v1/ephemeral_keys", EPHEMERAL_KEY)
    stripe_api.respond("POST", "/v1/payment_intents", PAYMENT_INTENT)

    response = client.post(reverse("stripe-payment-sheet"), {"membership_type": membership_type.slug})

    assert response.status_code == HTTPStatus.OK, getattr(response, "data", response.status_code)
    assert response.json() == {
        "paymentIntent": PAYMENT_INTENT["client_secret"],
        "ephemeralKey": EPHEMERAL_KEY["secret"],
        "customer": CUSTOMER["id"],
        "publishableKey": settings.STRIPE_PUBLIC_KEY,
    }
    assert stripe_api.calls() == [
        ("POST", "/v1/customers", {"email": user.email}),
        ("POST", "/v1/ephemeral_keys", {"customer": CUSTOMER["id"]}),
        (
            "POST",
            "/v1/payment_intents",
            {
                "amount": str(membership_type.price),
                "currency": "nok",
                "customer": CUSTOMER["id"],
                "automatic_payment_methods[enabled]": "true",
            },
        ),
    ]
    # The app's Stripe SDK needs the ephemeral key in the API version it was built for
    ephemeral_key_request = stripe_api.requests_mock.request_history[1]
    assert ephemeral_key_request.headers["Stripe-Version"] == "2018-05-21"

    sp = StripePayment.objects.get()
    assert sp.stripe_id == PAYMENT_INTENT["id"]
    assert sp.membership_type.id == membership_type.id
    assert sp.user.id == user.id
    assert sp.status == StripePayment.Status.OPEN
    assert sp.source == Order.PaymentSource.APP
    assert sp.stripe_model == StripePayment.StripeModel.PAYMENT_INTENT


@pytest.mark.django_db
@pytest.mark.parametrize("failing_path", ["/v1/ephemeral_keys", "/v1/payment_intents"])
def test_stripe_payment_sheet_error_fails_payment(user, membership_type, client, stripe_api, failing_path):
    client.force_login(user)
    stripe_api.respond("POST", "/v1/customers", CUSTOMER)
    stripe_api.respond("POST", "/v1/ephemeral_keys", EPHEMERAL_KEY)
    stripe_api.respond("POST", "/v1/payment_intents", PAYMENT_INTENT)
    stripe_api.fail("POST", failing_path, "invalid_request_error", "parameter_invalid_integer")

    response = client.post(reverse("stripe-payment-sheet"), {"membership_type": membership_type.slug})

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Payment failed with a Stripe API error"}
    assert not StripePayment.objects.exists()


@pytest.mark.django_db
def test_stripe_webhook_invalid_signature(client):
    url = reverse("stripe-webhook")
    response = client.post(url, format="json")

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == ["Invalid stripe webhook signature"]


@pytest.mark.django_db
@pytest.mark.usefixtures("_use_fake_signing_secret")
def test_stripe_webhook_invalid_payload(client: Client):
    response = _post_signed_webhook(client, "this is not json")

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == ["Invalid stripe webhook payload"]


@pytest.mark.django_db
@pytest.mark.usefixtures("_use_fake_signing_secret")
def test_stripe_webhook_unhandled_event(client: Client):
    response = _post_signed_webhook(client, json.dumps({"type": "finished-showering"}))

    assert response.status_code == HTTPStatus.OK, response.json()
    assert not response.json()["handled"]


@pytest.mark.django_db
@pytest.mark.usefixtures("_use_fake_signing_secret")
def test_stripe_webhook_checkout_session_complete(client: Client, stripe_payment: StripePayment):
    event_name = (
        "checkout.session.completed"
        if stripe_payment.stripe_model == StripePayment.StripeModel.CHECKOUT_SESSION
        else "payment_intent.succeeded"
    )
    payload = {"type": event_name, "data": {"object": {"id": stripe_payment.stripe_id}}}

    assert not stripe_payment.user.is_member

    response = _post_signed_webhook(client, json.dumps(payload))

    assert response.status_code == HTTPStatus.OK, response.json()
    assert response.json() == {"handled": True, "event_type": event_name}

    stripe_payment.refresh_from_db()
    assert stripe_payment.status == StripePayment.Status.COMPLETE
    assert stripe_payment.user.is_member
    order = Order.objects.get()
    assert order.transaction_id == stripe_payment.stripe_id
    assert order.price_nok == stripe_payment.membership_type.price
    assert order.payment_source == stripe_payment.source
    expected_method = Order.BY_APP if stripe_payment.source == Order.PaymentSource.APP else Order.BY_CARD
    assert order.payment_method == expected_method


@pytest.mark.django_db
@pytest.mark.usefixtures("_use_fake_signing_secret")
def test_stripe_webhook_skips_payment_intent_from_web_checkout(client: Client, user):
    # A web checkout also sends payment_intent.succeeded, for a payment intent we never stored
    payload = {"type": "payment_intent.succeeded", "data": {"object": {"id": "pi_from_checkout"}}}

    response = _post_signed_webhook(client, json.dumps(payload))

    assert response.status_code == HTTPStatus.OK, response.json()
    assert response.json()["handled"]
    assert not Order.objects.exists()


@pytest.mark.django_db
@pytest.mark.usefixtures("_use_fake_signing_secret")
@pytest.mark.parametrize("status", [None, StripePayment.Status.COMPLETE], ids=["unknown", "already-complete"])
def test_stripe_webhook_rejects_checkout_session_without_open_payment(client: Client, user, membership_type, status):
    if status:
        StripePayment.objects.create(user=user, membership_type=membership_type, stripe_id="cs_known", status=status)
    payload = {"type": "checkout.session.completed", "data": {"object": {"id": "cs_known"}}}

    response = _post_signed_webhook(client, json.dumps(payload))

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "does not exist" in response.json()[0]
    assert not Order.objects.exists()


def _post_signed_webhook(client: Client, body: str):
    ts = int(time.time())
    signature = WebhookSignature._compute_signature(f"{ts}.{body}", "yolo")  # noqa: SLF001
    return client.post(
        reverse("stripe-webhook"),
        body,
        content_type="application/json",
        headers={"stripe-signature": f"t={ts},v1={signature}"},
    )
