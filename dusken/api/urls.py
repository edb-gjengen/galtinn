from rest_framework.routers import DefaultRouter

from dusken.api.views import DuskenUserViewSet, MembershipViewSet

router = DefaultRouter()
router.register(r'users', DuskenUserViewSet)
router.register(r'memberships', MembershipViewSet)
urlpatterns = router.urls
