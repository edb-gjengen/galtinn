from django.conf.urls import include, url
from django.contrib import admin
from rest_framework.authtoken.views import obtain_auth_token

from dusken import urls as dusken_urls


admin.autodiscover()

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'', include(dusken_urls)),
    url(r'^auth/obtain-token/', obtain_auth_token),
    # Built in auth views
    url('^auth/', include('django.contrib.auth.urls'))
]
