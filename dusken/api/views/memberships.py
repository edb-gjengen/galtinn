from django.conf import settings
import logging

from django.contrib.auth import login
from rest_framework import status
from rest_framework import viewsets
from rest_framework.exceptions import APIException
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny, DjangoModelPermissions
import stripe
from rest_framework.response import Response

from dusken.api.serializers.memberships import MembershipSerializer
from dusken.api.serializers.orders import OrderChargeRenewSerializer, OrderChargeSerializer
from dusken.models import Membership
from dusken.utils import InlineClass


logger = logging.getLogger(__name__)


class MembershipViewSet(viewsets.ModelViewSet):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class MembershipChargeView(GenericAPIView):
    queryset = Membership.objects.none()
    permission_classes = (AllowAny, )
    serializer_class = OrderChargeSerializer

    CURRENCY = 'NOK'
    STATUS_CHARGE_SUCCEEDED = 'succeeded'
    _logged_in_user = None

    def post(self, request):
        stripe.api_key = settings.STRIPE_SECRET_KEY

        # Validate
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        # Customer
        if self._logged_in_user and self._logged_in_user.stripe_customer_id:
            # Existing
            customer = self._get_stripe_customer(self._logged_in_user.stripe_customer_id)
        else:
            # New
            customer = self._create_stripe_customer(request.data.get('stripe_token'))

        # Charge
        membership_type = serializer.validated_data.get('product')
        description = '{}: {}'.format(membership_type.name, membership_type.description)
        charge = self._create_stripe_charge(customer, membership_type.price, description)

        if charge.status != self.STATUS_CHARGE_SUCCEEDED:
            logger.warning('stripe.Charge did not succeed: %s', charge.status)
            return Response({'error': 'stripe.Charge did not succeed :-('})

        # Winning, save new order, with user and stripe customer id :-)
        order = serializer.save(
            transaction_id=charge.id,
            stripe_customer_id=customer.id,
            logged_in_user=self._logged_in_user
        )

        if self._logged_in_user is None:
            self._login_user(order.user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _create_order(self, amount, charge, membership_type):
        return

    def _create_stripe_customer(self, stripe_token):
        if settings.TESTING:
            return InlineClass({'id': 'someid'})

        try:
            return stripe.Customer.create(
                email=stripe_token['email'],
                card=stripe_token['id'])
        except stripe.error.InvalidRequestError as e:
            logger.warning('Invalid Stripe request! %s', str(e))
            if settings.DEBUG:
                raise APIException(e)
            else:
                raise APIException('Stripe charge failed with API error.')

    def _create_stripe_charge(self, customer, amount, description):
        if settings.TESTING:
            return InlineClass({'status': self.STATUS_CHARGE_SUCCEEDED, 'id': 'someid'})

        try:
            return stripe.Charge.create(
                customer=customer.id,
                amount=amount,
                currency=self.CURRENCY,
                description=description)
        except stripe.error.InvalidRequestError as e:
            logger.warning('Invalid Stripe request! %s', str(e))
            if settings.DEBUG:
                raise APIException(e)
            else:
                raise APIException('Stripe charge failed with API error.')

    def _login_user(self, user):
        user.backend = 'django.contrib.auth.backends.ModelBackend'  # FIXME: Ninja!
        login(self.request, user)

    def _get_stripe_customer(self, stripe_customer_id):
        if settings.TESTING:
            return InlineClass({'id': 'someid'})

        try:
            return stripe.Customer.retrieve(stripe_customer_id)
        except stripe.error.InvalidRequestError as e:
            logger.warning('Invalid Stripe request! %s', str(e))
            if settings.DEBUG:
                raise APIException(e)
            else:
                raise APIException('Stripe charge failed with API error.')


class MembershipChargeRenewView(MembershipChargeView):
    permission_classes = (IsAuthenticated, )
    serializer_class = OrderChargeRenewSerializer

    def post(self, request):
        self._logged_in_user = request.user
        return super().post(request)
