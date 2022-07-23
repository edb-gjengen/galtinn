from django.conf import settings
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from dusken.apps.mailchimp.models import MailChimpSubscription
from dusken.apps.mailchimp.serializers import MailChimpSubscriptionSerializer


class MailChimpSubscriptionViewSet(viewsets.ModelViewSet):
    queryset = MailChimpSubscription.objects.all()
    serializer_class = MailChimpSubscriptionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.queryset.filter(email=self.request.user.email)

    def get_serializer_context(self):
        return {"request": self.request}


class MailChimpIncoming(APIView):
    """Ref: https://apidocs.mailchimp.com/webhooks/"""

    VALID_TYPES = ["unsubscribe", "subscribe"]
    permission_classes = (AllowAny,)

    type_to_status = {
        "subscribe": MailChimpSubscription.STATUS_SUBSCRIBED,
        "unsubscribe": MailChimpSubscription.STATUS_UNSUBSCRIBED,
    }

    def get(self, request):
        """Note: Mailchimp webhook URL validator sends a
        GET request and expects HTTP status code 200."""
        self._validate_secret()
        return Response()

    def post(self, request):
        self._validate_secret()
        self._validate_type()
        self._validate_list_id()

        email = self.request.data.get("data[email]")

        subscriptions = MailChimpSubscription.objects.filter(email=email)
        if subscriptions:
            subscriptions.update(status=self.new_status)

        if self._type == "subscribe":
            MailChimpSubscription.objects.create(email=email, status=self.new_status)

        return Response()

    def _validate_list_id(
        self,
    ):
        list_id = self.request.data.get("data[list_id]")
        if list_id is None or list_id not in settings.MAILCHIMP_LIST_ID:
            raise ValidationError("Missing or invalid data[list_id]")

        self.list_id = list_id

    def _validate_type(
        self,
    ):
        _type = self.request.data.get("type")
        if _type is None or _type not in self.VALID_TYPES:
            raise ValidationError("Missing or invalid type")

        self._type = _type
        self.new_status = self.type_to_status[self._type]

    def _validate_secret(self):
        secret = self.request.query_params.get("secret")
        if secret is None or secret != settings.MAILCHIMP_WEBHOOK_SECRET:
            raise ValidationError("Missing or invalid secret in URL")
