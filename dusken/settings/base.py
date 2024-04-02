from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).parent.parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/
DEBUG = True
ALLOWED_HOSTS: List[str] = []
SECRET_KEY = os.getenv("SECRET_KEY", "insecure_default")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.flatpages",
    "django.contrib.humanize",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "rest_framework",
    "rest_framework.authtoken",
    "mptt",
    "django_countries",
    "django_bootstrap5",
    "django_extensions",
    "django_filters",
    "django_select2",
    "captcha",
    "svg",
]
INSTALLED_APPS += [
    "dusken",
    "dusken.apps.neuf_ldap",
    "dusken.apps.neuf_auth",
    "dusken.apps.mailman",
    "dusken.apps.common",
    # FIXME Keep these for easy referencing in django admin for now
    "dusken.apps.kassa",
    "dusken.apps.tekstmelding",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.flatpages.middleware.FlatpageFallbackMiddleware",
]

ROOT_URLCONF = "dusken.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "dusken/templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "dusken.context_processors.sentry",
            ],
        },
    },
]

WSGI_APPLICATION = "dusken.wsgi.application"

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    },
}
# LDAP, Inside, Kassa and tekstmelding DB's
DATABASE_ROUTERS = ["dusken.router.Router"]

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/
LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", "en")
TIME_ZONE = os.getenv("TIME_ZONE", "Europe/Oslo")
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ("nb", _("Norwegian")),
    ("en", _("English")),
]

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "frontend/dist"]

SITE_ID = 1

# Email
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "webmaster@localhost")
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

AUTH_USER_MODEL = "dusken.DuskenUser"
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "dusken.authentication.UsernameModelBackend",
]

LOGIN_REDIRECT_URL = reverse_lazy("home")
LOGOUT_REDIRECT_URL = reverse_lazy("index")
LOGIN_URL = reverse_lazy("login")

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.BCryptPasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.DjangoModelPermissions",
    ],
    "PAGE_SIZE": 25,
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "EXCEPTION_HANDLER": "dusken.api.views.api_500_handler",
}

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "")

TESTING = any(m in sys.modules for m in ["pytest", "py.test"])

PHONENUMBER_DB_FORMAT = "E164"
PHONENUMBER_DEFAULT_REGION = "NO"

TEKSTMELDING_API_URL = "https://tekstmelding.neuf.no/"
TEKSTMELDING_API_KEY = os.getenv("TEKSTMELDING_API_KEY", "")

# Fallback keys from # from captcha.constants import TEST_PUBLIC_KEY, TEST_PRIVATE_KEY
TEST_PUBLIC_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
RECAPTCHA_PUBLIC_KEY = os.getenv("RECAPTCHA_PUBLIC_KEY", TEST_PUBLIC_KEY)
TEST_PRIVATE_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"
RECAPTCHA_PRIVATE_KEY = os.getenv("RECAPTCHA_PRIVATE_KEY", TEST_PRIVATE_KEY)
NOCAPTCHA = True

SILENCED_SYSTEM_CHECKS = ["captcha.recaptcha_test_key_error"] if RECAPTCHA_PUBLIC_KEY == TEST_PUBLIC_KEY else []

SVG_DIRS = [BASE_DIR / "frontend/app/images"]

# neuf_auth

# LDAP
LDAP_BASE_DN = "dc=neuf,dc=no"
LDAP_USER_DN = f"ou=People,{LDAP_BASE_DN}"
LDAP_GROUP_DN = f"ou=Groups,{LDAP_BASE_DN}"
LDAP_AUTOMOUNT_DN = f"ou=Automount,{LDAP_BASE_DN}"

LDAP_UID_MIN = 10000
LDAP_UID_MAX = 100000
LDAP_GID_MIN = 9000
LDAP_GID_MAX = 9999
LDAP_USER_GID_MIN = 10000
LDAP_USER_GID_MAX = 100000

LDAP_LOGIN_SHELL = "/bin/bash"
LDAP_HOME_DIRECTORY_PREFIX = "/home"
# Ref: http://tille.garrels.be/training/ldap/ch02s02.html
LDAP_SHADOW_LAST_CHANGE = 0  # Days since password last change
LDAP_SHADOW_MIN = 8  #
LDAP_SHADOW_MAX = 999999
LDAP_SHADOW_WARNING = 7  #
LDAP_SHADOW_EXPIRE = -1  #
LDAP_SHADOW_FLAG = 0

# Home dir
FILESERVER_HOST = "localhost"
FILESERVER_SSH_USER = "nikolark"  # change this to your own user for development
FILESERVER_SSH_KEY_PATH = ""  # e.g. '/home/nikolark/.ssh/id_rsa'
FILESERVER_HOME_PATH = "/tmp/"  # noqa: S108
FILESERVER_CREATE_HOMEDIR_SCRIPT = BASE_DIR / "scripts/create_home_directory.sh"

# Celery
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

# Mailman API
MAILMAN_API_URL = os.getenv("MAILMAN_API_URL", "https://mailman-api.neuf.no")
MAILMAN_API_USERNAME = os.getenv("MAILMAN_API_USERNAME", "")
MAILMAN_API_PASSWORD = os.getenv("MAILMAN_API_PASSWORD", "")

# Google Analytics
GOOGLE_ANALYTICS_PROPERTY_ID = os.getenv("GOOGLE_ANALYTICS_PROPERTY_ID", "")

# Wordpress sync
WP_PHP_SCRIPT_PATH = BASE_DIR / "scripts"
WP_OUT_FILENAME = WP_PHP_SCRIPT_PATH / "users_in_group_active.json"
WP_LOAD_PATHS = ["/var/www/studentersamfundet.no/www/wp/wp-load.php", "/var/www/neuf.no/aktivweb/wp/wp-load.php"]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
    "formatters": {
        "verbose": {"format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"},
    },
    "handlers": {"console": {"level": "DEBUG", "class": "logging.StreamHandler", "formatter": "verbose"}},
    "loggers": {
        "django.db.backends": {
            "level": "ERROR",
            "handlers": ["console"],
            "propagate": False,
        },
        "stripe": {
            "level": "WARNING",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}
SENTRY_DSN = ""
SENTRY_ENVIRONMENT = "dev"

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
