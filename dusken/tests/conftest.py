import datetime as dt
from http import HTTPStatus
from urllib.parse import parse_qsl, urlsplit

import pytest
import stripe

from dusken.models.orders import MembershipType
from dusken.models.users import DuskenUser

STRIPE_API = "https://api.stripe.com"


class FakeStripe:
    """Answers the Stripe SDK's HTTP requests, so the real SDK builds requests and parses responses"""

    def __init__(self, requests_mock):
        self.requests_mock = requests_mock

    def respond(self, method: str, path: str, body: dict):
        self.requests_mock.register_uri(method, f"{STRIPE_API}{path}", json=body)

    def fail(self, method: str, path: str, error_type: str, code: str = ""):
        status = HTTPStatus.PAYMENT_REQUIRED if error_type == "card_error" else HTTPStatus.BAD_REQUEST
        body = {"error": {"type": error_type, "code": code, "message": f"Stripe says {code or error_type}"}}
        self.requests_mock.register_uri(method, f"{STRIPE_API}{path}", status_code=status, json=body)

    def calls(self) -> list[tuple[str, str, dict[str, str]]]:
        return [
            (request.method, urlsplit(request.url).path, dict(parse_qsl(request.text or "")))
            for request in self.requests_mock.request_history
        ]


@pytest.fixture
def stripe_api(requests_mock, monkeypatch):
    monkeypatch.setattr(stripe, "api_key", "sk_test_fake")
    monkeypatch.setattr(stripe, "max_network_retries", 0)
    return FakeStripe(requests_mock)


@pytest.fixture
def user(db):
    return DuskenUser.objects.create_user(
        "olanord",
        email="olanord@example.com",
        password="mypassword",
        phone_number="+4794430002",
    )


@pytest.fixture
def membership_type(db):
    return MembershipType.objects.create(
        name="Cool Club Membership",
        slug="standard",
        duration=dt.timedelta(days=365),
        is_default=True,
        price=50000,
        stripe_price_id="price_asdf",
    )
