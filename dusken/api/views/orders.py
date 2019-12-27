import django_filters
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import viewsets
from phonenumber_field.modelfields import PhoneNumberField
from dusken.api.serializers.orders import OrderSerializer
from dusken.models import Order


class OrderFilter(FilterSet):
    # Filter users and member cards by number to avoid DRF dropdown
    user = django_filters.NumberFilter()
    card_number = django_filters.NumberFilter(field_name='member_card__card_number')

    class Meta:
        model = Order
        fields = ('uuid', 'created', 'price_nok', 'user', 'product', 'payment_method',
                  'transaction_id', 'phone_number', 'card_number')
        filter_overrides = {
            PhoneNumberField: {
                'filter_class': django_filters.CharFilter
            }
        }


class OrderViewSet(viewsets.ModelViewSet):
    """Order API"""
    queryset = Order.objects.all().order_by('-created')
    serializer_class = OrderSerializer
    filter_backends = (DjangoFilterBackend, )
    filter_class = OrderFilter
    lookup_field = 'uuid'

    def get_queryset(self):
        if self.request.user.has_perm('dusken.view_order'):
            return self.queryset
        return self.queryset.filter(user=self.request.user.pk)
