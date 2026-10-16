from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import filters, mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from dusken.api.serializers.orgunits import (
    OrgUnitMemberCreateSerializer,
    OrgUnitMemberSerializer,
    OrgUnitMemberUpdateSerializer,
    OrgUnitSerializer,
)
from dusken.models import DuskenUser, Membership, OrgUnit


class OrgUnitFilter(FilterSet):
    class Meta:
        model = OrgUnit
        fields = ("id", "name", "slug")


class OrgUnitViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """OrgUnit API"""

    queryset = OrgUnit.objects.all().order_by("id")
    serializer_class = OrgUnitSerializer
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
    )
    filterset_class = OrgUnitFilter
    search_fields = (
        "id",
        "name",
        "slug",
    )
    lookup_field = "id"

    def get_queryset(self):
        if self.request.user.has_perm("dusken.view_orgunit"):
            return self.queryset
        return self.queryset.filter(pk=self.request.user.pk)


class IsOrgUnitAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        admin_group = view.orgunit.admin_group
        return admin_group is not None and user.has_group(admin_group)


class OrgUnitMemberViewSet(viewsets.GenericViewSet):
    """Members of an OrgUnit, managed by its admins"""

    permission_classes = (IsOrgUnitAdmin,)
    serializer_class = OrgUnitMemberSerializer
    pagination_class = None

    @cached_property
    def orgunit(self):
        return get_object_or_404(OrgUnit, slug=self.kwargs["slug"])

    def get_queryset(self):
        groups = [group for group in (self.orgunit.group, self.orgunit.admin_group) if group is not None]
        newest_memberships = Membership.objects.select_related("membership_type").order_by("-start_date")
        return (
            DuskenUser.objects.filter(groups__in=groups)
            .distinct()
            .order_by("first_name", "last_name", "username")
            .prefetch_related(Prefetch("memberships", queryset=newest_memberships, to_attr="memberships_by_newest"))
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        admin_group = self.orgunit.admin_group
        context["admin_ids"] = set(admin_group.user_set.values_list("pk", flat=True)) if admin_group else set()
        return context

    def _check_manageable(self):
        if self.orgunit.group is None or self.orgunit.admin_group is None:
            raise ValidationError(_("This organisation has no member or admin group"))

    def _member_response(self, user, status_code=status.HTTP_200_OK):
        member = self.get_queryset().get(pk=user.pk)
        return Response(self.get_serializer(member).data, status=status_code)

    def list(self, _request, *_args, **_kwargs):
        members = self.get_serializer(self.get_queryset(), many=True).data
        # Admins first, keeping the name ordering within each role
        members = sorted(members, key=lambda member: member["role"] != OrgUnitMemberSerializer.ROLE_ADMIN)
        return Response(members)

    def create(self, request, *_args, **_kwargs):
        self._check_manageable()
        serializer = OrgUnitMemberCreateSerializer(data=request.data, context={"members": self.get_queryset()})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        if serializer.validated_data["role"] == OrgUnitMemberSerializer.ROLE_ADMIN:
            self.orgunit.add_admin(user, request.user)
        else:
            self.orgunit.add_user(user, request.user)
        return self._member_response(user, status.HTTP_201_CREATED)

    def partial_update(self, request, *_args, **_kwargs):
        self._check_manageable()
        user = self.get_object()
        serializer = OrgUnitMemberUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        is_admin = user.pk in self.get_serializer_context()["admin_ids"]
        make_admin = serializer.validated_data["role"] == OrgUnitMemberSerializer.ROLE_ADMIN
        if is_admin != make_admin:
            if self.orgunit.group == self.orgunit.admin_group:
                raise ValidationError(_("All members of this organisation are admins"))
            if make_admin:
                self.orgunit.add_admin(user, request.user)
            else:
                self.orgunit.remove_admin(user, request.user)
        return self._member_response(user)

    def destroy(self, request, *_args, **_kwargs):
        self._check_manageable()
        user = self.get_object()
        self.orgunit.remove_user(user, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
