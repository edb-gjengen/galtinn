import logging
import os

from django.conf import settings
from fabric.api import settings as fab_settings
from fabric.context_managers import hide
from fabric.operations import sudo, run

logger = logging.getLogger(__name__)


def _get_fabric_settings(host_string):
    my_fab_settings = {
        'user': settings.FILESERVER_SSH_USER,
        'key_filename': settings.FILESERVER_SSH_KEY_PATH,
        'host_string': host_string,
        'warn_only': True
    }
    return my_fab_settings


def create_home_dir(username, dry_run=False):
    """
    Create homedir for username via shell script on fileserver host

    This use fabric (SSH) for running the remote command

    Ref: http://stackoverflow.com/questions/6741523/using-python-fabric-without-the-command-line-tool-fab
    """
    host_string = '{}@{}'.format(settings.FILESERVER_SSH_USER, settings.FILESERVER_HOST)
    fabric_settings = _get_fabric_settings(host_string)

    with fab_settings(**fabric_settings):
        with hide('running', 'stdout', 'stderr'):
            script_cmd = ' '.join([settings.FILESERVER_CREATE_HOMEDIR_SCRIPT, settings.FILESERVER_HOME_PATH, username])

            logger.debug('Creating homedir on {} with command: {}'.format(host_string, script_cmd))
            if not dry_run:
                return_val = sudo(script_cmd, shell=False)
                if not return_val:
                    return False

    return True


def get_home_dirs():
    host_string = '{}@{}'.format(settings.FILESERVER_SSH_USER, settings.FILESERVER_HOST)
    fabric_settings = _get_fabric_settings(host_string)

    separator = '\r\n{}'.format(settings.FILESERVER_HOME_PATH)
    if settings.FILESERVER_HOME_PATH[-1] != '/':
        separator = '{}/'.format(separator)

    with fab_settings(**fabric_settings):
        with hide('running', 'stdout', 'stderr'):
            homedirs_str = run('find {} -maxdepth 1 -type d'.format(settings.FILESERVER_HOME_PATH))
            homedirs = homedirs_str.split(separator)[1:]

    return homedirs


def homedir_exists(username):
    host_string = '{}@{}'.format(settings.FILESERVER_SSH_USER, settings.FILESERVER_HOST)
    fabric_settings = _get_fabric_settings(host_string)

    with fab_settings(**fabric_settings):
        with hide('running', 'stdout', 'stderr'):
            return run('ls {} &>/dev/null'.format(os.path.join(settings.FILESERVER_HOME_PATH, username)))
