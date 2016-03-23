from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.views import login, logout, password_reset, password_reset_done
from rest_framework.authtoken.views import obtain_auth_token

from dusken import urls as dusken_urls


admin.autodiscover()

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'', include(dusken_urls)),
    url(r'^auth/', obtain_auth_token)
]

# Auth
urlpatterns += [
    url(r'^login/$', login, name='login'),
    url(r'^logout/$', logout, name='logout'),
    url(r'^password_reset/$', password_reset, name='password_reset'),
    url(r'^password_reset_done/$', password_reset_done, name='password_reset_done'),
]
