import logging
import sys

from contextlib import contextmanager as _contextmanager
from fabric.api import run, sudo, env, cd, prefix, lcd
from fabric.api import local as lrun

env.use_ssh_config = True
env.hosts = ['dreamcast.neuf.no']
env.project_path = '/var/www/neuf.no/dusken'
env.user = 'gitdeploy'
env.activate = 'source {}/venv/bin/activate'.format(env.project_path)


@_contextmanager
def virtualenv():
    with cd(env.project_path):
        with prefix(env.activate):
            yield


def __git_validate_clean():
    with lcd(env.project_path):
        if lrun('git diff-files', capture=True) != '':
            logging.error("Your git-tree isn't clean! Commit your changes before deploying.")
            sys.exit(1)


def deploy():
    # __git_validate_clean()
    with virtualenv():
        run('git pull')  # Get source
        run('pip install -r requirements.txt')  # install deps in virtualenv
        cd('dusken/static')
        run('npm install')
        run('bower install')
        run('gulp')
        cd('../..')
        run('python manage.py collectstatic --noinput')  # Collect static
        run('python manage.py migrate')  # Run DB migrations

    # Reload gunicorn
    sudo('/usr/bin/supervisorctl pid dusken.neuf.no | xargs kill -HUP', shell=False)
