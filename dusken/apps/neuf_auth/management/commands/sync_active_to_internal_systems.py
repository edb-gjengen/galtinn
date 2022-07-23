from datetime import datetime

from django.core.management.base import BaseCommand

from dusken.apps.neuf_auth.ssh import create_home_dir
from dusken.apps.neuf_ldap.models import LdapGroup, LdapUser
from dusken.apps.neuf_ldap.utils import (
    create_ldap_automount,
    create_ldap_user,
    ldap_update_user_details,
    ldap_update_user_groups,
)
from dusken.models import DuskenUser, GroupProfile


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
    COUNTS = dict(create=0, update=0, in_sync=0)
    verbosity = 1
    dry_run = False

    def __init__(self):
        super().__init__()
        self.volunteer_group = GroupProfile.objects.get(type=GroupProfile.TYPE_VOLUNTEERS).group

    def handle(self, *args, **options):
        self.verbosity = int(options["verbosity"])
        self.dry_run = bool(options["dry_run"])

        if self.verbosity >= 2:
            self.stdout.write(f"[{datetime.utcnow()}] Started sync job")

        # Get all active user from Dusken
        dusken_users_diffable = self.get_dusken_users_diffable()

        # Get all existing users in LDAP
        ldap_users_diffable = self.get_all_ldap_users_diffable()

        # Do actual sync
        self.sync_users(dusken_users_diffable, ldap_users_diffable, options["delete_group_memberships"])

        self.log_totals()

        if self.verbosity >= 2:
            self.stdout.write(f"[{datetime.utcnow()}] Finished sync job")

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

        if self.verbosity == 3:
            self.stdout.write(f"Found {len(dusken_users_diffable)} Dusken users")

        return dusken_users_diffable

    def get_all_ldap_users_diffable(self):
        ldap_users_diffable = {}
        ldap_users = LdapUser.objects.all()

        for u in ldap_users:
            ldap_groups = LdapGroup.objects.filter(name__startswith=self.SYNC_GROUP_PREFIX)
            ldap_groups = ldap_groups.filter(members__contains=u.username).values_list("name", flat=True)

            ldap_users_diffable[u.username] = {
                "username": u.username,
                "ldap_password": u.password,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "email": u.email,
                "groups": ldap_groups,
            }
        if self.verbosity == 3:
            self.stdout.write(f"Found {len(ldap_users_diffable)} LDAP users")

        return ldap_users_diffable

    def sync_users(self, dusken_users_diffable, ldap_users_diffable, delete_group_memberships):
        for username, user in dusken_users_diffable.items():
            if username not in ldap_users_diffable:
                # Create
                create_ldap_user(user, dry_run=self.dry_run)
                create_home_dir(user["username"], dry_run=self.dry_run)
                create_ldap_automount(user["username"], dry_run=self.dry_run)

                self.COUNTS["create"] += 1
                if self.verbosity >= 2:
                    self.stdout.write(f"[CREATED] Dusken user {username} is not in LDAP")
            elif not self.user_details_in_sync(user, ldap_users_diffable[username]) or not self.user_groups_in_sync(
                user, ldap_users_diffable[username], delete_group_memberships
            ):
                # Update
                ldap_update_user_details(user, dry_run=self.dry_run)
                ldap_update_user_groups(
                    user,
                    ldap_users_diffable[username],
                    dry_run=self.dry_run,
                    delete_group_memberships=delete_group_memberships,
                )

                self.COUNTS["update"] += 1
                if self.verbosity >= 2:
                    self.stdout.write(f"[UPDATED] Dusken user {username} is out of sync with LDAP")
            else:
                # In sync :-)
                self.COUNTS["in_sync"] += 1
                if self.verbosity == 3:
                    self.stdout.write(f"[OK] Dusken user {username} is in sync with LDAP")

    def log_totals(self):
        if self.COUNTS["create"] > 0 or self.COUNTS["update"] > 0 or self.verbosity >= 2:
            self.stdout.write(
                "Totals: created {}, updated {}, in sync: {}".format(
                    self.COUNTS["create"], self.COUNTS["update"], self.COUNTS["in_sync"]
                )
            )

    def user_details_in_sync(self, dusken_user, ldap_user):
        for attr in self.DIFF_ATTRIBUTES:
            if dusken_user[attr] != ldap_user[attr]:
                if self.verbosity >= 2:
                    self.stdout.write(
                        "{}: {} (Dusken) != {} (LDAP)".format(
                            dusken_user["username"], dusken_user[attr], ldap_user[attr]
                        )
                    )
                return False

        return True

    def user_groups_in_sync(self, dusken_user, ldap_user, delete_group_memberships):
        # Compare set of group names
        dusken_groups = set(dusken_user["groups"])
        ldap_groups = set(ldap_user["groups"])
        if delete_group_memberships:
            in_sync = dusken_groups == ldap_groups
            if not in_sync and self.verbosity >= 2:
                self.stdout.write(
                    "{}: {} (Dusken) != {} (LDAP)".format(
                        dusken_user["username"], ",".join(dusken_groups), ",".join(ldap_groups)
                    )
                )
        else:
            missing_groups = dusken_groups.difference(ldap_groups)
            in_sync = len(missing_groups) == 0
            if not in_sync and self.verbosity >= 2:
                self.stdout.write(
                    "{}: Not in LDAP groups: {}".format(dusken_user["username"], ",".join(missing_groups))
                )

        return in_sync
