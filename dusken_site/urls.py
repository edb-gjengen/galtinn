from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
admin.autodiscover()
admin.site.login = login_required(admin.site.login)

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),

    # Django Rest Framework
    url(r'', include('rest_framework.urls', namespace='rest_framework')),

    # Dusken
    url(r'api/', include('dusken_api.urls')),

    # Token Auth
    url(r'^auth/', 'rest_framework.authtoken.views.obtain_auth_token')
)
