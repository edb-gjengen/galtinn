from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required

admin.autodiscover()
admin.site.login = login_required(admin.site.login)

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'', include('dusken.urls')),
    url(r'', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^auth/', 'rest_framework.authtoken.views.obtain_auth_token'),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', name='logout')
]
