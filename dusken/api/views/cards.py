import django_filters
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import viewsets
from dusken.api.serializers.cards import MemberCardSerializer
from dusken.models import MemberCard


class MemberCardFilter(FilterSet):
    # Filter users by number to avoid DRF dropdown
    user = django_filters.NumberFilter()

    class Meta:
        model = MemberCard
        fields = ('user', 'is_active')


class MemberCardViewSet(viewsets.ModelViewSet):
    """MemberCard API"""
    queryset = MemberCard.objects.all()
    serializer_class = MemberCardSerializer
    filter_backends = (DjangoFilterBackend, )
    filter_class = MemberCardFilter
    lookup_field = 'card_number'

    def get_queryset(self):
        if self.request.user.has_perm('dusken.view_membercard'):
            return self.queryset
        return self.queryset.filter(user=self.request.user.pk)
