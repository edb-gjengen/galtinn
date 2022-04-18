import logging
import os

from django.conf import settings
from fabric import Connection

logger = logging.getLogger(__name__)


def get_connection():
    connect_kwargs = {"key_filename": settings.FILESERVER_SSH_KEY_PATH}
    return Connection(settings.FILESERVER_HOST, user=settings.FILESERVER_SSH_USER, connect_kwargs=connect_kwargs)


def create_home_dir(username, dry_run=False):
    """
    Create homedir for username via shell script on fileserver host

    This use fabric (SSH) for running the remote command

    Ref: https://stackoverflow.com/questions/6741523/using-python-fabric-without-the-command-line-tool-fab
    """
    conn = get_connection()
    script_cmd = f"{settings.FILESERVER_CREATE_HOMEDIR_SCRIPT} {settings.FILESERVER_HOME_PATH} {username}"

    logger.debug(f"Creating homedir on {settings.FILESERVER_HOST} with command: {script_cmd}")
    if not dry_run:
        res = conn.sudo(script_cmd, warn=True, hide=True)
        if not res.ok:
            logger.info(f"Could not create homedir: {res.stdout if res.stdout else res.stderr}")
        return res.ok

    return True


def get_home_dirs():
    conn = get_connection()

    separator = "\n{}".format(settings.FILESERVER_HOME_PATH)
    if settings.FILESERVER_HOME_PATH[-1] != "/":
        separator = "{}/".format(separator)

    res = conn.run(f"find {settings.FILESERVER_HOME_PATH} -maxdepth 1 -type d", hide=True)
    return res.stdout.split(separator)[1:]


def homedir_exists(username):
    conn = get_connection()
    res = conn.run("ls {} &>/dev/null".format(os.path.join(settings.FILESERVER_HOME_PATH, username)), hide=True)
    return res.ok
