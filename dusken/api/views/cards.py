from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from dusken.api.serializers.cards import MemberCardSerializer
from dusken.models import MemberCard


class MemberCardViewSet(viewsets.ModelViewSet):
    queryset = MemberCard.objects.all()
    serializer_class = MemberCardSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        return self.queryset.filter(pk=self.request.user.pk)
