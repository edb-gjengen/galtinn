import os

from fabric.api import run, sudo, env, cd, lcd, local
from fabric.context_managers import shell_env

env.use_ssh_config = True
env.hosts = ['dreamcast.neuf.no']
env.project_path = '/var/www/neuf.no/dusken'
env.user = 'gitdeploy'

LOCALES = ['nb']
LOCAL_APPS = ['common', 'hooks', 'mailchimp', 'mailman', 'neuf_auth', 'neuf_ldap']


def _lrun_locale_task(command, limit=None):
    param = ' -l '
    locale_params = param.join(LOCALES)

    if limit is not None and limit in LOCAL_APPS + ['dusken']:
        app_paths = [os.path.join('apps', limit)] if limit != 'dusken' else ['dusken']
    else:
        app_paths = [os.path.join('apps', app) for app in LOCAL_APPS] + ['dusken']

    for cur_path in app_paths:
        with lcd(cur_path):
            locale_path = os.path.join(cur_path, 'locale')
            if not os.path.exists(locale_path):
                local('mkdir locale')

            if cur_path.endswith('dusken'):
                run_cmd = '../manage.py {}{}{}'.format(command, param, locale_params)
            else:
                run_cmd = '../../manage.py {}{}{}'.format(command, param, locale_params)
            local(run_cmd)


def makemessages(limit=None):
    _lrun_locale_task('makemessages', limit=limit)


def compilemessages(limit=None):
    _lrun_locale_task('compilemessages', limit=limit)


def poedit(app):
    app_path = os.path.join('apps', app) if app != 'dusken' else 'dusken'
    po_path = os.path.join(app_path, 'locale/nb/LC_MESSAGES/django.po')
    local('poedit {}'.format(po_path))


def deploy():
    with cd(env.project_path):
        run('git pull')  # Get source
        with shell_env(PIPENV_NOSPIN='1'):
            run('pipenv sync')  # install deps in virtualenv
        with cd('dusken/static'):  # install and compile frontend deps
            run('yarn')
            run('yarn build')
        with shell_env(DJANGO_SETTINGS_MODULE='duskensite.settings.prod'):
            run('umask 022; pipenv run python manage.py collectstatic --noinput -i node_modules')  # Collect static
            run('pipenv run python manage.py migrate')  # Run DB migrations

    # Reload gunicorn
    sudo('/usr/bin/supervisorctl pid galtinn.neuf.no | xargs kill -HUP', shell=False)
    # Reload celery
    sudo('/usr/bin/supervisorctl pid galtinn.neuf.no-celery | xargs kill -HUP', shell=False)


def install():
    with lcd('dusken/static/'):
        local('yarn')
        local('yarn build')


def serve():
    with lcd('dusken/static/'):
        local('yarn start')


def celery():
    local('DJANGO_SETTINGS_MODULE=duskensite.settings.dev celery -B -A duskensite worker')

def redis():
    local('docker run -p 6379:6379 redis')
