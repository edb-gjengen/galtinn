from django.core.management.base import BaseCommand

from dusken.apps.neuf_ldap.models import LdapGroup, LdapUser

# from neuf_auth.ssh import get_home_dirs
from dusken.models import DuskenUser, GroupProfile


class Command(BaseCommand):
    help = "List stale LDAP users not in the Dusken volunteer group"
    verbosity = 1

    def add_arguments(self, parser):
        parser.add_argument(
            "--exclude-existing",
            action="store_true",
            dest="exclude_existing",
            default=False,
            help="Excludes users in the LDAP group dns-aktiv from the list",
        )

    def __init__(self):
        super().__init__()
        self.group_profile = GroupProfile.objects.get(type=GroupProfile.TYPE_VOLUNTEERS)

    def handle(self, *args, **options):
        self.verbosity = int(options["verbosity"])

        inside_users_active = self.get_dusken_users()
        ldap_users_all = self.get_ldap_users(options["exclude_existing"])
        stale_ldap_users = ldap_users_all - inside_users_active

        self.stdout.write(
            "{} LDAP users not in group {} in Dusken:\n{}".format(
                len(stale_ldap_users), self.group_profile.posix_name, "\n".join(stale_ldap_users)
            )
        )
        self.stdout.write("")

    def get_dusken_users(self):
        users = DuskenUser.objects.filter(groups=self.group_profile.group, is_active=True, username__isnull=False)
        users = users.values_list("username", flat=True)

        if self.verbosity == 3:
            self.stdout.write(f"Found {len(users)} Dusken users")

        return set(users)

    def get_ldap_users(self, exclude_existing):
        # TODO: What about system users, should they be allowlisted?
        ldap_users = LdapUser.objects.all()
        if exclude_existing:
            ldap_active_members = LdapGroup.objects.get(name=self.group_profile.posix_name).members
            ldap_users = ldap_users.exclude(username__in=ldap_active_members)
        ldap_users = ldap_users.values_list("username", flat=True)

        if self.verbosity == 3:
            self.stdout.write(f"Found {len(ldap_users)} LDAP users")

        return set(ldap_users)
