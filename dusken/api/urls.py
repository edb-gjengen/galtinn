from django.conf.urls import url
from rest_framework.routers import DefaultRouter

from dusken.api.views import ResendValidationEmailView
from dusken.api.views.cards import (MemberCardViewSet,
                                    KassaMemberCardUpdateView)
from dusken.api.views.memberships import (MembershipViewSet,
                                          MembershipChargeView,
                                          KassaMembershipView)
from dusken.api.views.users import DuskenUserViewSet, CurrentUserView, user_pk_to_uuid
from dusken.api.views.orders import OrderViewSet
from dusken.api.views.validate import validate
from dusken.api.views.orgunits import remove_user, add_user

router = DefaultRouter()
router.register(r'users', DuskenUserViewSet, base_name='user-api')
router.register(r'cards', MemberCardViewSet, base_name='membercard-api')
router.register(r'memberships', MembershipViewSet, base_name='membership-api')
router.register(r'orders', OrderViewSet, base_name='order-api')
urlpatterns = router.urls

urlpatterns += [
    # Current user
    url(r'me/$', CurrentUserView.as_view(), name='user-current'),

    # Stripe
    url(r'membership/charge/$', MembershipChargeView.as_view(),
        name='membership-charge'),

    # Kassa
    url(r'kassa/membership/$', KassaMembershipView.as_view(),
        name='kassa-membership'),
    url(r'kassa/card/$', KassaMemberCardUpdateView.as_view(),
        name='kassa-card-update'),

    # Users
    url(r'user/resend_validation_email/$', ResendValidationEmailView.as_view(),
        name='resend-validation-email'),
    url(r'user/pk/to/uuid/$', user_pk_to_uuid, name='user_pk_to_uuid'),

    # Validation
    url(r'validate/$', validate, name='validate'),

    # OrgUnit
    url(r'orgunit/remove/user/$', remove_user, name='remove_user'),
    url(r'orgunit/add/user/$', add_user, name='add_user'),

]
