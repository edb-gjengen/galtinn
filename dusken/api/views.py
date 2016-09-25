from django.conf import settings
from django.contrib.auth import login
from django.utils import timezone
import logging

from rest_framework import status
from rest_framework import viewsets
from rest_framework.exceptions import APIException
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
import stripe

from dusken.api.serializers import DuskenUserSerializer, MembershipSerializer, OrderChargeSerializer
from dusken.models import DuskenUser, Membership, MembershipType, Order
from dusken.utils import InlineClass

logger = logging.getLogger(__name__)


class DuskenUserViewSet(viewsets.ModelViewSet):
    queryset = DuskenUser.objects.all()
    serializer_class = DuskenUserSerializer


class MembershipViewSet(viewsets.ModelViewSet):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = (IsAuthenticated, )


class MembershipChargeView(GenericAPIView):
    queryset = Membership.objects.none()
    permission_classes = (AllowAny, )
    serializer_class = OrderChargeSerializer

    CURRENCY = 'NOK'
    STATUS_CHARGE_SUCCEEDED = 'succeeded'
    _user = None

    def post(self, request):
        stripe.api_key = settings.STRIPE_SECRET_KEY

        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        stripe_token = request.data.get('stripe_token')

        membership_type = serializer.validated_data.get('product')
        amount = membership_type.price  # Amount in ore

        # New customer
        customer = self._create_stripe_customer(stripe_token)

        # Charge
        description = '{}: {}'.format(membership_type.name, membership_type.description)
        charge = self._create_stripe_charge(customer, amount, description)

        if charge.status != self.STATUS_CHARGE_SUCCEEDED:
            logger.warning('stripe.Charge did not succeed: %s', charge.status)
            return Response({'error': 'stripe.Charge did not succeed :-('})

        # Winning, save new order, with user and stripe customer id :-)
        order = serializer.save(
            transaction_id=charge.id,
            stripe_customer_id=customer.id
        )
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


class MembershipRenewChargeView(MembershipChargeView):
    permission_classes = (IsAuthenticated, )

    def post(self, request):
        stripe_customer_id = self.request.user.stripe_customer_id
        # TODO implement for existing, logged in user
