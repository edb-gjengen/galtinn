import json

import pytest
from django.urls import reverse

from dusken.models import DuskenUser


@pytest.mark.django_db
@pytest.fixture
def admin():
    return DuskenUser.objects.create_superuser(
        "admin", email="admin@example.com", password="password"
    )


@pytest.mark.django_db
@pytest.fixture
def foo_bar_user():
    return DuskenUser.objects.create_user(
        "foobar", email="foobar@example.com", first_name="Foo", last_name="Bar"
    )


def search_autocomplete(client, query):
    url = reverse("user-autocomplete")
    response = client.get(url, {"q": query})
    assert response.status_code == 200
    return json.loads(response.content)


def test_search_by_full_name(client, admin, foo_bar_user):  # noqa: ARG001
    """Searching 'Foo Bar' should find a user with first_name='Foo' and last_name='Bar'."""
    client.force_login(admin)
    data = search_autocomplete(client, "Foo Bar")
    results = data.get("results", [])
    usernames = [item["username"] for item in results]
    assert "foobar" in usernames

    result = next(item for item in results if item["username"] == "foobar")
    assert result["full_name"] == "Foo Bar"
    assert "Foo Bar" in result["display_label"]
