import pytest
from rest_framework import status
from rest_framework.reverse import reverse


@pytest.fixture
def update_url(orgunit):
    return reverse("api-orgunit-update", kwargs={"slug": orgunit.slug})


@pytest.fixture
def add_url(orgunit):
    return reverse("api-orgunit-add-member", kwargs={"slug": orgunit.slug})


@pytest.fixture
def remove_url(orgunit):
    return reverse("api-orgunit-remove-member", kwargs={"slug": orgunit.slug})


@pytest.mark.django_db
class TestOrgUnitUpdateAPIView:
    def test_admin_can_update(self, client, volunteer_group, admin_user, orgunit, update_url):
        volunteer_group.user_set.add(admin_user)
        client.force_login(admin_user)
        response = client.patch(update_url, {"description": "New description"}, content_type="application/json")
        assert response.status_code == status.HTTP_200_OK
        orgunit.refresh_from_db()
        assert orgunit.description == "New description"

    def test_non_admin_is_rejected(self, client, volunteer_group, regular_user, update_url):
        volunteer_group.user_set.add(regular_user)
        client.force_login(regular_user)
        response = client.patch(update_url, {"description": "Hacked"}, content_type="application/json")
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestOrgUnitAddMemberAPIView:
    def test_unauthenticated_is_rejected(self, client, volunteer_group, target_user, add_url):
        data = {"user_id": target_user.pk, "role": "member"}
        response = client.post(add_url, data, content_type="application/json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_non_admin_is_rejected(self, client, volunteer_group, regular_user, target_user, add_url):
        client.force_login(regular_user)
        data = {"user_id": target_user.pk, "role": "member"}
        response = client.post(add_url, data, content_type="application/json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_add_member(self, client, volunteer_group, admin_user, target_user, member_group, add_url):
        client.force_login(admin_user)
        data = {"user_id": target_user.pk, "role": "member"}
        response = client.post(add_url, data, content_type="application/json")
        assert response.status_code == status.HTTP_201_CREATED
        assert member_group.user_set.filter(pk=target_user.pk).exists()

    def test_admin_can_add_admin(
        self, client, volunteer_group, admin_user, target_user, member_group, admin_group, add_url
    ):
        client.force_login(admin_user)
        data = {"user_id": target_user.pk, "role": "admin"}
        response = client.post(add_url, data, content_type="application/json")
        assert response.status_code == status.HTTP_201_CREATED
        assert member_group.user_set.filter(pk=target_user.pk).exists()
        assert admin_group.user_set.filter(pk=target_user.pk).exists()

    def test_superuser_can_add_member(self, client, volunteer_group, superuser, target_user, member_group, add_url):
        client.force_login(superuser)
        data = {"user_id": target_user.pk, "role": "member"}
        response = client.post(add_url, data, content_type="application/json")
        assert response.status_code == status.HTTP_201_CREATED
        assert member_group.user_set.filter(pk=target_user.pk).exists()

    def test_invalid_user_id(self, client, volunteer_group, admin_user, add_url):
        client.force_login(admin_user)
        data = {"user_id": 99999, "role": "member"}
        response = client.post(add_url, data, content_type="application/json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_role(self, client, volunteer_group, admin_user, target_user, add_url):
        client.force_login(admin_user)
        data = {"user_id": target_user.pk, "role": "owner"}
        response = client.post(add_url, data, content_type="application/json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_slug_in_body(self, client, volunteer_group, admin_user, target_user, member_group):
        client.force_login(admin_user)
        data = {"slug": "nonexistent", "user_id": target_user.pk, "role": "member"}
        add_url = reverse("api-orgunit-add-member", kwargs={"slug": "non-existent"})
        response = client.post(add_url, data, content_type="application/json")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert not member_group.user_set.filter(pk=target_user.pk).exists()


@pytest.mark.django_db
class TestOrgUnitRemoveMemberAPIView:
    @pytest.fixture(autouse=True)
    def _add_target_as_member(self, target_user, member_group):
        member_group.user_set.add(target_user)

    def test_unauthenticated_is_rejected(self, client, volunteer_group, target_user, remove_url):
        data = {"user_id": target_user.pk, "role": "member"}
        response = client.post(remove_url, data, content_type="application/json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_non_admin_is_rejected(self, client, volunteer_group, regular_user, target_user, remove_url):
        client.force_login(regular_user)
        data = {"user_id": target_user.pk, "role": "member"}
        response = client.post(remove_url, data, content_type="application/json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_remove_member(self, client, volunteer_group, admin_user, target_user, member_group, remove_url):
        client.force_login(admin_user)
        data = {"user_id": target_user.pk, "role": "member"}
        response = client.post(remove_url, data, content_type="application/json")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not member_group.user_set.filter(pk=target_user.pk).exists()

    def test_admin_can_remove_admin(
        self, client, volunteer_group, admin_user, target_user, admin_group, member_group, remove_url
    ):
        admin_group.user_set.add(target_user)
        client.force_login(admin_user)
        data = {"user_id": target_user.pk, "role": "admin"}
        response = client.post(remove_url, data, content_type="application/json")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not admin_group.user_set.filter(pk=target_user.pk).exists()
        # User should still be a regular member after admin removal
        assert member_group.user_set.filter(pk=target_user.pk).exists()

    def test_remove_member_also_removes_admin(
        self, client, volunteer_group, admin_user, target_user, member_group, admin_group, remove_url
    ):
        admin_group.user_set.add(target_user)
        client.force_login(admin_user)
        data = {"user_id": target_user.pk, "role": "member"}
        response = client.post(remove_url, data, content_type="application/json")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not member_group.user_set.filter(pk=target_user.pk).exists()
        assert not admin_group.user_set.filter(pk=target_user.pk).exists()

    def test_superuser_can_remove_member(
        self, client, volunteer_group, superuser, target_user, member_group, remove_url
    ):
        client.force_login(superuser)
        data = {"user_id": target_user.pk, "role": "member"}
        response = client.post(remove_url, data, content_type="application/json")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not member_group.user_set.filter(pk=target_user.pk).exists()

    def test_invalid_user_id(self, client, volunteer_group, admin_user, remove_url):
        client.force_login(admin_user)
        data = {"user_id": 99999, "role": "member"}
        response = client.post(remove_url, data, content_type="application/json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
