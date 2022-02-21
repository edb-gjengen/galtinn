from django.urls import path
from rest_framework import routers

from .views import MailChimpIncoming, MailChimpSubscriptionViewSet

app_name = "mailchimp"

router = routers.SimpleRouter()
router.register(r"subscriptions", MailChimpSubscriptionViewSet, basename="subscription")
urlpatterns = router.urls

urlpatterns += [
    path("incoming/", MailChimpIncoming.as_view(), name="incoming"),
]
