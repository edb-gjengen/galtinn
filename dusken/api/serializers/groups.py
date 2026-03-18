from django.contrib.auth.models import Group as DjangoGroup
from rest_framework import serializers

from dusken.models import GroupDiscordRole, GroupProfile, OrgUnit


class GroupDiscordRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupDiscordRole
        fields = ("id", "discord_id", "description")
        read_only_fields = ("id",)


class GroupProfileSerializer(serializers.ModelSerializer):
    discord_roles = GroupDiscordRoleSerializer(many=True)

    class Meta:
        model = GroupProfile
        fields = ("id", "posix_name", "description", "type", "discord_roles")
        read_only_fields = ("id", "posix_name", "description", "type", "discord_roles")


class GroupOrgUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrgUnit
        fields = ("id", "name", "slug")
        read_only_fields = ("id", "name", "slug")


class GroupSerializer(serializers.ModelSerializer):
    profile = GroupProfileSerializer()
    member_orgunits = GroupOrgUnitSerializer(many=True, read_only=True)

    class Meta:
        model = DjangoGroup
        fields = ("id", "name", "profile", "member_orgunits")
        read_only_fields = ("id",)
