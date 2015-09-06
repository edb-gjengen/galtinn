from django.conf.urls import url
from rest_framework.routers import DefaultRouter

from dusken.api.views import DuskenUserViewSet, MembershipViewSet, MembershipChargeView

router = DefaultRouter()
router.register(r'users', DuskenUserViewSet)
router.register(r'memberships', MembershipViewSet)
urlpatterns = router.urls

urlpatterns += [
    url(r'membership/charge/$', MembershipChargeView.as_view(), name='membership-charge')
]
