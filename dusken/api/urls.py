from django.conf.urls import url
from rest_framework.routers import DefaultRouter

from dusken.api.views import ResendValidationEmailView
from dusken.api.views.cards import MemberCardViewSet
from dusken.api.views.memberships import MembershipViewSet, MembershipChargeView, MembershipChargeRenewView
from dusken.api.views.users import DuskenUserViewSet

router = DefaultRouter()
router.register(r'users', DuskenUserViewSet, base_name='user-api')
router.register(r'cards', MemberCardViewSet, base_name='membercard-api')
router.register(r'memberships', MembershipViewSet, base_name='membership-api')
urlpatterns = router.urls

urlpatterns += [
    url(r'membership/charge/$', MembershipChargeView.as_view(), name='membership-charge'),
    url(r'membership/charge_renew/$', MembershipChargeRenewView.as_view(), name='membership-charge-renew'),

    url(r'user/resend_validation_email/$', ResendValidationEmailView.as_view(), name='resend-validation-email'),
]