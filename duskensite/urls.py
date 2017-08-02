from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import urls as auth_urls
from rest_framework.authtoken.views import obtain_auth_token

from apps.neuf_auth.views import NeufPasswordChangeView, NeufPasswordResetConfirmView
from apps.mailchimp import urls as mailchimp_urls
from apps.mailman import urls as mailman_urls
from dusken import urls as dusken_urls

admin.autodiscover()

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'', include(dusken_urls)),
    url(r'^mailchimp/', include(mailchimp_urls, namespace='mailchimp')),
    url(r'^mailman/', include(mailman_urls, namespace='mailman')),
    # Language selection
    url(r'^i18n/', include('django.conf.urls.i18n')),
]

# Authentication
urlpatterns += [
    url(r'^auth/password_change/$', NeufPasswordChangeView.as_view(), name='password_change'),
    url(r'^auth/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        NeufPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    # Built in auth views
    url(r'auth/', include(auth_urls)),
    # API auth
    url(r'^auth/obtain-token/', obtain_auth_token, name='obtain-auth-token'),
]

# Flatpages
urlpatterns += [
    url(r'^pages/', include('django.contrib.flatpages.urls')),
]
