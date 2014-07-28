from django.conf.urls import patterns, include, url
from rest_framework.routers import DefaultRouter
from .views import MemberViewSet, MembershipViewSet

router = DefaultRouter()
router.register(r'users', MemberViewSet)
router.register(r'memberships', MembershipViewSet)
urlpatterns = router.urls
