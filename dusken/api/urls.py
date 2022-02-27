from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from rest_framework.routers import DefaultRouter

from dusken.api.views import ResendValidationEmailView
from dusken.api.views.cards import KassaMemberCardUpdateView, MemberCardViewSet
from dusken.api.views.memberships import KassaMembershipView, MembershipChargeView, MembershipViewSet
from dusken.api.views.orders import OrderViewSet
from dusken.api.views.orgunits import add_user, remove_user
from dusken.api.views.stats import membership_stats
from dusken.api.views.users import (
    BasicAuthCurrentUserView,
    CurrentUserView,
    DuskenUserViewSet,
    RegisterUserView,
    user_pk_to_uuid,
)

router = DefaultRouter()
router.register(r"users", DuskenUserViewSet, basename="user-api")
router.register(r"cards", MemberCardViewSet, basename="membercard-api")
router.register(r"memberships", MembershipViewSet, basename="membership-api")
router.register(r"orders", OrderViewSet, basename="order-api")
urlpatterns = router.urls

urlpatterns += [
    # Current user
    url(r"me/$", CurrentUserView.as_view(), name="user-current"),
    url(r"me/basic/$", BasicAuthCurrentUserView.as_view(), name="user-current-basic-auth"),
    # Stripe
    url(r"membership/charge/$", MembershipChargeView.as_view(), name="membership-charge"),
    # Kassa
    url(r"kassa/membership/$", KassaMembershipView.as_view(), name="kassa-membership"),
    url(r"kassa/card/$", KassaMemberCardUpdateView.as_view(), name="kassa-card-update"),
    # Users
    url(r"user/resend_validation_email/$", ResendValidationEmailView.as_view(), name="resend-validation-email"),
    url(r"user/register/$", RegisterUserView.as_view(), name="user-api-register"),
    url(r"user/pk/to/uuid/$", user_pk_to_uuid, name="user_pk_to_uuid"),
    # OrgUnit
    url(r"orgunit/remove/user/$", remove_user, name="remove_user"),
    url(r"orgunit/add/user/$", add_user, name="add_user"),
    # Stats
    url(r"stats/$", membership_stats, name="membership-stats"),
    # GraphQL API
    url(r"^graphql/$", csrf_exempt(GraphQLView.as_view(graphiql=True)), name="graphql"),
]
