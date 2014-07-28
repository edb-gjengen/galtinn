from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),

    # Oauth2 Framework
    url(r'^oauth2/', include('provider.oauth2.urls', namespace='oauth2')),

    # Django Rest Framework
    url(r'', include('rest_framework.urls', namespace='rest_framework')),

    # Django Rest Framework Swagger
    url(r'^docs/', include('rest_framework_swagger.urls')),

    # Dusken
    url(r'api/', include('dusken_api.urls')),
)
