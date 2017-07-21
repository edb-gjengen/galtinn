from django.conf.urls import url
from rest_framework.routers import DefaultRouter

from dusken.api.views import ResendValidationEmailView
from dusken.api.views.cards import MemberCardViewSet
from dusken.api.views.memberships import (MembershipViewSet,
                                          MembershipChargeView,
                                          MembershipChargeRenewView,
                                          KassaMembershipView)
from dusken.api.views.users import DuskenUserViewSet
from dusken.api.views.orders import OrderViewSet
from dusken.api.views.validate import validate

router = DefaultRouter()
router.register(r'users', DuskenUserViewSet, base_name='user-api')
router.register(r'cards', MemberCardViewSet, base_name='membercard-api')
router.register(r'memberships', MembershipViewSet, base_name='membership-api')
router.register(r'orders', OrderViewSet, base_name='order-api')
urlpatterns = router.urls

urlpatterns += [
    # Stripe
    url(r'membership/charge/$', MembershipChargeView.as_view(),
        name='membership-charge'),
    url(r'membership/charge_renew/$', MembershipChargeRenewView.as_view(),
        name='membership-charge-renew'),

    # Kassa
    url(r'kassa/membership/$', KassaMembershipView.as_view(),
        name='membership-kassa'),

    # Users
    url(r'user/resend_validation_email/$', ResendValidationEmailView.as_view(),
        name='resend-validation-email'),

    # Validation
    url(r'validate/$', validate, name='validate'),
]
