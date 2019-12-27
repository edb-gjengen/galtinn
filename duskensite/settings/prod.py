import dj_database_url
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from dusken.fetch_git_sha import fetch_git_sha, InvalidGitRepository
from .base import *

DATABASES['default'] = dj_database_url.config(conn_max_age=600)

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'mx.neuf.no')

# Security
# https://docs.djangoproject.com/en/1.10/topics/security/#ssl-https
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
DEBUG = False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS').split(',') if os.getenv('ALLOWED_HOSTS') else []

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Sentry
try:
    release = fetch_git_sha(BASE_DIR)
except InvalidGitRepository:
    release = "N/A"

SENTRY_DSN = os.getenv('SENTRY_DSN', 'https://0f0067c4548445a6867a471e2b69a419@sentry.neuf.no/2')
SENTRY_ENVIRONMENT = os.getenv('SENTRY_ENVIRONMENT', 'production')
sentry_sdk.init(
    dsn=SENTRY_DSN,
    environment=SENTRY_ENVIRONMENT,
    release=release,
    integrations=[DjangoIntegration(), CeleryIntegration(), RedisIntegration()]
)

# Cache (redis)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}


try:
    from .local import *
except ImportError:
    pass
