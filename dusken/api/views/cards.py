import django_filters
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import status, viewsets
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response

from dusken.api.serializers.cards import KassaMemberCardUpdateSerializer, MemberCardSerializer
from dusken.models import MemberCard


class MemberCardFilter(FilterSet):
    # Filter users by number to avoid DRF dropdown
    user = django_filters.NumberFilter()

    class Meta:
        model = MemberCard
        fields = ("user", "is_active")


class MemberCardViewSet(viewsets.ModelViewSet):
    """MemberCard API"""

    queryset = MemberCard.objects.all().order_by("pk")
    serializer_class = MemberCardSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = MemberCardFilter
    lookup_field = "card_number"

    def get_queryset(self):
        if self.request.user.has_perm("dusken.view_membercard"):
            return self.queryset
        return self.queryset.filter(user=self.request.user.pk)


class KassaMemberCardUpdateView(UpdateAPIView):
    queryset = MemberCard.objects.none()
    permission_classes = (DjangoModelPermissions,)
    serializer_class = KassaMemberCardUpdateSerializer

    def patch(self, _request, *_args, **_kwargs):
        # Validate
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = data.get("user")
        order = data.get("order")
        member_card = data.get("member_card")
        transaction_id = data.get("transaction_id")

        if user:
            member_card.register(user=user)
        elif order:
            member_card.register(order=order)
            if transaction_id:
                order.transaction_id = transaction_id
                order.save()

        return Response(serializer.data, status=status.HTTP_200_OK)
