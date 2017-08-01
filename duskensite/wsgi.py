import os
from django.core.wsgi import get_wsgi_application
from raven.contrib.django.middleware.wsgi import Sentry

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "duskensite.settings.prod")

application = get_wsgi_application()
application = Sentry(application)
