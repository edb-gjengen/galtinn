from rest_framework import serializers

from dusken.models import Membership, MembershipType


class MembershipSerializer(serializers.ModelSerializer):
    membership_type = serializers.SlugRelatedField(slug_field="slug", queryset=MembershipType.objects.all())

    class Meta:
        model = Membership
        fields = ("id", "start_date", "end_date", "order", "user", "membership_type", "is_valid")
        read_only_fields = ("id", "is_valid")
