from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

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

    def test_description_is_sanitized(self):
        self.orgunit.description = '<p onclick="alert(1)">Hello <b>world</b></p><script>alert(2)</script>'
        self.orgunit.save()
        self.client.force_login(self.volunteer)
        response = self.client.get(reverse("orgunit-detail", args=[self.orgunit.slug]))
        content = response.content.decode()
        assert "<b>world</b>" in content
        assert "<script>" not in content
        assert "onclick" not in content
