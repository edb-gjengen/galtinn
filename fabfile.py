import os
from contextlib import contextmanager as _contextmanager

from fabric.api import run, sudo, env, cd, prefix, lcd, local
from fabric.context_managers import shell_env

env.use_ssh_config = True
env.hosts = ['dreamcast.neuf.no']
env.project_path = '/var/www/neuf.no/dusken'
env.user = 'gitdeploy'
env.activate = 'source {}/venv/bin/activate'.format(env.project_path)

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


@_contextmanager
def virtualenv():
    with cd(env.project_path):
        with prefix(env.activate):
            yield


def makemessages(limit=None):
    _lrun_locale_task('makemessages', limit=limit)


def compilemessages(limit=None):
    _lrun_locale_task('compilemessages', limit=limit)


def poedit(app):
    app_path = os.path.join('apps', app) if app != 'dusken' else 'dusken'
    po_path = os.path.join(app_path, 'locale/nb/LC_MESSAGES/django.po')
    local('poedit {}'.format(po_path))


def deploy():
    with virtualenv():
        run('git pull')  # Get source
        run('pip install -r requirements.txt')  # install deps in virtualenv
        with cd('dusken/static'):  # install and compile frontend deps
            run('yarn')
            run('gulp')
        with shell_env(DJANGO_SETTINGS_MODULE='duskensite.settings.prod'):
            run('python manage.py collectstatic --noinput -i node_modules')  # Collect static
            run('python manage.py migrate')  # Run DB migrations

    # Reload gunicorn
    sudo('/usr/bin/supervisorctl pid galtinn.neuf.no | xargs kill -HUP', shell=False)
    # Reload celery
    sudo('/usr/bin/supervisorctl pid galtinn.neuf.no-celery | xargs kill -HUP', shell=False)


def install():
    with lcd('dusken/static/'):
        local('yarn')
        local('gulp')


def serve():
    with lcd('dusken/static/'):
        local('gulp serve')
