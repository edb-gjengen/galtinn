from dusken_api.models import Membership
from dusken_api.serializers import MembershipSerializer
from rest_framework import generics

class MembershipList(generics.ListCreateAPIView):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer

class MembershipDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer

