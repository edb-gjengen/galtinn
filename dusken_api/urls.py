from django.conf.urls import patterns, include, url
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, MembershipViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'memberships', MembershipViewSet)
urlpatterns = router.urls

urlpatterns += patterns('',
    url(r'login/', 'rest_framework.authtoken.views.obtain_auth_token', name='user-login'),
)