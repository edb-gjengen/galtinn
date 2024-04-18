from django.contrib.auth.models import Group as DjangoGroup
from rest_framework import serializers

from dusken.models import GroupDiscordRole, GroupProfile


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


class GroupSerializer(serializers.ModelSerializer):
    profile = GroupProfileSerializer()

    class Meta:
        model = DjangoGroup
        fields = ("id", "name", "profile")
        read_only_fields = ("id",)
