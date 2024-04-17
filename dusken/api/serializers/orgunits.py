from rest_framework import serializers
from rest_framework.authtoken.models import Token

from dusken.models import DuskenUser, OrgUnit


class OrgUnitUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = DuskenUser
        fields = ("id", "username", "discord_id")
        read_only_fields = ("id", "username", "discord_id")


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
            "discord_role_id",
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
            "discord_role_id",
            "group",
            "admin_group",
            "parent",
            "users",
            "admins",
        )


class OrgUnitRegisterSerializer(serializers.ModelSerializer):
    auth_token = serializers.SlugRelatedField(read_only=True, slug_field="key")  # type: ignore

    def create(self, validated_data):
        validated_data["slug"] = validated_data.get("slug", validated_data["name"].lower())
        obj = super().create(validated_data)
        obj.save()

        Token.objects.create(user=obj)

        return obj

    class Meta:
        model = OrgUnit
        fields = (
            "id",
            "name",
            "slug",
            "short_name",
            "is_active",
            "description",
            "discord_role_id",
            "has_discord_role_id",
            "email",
            "contact_person",
            "website",
            "group",
            "admin_group",
            "parent",
        )
        read_only_fields = (
            "id",
            "is_active",
            "discord_role_id",
            "has_discord_role_id",
            "group",
            "admin_group",
            "parent",
        )
        extra_kwargs = {
            "name": {"required": True},
            "slug": {"required": True},
        }
