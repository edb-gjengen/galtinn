from django.conf import settings


def sentry(request):
    return {'SENTRY_DSN': settings.SENTRY_DSN or '', 'SENTRY_ENVIRONMENT': settings.SENTRY_ENVIRONMENT}
