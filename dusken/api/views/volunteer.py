from django.db import models
from rest_framework import permissions, serializers, status
from rest_framework.generics import (
    CreateAPIView,
    GenericAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.response import Response

from dusken.api.serializers.orgunits import OrgUnitSerializer
from dusken.models import DuskenUser, OrgUnit


class IsVolunteer(permissions.BasePermission):
    def has_permission(self, request, _view):
        if not request.user.is_authenticated:
            return False

        return request.user.is_volunteer or request.user.is_superuser


class IsOrgUnitAdmin(permissions.BasePermission):
    """Checks if the user is an admin of the OrgUnit. Only meaningful in a generic view where the object is an OrgUnit.
    Ref: https://www.django-rest-framework.org/api-guide/permissions/#custom-permissions
    """

    def has_object_permission(self, request, _view, org_unit):
        if not request.user.is_authenticated:
            return False

        return request.user.is_superuser or request.user.has_group(org_unit.admin_group)


class OrgUnitListAPIView(ListAPIView):
    permission_classes = [IsVolunteer]
    serializer_class = OrgUnitSerializer
    queryset = OrgUnit.objects.filter(is_active=True).order_by("name")
    pagination_class = None


class MyOrgUnitsAPIView(ListAPIView):
    """OrgUnits that the current user is a member or admin of."""

    permission_classes = [IsVolunteer]
    serializer_class = OrgUnitSerializer
    pagination_class = None

    def get_queryset(self):
        user_groups = self.request.user.groups.all()
        return OrgUnit.objects.filter(is_active=True, group__in=user_groups).order_by("name").distinct()


class OrgUnitDetailAPIView(RetrieveAPIView):
    permission_classes = [IsVolunteer]
    serializer_class = OrgUnitSerializer
    queryset = OrgUnit.objects.filter(is_active=True)
    lookup_field = "slug"


class OrgUnitUpdateAPIView(UpdateAPIView):
    permission_classes = [IsVolunteer]
    serializer_class = OrgUnitSerializer
    queryset = OrgUnit.objects.filter(is_active=True)
    lookup_field = "slug"

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if not request.user.is_superuser and not request.user.has_group(obj.admin_group):
            self.permission_denied(request)


class OrgUnitMemberSerializer(serializers.ModelSerializer):
    is_admin = serializers.SerializerMethodField()
    membership_end_date = serializers.SerializerMethodField()
    membership_is_valid = serializers.SerializerMethodField()

    class Meta:
        model = DuskenUser
        fields = (
            "id",
            "uuid",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_admin",
            "membership_end_date",
            "membership_is_valid",
        )
        read_only_fields = fields

    def get_is_admin(self, obj):
        admin_group = self.context.get("admin_group")
        if admin_group is None:
            return False
        return obj.groups.filter(pk=admin_group.pk).exists()

    def get_membership_end_date(self, obj):
        ms = obj.last_membership
        if ms is None:
            return None
        return ms.end_date

    def get_membership_is_valid(self, obj):
        ms = obj.last_membership
        if ms is None:
            return False
        return ms.is_valid


class OrgUnitMembersAPIView(GenericAPIView):
    permission_classes = [IsVolunteer]

    def get(self, request, slug):
        orgunit = OrgUnit.objects.get(slug=slug, is_active=True)
        members = list(orgunit.users)
        is_admin = request.user.is_superuser or request.user.has_group(orgunit.admin_group)
        serializer = OrgUnitMemberSerializer(members, many=True, context={"admin_group": orgunit.admin_group})
        return Response({"members": serializer.data, "is_admin": is_admin})


class OrgUnitManageMemberSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()

    def validate(self, attrs):
        try:
            user = DuskenUser.objects.get(pk=attrs.get("user_id"))
        except DuskenUser.DoesNotExist as err:
            raise serializers.ValidationError("User does not exist.") from err

        attrs["user"] = user
        return attrs


class OrgUnitAddMemberSerializer(OrgUnitManageMemberSerializer):
    role = serializers.ChoiceField(choices=["member", "admin"])


class OrgUnitManageMemberBaseAPIView(CreateAPIView):
    permission_classes = [IsOrgUnitAdmin]
    queryset = OrgUnit.objects.filter(is_active=True)
    lookup_field = "slug"


class OrgUnitAddMemberAPIView(OrgUnitManageMemberBaseAPIView):
    serializer_class = OrgUnitAddMemberSerializer

    def perform_create(self, serializer):
        org_unit = self.get_object()
        user = serializer.validated_data["user"]
        role = serializer.validated_data["role"]

        if role == "admin":
            org_unit.add_admin(user, self.request.user)
        else:
            org_unit.add_user(user, self.request.user)


class OrgUnitRemoveMemberAPIView(OrgUnitManageMemberBaseAPIView):
    """Remove a member from an organization unit"""

    serializer_class = OrgUnitManageMemberSerializer

    def create(self, request, *args, **kwargs):
        res = super().create(request, *args, **kwargs)
        res.status_code = status.HTTP_200_OK
        return res

    def perform_create(self, serializer):
        org_unit = self.get_object()
        user = serializer.validated_data["user"]
        org_unit.remove_user(user, self.request.user)
        org_unit.remove_admin(user, self.request.user)


MIN_SEARCH_LENGTH = 2


class UserSearchAPIView(ListAPIView):
    """Search users by name/email for the volunteer user search."""

    permission_classes = [IsVolunteer]
    pagination_class = None

    class UserSearchResultSerializer(serializers.ModelSerializer):
        class Meta:
            model = DuskenUser
            fields = ("id", "uuid", "username", "first_name", "last_name", "email")
            read_only_fields = fields

    serializer_class = UserSearchResultSerializer

    def get_queryset(self):
        q = self.request.query_params.get("q", "").strip()
        if len(q) < MIN_SEARCH_LENGTH:
            return DuskenUser.objects.none()
        return DuskenUser.objects.filter(
            models.Q(first_name__icontains=q)
            | models.Q(last_name__icontains=q)
            | models.Q(email__icontains=q)
            | models.Q(username__icontains=q)
        )[:20]
