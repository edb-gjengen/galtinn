import unittest

from django.test import TestCase

from dusken.apps.neuf_auth.ssh import create_home_dir, get_home_dirs, homedir_exists


@unittest.skip("Skip integration tests")
class SSHTestCase(TestCase):
    def test_create_home_dir(self):
        with self.settings(
            FILESERVER_HOST="localhost",
            FILESERVER_SSH_KEY_PATH="/home/nikolark/.ssh/id_rsa",
            FILESERVER_SSH_USER="nikolark",
        ):
            username = "nikolark"
            res = create_home_dir(username)
            self.assertTrue(res)
            self.assertTrue(homedir_exists(username))

    def test_list_homedirs(self):
        with self.settings(
            FILESERVER_HOST="localhost",
            FILESERVER_SSH_KEY_PATH="/home/nikolark/.ssh/id_rsa",
            FILESERVER_SSH_USER="nikolark",
        ):
            homedirs = get_home_dirs()
            self.assertTrue(homedirs)

    def test_homedir_exists(self):
        with self.settings(
            FILESERVER_HOST="localhost",
            FILESERVER_SSH_KEY_PATH="/home/nikolark/.ssh/id_rsa",
            FILESERVER_SSH_USER="nikolark",
        ):
            self.assertTrue(homedir_exists(".X11-unix"))
