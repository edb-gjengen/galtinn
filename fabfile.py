import os

from invoke import task

# FIXME: rewrite without fabric
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
