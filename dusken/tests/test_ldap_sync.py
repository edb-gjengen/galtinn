from types import SimpleNamespace
from unittest import mock

import ldap
import pytest
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from dusken.apps.neuf_auth.management.commands import sync_active_to_internal_systems as sync
from dusken.apps.neuf_auth.models import AuthProfile
from dusken.models import DuskenUser, GroupProfile


class FakeLdapGroups:
    """Stands in for LdapGroup.objects with the two filters the sync uses."""

    def __init__(self, groups):
        self.groups = groups

    def filter(self, name__startswith=None, name__in=None):
        if name__startswith is not None:
            return [
                SimpleNamespace(name=n, members=m) for n, m in self.groups.items() if n.startswith(name__startswith)
            ]
        names = [n for n in self.groups if n in name__in]
        return mock.Mock(values_list=mock.Mock(return_value=names))


class LdapSyncTestCase(TestCase):
    def setUp(self):
        self.groups = {}
        for posix_name in ["dns-aktiv", "dns-ggg", "dns-new", "edb", "dns-Bad Name"]:
            self.groups[posix_name] = Group.objects.create(name=posix_name)
            GroupProfile.objects.create(
                group=self.groups[posix_name],
                posix_name=posix_name,
                type=GroupProfile.TYPE_VOLUNTEERS if posix_name == "dns-aktiv" else GroupProfile.TYPE_STANDARD,
            )

        self.ldap_groups = {"dns-aktiv": ["alice", "bob"], "dns-ggg": ["alice", "Bob"]}
        self.ldap_users = []
        patches = {
            "LdapGroup": mock.Mock(objects=FakeLdapGroups(self.ldap_groups)),
            "LdapUser": mock.Mock(objects=mock.Mock(all=lambda: self.ldap_users)),
            "create_ldap_group": mock.Mock(return_value=9100),
            "create_ldap_user": mock.Mock(return_value=True),
            "create_home_dir": mock.Mock(return_value=True),
            "create_ldap_automount": mock.Mock(return_value=True),
            "ldap_update_user_details": mock.Mock(),
            "ldap_update_user_groups": mock.Mock(),
        }
        self.mocks = {}
        for name, value in patches.items():
            patcher = mock.patch.object(sync, name, value)
            self.mocks[name] = patcher.start()
            self.addCleanup(patcher.stop)
        sync.Command.COUNTS = {"create": 0, "update": 0, "in_sync": 0, "failed": 0}

    def add_user(self, username, *groups, in_ldap=True):
        user = DuskenUser.objects.create_user(username, email=f"{username}@example.com", first_name=username)
        user.groups.add(self.groups["dns-aktiv"], *(self.groups[g] for g in groups))
        AuthProfile.objects.create(user=user, ldap_password="{SSHA}x", username_updated=timezone.now())
        if in_ldap:
            self.ldap_users.append(
                SimpleNamespace(
                    username=username,
                    password="{SSHA}x",
                    first_name=username,
                    last_name="",
                    email=f"{username}@example.com",
                ),
            )

    def test_reads_group_members_case_exact(self):
        self.add_user("alice")
        self.add_user("bob")
        users = sync.Command().get_all_ldap_users_diffable()
        assert sorted(users["alice"]["groups"]) == ["dns-aktiv", "dns-ggg"]
        assert users["bob"]["groups"] == ["dns-aktiv"]

    def test_creates_only_missing_dns_groups(self):
        self.add_user("alice", "dns-ggg", "dns-new", "edb", "dns-Bad Name")
        call_command("sync_active_to_internal_systems")
        self.mocks["create_ldap_group"].assert_called_once_with("dns-new", dry_run=False)

    def test_one_failure_does_not_stop_the_rest(self):
        self.add_user("alice", "dns-ggg")
        self.add_user("carol", in_ldap=False)
        self.add_user("dave", in_ldap=False)
        self.mocks["create_ldap_user"].side_effect = lambda user, **_: user["username"] != "carol"
        with pytest.raises(CommandError, match="carol"):
            call_command("sync_active_to_internal_systems")
        created = [c.args[0]["username"] for c in self.mocks["create_ldap_user"].call_args_list]
        assert sorted(created) == ["carol", "dave"]
        assert sync.Command.COUNTS == {"create": 1, "update": 0, "in_sync": 1, "failed": 1}

    def test_failed_home_dir_fails_the_run(self):
        self.add_user("carol", in_ldap=False)
        self.mocks["create_home_dir"].return_value = False
        with pytest.raises(CommandError, match="carol"):
            call_command("sync_active_to_internal_systems")
        self.mocks["create_ldap_automount"].assert_called_once_with("carol", dry_run=False)

    def test_ldap_down_stops_the_run(self):
        self.add_user("carol", in_ldap=False)
        self.add_user("dave", in_ldap=False)
        self.mocks["create_ldap_user"].side_effect = ldap.SERVER_DOWN
        with pytest.raises(ldap.SERVER_DOWN):
            call_command("sync_active_to_internal_systems")
        assert self.mocks["create_ldap_user"].call_count == 1
