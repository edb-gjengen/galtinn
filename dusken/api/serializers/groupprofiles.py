from rest_framework import serializers
from rest_framework.authtoken.models import Token

from dusken.models import GroupProfile


class GroupProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = GroupProfile
        fields = (
            "id",
            "posix_name",
            "description",
            "type",
            "discord_role_id",
            "group",
        )
        read_only_fields = (
            "id",
            "posix_name",
            "description",
            "type",
            "discord_role_id",
            "group",
        )


# FIXME: this does not work, like, at all
class GroupProfileRegisterSerializer(serializers.ModelSerializer):
    auth_token = serializers.SlugRelatedField(read_only=True, slug_field="key")  # type: ignore

    def create(self, validated_data):
        obj = super().create(validated_data)
        obj.save()

        Token.objects.create(GroupProfile=obj)

        return obj

    class Meta:
        model = GroupProfile
        fields = (
            "id",
            "posix_name",
            "description",
            "type",
            "discord_role_id",
            "group",
        )
        read_only_fields = (
            "id",
            "posix_name",
            "description",
            "type",
            "discord_role_id",
            "group",
        )
