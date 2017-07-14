from rest_framework import viewsets
from dusken.api.serializers.users import DuskenUserSerializer
from dusken.models import DuskenUser


class DuskenUserViewSet(viewsets.ModelViewSet):
    """ DuskenUser API """
    queryset = DuskenUser.objects.all()
    serializer_class = DuskenUserSerializer

    def get_queryset(self):
        if self.request.user.has_perm('dusken.view_duskenuser'):
            return self.queryset
        return self.queryset.filter(pk=self.request.user.pk)
