import datetime as dt
from http import HTTPStatus

import pytest
from django.urls import reverse

from dusken.models import Membership, Order

CUSTOMER = {"id": "cus_new", "object": "customer", "email": "asdf@example.com"}
EXISTING_CUSTOMER = {"id": "cus_existing", "object": "customer", "email": "old@example.com"}
CHARGE = {"id": "ch_123", "object": "charge", "status": "succeeded"}
STRIPE_TOKEN = {"id": "tok_visa", "email": "asdf@example.com"}

API_ERROR = "Stripe charge failed with API error."
FAILURES = [
    ("invalid_request_error", "resource_missing", API_ERROR),
    ("card_error", "card_declined", "The card was declined."),
    ("card_error", "insufficient_funds", "Your card has been declined."),
]


def _charge(client, membership_type):
    payload = {"membership_type": membership_type.slug, "stripe_token": STRIPE_TOKEN}
    return client.post(reverse("membership-charge"), payload, content_type="application/json")


def _description(membership_type):
    return f"{membership_type.name}: {membership_type.description}"


@pytest.fixture
def existing_customer(user, stripe_api):
    user.stripe_customer_id = EXISTING_CUSTOMER["id"]
    user.save()
    stripe_api.respond("GET", "/v1/customers/cus_existing", EXISTING_CUSTOMER)
    stripe_api.respond("POST", "/v1/customers/cus_existing", {**EXISTING_CUSTOMER, "email": STRIPE_TOKEN["email"]})
    stripe_api.respond("POST", "/v1/charges", CHARGE)


@pytest.mark.django_db
def test_stripe_create_charge(user, membership_type, client, stripe_api):
    client.force_login(user)
    stripe_api.respond("POST", "/v1/customers", CUSTOMER)
    stripe_api.respond("POST", "/v1/charges", CHARGE)

    response = _charge(client, membership_type)

    assert response.status_code == HTTPStatus.CREATED, response.json()
    assert stripe_api.calls() == [
        ("POST", "/v1/customers", {"email": STRIPE_TOKEN["email"], "card": STRIPE_TOKEN["id"]}),
        (
            "POST",
            "/v1/charges",
            {
                "customer": CUSTOMER["id"],
                "amount": str(membership_type.price),
                "currency": "NOK",
                "description": _description(membership_type),
            },
        ),
    ]
    user.refresh_from_db()
    assert user.stripe_customer_id == CUSTOMER["id"]
    order = Order.objects.get()
    assert order.payment_method == Order.BY_CARD
    assert order.transaction_id == CHARGE["id"]
    assert order.user == user
    assert Membership.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.usefixtures("existing_customer")
def test_stripe_charge_updates_existing_customer(user, membership_type, client, stripe_api):
    client.force_login(user)

    response = _charge(client, membership_type)

    assert response.status_code == HTTPStatus.CREATED, response.json()
    calls = stripe_api.calls()
    assert calls[:2] == [
        ("GET", "/v1/customers/cus_existing", {}),
        ("POST", "/v1/customers/cus_existing", {"email": STRIPE_TOKEN["email"], "source": STRIPE_TOKEN["id"]}),
    ]
    assert calls[2][2]["customer"] == EXISTING_CUSTOMER["id"]
    assert Order.objects.get().transaction_id == CHARGE["id"]


@pytest.mark.django_db
def test_stripe_renewing_valid_membership_gives_proper_start_date(user, membership_type, client, stripe_api):
    today = dt.datetime.now(tz=dt.UTC).date()
    old_membership_ends = today + dt.timedelta(days=10)
    Membership.objects.create(
        start_date=today,
        end_date=old_membership_ends,
        membership_type=membership_type,
        user=user,
    )
    client.force_login(user)
    stripe_api.respond("POST", "/v1/customers", CUSTOMER)
    stripe_api.respond("POST", "/v1/charges", CHARGE)

    response = _charge(client, membership_type)

    assert response.status_code == HTTPStatus.CREATED, response.json()
    assert user.last_membership.start_date == old_membership_ends + dt.timedelta(days=1)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "failure", [("POST", path, *failure) for path in ["/v1/customers", "/v1/charges"] for failure in FAILURES]
)
def test_stripe_charge_error_for_new_customer(user, membership_type, client, stripe_api, failure):
    method, failing_path, error_type, code, message = failure
    client.force_login(user)
    stripe_api.respond("POST", "/v1/customers", CUSTOMER)
    stripe_api.respond("POST", "/v1/charges", CHARGE)
    stripe_api.fail(method, failing_path, error_type, code)

    response = _charge(client, membership_type)

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": message}
    assert not Order.objects.exists()
    assert not Membership.objects.exists()


@pytest.mark.django_db
@pytest.mark.usefixtures("existing_customer")
@pytest.mark.parametrize(
    "failure",
    [
        ("GET", "/v1/customers/cus_existing", "invalid_request_error", "resource_missing", API_ERROR),
        *[("POST", path, *failure) for path in ["/v1/customers/cus_existing", "/v1/charges"] for failure in FAILURES],
    ],
)
def test_stripe_charge_error_for_existing_customer(user, membership_type, client, stripe_api, failure):
    method, failing_path, error_type, code, message = failure
    client.force_login(user)
    stripe_api.fail(method, failing_path, error_type, code)

    response = _charge(client, membership_type)

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": message}
    assert not Order.objects.exists()
    assert not Membership.objects.exists()
