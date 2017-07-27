# encoding: utf-8

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import sys
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _


BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/
DEBUG = True
ALLOWED_HOSTS = []
SECRET_KEY = os.getenv('SECRET_KEY', 'insecure_default')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    'rest_framework',
    'rest_framework.authtoken',
    'mptt',
    'django_countries',
    'bootstrap4',
    'django_extensions',
    'django_filters',
    'captcha',
    'svg',
]
INSTALLED_APPS += [
    'dusken',
    # 'apps.hooks',
    'apps.neuf_ldap',
    'apps.neuf_auth',
    # TODO Remove these after import and new integrations are OK
    'apps.inside',
    'apps.kassa',
    'apps.tekstmelding',
]

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
)

ROOT_URLCONF = 'duskensite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'dusken/templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'duskensite.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
# LDAP, Inside, Kassa and tekstmelding dbs
DATABASE_ROUTERS = ['duskensite.router.Router']

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/
LANGUAGE_CODE = 'en'
TIME_ZONE = 'Europe/Oslo'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('nb', _('Norwegian')),
    ('en', _('English')),
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

SITE_ID = 1

# Email
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'webmaster@localhost')
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

AUTH_USER_MODEL = 'dusken.DuskenUser'
LOGIN_REDIRECT_URL = reverse_lazy('home')
LOGOUT_REDIRECT_URL = reverse_lazy('index')
LOGIN_URL = reverse_lazy('login')
LOGOUT_URL = reverse_lazy('logout')

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissions',
    ],
    'PAGE_SIZE': 256
}

STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY', '')

TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'

PHONENUMBER_DB_FORMAT = 'E164'
PHONENUMBER_DEFAULT_REGION = 'NO'

NOCAPTCHA = True

SVG_DIRS = [
    os.path.join(BASE_DIR, 'dusken/static/dist/images')
]

# neuf_auth

# LDAP
LDAP_BASE_DN = "dc=neuf,dc=no"
LDAP_USER_DN = "ou=People,{}".format(LDAP_BASE_DN)
LDAP_GROUP_DN = "ou=Groups,{}".format(LDAP_BASE_DN)
LDAP_AUTOMOUNT_DN = "ou=Automount,{}".format(LDAP_BASE_DN)

LDAP_UID_MIN = 10000
LDAP_UID_MAX = 100000
LDAP_GID_MIN = 9000
LDAP_GID_MAX = 9999
LDAP_USER_GID_MIN = 10000
LDAP_USER_GID_MAX = 100000

LDAP_LOGIN_SHELL = '/bin/bash'
LDAP_HOME_DIRECTORY_PREFIX = '/home'
# Ref: http://tille.garrels.be/training/ldap/ch02s02.html
LDAP_SHADOW_LAST_CHANGE = 0  # Days since password last change
LDAP_SHADOW_MIN = 8  #
LDAP_SHADOW_MAX = 999999
LDAP_SHADOW_WARNING = 7  #
LDAP_SHADOW_EXPIRE = -1  #
LDAP_SHADOW_FLAG = 0

# Home dir
FILESERVER_HOST = "localhost"
FILESERVER_SSH_USER = 'nikolark'  # change this to your own user for development
FILESERVER_SSH_KEY_PATH = ''  # e.g. '/home/nikolark/.ssh/id_rsa'
FILESERVER_HOME_PATH = "/tmp/"
FILESERVER_CREATE_HOMEDIR_SCRIPT = os.path.join(BASE_DIR, 'scripts', 'create_home_directory.sh')


try:
    from .local_settings import *
except ImportError:
    pass
