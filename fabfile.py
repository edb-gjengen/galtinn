import os

from fabric import Connection
from invoke import task


LOCALES = ['nb']
LOCAL_APPS = ['common', 'hooks', 'mailchimp', 'mailman', 'neuf_auth', 'neuf_ldap']


def _lrun_locale_task(command, c, limit=None):
    param = ' -l '
    locale_params = param.join(LOCALES)

    if limit is not None and limit in LOCAL_APPS + ['dusken']:
        app_paths = [os.path.join('apps', limit)] if limit != 'dusken' else ['dusken']
    else:
        app_paths = [os.path.join('apps', app) for app in LOCAL_APPS] + ['dusken']

    for cur_path in app_paths:
        with c.cd(cur_path):
            locale_path = os.path.join(cur_path, 'locale')
            if not os.path.exists(locale_path):
                c.run('mkdir locale')

            if cur_path.endswith('dusken'):
                run_cmd = '../manage.py {}{}{}'.format(command, param, locale_params)
            else:
                run_cmd = '../../manage.py {}{}{}'.format(command, param, locale_params)
            c.run(run_cmd)


def makemessages(c, limit=None):
    _lrun_locale_task('makemessages', c, limit=limit)


def compilemessages(c, limit=None):
    _lrun_locale_task('compilemessages', c, limit=limit)


@task
def poedit(c, app):
    app_path = os.path.join('apps', app) if app != 'dusken' else 'dusken'
    po_path = os.path.join(app_path, 'locale/nb/LC_MESSAGES/django.po')
    c.run('poedit {}'.format(po_path))


@task()
def deploy(c):
    """
    Deploy galtinn.

    Make sure proxy_user is set to your neuf username.
    """
    proxy_user = os.getenv('DEPLOY_USER', os.getenv('USER'))
    c = Connection(host='gitdeploy@dreamcast.neuf.no', gateway=Connection('login.neuf.no', user=proxy_user))
    django_env = {'DJANGO_SETTINGS_MODULE': 'duskensite.settings.prod'}
    project_path = '/var/www/neuf.no/dusken'

    with c.cd(project_path):
        c.run('git pull')  # Get source
        c.run('source ~/.profile && pipenv sync', env={'PIPENV_NOSPIN': '1'})  # install deps in virtualenv

        with c.cd('dusken/static'):  # install and compile frontend deps
            c.run('npm i')
            c.run('npm run build')

        # Collect static
        c.run(
            'source ~/.profile && umask 022; pipenv run python manage.py collectstatic --noinput -i node_modules -c',
            env=django_env
        )
        # Run migrations
        c.run('source ~/.profile && pipenv run python manage.py migrate', env=django_env)

    # Reload gunicorn
    c.sudo('/usr/bin/supervisorctl pid galtinn.neuf.no | xargs kill -HUP', shell=False)
    # Reload celery
    c.sudo('/usr/bin/supervisorctl pid galtinn.neuf.no-celery | xargs kill -HUP', shell=False)


@task
def install(c):
    local_static_path = 'dusken/static/'
    c.run(f'cd {local_static_path} && npm i')
    c.run(f'cd {local_static_path} && npm run build')


@task
def serve(c):
    local_static_path = 'dusken/static/'
    c.run(f'cd {local_static_path} && npm start')


@task
def celery(c):
    c.run('DJANGO_SETTINGS_MODULE=duskensite.settings.dev celery -B -A duskensite worker')


@task
def redis(c):
    c.run('docker run -p 6379:6379 redis')
