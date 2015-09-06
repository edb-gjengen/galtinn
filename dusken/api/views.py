from datetime import timedelta
import logging
from django.conf import settings
from django.contrib.auth import login
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny

from dusken.models import DuskenUser, Membership, MembershipType, Payment
from dusken.api.serializers import DuskenUserSerializer, MembershipSerializer, SimpleDuskenUserSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
import stripe


logger = logging.getLogger(__name__)


class DuskenUserViewSet(viewsets.ModelViewSet):
    queryset = DuskenUser.objects.all()
    serializer_class = DuskenUserSerializer


class MembershipViewSet(viewsets.ModelViewSet):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = (IsAuthenticated, )


class MembershipChargeView(APIView):
    queryset = Membership.objects.none()
    permission_classes = (AllowAny, )

    def post(self, request):
        membership_type = MembershipType.objects.get(pk=settings.MEMBERSHIP_TYPE_ID)
        stripe.api_key = settings.STRIPE_SECRET_KEY
        currency = 'NOK'
        amount = membership_type.price  # Amount in ore

        user_serializer = SimpleDuskenUserSerializer(data=self.request.data.get('user'))
        user_serializer.is_valid(raise_exception=True)

        stripe_token = request.data.get('stripe_token')
        email = stripe_token.get('email')

        # New customer
        customer = stripe.Customer.create(
            email=email,
            card=stripe_token.get('id')
        )

        charge = stripe.Charge.create(
            customer=customer.id,
            amount=amount,
            currency=currency,
            description='{}: {}'.format(membership_type.name, membership_type.description)
        )

        if charge['status'] != 'succeeded':
            logger.warning('stripe.Charge did not succeed: %s', charge['status'])
            return Response({'error': 'stripe.Charge did not succeed :-('})

        # Winning!
        user = user_serializer.save(stripe_customer_id=customer.id)
        # Log the user in
        user.backend = 'django.contrib.auth.backends.ModelBackend'  # FIXME: Ninja!
        login(self.request, user)

        payment = Payment.objects.create(
            payment_method=Payment.BY_CARD,
            transaction_id=charge.id,
            value=amount
        )
        start_date = timezone.now()
        membership = Membership.objects.create(
            start_date=start_date,
            end_date=start_date + timedelta(days=365),
            membership_type=membership_type,
            user=user,
            payment=payment
        )
        return Response({'result': 'Success!'})


class MembershipRenewChargeView(APIView):
    queryset = Membership.objects.none()
    permission_classes = (IsAuthenticated, )

    def post(self, request):
        stripe_customer_id = self.request.user.stripe_customer_id
        # TODO implement for existing user
