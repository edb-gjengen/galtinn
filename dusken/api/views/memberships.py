import logging
import stripe
import django_filters

from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import status
from rest_framework import viewsets
from rest_framework.exceptions import APIException
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from dusken.api.serializers.memberships import MembershipSerializer
from dusken.api.serializers.orders import (StripeOrderChargeSerializer,
                                           StripeOrderChargeRenewSerializer)
from dusken.models import Membership
from dusken.utils import InlineClass
from django.utils.translation import ugettext_lazy as _
logger = logging.getLogger(__name__)


class MembershipFilter(FilterSet):
    # Filter users by number to avoid DRF dropdown
    user = django_filters.NumberFilter()

    class Meta:
        model = Membership
        fields = ('id', 'user', 'start_date')


class MembershipViewSet(viewsets.ModelViewSet):
    """ Membership API """
    queryset = Membership.objects.all().order_by('pk')
    serializer_class = MembershipSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = MembershipFilter
    pagination_class = PageNumberPagination

    def get_queryset(self):
        if self.request.user.has_perm('dusken.view_membership'):
            return self.queryset
        return self.queryset.filter(user=self.request.user.pk)


class MembershipChargeView(GenericAPIView):
    queryset = Membership.objects.none()
    permission_classes = (IsAuthenticated, )
    serializer_class = StripeOrderChargeSerializer

    CURRENCY = 'NOK'
    STATUS_CHARGE_SUCCEEDED = 'succeeded'
    STATUS_CHARGE_FAILED = 'failed'

    def post(self, request):
        stripe.api_key = settings.STRIPE_SECRET_KEY

        # Validate
        serializer = self.serializer_class(data=self.request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)

        # Stripe customer
        if request.user.stripe_customer_id:
            # Existing
            customer = self._get_stripe_customer(request.user.stripe_customer_id)
        else:
            # New
            customer = self._create_stripe_customer(request.data.get('stripe_token'))
            request.user.stripe_customer_id = customer.id
            request.user.save()

        # Charge
        membership_type = serializer.validated_data.get('membership_type')
        description = '{}: {}'.format(membership_type.name, membership_type.description)
        charge = self._create_stripe_charge(customer, membership_type.price, description)

        if charge.status != self.STATUS_CHARGE_SUCCEEDED:
            logger.warning('stripe.Charge did not succeed: %s', charge.status)
            return Response({'error': _('Your card has been declined')}, status=400)

        # Winning, save new order, with user and stripe customer id :-)
        order = serializer.save(
            transaction_id=charge.id,
            stripe_customer_id=customer.id,
            user=request.user
        )

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
        except stripe.error.CardError:
            return InlineClass({'status': self.STATUS_CHARGE_FAILED})

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
    serializer_class = StripeOrderChargeRenewSerializer
