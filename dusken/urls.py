from django.contrib import admin
from django.contrib.auth import urls as auth_urls
from django.contrib.flatpages.views import flatpage
from django.urls import include, path, re_path
from rest_framework.authtoken.views import obtain_auth_token

from dusken.api import urls as api_urls
from dusken.apps.mailchimp import urls as mailchimp_urls
from dusken.apps.mailman import urls as mailman_urls
from dusken.apps.neuf_auth.views import NeufPasswordChangeView, NeufPasswordResetConfirmView
from dusken.views.email import EmailSubscriptions
from dusken.views.general import HomeView, HomeVolunteerView, IndexView, OrderDetailView, StatsView
from dusken.views.membership import MembershipListView
from dusken.views.orgunit import OrgUnitDetailView, OrgUnitEditUsersView, OrgUnitEditView, OrgUnitListView
from dusken.views.user import (
    UserActivateView,
    UserDeleteView,
    UserDetailMeView,
    UserDetailView,
    UserListView,
    UserRegisterView,
    UserSetUsernameView,
    UserUpdateMeView,
    UserUpdateView,
)
from dusken.views.validation import UserEmailValidateView, UserPhoneValidateView

admin.autodiscover()


urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("home/", HomeView.as_view(), name="home"),
    # User
    path("me/", UserDetailMeView.as_view(), name="user-detail-me"),
    path("me/update/", UserUpdateMeView.as_view(), name="user-update-me"),
    path("me/update/username/", UserSetUsernameView.as_view(), name="user-update-username"),
    path("me/delete/", UserDeleteView.as_view(), name="user-delete"),
    path("users/<slug:slug>/", UserDetailView.as_view(), name="user-detail"),
    path("users/<slug:slug>/update/", UserUpdateView.as_view(), name="user-update"),
    path("users/", UserListView.as_view(), name="user-list"),
    # Registration
    path("register/", UserRegisterView.as_view(), name="user-register"),
    path("activate/<int:phone>/<code>", UserActivateView.as_view(), name="user-activate"),
    # Contact info validation
    path(
        "users/<slug:slug>/validate_email/<email_key>",
        UserEmailValidateView.as_view(),
        name="user-email-validate",
    ),
    path("me/validate_phone/", UserPhoneValidateView.as_view(), name="user-phone-validate"),
    # Membership
    path("memberships/", MembershipListView.as_view(), name="membership-list"),
    path("order/<slug:slug>/", OrderDetailView.as_view(), name="payment-detail"),
    # Volunteer
    path("volunteer/", HomeVolunteerView.as_view(), name="home-volunteer"),
    path("orgunits/", OrgUnitListView.as_view(), name="orgunit-list"),
    path("orgunit/<slug:slug>/", OrgUnitDetailView.as_view(), name="orgunit-detail"),
    path("orgunit/edit/<slug:slug>/", OrgUnitEditView.as_view(), name="orgunit-edit"),
    path("orgunit/edit/users/<slug:slug>/", OrgUnitEditUsersView.as_view(), name="orgunit-edit-users"),
    path("orgunits/<slug:slug>/", OrgUnitDetailView.as_view(), name="orgunit-detail"),
    # Email
    path("email/subscriptions/", EmailSubscriptions.as_view(), name="email-subscriptions"),
    # Stats
    path("stats/", StatsView.as_view(), name="stats"),
    # Other apps
    path("admin/", admin.site.urls),
    path("api/", include(api_urls)),
    path("mailchimp/", include(mailchimp_urls, namespace="mailchimp")),
    path("mailman/", include(mailman_urls, namespace="mailman")),
    # Language selection
    path("i18n/", include("django.conf.urls.i18n")),
    path("select2/", include("django_select2.urls")),
    # Authentication
    path("auth/password_change/", NeufPasswordChangeView.as_view(), name="password_change"),
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
