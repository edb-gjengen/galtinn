from django.contrib import admin
from django.contrib.auth import urls as auth_urls
from django.contrib.flatpages.views import flatpage
from django.urls import include, path, re_path
from rest_framework.authtoken.views import obtain_auth_token

from dusken import urls as dusken_urls
from dusken.apps.mailchimp import urls as mailchimp_urls
from dusken.apps.mailman import urls as mailman_urls
from dusken.apps.neuf_auth.views import NeufPasswordChangeView, NeufPasswordResetConfirmView

admin.autodiscover()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(dusken_urls)),
    path("mailchimp/", include(mailchimp_urls, namespace="mailchimp")),
    path("mailman/", include(mailman_urls, namespace="mailman")),
    # Language selection
    path("i18n/", include("django.conf.urls.i18n")),
]

# Authentication
urlpatterns += [
    re_path(r"^auth/password_change/$", NeufPasswordChangeView.as_view(), name="password_change"),
    re_path(
        r"^auth/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$",
        NeufPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    # Built in auth views
    path("auth/", include(auth_urls)),
    # API auth
    re_path(r"^auth/obtain-token/", obtain_auth_token, name="obtain-auth-token"),
]

# Select2
urlpatterns += [
    path("select2/", include("django_select2.urls")),
]

# Flatpages
urlpatterns += [
    re_path(r"^(?P<url>.*/)$", flatpage),
]
