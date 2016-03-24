from django.conf.urls import url
from rest_framework.routers import DefaultRouter

from dusken.api.views import DuskenUserViewSet, MembershipViewSet, MembershipChargeView

router = DefaultRouter()
router.register(r'users', DuskenUserViewSet, base_name='user-api')
router.register(r'memberships', MembershipViewSet, base_name='membership-api')
urlpatterns = router.urls

urlpatterns += [
    url(r'membership/charge/$', MembershipChargeView.as_view(), name='membership-charge')
]
