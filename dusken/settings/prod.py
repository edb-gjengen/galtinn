import contextlib
import os
from pathlib import Path

import dj_database_url
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from .base import *  # noqa: F403

DATABASES["default"] = dj_database_url.config(conn_max_age=600)  # noqa: F405
DATABASES["ldap"] = {  # noqa: F405
    "ENGINE": "ldapdb.backends.ldap",
    "NAME": os.getenv("LDAP_URL", "ldaps://pacman.neuf.no/"),
    "USER": os.getenv("LDAP_BIND_DN", "cn=admin,dc=neuf,dc=no"),
    "PASSWORD": os.getenv("LDAP_BIND_PASSWORD", ""),
}

# A PEM key is several lines, which an env file cannot carry
if key_file := os.getenv("OIDC_RSA_PRIVATE_KEY_FILE"):
    OAUTH2_PROVIDER["OIDC_RSA_PRIVATE_KEY"] = Path(key_file).read_text()  # noqa: F405

# Home directories
FILESERVER_HOST = os.getenv("FILESERVER_HOST", "c64.neuf.no")
FILESERVER_SSH_USER = os.getenv("FILESERVER_SSH_USER", "localedb")
FILESERVER_SSH_KEY_PATH = os.getenv("FILESERVER_SSH_KEY_PATH", "/run/secrets/fileserver_ssh_key")
FILESERVER_HOME_PATH = os.getenv("FILESERVER_HOME_PATH", "/export/homes")
FILESERVER_CREATE_HOMEDIR_SCRIPT = os.getenv("FILESERVER_CREATE_HOMEDIR_SCRIPT", "/opt/ldap/create_home_directory.sh")

# Email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "mx.neuf.no")

# Security
# https://docs.djangoproject.com/en/1.10/topics/security/#ssl-https
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
DEBUG = False
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

_security = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware")  # noqa: F405
MIDDLEWARE.insert(_security + 1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Sentry
SENTRY_DSN = os.getenv("SENTRY_DSN", "https://f897a7de435f495995e5b2a2a75248fa@bugsink.neuf.no/1")
SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT", "production")
sentry_sdk.init(
    dsn=SENTRY_DSN,
    environment=SENTRY_ENVIRONMENT,
    release=os.getenv("SENTRY_RELEASE", "N/A"),
    integrations=[DjangoIntegration(), CeleryIntegration(), RedisIntegration()],
    # Bugsink likes the following settings
    send_default_pii=True,
    max_request_body_size="always",
    # Disable event types which are not supported by Bugsink:
    traces_sample_rate=0,
    send_client_reports=False,
    auto_session_tracking=False,
)

# Cache with Redis
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://127.0.0.1:6379"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
}


with contextlib.suppress(ImportError):
    from .local import *  # noqa: F403
