from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from dusken.api.serializers.cards import MemberCardSerializer
from dusken.models import MemberCard


class MemberCardViewSet(viewsets.ModelViewSet):
    """MemberCard internal API"""
    queryset = MemberCard.objects.all()
    serializer_class = MemberCardSerializer
    filter_backends = (DjangoFilterBackend,)
