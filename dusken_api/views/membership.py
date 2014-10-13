from dusken_api.models import Membership
from dusken_api.serializers import MembershipSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated


class MembershipViewSet(viewsets.ModelViewSet):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = (IsAuthenticated, )

