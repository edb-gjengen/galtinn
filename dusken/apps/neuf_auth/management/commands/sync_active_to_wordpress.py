import json
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from dusken.models import DuskenUser, GroupProfile


class Command(BaseCommand):
    # TODO: Replace this weird stuff with https://developer.wordpress.org/rest-api/reference/users/#create-a-user
    help = "Syncs users from Dusken to our Wordpress installations (to allow SSO)"

    def __init__(self):
        super().__init__()
        self.volunteer_group = GroupProfile.objects.get(type=GroupProfile.TYPE_VOLUNTEERS).group

    def get_active_users(self):
        users = DuskenUser.objects.filter(groups=self.volunteer_group, is_active=True)
        return users.filter(authprofile__isnull=False, authprofile__username_updated__isnull=False)

    def handle(self, *_args, **_options):
        active_users = self.get_active_users()
        users_out = [[u.username, u.first_name, u.last_name, u.email] for u in active_users]

        with Path(settings.WP_OUT_FILENAME).open("w+", encoding="utf-8") as out_file:
            json.dump(users_out, out_file, ensure_ascii=False)

        for load_path in settings.WP_LOAD_PATHS:
            cmd = [
                "php",
                settings.WP_PHP_SCRIPT_PATH / "import_users.php",
                settings.WP_OUT_FILENAME,
                load_path,
            ]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)  # noqa: S603
            script_response = proc.stdout.read()

            if len(script_response) != 0:
                self.stdout.write(script_response.decode("utf-8"))
