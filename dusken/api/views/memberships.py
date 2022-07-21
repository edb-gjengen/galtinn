import logging

import django_filters
import stripe
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import status, viewsets
from rest_framework.exceptions import APIException
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.response import Response
from stripe.error import CardError, InvalidRequestError

from dusken.api.serializers.memberships import MembershipSerializer
from dusken.api.serializers.orders import KassaOrderSerializer, StripeOrderSerializer
from dusken.models import Membership
from dusken.utils import InlineClass

logger = logging.getLogger(__name__)


STRIPE_ERRORS = {
    "incorrect_number": _("The card number is incorrect."),
    "invalid_number": _("The card number is not a valid credit card number."),
    "invalid_expiry_month": _("The card's expiration month is invalid."),
    "invalid_expiry_year": _("The card's expiration year is invalid."),
    "invalid_cvc": _("The card's security code is invalid."),
    "expired_card": _("The card has expired."),
    "incorrect_cvc": _("The card's security code is incorrect."),
    "incorrect_zip": _("The card's zip code failed validation."),
    "card_declined": _("The card was declined."),
    "missing": _("There is no card on a customer that is being charged."),
    "processing_error": _("An error occurred while processing the card."),
    "rate_limit": _(
        "An error occurred due to requests hitting the API too quickly. Please let us know if you're consistently running into this error."
    ),
}


class MembershipFilter(FilterSet):
    # Filter users by number to avoid DRF dropdown
    user = django_filters.NumberFilter()

    class Meta:
        model = Membership
        fields = ("id", "user", "start_date")


class MembershipViewSet(viewsets.ModelViewSet):
    """Membership API"""

    queryset = Membership.objects.all().order_by("pk")
    serializer_class = MembershipSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = MembershipFilter
    pagination_class = PageNumberPagination

    def get_queryset(self):
        if self.request.user.has_perm("dusken.view_membership"):
            return self.queryset
        return self.queryset.filter(user=self.request.user.pk)


class KassaMembershipView(GenericAPIView):
    queryset = Membership.objects.none()
    permission_classes = (DjangoModelPermissions,)
    serializer_class = KassaOrderSerializer

    def post(self, request):
        # Validate
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        # TODO: Do something here?

        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MembershipChargeView(GenericAPIView):
    queryset = Membership.objects.none()
    permission_classes = (IsAuthenticated,)
    serializer_class = StripeOrderSerializer

    CURRENCY = "NOK"
    STATUS_CHARGE_SUCCEEDED = "succeeded"
    STATUS_CHARGE_FAILED = "failed"

    def post(self, request):
        stripe.api_key = settings.STRIPE_SECRET_KEY

        # Validate
        serializer = self.serializer_class(data=self.request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        # Stripe customer
        if request.user.stripe_customer_id:
            # Existing
            customer = self._get_stripe_customer(request.user.stripe_customer_id)
            self._update_stripe_customer(customer, request.data.get("stripe_token"))
        else:
            # New
            customer = self._create_stripe_customer(request.data.get("stripe_token"))
            request.user.stripe_customer_id = customer.id
            request.user.save()

        # Charge
        membership_type = serializer.validated_data.get("membership_type")
        description = f"{membership_type.name}: {membership_type.description}"
        charge = self._create_stripe_charge(customer, membership_type.price, description)

        # Winning, save new order, with user and stripe customer id :-)
        serializer.save(transaction_id=charge.id, stripe_customer_id=customer.id, user=request.user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _create_stripe_customer(self, stripe_token):
        if settings.TESTING:
            return InlineClass({"id": "someid"})

        try:
            return stripe.Customer.create(email=stripe_token["email"], card=stripe_token["id"])
        except InvalidRequestError as e:
            logger.warning("Invalid Stripe request! %s", str(e))
            if settings.DEBUG:
                raise APIException(e)

            raise APIException(_("Stripe charge failed with API error."))
        except CardError as e:
            logger.info("stripe.Customer.create did not succeed: %s", e)
            if settings.DEBUG:
                raise APIException(e)

            raise APIException(STRIPE_ERRORS.get(e.code, _("Your card has been declined.")))

    def _update_stripe_customer(self, customer, stripe_token):
        if settings.TESTING:
            return InlineClass({"id": "someid"})

        try:
            return stripe.Customer.modify(customer.id, email=stripe_token["email"], source=stripe_token["id"])
        except InvalidRequestError as e:
            logger.warning("Invalid Stripe request! %s", str(e))
            if settings.DEBUG:
                raise APIException(e)

            raise APIException(_("Stripe charge failed with API error."))
        except CardError as e:
            logger.info("stripe.Customer.modify did not succeed: %s", e)
            if settings.DEBUG:
                raise APIException(e)

            raise APIException(STRIPE_ERRORS.get(e.code, _("Your card has been declined.")))

    def _create_stripe_charge(self, customer, amount, description):
        if settings.TESTING:
            return InlineClass({"status": self.STATUS_CHARGE_SUCCEEDED, "id": "someid"})

        try:
            return stripe.Charge.create(
                customer=customer.id, amount=amount, currency=self.CURRENCY, description=description
            )
        except InvalidRequestError as e:
            logger.warning("Invalid Stripe request! %s", str(e))
            if settings.DEBUG:
                raise APIException(e)

            raise APIException("Stripe charge failed with API error.")
        except CardError as e:
            logger.info("stripe.Charge.create did not succeed: %s", e)
            if settings.DEBUG:
                raise APIException(e)

            raise APIException(STRIPE_ERRORS.get(e.code, _("Your card has been declined.")))

    def _get_stripe_customer(self, stripe_customer_id):
        if settings.TESTING:
            return InlineClass({"id": "someid"})

        try:
            return stripe.Customer.retrieve(stripe_customer_id)
        except InvalidRequestError as e:
            logger.warning("Invalid Stripe request! %s", str(e))
            if settings.DEBUG:
                raise APIException(e)

            raise APIException(_("Stripe charge failed with API error."))
