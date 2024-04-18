from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import filters, viewsets

from dusken.api.serializers.users import UserDiscordProfileSerializer
from dusken.models import UserDiscordProfile


class UserDiscordProfileFilter(FilterSet):
    class Meta:
        model = UserDiscordProfile
        fields = ("id", "discord_id", "user")


class UserDiscordProfileViewSet(viewsets.ModelViewSet):
    """Discord User API"""

    queryset = UserDiscordProfile.objects.all().order_by("id")
    serializer_class = UserDiscordProfileSerializer
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
    )
    filterset_class = UserDiscordProfileFilter
    search_fields = ("discord_id", "user__id")
    lookup_field = "id"

    def get_queryset(self):
        if self.request.user.has_perm("dusken.view_discord_profile"):
            return self.queryset
        return self.queryset.filter(pk=self.request.user.pk)
