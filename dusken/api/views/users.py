import django_filters
from phonenumber_field.modelfields import PhoneNumberField
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import views, viewsets, filters, permissions
from rest_framework.response import Response
from dusken.api.serializers.users import DuskenUserSerializer
from dusken.models import DuskenUser
from django.http import JsonResponse, HttpResponseForbidden


class DuskenUserFilter(FilterSet):
    class Meta:
        model = DuskenUser
        fields = ('username', 'email', 'phone_number')
        filter_overrides = {
            PhoneNumberField: {
                'filter_class': django_filters.CharFilter
            }
        }


class DuskenUserViewSet(viewsets.ModelViewSet):
    """ DuskenUser API """
    queryset = DuskenUser.objects.all().order_by('id')
    serializer_class = DuskenUserSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, )
    filter_class = DuskenUserFilter
    search_fields = ('first_name', 'last_name', 'email', 'member_cards__card_number', 'phone_number')
    lookup_field = 'id'

    def get_queryset(self):
        if self.request.user.has_perm('dusken.view_duskenuser'):
            return self.queryset
        return self.queryset.filter(pk=self.request.user.pk)


class CurrentUserView(views.APIView):
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request):
        serializer = DuskenUserSerializer(request.user)
        return Response(serializer.data)


def user_pk_to_uuid(request):
    if not request.user.is_authenticated or not (request.user.is_volunteer or request.user.is_superuser):
        return HttpResponseForbidden()
    user_pk = request.GET.get('user', None)
    user = DuskenUser.objects.get(pk=user_pk)

    data = {
        'uuid': user.uuid
    }
    return JsonResponse(data)
