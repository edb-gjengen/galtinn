from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from dusken.api.serializers.membership_types import MembershipTypeSerializer
from dusken.models import MembershipType


class MembershipTypeListView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = MembershipTypeSerializer
    queryset = MembershipType.objects.filter(is_active=True).order_by("order")
    pagination_class = None
