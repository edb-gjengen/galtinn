import dj_database_url
import os
import logging
import raven

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
RAVEN_CONFIG = {
    'dsn': os.getenv('SENTRY_DSN'),
    'release': raven.fetch_git_sha(BASE_DIR),
    'CELERY_LOGLEVEL': logging.WARNING,
    'environment': os.getenv('SENTRY_ENVIRONMENT', 'production')
}

MIDDLEWARE.insert(0, 'raven.contrib.django.middleware.SentryResponseErrorIdMiddleware')

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
