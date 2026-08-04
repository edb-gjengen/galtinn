import pytest
from django.urls import reverse

from dusken.models import DuskenUser, OrgUnit


@pytest.fixture
def admin(db):
    return DuskenUser.objects.create_superuser("admin", email="admin@example.com", password="password")


@pytest.fixture
def orgunit(db):
    return OrgUnit.objects.create(name="Test Unit", slug="test-unit")


def test_orgunit_edit_includes_widget_media(client, admin, orgunit):
    """The contact person autocomplete needs the tomselect JS from form media."""
    client.force_login(admin)
    response = client.get(reverse("orgunit-edit", args=[orgunit.slug]))
    assert response.status_code == 200
    content = response.content.decode()
    assert "django_tomselect" in content
