from rest_framework import serializers

from dusken.models import MembershipType


class MembershipTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipType
        fields = (
            "id",
            "name",
            "slug",
            "price",
            "price_nok_kr",
            "description",
            "is_active",
            "is_default",
            "expiry_type",
        )
        read_only_fields = fields
