from dusken_api.models import Member
from dusken_api.serializers import MemberSerializer
from rest_framework import viewsets

class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

