import pytest
from django.contrib.auth.models import Group
from django.test import RequestFactory
from django.urls import reverse

from dusken.api.oauth_validators import CustomOAuth2Validator
from dusken.models import DuskenUser, GroupProfile, OrgUnit


@pytest.fixture
def admin(db):
    return DuskenUser.objects.create_superuser("admin", email="admin@example.com", password="password")


@pytest.fixture
def user(db):
    return DuskenUser.objects.create_user("kari", email="kari@example.com", password="password")


@pytest.fixture
def volunteers(db):
    group = Group.objects.create(name="Aktive")
    GroupProfile.objects.create(group=group, type=GroupProfile.TYPE_VOLUNTEERS)
    return group


@pytest.fixture
def orgunit(db):
    return OrgUnit.objects.create(
        name="Test Unit",
        slug="test-unit",
        group=Group.objects.create(name="test-unit"),
        admin_group=Group.objects.create(name="test-unit-admin"),
    )


@pytest.fixture
def standalone(db):
    """A group no org unit points at, like the CMS access group."""
    return Group.objects.create(name="Nettsidetilgang")


def test_groups_claim_includes_standalone_group(user, standalone):
    user.groups.add(standalone)
    request = RequestFactory().get("/")
    request.user = user

    claims = CustomOAuth2Validator().get_additional_claims(request)

    assert claims["groups"] == ["Nettsidetilgang"]


def test_group_admin_lists_and_adds_members(client, admin, user, standalone):
    user.groups.add(standalone)
    client.force_login(admin)
    url = reverse("admin:auth_group_change", args=[standalone.pk])

    response = client.get(url)
    assert response.status_code == 200
    assert "kari" in response.content.decode()

    prefix = "DuskenUser_groups"
    membership = DuskenUser.groups.through.objects.get(group=standalone)
    response = client.post(
        url,
        {
            "name": standalone.name,
            f"{prefix}-TOTAL_FORMS": 2,
            f"{prefix}-INITIAL_FORMS": 1,
            f"{prefix}-0-id": membership.pk,
            f"{prefix}-0-group": standalone.pk,
            f"{prefix}-0-duskenuser": user.pk,
            f"{prefix}-0-DELETE": "on",
            f"{prefix}-1-group": standalone.pk,
            f"{prefix}-1-duskenuser": admin.pk,
        },
    )

    assert response.status_code == 302
    assert list(standalone.user_set.all()) == [admin]


def test_group_admin_requires_staff(client, user, standalone):
    client.force_login(user)

    response = client.get(reverse("admin:auth_group_change", args=[standalone.pk]))

    assert response.status_code == 302
    assert reverse("admin:login") in response.url


@pytest.mark.usefixtures("volunteers")
def test_orgunit_api_only_touches_the_orgunit_groups(client, admin, user, orgunit, standalone):
    user.groups.add(standalone)
    client.force_login(admin)

    response = client.post(
        reverse("orgunit-member-list", args=[orgunit.slug]),
        {"user": user.pk, "role": "member"},
        content_type="application/json",
    )
    assert response.status_code == 201
    assert {group.name for group in user.groups.all()} == {"Nettsidetilgang", "test-unit", "Aktive"}

    response = client.delete(reverse("orgunit-member-detail", args=[orgunit.slug, user.pk]))
    assert response.status_code == 204
    assert set(user.groups.all()) == {standalone}


def test_volunteer_status_follows_orgunit_membership(admin, user, orgunit, volunteers):
    orgunit.add_user(user, admin)
    assert user.is_volunteer

    orgunit.remove_user(user, admin)
    assert not user.is_volunteer


def test_standalone_group_does_not_keep_volunteer_status(admin, user, orgunit, standalone, volunteers):
    user.groups.add(standalone)
    orgunit.add_user(user, admin)

    orgunit.remove_user(user, admin)

    assert not user.is_volunteer
    assert user.groups.filter(pk=standalone.pk).exists()


def test_standalone_group_alone_does_not_grant_volunteer_status(user, standalone, volunteers):
    user.groups.add(standalone)

    user.update_volunteer_status()

    assert not user.is_volunteer
