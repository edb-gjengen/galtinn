from django.urls import include, path

from dusken.api import urls as api_urls
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
]

urlpatterns += [
    path("api/", include(api_urls)),
]
