import logging

import django_filters
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import status, viewsets
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.response import Response

from dusken.api.serializers.memberships import MembershipSerializer
from dusken.api.serializers.orders import (
    KassaOrderSerializer,
    StripeOrderSerializer,
)
from dusken.api.views.stripe_mixin import StripeAPIMixin
from dusken.models import Membership

logger = logging.getLogger(__name__)


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

    def post(self, _request):
        # Validate
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        # TODO: Do something here?

        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MembershipChargeView(GenericAPIView, StripeAPIMixin):
    queryset = Membership.objects.none()
    permission_classes = (IsAuthenticated,)
    serializer_class = StripeOrderSerializer

    CURRENCY = "NOK"

    def post(self, request):
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
        charge = self._create_stripe_charge(customer, membership_type.price, description, self.CURRENCY)

        # Winning, save new order, with user and stripe customer id :-)
        serializer.save(transaction_id=charge.id, stripe_customer_id=customer.id, user=request.user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
