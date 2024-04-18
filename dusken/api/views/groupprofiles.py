from django_filters.rest_framework import BooleanFilter, DjangoFilterBackend, FilterSet
from rest_framework import filters, permissions, viewsets
from rest_framework.generics import CreateAPIView, RetrieveAPIView

from dusken.api.serializers.groupprofiles import (
    GroupProfileRegisterSerializer,
    GroupProfileSerializer,
)
from dusken.models import GroupProfile


class GroupProfileFilter(FilterSet):
    no_discord_role = BooleanFilter(field_name="discord_role_id", lookup_expr="isnull")

    class Meta:
        model = GroupProfile
        fields = ("id", "posix_name", "description", "group", "discord_role_id")


class GroupProfileViewSet(viewsets.ModelViewSet):
    """GroupProfile API"""

    queryset = GroupProfile.objects.all().order_by("id")
    serializer_class = GroupProfileSerializer
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
    )
    filterset_class = GroupProfileFilter
    search_fields = (
        "id",
        "posix_name",
        "group",
        "discord_role_id",
    )
    lookup_field = "id"

    def get_queryset(self):
        if self.request.user.has_perm(
            "dusken.view_groupprofile"
        ):  # TODO: find correct perm
            return self.queryset
        return self.queryset.filter(pk=self.request.user.pk)


class CurrentUserView(RetrieveAPIView):  # TODO: fix
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GroupProfileSerializer

    def get_object(self):
        return self.request.groupprofile


class RegisterOrgUnitView(CreateAPIView):
    # FIXME: a user can create a orgunit without a slug, which will crash the frontend on /orgunits
    permission_classes = [permissions.AllowAny]
    serializer_class = GroupProfileRegisterSerializer
    queryset = GroupProfile.objects.all()
