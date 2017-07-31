from django.conf.urls import url
from rest_framework import routers

from .views import MailChimpIncoming, MailChimpSubscriptionViewSet

router = routers.SimpleRouter()
router.register(r'subscriptions', MailChimpSubscriptionViewSet, base_name='subscription')

urlpatterns = router.urls

urlpatterns += [
    url(r'^incoming/$', MailChimpIncoming.as_view(), name='incoming'),
]
