from django.contrib.auth.models import Group as DjangoGroup
from django_filters.rest_framework import BooleanFilter, DjangoFilterBackend, FilterSet
from rest_framework import filters, mixins, viewsets

from dusken.api.serializers.groups import GroupSerializer


class GroupFilter(FilterSet):
    no_discord_roles = BooleanFilter(field_name="profile__discord_roles", lookup_expr="isnull")

    class Meta:
        model = DjangoGroup
        fields = ("id", "name", "profile", "profile__discord_roles__discord_id")


class GroupViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Group API"""

    queryset = DjangoGroup.objects.all().order_by("id")
    serializer_class = GroupSerializer
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
    )
    filterset_class = GroupFilter
    search_fields = ("id", "name", "profile", "profile__discord_roles__discord_id")
    lookup_field = "id"

    def get_queryset(self):
        if self.request.user.has_perm("dusken.view_groups"):  # TODO: find correct perm
            return self.queryset
        return self.queryset.filter(pk=self.request.user.pk)
