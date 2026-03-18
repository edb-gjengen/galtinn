from django.contrib import admin
from django.contrib.auth import urls as auth_urls
from django.contrib.flatpages.views import flatpage
from django.urls import include, path, re_path
from rest_framework.authtoken.views import obtain_auth_token

from dusken.api import urls as api_urls
from dusken.apps.neuf_auth.views import NeufPasswordResetConfirmView
from dusken.autocompletes import UserAutocompleteView
from dusken.views.general import OrderDetailView, StatsView, spa_view
from dusken.views.user import (
    UserActivateView,
    UserDetailView,
    UserListView,
    UserUpdateView,
)
from dusken.views.validation import UserEmailValidateView, UserPhoneValidateView

admin.autodiscover()


urlpatterns = [
    path("", spa_view, name="index"),
    path("home/", spa_view, name="home"),
    path("login/", spa_view, name="login"),
    path("register/", spa_view, name="register"),
    # User
    path("me/", spa_view, name="user-detail-me"),
    path("me/update/", spa_view, name="user-update-me"),
    path("me/update/username/", spa_view, name="user-update-username"),
    path("me/delete/", spa_view, name="user-delete"),
    # Membership
    path("memberships/", spa_view, name="membership-list"),
    # Change password
    path("auth/password_change/", spa_view, name="password_change"),
    path("users/autocomplete/", UserAutocompleteView.as_view(), name="user-autocomplete"),
    path("users/<slug:slug>/", UserDetailView.as_view(), name="user-detail"),
    path("users/<slug:slug>/update/", UserUpdateView.as_view(), name="user-update"),
    path("users/", UserListView.as_view(), name="user-list"),
    # Registration
    path("activate/<int:phone>/<code>", UserActivateView.as_view(), name="user-activate"),
    # Contact info validation
    path(
        "users/<slug:slug>/validate_email/<email_key>",
        UserEmailValidateView.as_view(),
        name="user-email-validate",
    ),
    path("me/validate_phone/", UserPhoneValidateView.as_view(), name="user-phone-validate"),
    # Membership
    path("order/<slug:slug>/", OrderDetailView.as_view(), name="payment-detail"),
    # Volunteer
    path("volunteer/", spa_view, name="home-volunteer"),
    path("orgunits/", spa_view, name="orgunit-list"),
    re_path(r"^orgunit/.*", spa_view, name="orgunit-views"),
    # Stats
    path("stats/", StatsView.as_view(), name="stats"),
    # Other apps
    path("admin/", admin.site.urls),
    path("api/", include(api_urls)),
    # Language selection
    path("i18n/", include("django.conf.urls.i18n")),
    # Authentication
    re_path(
        r"^auth/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$",
        NeufPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    # Built in auth views
    path("auth/", include(auth_urls)),
    # API auth
    re_path(r"^auth/obtain-token/", obtain_auth_token, name="obtain-auth-token"),
    # Flatpages
    re_path(r"^(?P<url>.*/)$", flatpage),
]
