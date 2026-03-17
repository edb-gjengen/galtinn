import pytest
from django.contrib.auth.models import Group

from dusken.models import DuskenUser, OrgUnit
from dusken.models.users import GroupProfile


@pytest.fixture
def volunteer_group(db):
    group = Group.objects.create(name="volunteers")
    GroupProfile.objects.create(group=group, type=GroupProfile.TYPE_VOLUNTEERS)
    return group


@pytest.fixture
def member_group(db):
    return Group.objects.create(name="test-members")


@pytest.fixture
def admin_group(db):
    return Group.objects.create(name="test-admins")


@pytest.fixture
def orgunit(member_group, admin_group):
    return OrgUnit.objects.create(
        name="Test Unit",
        slug="test-unit",
        is_active=True,
        group=member_group,
        admin_group=admin_group,
    )


@pytest.fixture
def admin_user(orgunit):
    user = DuskenUser.objects.create_user("admin", email="admin@example.com", password="pass")
    orgunit.admin_group.user_set.add(user)
    orgunit.group.user_set.add(user)
    return user


@pytest.fixture
def superuser(db):
    return DuskenUser.objects.create_superuser("super", email="super@example.com", password="pass")


@pytest.fixture
def regular_user(db):
    return DuskenUser.objects.create_user("regular", email="regular@example.com", password="pass")


@pytest.fixture
def target_user(db):
    return DuskenUser.objects.create_user("target", email="target@example.com", password="pass")
