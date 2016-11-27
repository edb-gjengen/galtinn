from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from dusken.api.serializers.users import DuskenUserSerializer
from dusken.models import DuskenUser


class DuskenUserViewSet(viewsets.ModelViewSet):
    queryset = DuskenUser.objects.all()
    serializer_class = DuskenUserSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        return self.queryset.filter(pk=self.request.user.pk)
