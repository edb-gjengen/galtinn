import json

import pytest
from django.urls import reverse

from dusken.models import DuskenUser


@pytest.fixture
def admin(db):
    return DuskenUser.objects.create_superuser("admin", email="admin@example.com", password="password")


@pytest.fixture
def foo_bar_user(db):
    return DuskenUser.objects.create_user("foobar", email="foobar@example.com", first_name="Foo", last_name="Bar")


@pytest.fixture
def middle_name_user(db):
    return DuskenUser.objects.create_user(
        "firstlast", email="firstlast@example.com", first_name="First Middle", last_name="Last"
    )


def search_autocomplete(client, query):
    url = reverse("user-autocomplete")
    response = client.get(url, {"q": query})
    assert response.status_code == 200
    return json.loads(response.content)


def test_search_by_full_name(client, admin, foo_bar_user):
    """Searching 'Foo Bar' should find a user with first_name='Foo' and last_name='Bar'."""
    client.force_login(admin)
    data = search_autocomplete(client, "Foo Bar")
    results = data.get("results", [])
    usernames = [item["username"] for item in results]
    assert "foobar" in usernames

    result = next(item for item in results if item["username"] == "foobar")
    assert result["full_name"] == "Foo Bar"
    assert "Foo Bar" in result["display_label"]


def test_search_skipping_middle_name(client, admin, middle_name_user):
    """Searching 'First Last' should find a user named 'First Middle Last'."""
    client.force_login(admin)
    data = search_autocomplete(client, "First Last")
    usernames = [item["username"] for item in data.get("results", [])]
    assert "firstlast" in usernames


def test_search_last_name_first(client, admin, middle_name_user):
    """Word order should not matter: 'Last First' should find 'First Middle Last'."""
    client.force_login(admin)
    data = search_autocomplete(client, "Last First")
    usernames = [item["username"] for item in data.get("results", [])]
    assert "firstlast" in usernames


def test_search_all_terms_must_match(client, admin, foo_bar_user, middle_name_user):
    """A term matching nothing should exclude the user."""
    client.force_login(admin)
    data = search_autocomplete(client, "First Nomatch")
    usernames = [item["username"] for item in data.get("results", [])]
    assert usernames == []


def test_search_ranks_exact_match_first(client, admin, foo_bar_user):
    """An exact name match should rank above prefix and substring matches."""
    DuskenUser.objects.create_user("foofoo", email="foofoo@example.com", first_name="Foofoo", last_name="Barbar")
    client.force_login(admin)
    data = search_autocomplete(client, "Foo Bar")
    usernames = [item["username"] for item in data.get("results", [])]
    assert usernames == ["foobar", "foofoo"]
