from types import SimpleNamespace
from unittest import mock

import ldap
import pytest
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from dusken.apps.neuf_auth.management.commands import sync_active_to_internal_systems as sync
from dusken.apps.neuf_auth.models import AuthProfile
from dusken.apps.neuf_ldap.utils import create_ldap_group
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
            "get_home_dirs": mock.Mock(side_effect=lambda: [u.username for u in self.ldap_users]),
            "ldap_update_user_details": mock.Mock(),
            "ldap_update_user_groups": mock.Mock(),
        }
        self.mocks = {}
        for name, value in patches.items():
            patcher = mock.patch.object(sync, name, value)
            self.mocks[name] = patcher.start()
            self.addCleanup(patcher.stop)
        sync.Command.COUNTS = {"create": 0, "update": 0, "in_sync": 0, "home_dir": 0, "failed": 0}
        cache.clear()

    def add_user(self, username, *groups, in_ldap=True, ldap_password=None):
        user = DuskenUser.objects.create_user(username, email=f"{username}@example.com", first_name=username)
        user.groups.add(self.groups["dns-aktiv"], *(self.groups[g] for g in groups))
        ldap_password = "{SSHA}x" if ldap_password is None else ldap_password
        AuthProfile.objects.create(user=user, ldap_password=ldap_password, username_updated=timezone.now())
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
        self.mocks["create_ldap_group"].assert_called_once_with("dns-new", after=0, dry_run=False)

    def test_one_failure_does_not_stop_the_rest(self):
        self.add_user("alice", "dns-ggg")
        self.add_user("carol", in_ldap=False)
        self.add_user("dave", in_ldap=False)
        self.mocks["create_ldap_user"].side_effect = lambda user, **_: user["username"] != "carol"
        with pytest.raises(CommandError, match="carol"):
            call_command("sync_active_to_internal_systems")
        created = [c.args[0]["username"] for c in self.mocks["create_ldap_user"].call_args_list]
        assert sorted(created) == ["carol", "dave"]
        assert sync.Command.COUNTS == {"create": 1, "update": 0, "in_sync": 1, "home_dir": 0, "failed": 1}

    def test_failed_home_dir_fails_the_run(self):
        self.add_user("carol", in_ldap=False)
        self.mocks["create_home_dir"].return_value = False
        with pytest.raises(CommandError, match="carol"):
            call_command("sync_active_to_internal_systems")

    def test_ldap_down_stops_the_run(self):
        self.add_user("carol", in_ldap=False)
        self.add_user("dave", in_ldap=False)
        self.mocks["create_ldap_user"].side_effect = ldap.SERVER_DOWN
        with pytest.raises(ldap.SERVER_DOWN):
            call_command("sync_active_to_internal_systems")
        assert self.mocks["create_ldap_user"].call_count == 1

    def test_same_failures_alert_once_a_day(self):
        self.add_user("carol", in_ldap=False)
        self.add_user("dave", in_ldap=False)
        failing = {"carol"}
        self.mocks["create_ldap_user"].side_effect = lambda user, **_: user["username"] not in failing

        with pytest.raises(CommandError, match="carol"):
            call_command("sync_active_to_internal_systems")
        call_command("sync_active_to_internal_systems")  # carol again: no alert

        failing.add("dave")
        with pytest.raises(CommandError, match="dave"):
            call_command("sync_active_to_internal_systems")
        failing.discard("dave")
        call_command("sync_active_to_internal_systems")  # fewer failures: no alert

        last = cache.get(sync.Command.FAILED_CACHE_KEY)
        cache.set(sync.Command.FAILED_CACHE_KEY, {**last, "at": last["at"] - sync.Command.FAILED_ALERT_INTERVAL})
        with pytest.raises(CommandError, match="carol"):
            call_command("sync_active_to_internal_systems")

    def test_success_forgets_the_last_alert(self):
        self.add_user("carol", in_ldap=False)
        self.mocks["create_ldap_user"].return_value = False
        with pytest.raises(CommandError):
            call_command("sync_active_to_internal_systems")

        self.mocks["create_ldap_user"].return_value = True
        call_command("sync_active_to_internal_systems")
        assert cache.get(sync.Command.FAILED_CACHE_KEY) is None

    def test_dry_run_always_alerts_and_keeps_no_state(self):
        self.add_user("carol", in_ldap=False)
        self.mocks["create_ldap_user"].return_value = False
        for _ in range(2):
            with pytest.raises(CommandError):
                call_command("sync_active_to_internal_systems", "--dry-run")
        assert cache.get(sync.Command.FAILED_CACHE_KEY) is None

    def test_empty_password_hash_is_not_written(self):
        self.add_user("carol", in_ldap=False, ldap_password="")
        self.add_user("dave", ldap_password="")
        self.ldap_users[-1].password = "{SSHA}old"  # noqa: S105
        with pytest.raises(CommandError, match="carol, dave"):
            call_command("sync_active_to_internal_systems")
        self.mocks["create_ldap_user"].assert_not_called()
        self.mocks["ldap_update_user_details"].assert_not_called()

    def test_dry_run_reports_the_gids_a_real_run_takes(self):
        self.add_user("alice", "dns-new")
        self.groups["dns-newer"] = Group.objects.create(name="dns-newer")
        GroupProfile.objects.create(group=self.groups["dns-newer"], posix_name="dns-newer")
        self.groups["dns-newer"].user_set.add(DuskenUser.objects.get(username="alice"))
        self.mocks["create_ldap_group"].side_effect = lambda *_, after, **__: max(after, 9100) + 1
        call_command("sync_active_to_internal_systems", "--dry-run")
        assert [c.kwargs["after"] for c in self.mocks["create_ldap_group"].call_args_list] == [0, 9101]

    def test_creates_missing_home_dirs_of_existing_accounts(self):
        self.add_user("alice")
        self.add_user("bob")
        self.add_user("carol", in_ldap=False)
        self.mocks["get_home_dirs"].side_effect = lambda: ["alice"]
        call_command("sync_active_to_internal_systems")
        homes = [c.args[0] for c in self.mocks["create_home_dir"].call_args_list]
        assert homes == ["carol", "bob"]  # carol's with her account, bob's as a repair

    def test_too_many_missing_home_dirs_creates_none(self):
        for i in range(sync.Command.MAX_NEW_HOME_DIRS + 1):
            self.add_user(f"user{i}")
        self.mocks["get_home_dirs"].side_effect = list
        with pytest.raises(CommandError, match="too many missing home directories"):
            call_command("sync_active_to_internal_systems")
        self.mocks["create_home_dir"].assert_not_called()

    def test_failed_home_dir_listing_fails_the_run(self):
        self.add_user("alice", "dns-ggg")
        self.mocks["get_home_dirs"].side_effect = OSError("ssh: connect to host c64.neuf.no")
        with pytest.raises(CommandError, match="home directory listing"):
            call_command("sync_active_to_internal_systems")
        assert sync.Command.COUNTS["in_sync"] == 1

    def test_failed_home_dir_repair_fails_the_run(self):
        self.add_user("alice")
        self.mocks["get_home_dirs"].side_effect = list
        self.mocks["create_home_dir"].return_value = False
        with pytest.raises(CommandError, match="alice"):
            call_command("sync_active_to_internal_systems")


def test_create_ldap_group_counts_up_from_after():
    groups = mock.Mock()
    groups.objects.filter.return_value.values_list.return_value = [9001, 9500]
    with mock.patch("dusken.apps.neuf_ldap.models.LdapGroup", groups):
        assert create_ldap_group("dns-a", dry_run=True) == 9501
        assert create_ldap_group("dns-b", after=9501, dry_run=True) == 9502
    groups.return_value.save.assert_not_called()
