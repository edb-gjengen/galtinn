import django_filters
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import viewsets, filters
from dusken.api.serializers.users import DuskenUserSerializer
from dusken.models import DuskenUser


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
    search_fields = ('first_name', 'last_name', 'email', 'member_cards__card_number')
    lookup_field = 'id'

    def get_queryset(self):
        if self.request.user.has_perm('dusken.view_duskenuser'):
            return self.queryset
        return self.queryset.filter(pk=self.request.user.pk)
