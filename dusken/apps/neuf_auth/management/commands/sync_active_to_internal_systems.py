import re
import traceback
from collections import defaultdict
from datetime import UTC, datetime, timedelta

import ldap
from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError

from dusken.apps.neuf_auth.ssh import create_home_dir, get_home_dirs
from dusken.apps.neuf_ldap.models import LdapGroup, LdapUser
from dusken.apps.neuf_ldap.utils import (
    create_ldap_group,
    create_ldap_user,
    ldap_update_user_details,
    ldap_update_user_groups,
)
from dusken.models import DuskenUser, GroupProfile

VERBOSE = 2
VERY_VERBOSE = 3


class Command(BaseCommand):
    help = "Synchronizes users in volunteer group from Dusken to LDAP"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            default=False,
            help="Dry run when syncronizing, does not save anything.",
        )

        parser.add_argument(
            "--delete-group-memberships",
            action="store_true",
            dest="delete_group_memberships",
            default=False,
            help="Toggle if group memberships syncronization should delete or not",
        )

    DIFF_ATTRIBUTES = ["first_name", "last_name", "email", "ldap_password"]
    SYNC_GROUP_PREFIX = "dns-"
    # The sync creates a missing LDAP group only for a posix name of this form
    CREATABLE_GROUP_NAME = re.compile(r"dns-[a-z0-9]+(-[a-z0-9]+)*")
    COUNTS = {"create": 0, "update": 0, "in_sync": 0, "home_dir": 0, "failed": 0}
    # More missing home directories than this means a wrong path or an unmounted file system, not lost homes
    MAX_NEW_HOME_DIRS = 50
    # The users that failed when the run last exited with an error, and when. A failed run is posted to Discord,
    # so the same failures exit 0 again until FAILED_ALERT_INTERVAL has passed.
    FAILED_CACHE_KEY = "sync_active_to_internal_systems:failed"
    FAILED_ALERT_INTERVAL = timedelta(hours=24)
    verbosity = 1
    dry_run = False

    def __init__(self):
        super().__init__()
        self.volunteer_group = GroupProfile.objects.get(type=GroupProfile.TYPE_VOLUNTEERS).group

    def handle(self, *_args, **options):
        self.verbosity = int(options["verbosity"])
        self.dry_run = bool(options["dry_run"])

        if self.verbosity >= VERBOSE:
            self.stdout.write(f"[{datetime.now(tz=UTC)}] Started sync job")

        # Get all active user from Dusken
        dusken_users_diffable = self.get_dusken_users_diffable()

        self.create_missing_groups(dusken_users_diffable)

        # Get all existing users in LDAP
        ldap_users_diffable = self.get_all_ldap_users_diffable()

        # Do actual sync
        failed = self.sync_users(dusken_users_diffable, ldap_users_diffable, options["delete_group_memberships"])
        # Accounts created in this run got their home directory then
        existing = set(dusken_users_diffable) & set(ldap_users_diffable)
        failed += self.create_missing_home_dirs(existing - set(failed))

        self.log_totals()

        if failed and self.should_alert(failed):
            raise CommandError(f"Sync failed for {len(failed)} users: {', '.join(failed)}")
        if not self.dry_run and not failed:
            cache.delete(self.FAILED_CACHE_KEY)

        if self.verbosity >= VERBOSE:
            self.stdout.write(f"[{datetime.now(tz=UTC)}] Finished sync job")

        # Voila!

    def get_dusken_users_diffable(self):
        dusken_users_diffable = {}
        dusken_users = DuskenUser.objects.filter(groups=self.volunteer_group, is_active=True)
        dusken_users = dusken_users.filter(authprofile__isnull=False, authprofile__username_updated__isnull=False)
        dusken_users = dusken_users.select_related("authprofile").prefetch_related("groups", "groups__profile")

        for u in dusken_users:
            posix_groups = u.groups.exclude(profile__posix_name="")
            posix_groups = posix_groups.values_list("profile__posix_name", flat=True)
            dusken_groups = list(filter(lambda x: x is not None, posix_groups))
            dusken_users_diffable[u.username] = {
                "username": u.username,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "ldap_password": u.authprofile.ldap_password,
                "email": u.email,
                "groups": dusken_groups,
            }

        if self.verbosity == VERY_VERBOSE:
            self.stdout.write(f"Found {len(dusken_users_diffable)} Dusken users")

        return dusken_users_diffable

    def create_missing_groups(self, dusken_users_diffable):
        wanted = {g for user in dusken_users_diffable.values() for g in user["groups"]}
        wanted = {g for g in wanted if self.CREATABLE_GROUP_NAME.fullmatch(g)}
        existing = set(LdapGroup.objects.filter(name__in=wanted).values_list("name", flat=True))

        gid = 0
        for name in sorted(wanted - existing):
            gid = create_ldap_group(name, after=gid, dry_run=self.dry_run)
            self.stdout.write(f"[CREATED] Group {name} with gid {gid}")

    def get_all_ldap_users_diffable(self):
        # One search for every synced group's members, not one per user
        ldap_user_groups = defaultdict(list)
        for g in LdapGroup.objects.filter(name__startswith=self.SYNC_GROUP_PREFIX):
            for member in g.members:
                ldap_user_groups[member].append(g.name)

        ldap_users_diffable = {}
        ldap_users = LdapUser.objects.all()

        for u in ldap_users:
            ldap_users_diffable[u.username] = {
                "username": u.username,
                "ldap_password": u.password,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "email": u.email,
                "groups": ldap_user_groups[u.username],
            }
        if self.verbosity == VERY_VERBOSE:
            self.stdout.write(f"Found {len(ldap_users_diffable)} LDAP users")

        return ldap_users_diffable

    def sync_users(self, dusken_users_diffable, ldap_users_diffable, delete_group_memberships):
        """Sync each user on its own, so one failure does not stop the rest. Returns the usernames that failed."""
        failed = []
        for username, user in dusken_users_diffable.items():
            try:
                self.sync_user(user, ldap_users_diffable.get(username), delete_group_memberships)
            except ldap.SERVER_DOWN:
                # Every user after this one would fail the same way
                raise
            except Exception:  # noqa: BLE001
                failed.append(username)
                self.COUNTS["failed"] += 1
                self.stderr.write(f"[FAILED] Dusken user {username}\n{traceback.format_exc()}")

        return failed

    def create_missing_home_dirs(self, usernames):
        """Create the home directories the file server lacks for these accounts. Returns what failed."""
        try:
            missing = sorted(usernames - set(get_home_dirs()))
        except Exception:  # noqa: BLE001
            self.stderr.write(
                f"[FAILED] Listing home directories on {settings.FILESERVER_HOST}\n{traceback.format_exc()}"
            )
            return ["(home directory listing)"]

        if len(missing) > self.MAX_NEW_HOME_DIRS:
            self.stderr.write(
                f"[FAILED] {len(missing)} home directories missing in {settings.FILESERVER_HOME_PATH}, "
                f"more than MAX_NEW_HOME_DIRS ({self.MAX_NEW_HOME_DIRS}); created none",
            )
            return ["(too many missing home directories)"]

        failed = []
        for username in missing:
            if create_home_dir(username, dry_run=self.dry_run):
                self.COUNTS["home_dir"] += 1
                self.stdout.write(f"[CREATED] Home directory for {username}")
            else:
                failed.append(username)
                self.COUNTS["failed"] += 1
                self.stderr.write(f"[FAILED] Home directory for {username}")

        return failed

    def should_alert(self, failed):
        """True if a user failed who was not in the last alert, or once FAILED_ALERT_INTERVAL has passed."""
        if self.dry_run:
            return True

        now = datetime.now(tz=UTC)
        last = cache.get(self.FAILED_CACHE_KEY)
        if last and set(failed) <= set(last["users"]) and now - last["at"] < self.FAILED_ALERT_INTERVAL:
            self.stderr.write(
                f"No alert: the {len(failed)} failed users were all in the last one, {last['at']:%Y-%m-%d %H:%M} UTC"
            )
            return False

        cache.set(self.FAILED_CACHE_KEY, {"users": sorted(failed), "at": now}, timeout=None)
        return True

    @staticmethod
    def check_password_hash(user):
        # The auth profile's default is "", which would empty or remove the account's userPassword
        if not user["ldap_password"]:
            raise RuntimeError("No LDAP password hash in Galtinn")

    def sync_user(self, user, ldap_user, delete_group_memberships):
        username = user["username"]
        if ldap_user is None:
            # Create
            self.check_password_hash(user)
            if not create_ldap_user(user, dry_run=self.dry_run):
                raise RuntimeError("LDAP user not created")
            if not create_home_dir(username, dry_run=self.dry_run):
                raise RuntimeError("Home directory not created")

            self.COUNTS["create"] += 1
            if self.verbosity >= VERBOSE:
                self.stdout.write(f"[CREATED] Dusken user {username} is not in LDAP")
        elif not self.user_details_in_sync(user, ldap_user) or not self.user_groups_in_sync(
            user,
            ldap_user,
            delete_group_memberships,
        ):
            # Update
            self.check_password_hash(user)
            ldap_update_user_details(user, dry_run=self.dry_run)
            ldap_update_user_groups(
                user,
                ldap_user,
                dry_run=self.dry_run,
                delete_group_memberships=delete_group_memberships,
            )

            self.COUNTS["update"] += 1
            if self.verbosity >= VERBOSE:
                self.stdout.write(f"[UPDATED] Dusken user {username} is out of sync with LDAP")
        else:
            # In sync :-)
            self.COUNTS["in_sync"] += 1
            if self.verbosity == VERBOSE:
                self.stdout.write(f"[OK] Dusken user {username} is in sync with LDAP")

    def log_totals(self):
        if any(self.COUNTS[k] for k in ("create", "update", "home_dir", "failed")) or self.verbosity >= VERBOSE:
            self.stdout.write(
                "Totals: created {}, updated {}, in sync: {}, home directories created: {}, failed: {}".format(
                    self.COUNTS["create"],
                    self.COUNTS["update"],
                    self.COUNTS["in_sync"],
                    self.COUNTS["home_dir"],
                    self.COUNTS["failed"],
                ),
            )

    def user_details_in_sync(self, dusken_user, ldap_user):
        for attr in self.DIFF_ATTRIBUTES:
            if dusken_user[attr] != ldap_user[attr]:
                if self.verbosity >= VERBOSE:
                    self.stdout.write(
                        "{}: {} (Dusken) != {} (LDAP)".format(
                            dusken_user["username"],
                            dusken_user[attr],
                            ldap_user[attr],
                        ),
                    )
                return False

        return True

    def user_groups_in_sync(self, dusken_user, ldap_user, delete_group_memberships):
        # Compare set of group names
        dusken_groups = set(dusken_user["groups"])
        ldap_groups = set(ldap_user["groups"])
        if delete_group_memberships:
            in_sync = dusken_groups == ldap_groups
            if not in_sync and self.verbosity >= VERBOSE:
                self.stdout.write(
                    "{}: {} (Dusken) != {} (LDAP)".format(
                        dusken_user["username"],
                        ",".join(dusken_groups),
                        ",".join(ldap_groups),
                    ),
                )
        else:
            missing_groups = dusken_groups.difference(ldap_groups)
            in_sync = len(missing_groups) == 0
            if not in_sync and self.verbosity >= VERBOSE:
                self.stdout.write(
                    "{}: Not in LDAP groups: {}".format(dusken_user["username"], ",".join(missing_groups)),
                )

        return in_sync
