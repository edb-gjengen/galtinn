from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt
from oauth2_provider import urls as oauth2_provider_urls
from rest_framework.routers import DefaultRouter
from strawberry.django.views import GraphQLView

from dusken.api.graphql import schema
from dusken.api.views import ResendValidationEmailView
from dusken.api.views.auth import GenericOauth2Callback
from dusken.api.views.cards import KassaMemberCardUpdateView, MemberCardViewSet
from dusken.api.views.checkouts import StripeCheckoutSessionView, StripePaymentSheetView, StripeWebhookView
from dusken.api.views.discord import UserDiscordProfileViewSet
from dusken.api.views.groups import GroupViewSet
from dusken.api.views.membership_types import MembershipTypeListView
from dusken.api.views.memberships import KassaMembershipView, MembershipChargeView, MembershipViewSet
from dusken.api.views.orders import OrderViewSet
from dusken.api.views.orgunits import OrgUnitViewSet, add_user, remove_user
from dusken.api.views.profile import CurrentUserMembershipsView, SetUsernameView, UpdateCurrentUserView
from dusken.api.views.session import (
    SessionLoginView,
    SessionLogoutView,
    SessionPasswordChangeView,
    SessionPasswordResetConfirmView,
    SessionPasswordResetView,
    SessionView,
)
from dusken.api.views.stats import membership_stats
from dusken.api.views.users import (
    BasicAuthCurrentUserView,
    CurrentUserView,
    DeleteCurrentUserView,
    DuskenUserViewSet,
    Oauth2CurrentUserView,
    RegisterUserView,
    user_pk_to_uuid,
)
from dusken.api.views.volunteer import (
    MyOrgUnitsAPIView,
    OrgUnitAddMemberAPIView,
    OrgUnitDetailAPIView,
    OrgUnitListAPIView,
    OrgUnitMembersAPIView,
    OrgUnitRemoveMemberAPIView,
    OrgUnitUpdateAPIView,
    UserSearchAPIView,
)

router = DefaultRouter()
router.register(r"users", DuskenUserViewSet, basename="user-api")
router.register(r"orgunits", OrgUnitViewSet, basename="orgunit-api")
router.register(r"groups", GroupViewSet, basename="group-api")
router.register(r"discordprofiles", UserDiscordProfileViewSet, basename="discordprofile-api")
router.register(r"cards", MemberCardViewSet, basename="membercard-api")
router.register(r"memberships", MembershipViewSet, basename="membership-api")
router.register(r"orders", OrderViewSet, basename="order-api")
urlpatterns = router.urls

urlpatterns += [
    # Current user
    path("me/", CurrentUserView.as_view(), name="user-current"),
    path("me/basic/", BasicAuthCurrentUserView.as_view(), name="user-current-basic-auth"),
    path("me/oauth/", Oauth2CurrentUserView.as_view(), name="user-current-oauth2"),
    path("me/delete/", DeleteCurrentUserView.as_view(), name="user-current-delete"),
    path("me/update/", UpdateCurrentUserView.as_view(), name="user-current-update"),
    path("me/set-username/", SetUsernameView.as_view(), name="user-current-set-username"),
    path("me/memberships/", CurrentUserMembershipsView.as_view(), name="user-current-memberships"),
    # Stripe
    path("membership/charge/", MembershipChargeView.as_view(), name="membership-charge"),
    path("stripe/checkout-session/", StripeCheckoutSessionView.as_view(), name="stripe-checkout-session"),
    path("stripe/webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),
    path("stripe/payment-sheet/", StripePaymentSheetView.as_view(), name="stripe-payment-sheet"),
    # Kassa
    path("kassa/membership/", KassaMembershipView.as_view(), name="kassa-membership"),
    path("kassa/card/", KassaMemberCardUpdateView.as_view(), name="kassa-card-update"),
    # Users
    path(
        "user/resend_validation_email/",
        ResendValidationEmailView.as_view(),
        name="resend-validation-email",
    ),
    path("user/register/", RegisterUserView.as_view(), name="user-api-register"),
    path("user/pk/to/uuid/", user_pk_to_uuid, name="user_pk_to_uuid"),
    # Organizational Unit (legacy)
    path("orgunit/remove/user/", remove_user, name="remove_user"),
    path("orgunit/add/user/", add_user, name="add_user"),
    # Organizational Unit (SPA)
    path("volunteer/orgunits/", OrgUnitListAPIView.as_view(), name="api-orgunit-list"),
    path("volunteer/orgunits/mine/", MyOrgUnitsAPIView.as_view(), name="api-orgunit-mine"),
    path("volunteer/orgunits/<slug:slug>/", OrgUnitDetailAPIView.as_view(), name="api-orgunit-detail"),
    path("volunteer/orgunits/<slug:slug>/update/", OrgUnitUpdateAPIView.as_view(), name="api-orgunit-update"),
    path("volunteer/orgunits/<slug:slug>/members/", OrgUnitMembersAPIView.as_view(), name="api-orgunit-members"),
    path(
        "volunteer/orgunits/<slug:slug>/members/add/",
        OrgUnitAddMemberAPIView.as_view(),
        name="api-orgunit-add-member",
    ),
    path(
        "volunteer/orgunits/<slug:slug>/members/remove/",
        OrgUnitRemoveMemberAPIView.as_view(),
        name="api-orgunit-remove-member",
    ),
    path("volunteer/users/search/", UserSearchAPIView.as_view(), name="api-user-search"),
    # Session auth
    path("auth/login/", SessionLoginView.as_view(), name="api-auth-login"),
    path("auth/logout/", SessionLogoutView.as_view(), name="api-auth-logout"),
    path("auth/session/", SessionView.as_view(), name="api-auth-session"),
    path("auth/password/reset/", SessionPasswordResetView.as_view(), name="api-auth-password-reset"),
    path(
        "auth/password/reset/confirm/",
        SessionPasswordResetConfirmView.as_view(),
        name="api-auth-password-reset-confirm",
    ),
    path("auth/password/change/", SessionPasswordChangeView.as_view(), name="api-auth-password-change"),
    # Membership types
    path("membership-types/", MembershipTypeListView.as_view(), name="api-membership-types"),
    # Stats
    path("stats/", membership_stats, name="membership-stats"),
    # GraphQL API
    path("graphql/", csrf_exempt(GraphQLView.as_view(schema=schema)), name="graphql"),
    # OAuth2
    path(
        "oauth/generic-callback/",
        GenericOauth2Callback.as_view(),
        name="generic-oauth2-callback",
    ),
    path("oauth/", include(oauth2_provider_urls, namespace="oauth2_provider")),
]
