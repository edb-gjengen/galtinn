from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from dusken.models import DuskenUser, OrgUnit


class OrgUnitUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = DuskenUser
        fields = ("id", "username")
        read_only_fields = ("id", "username")


class OrgUnitSerializer(serializers.ModelSerializer):
    users = OrgUnitUserSerializer(many=True, read_only=True)
    admins = OrgUnitUserSerializer(many=True, read_only=True)
    contact_person = OrgUnitUserSerializer()

    class Meta:
        model = OrgUnit
        fields = (
            "id",
            "name",
            "slug",
            "short_name",
            "is_active",
            "description",
            "email",
            "contact_person",
            "website",
            "group",
            "admin_group",
            "parent",
            "users",
            "admins",
        )
        read_only_fields = (
            "id",
            "is_active",
            "group",
            "admin_group",
            "parent",
            "users",
            "admins",
        )


class OrgUnitMemberSerializer(serializers.ModelSerializer):
    ROLE_MEMBER = "member"
    ROLE_ADMIN = "admin"
    ROLES = (ROLE_MEMBER, ROLE_ADMIN)

    full_name = serializers.CharField(source="get_full_name", read_only=True)
    role = serializers.SerializerMethodField()
    membership = serializers.SerializerMethodField()

    class Meta:
        model = DuskenUser
        fields = ("id", "uuid", "full_name", "email", "role", "membership")
        read_only_fields = fields

    def get_role(self, user):
        return self.ROLE_ADMIN if user.pk in self.context["admin_ids"] else self.ROLE_MEMBER

    def get_membership(self, user):
        memberships = getattr(user, "memberships_by_newest", None)
        membership = memberships[0] if memberships else user.last_membership
        if membership is None:
            return None
        return {
            "end_date": membership.end_date,
            "is_valid": membership.is_valid,
            "is_lifelong": membership.end_date is None,
        }


class OrgUnitMemberCreateSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=DuskenUser.objects.all())
    role = serializers.ChoiceField(choices=OrgUnitMemberSerializer.ROLES, default=OrgUnitMemberSerializer.ROLE_MEMBER)

    def validate_user(self, user):
        if self.context["members"].filter(pk=user.pk).exists():
            raise serializers.ValidationError(_("User already added"))
        return user


class OrgUnitMemberUpdateSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=OrgUnitMemberSerializer.ROLES)
