from django.core.management.base import BaseCommand

from apps.neuf_ldap.models import LdapGroup, LdapUser

# from neuf_auth.ssh import get_home_dirs
from dusken.models import DuskenUser, GroupProfile


class Command(BaseCommand):
    help = "List stale LDAP users not in the Dusken volunteer group"

    def add_arguments(self, parser):
        parser.add_argument(
            "--exclude-existing",
            action="store_true",
            dest="exclude_existing",
            default=False,
            help="Excludes users in the LDAP group dns-aktiv from the list",
        )

    options = {}

    def __init__(self):
        super().__init__()
        self.group_profile = GroupProfile.objects.get(type=GroupProfile.TYPE_VOLUNTEERS)

    def handle(self, *args, **options):
        self.options = options
        # home_dirs = get_home_dirs()
        inside_users_active = self.get_dusken_users()
        ldap_users_all = self.get_ldap_users()
        stale_ldap_users = ldap_users_all - inside_users_active
        # stale_homedirs = set(home_dirs) - inside_users_active

        self.stdout.write(
            "{} LDAP users not in group {} in Dusken:\n{}".format(
                len(stale_ldap_users), self.group_profile.posix_name, "\n".join(stale_ldap_users)
            )
        )
        self.stdout.write("")
        # self.stdout.write('{} stale home directories:\n{}'.format(
        #     len(stale_homedirs),
        #     '\n'.join(stale_homedirs)))

    def get_dusken_users(self):
        users = DuskenUser.objects.filter(groups=self.group_profile.group, is_active=True, username__isnull=False)
        users = users.values_list("username", flat=True)

        if self.options["verbosity"] == "3":
            self.stdout.write(f"Found {len(users)} Dusken users")

        return set(users)

    def get_ldap_users(self):
        # TODO: What about system users, should they be whitelisted?
        ldap_users = LdapUser.objects.all()
        if self.options["exclude_existing"]:
            ldap_active_members = LdapGroup.objects.get(name=self.group_profile.posix_name).members
            ldap_users = ldap_users.exclude(username__in=ldap_active_members)
        ldap_users = ldap_users.values_list("username", flat=True)

        if self.options["verbosity"] == "3":
            self.stdout.write(f"Found {len(ldap_users)} LDAP users")

        return set(ldap_users)
