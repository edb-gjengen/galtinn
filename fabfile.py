from contextlib import contextmanager as _contextmanager
from fabric.api import run, sudo, env, cd, prefix, lcd, local

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


def deploy():
    with virtualenv():
        run('git pull')  # Get source
        run('pip install -r requirements.txt')  # install deps in virtualenv
        with cd('dusken/static'):  # install and compile frontend deps
            run('yarn')
            run('gulp')
        run('python manage.py collectstatic --noinput -i node_modules -i bower_components')  # Collect static
        run('python manage.py migrate')  # Run DB migrations

    # Reload gunicorn
    sudo('/usr/bin/supervisorctl pid dusken.neuf.no | xargs kill -HUP', shell=False)


def install():
    with lcd('dusken/static/'):
        local('yarn')
        local('gulp')


def serve():
    with lcd('dusken/static/'):
        local('gulp serve')
