import sys
from distutils.util import strtobool
from pathlib import Path

from django.core.management.base import BaseCommand

from dusken.apps.neuf_ldap.models import LdapAutomountHome, LdapGroup, LdapUser


class Command(BaseCommand):
    args = "filename"
    help = "Takes a file with a newline separated list of usernames and removes matching users (with associated data) from LDAP"
    dry_run = False
    no_prompt = False

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            default=False,
            help="Dry run when syncronizing, does not save anything.",
        )

        parser.add_argument(
            "--no-prompt",
            action="store_true",
            dest="no_prompt",
            default=False,
            help="Does not prompt for deletion",
        )

    def handle(self, *args, **options):
        self.dry_run = bool(options["dry_run"])
        self.no_prompt = bool(options["no_prompt"])

        if len(args) != 1:
            self.stderr.write("Missing filename")
            sys.exit()

        filename = args[0]
        if not Path(filename).is_file():
            self.stderr.write(f"{filename} is not a file")
            sys.exit()

        with Path(filename).open() as f:
            usernames = f.read().strip().split()
            self.stdout.write(f"Found {len(usernames)} usernames in file")

            ldap_users = LdapUser.objects.filter(username__in=usernames)
            self.stdout.write(f"Matched {ldap_users.count()} PosixUser objects")
            for user in ldap_users:
                username = user.username
                self.delete_automount_entry(username)
                self.delete_group_memberships(username)
                self.delete_personal_group(username)
                self.delete_ldap_user(user)

    def _user_confirmes_deletion(self, username, object_type):
        if self.no_prompt:
            return True

        val = input(f"Do you want to permanently remove {object_type} '{username}'? [y/N]")
        try:
            confirmed = strtobool(val)
        except ValueError:
            confirmed = False

        return confirmed

    def delete_group_memberships(self, username):
        # FIXME: Horribly inefficient
        groups_with_memberships = LdapGroup.objects.filter(members__contains=username)
        if groups_with_memberships.count() == 0:
            return

        group_list_formatted = ", ".join(groups_with_memberships.values_list("name", flat=True))
        self.stdout.write(f"Listing '{username}' group memberships: {group_list_formatted}")

        if self._user_confirmes_deletion(username, "all PosixGroup memberships for"):
            for g in groups_with_memberships:
                if not self.dry_run:
                    g.members.remove(username)
                    g.save()
                self.stdout.write(f"Removed PosixGroup membership in {g.name} for '{username}'")

        else:
            self.stdout.write(f"Did nothing with '{username}' membership in groups: {group_list_formatted}")

    def delete_personal_group(self, username):
        if self._user_confirmes_deletion(username, "personal PosixGroup for"):
            if not self.dry_run:
                LdapGroup.objects.filter(name=username).delete()
            self.stdout.write(f"Removed personal PosixGroup for '{username}'")
        else:
            self.stdout.write(f"Did nothing with personal PosixGroup for '{username}'")

    def delete_automount_entry(self, username):
        if self._user_confirmes_deletion(username, "Automount entry for"):
            if not self.dry_run:
                LdapAutomountHome.objects.filter(username=username).delete()
            self.stdout.write(f"Removed automount for '{username}'")
        else:
            self.stdout.write(f"Did nothing with automount for '{username}'")

    def delete_ldap_user(self, user):
        username = user.username
        if self._user_confirmes_deletion(username, "PosixUser"):
            if not self.dry_run:
                user.delete()
            self.stdout.write(f"Removed '{username}'")
        else:
            self.stdout.write(f"Did nothing with '{username}'")
