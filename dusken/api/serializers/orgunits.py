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
