from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from dusken.models import DuskenUser, Membership
from dusken.api.serializers import DuskenUserSerializer, MembershipSerializer


class DuskenUserViewSet(viewsets.ModelViewSet):
    queryset = DuskenUser.objects.all()
    serializer_class = DuskenUserSerializer


class MembershipViewSet(viewsets.ModelViewSet):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = (IsAuthenticated, )

