from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from dusken.models import DuskenUser, GroupProfile, OrgUnit


class OrgUnitEditTestCase(TestCase):
    def setUp(self):
        volunteers = Group.objects.create(name="Volunteers")
        GroupProfile.objects.create(group=volunteers, type=GroupProfile.TYPE_VOLUNTEERS)
        self.admin_group = Group.objects.create(name="Unit admins")
        self.orgunit = OrgUnit.objects.create(
            name="Unit",
            slug="unit",
            group=Group.objects.create(name="Unit members"),
            admin_group=self.admin_group,
        )

        self.volunteer = DuskenUser.objects.create_user("volunteer", email="volunteer@example.com")
        self.volunteer.groups.add(volunteers)
        self.admin = DuskenUser.objects.create_user("admin", email="admin@example.com")
        self.admin.groups.add(volunteers, self.admin_group)

        self.data = {"name": "Hacked", "description": "", "contact_person": self.volunteer.pk}

    def test_volunteer_cannot_view_edit_pages(self):
        self.client.force_login(self.volunteer)
        for name in ["orgunit-edit", "orgunit-edit-users"]:
            response = self.client.get(reverse(name, args=[self.orgunit.slug]))
            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_volunteer_cannot_edit_orgunit(self):
        self.client.force_login(self.volunteer)
        response = self.client.post(reverse("orgunit-edit", args=[self.orgunit.slug]), self.data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        self.orgunit.refresh_from_db()
        assert self.orgunit.name == "Unit"

    def test_volunteer_cannot_edit_orgunit_without_admin_group(self):
        self.orgunit.admin_group = None
        self.orgunit.save()
        self.client.force_login(self.volunteer)
        response = self.client.post(reverse("orgunit-edit", args=[self.orgunit.slug]), self.data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_orgunit_admin_can_edit_orgunit(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("orgunit-edit", args=[self.orgunit.slug]), self.data)
        assert response.status_code == status.HTTP_302_FOUND
        self.orgunit.refresh_from_db()
        assert self.orgunit.name == "Hacked"

    def test_superuser_can_edit_orgunit(self):
        superuser = DuskenUser.objects.create_superuser("root", email="root@example.com", password="mypassword")
        self.client.force_login(superuser)
        response = self.client.post(reverse("orgunit-edit", args=[self.orgunit.slug]), self.data)
        assert response.status_code == status.HTTP_302_FOUND

    def test_edit_page_includes_contact_person_widget_media(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("orgunit-edit", args=[self.orgunit.slug]))
        assert response.status_code == status.HTTP_200_OK
        # The contact person autocomplete needs the tomselect JS from form media
        assert "django_tomselect" in response.content.decode()

    def test_description_is_sanitized(self):
        self.orgunit.description = '<p onclick="alert(1)">Hello <b>world</b></p><script>alert(2)</script>'
        self.orgunit.save()
        self.client.force_login(self.volunteer)
        response = self.client.get(reverse("orgunit-detail", args=[self.orgunit.slug]))
        content = response.content.decode()
        assert "<b>world</b>" in content
        assert "<script>" not in content
        assert "onclick" not in content


class OrgUnitMemberAPITestCase(APITestCase):
    def setUp(self):
        volunteers = Group.objects.create(name="Volunteers")
        GroupProfile.objects.create(group=volunteers, type=GroupProfile.TYPE_VOLUNTEERS)
        self.group = Group.objects.create(name="Unit members")
        self.admin_group = Group.objects.create(name="Unit admins")
        self.orgunit = OrgUnit.objects.create(name="Unit", slug="unit", group=self.group, admin_group=self.admin_group)

        self.admin = DuskenUser.objects.create_user("admin", email="admin@example.com", first_name="Ada")
        self.admin.groups.add(volunteers, self.group, self.admin_group)
        self.member = DuskenUser.objects.create_user("member", email="member@example.com", first_name="Bob")
        self.member.groups.add(volunteers, self.group)
        self.outsider = DuskenUser.objects.create_user("outsider", email="outsider@example.com")

        self.list_url = reverse("orgunit-member-list", args=[self.orgunit.slug])

    def detail_url(self, user):
        return reverse("orgunit-member-detail", args=[self.orgunit.slug, user.pk])

    def test_list_members(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert [(m["id"], m["role"]) for m in response.data] == [(self.admin.pk, "admin"), (self.member.pk, "member")]
        assert response.data[1]["membership"] is None

    def test_add_member(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.list_url, {"user": self.outsider.pk, "role": "member"}, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["role"] == "member"
        assert self.outsider.has_group(self.group)
        assert not self.outsider.has_group(self.admin_group)
        assert self.outsider.is_volunteer

    def test_add_admin(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.list_url, {"user": self.outsider.pk, "role": "admin"}, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["role"] == "admin"
        assert self.outsider.has_group(self.group)
        assert self.outsider.has_group(self.admin_group)

    def test_add_existing_member_fails(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.list_url, {"user": self.member.pk, "role": "admin"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "user" in response.data
        assert not self.member.has_group(self.admin_group)

    def test_invalid_role_fails(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.list_url, {"user": self.outsider.pk, "role": "owner"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "role" in response.data

    def test_change_role(self):
        self.client.force_login(self.admin)
        response = self.client.patch(self.detail_url(self.member), {"role": "admin"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["role"] == "admin"
        assert self.member.has_group(self.admin_group)

        response = self.client.patch(self.detail_url(self.member), {"role": "member"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["role"] == "member"
        assert not self.member.has_group(self.admin_group)
        assert self.member.has_group(self.group)

    def test_change_role_when_all_members_are_admins_fails(self):
        self.orgunit.admin_group = self.group
        self.orgunit.save()
        self.client.force_login(self.admin)
        response = self.client.patch(self.detail_url(self.admin), {"role": "member"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_remove_member(self):
        self.client.force_login(self.admin)
        response = self.client.delete(self.detail_url(self.member))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not self.member.has_group(self.group)

    def test_remove_non_member_returns_404(self):
        self.client.force_login(self.admin)
        response = self.client.delete(self.detail_url(self.outsider))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unknown_orgunit_returns_404(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("orgunit-member-list", args=["nope"]))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_superuser_can_manage_orgunit_without_admin_group(self):
        self.orgunit.admin_group = None
        self.orgunit.save()
        superuser = DuskenUser.objects.create_superuser("root", email="root@example.com", password="mypassword")
        self.client.force_login(superuser)
        assert self.client.get(self.list_url).status_code == status.HTTP_200_OK
        response = self.client.post(self.list_url, {"user": self.outsider.pk}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_non_admin_cannot_manage_members(self):
        self.client.force_login(self.member)
        assert self.client.get(self.list_url).status_code == status.HTTP_403_FORBIDDEN
        response = self.client.post(self.list_url, {"user": self.outsider.pk}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert (
            self.client.patch(self.detail_url(self.member), {"role": "admin"}).status_code == status.HTTP_403_FORBIDDEN
        )
        assert self.client.delete(self.detail_url(self.admin)).status_code == status.HTTP_403_FORBIDDEN
        assert not self.outsider.has_group(self.group)
        assert self.admin.has_group(self.admin_group)

    def test_anonymous_cannot_manage_members(self):
        assert self.client.get(self.list_url).status_code == status.HTTP_403_FORBIDDEN

    def test_session_auth_requires_csrf_token(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.admin)
        response = client.post(self.list_url, {"user": self.outsider.pk}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not self.outsider.has_group(self.group)

    def test_old_endpoints_are_removed(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            "/api/orgunit/add/user/", {"user": self.outsider.pk, "orgunit": "unit", "type": "admin"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert self.client.get("/api/orgunit/remove/user/").status_code == status.HTTP_404_NOT_FOUND

    def test_edit_users_page_renders_member_config(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("orgunit-edit-users", args=[self.orgunit.slug]))
        assert response.status_code == status.HTTP_200_OK
        assert response.context["members_config"]["membersUrl"] == self.list_url
        assert response.context["members_config"]["currentUserId"] == self.admin.pk
        assert b'id="orgunit-members-config"' in response.content
        assert b'class="form-select js-role"' in response.content
