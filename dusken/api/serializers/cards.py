from rest_framework import serializers
from rest_framework.serializers import ValidationError

from dusken.models import DuskenUser, MemberCard, Order


class MemberCardSerializer(serializers.ModelSerializer):
    orders = serializers.SlugRelatedField(read_only=True, many=True, slug_field="uuid")  # type: ignore

    class Meta:
        model = MemberCard
        fields = ("card_number", "registered", "is_active", "user", "created", "orders")


class KassaMemberCardUpdateSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(allow_null=True, queryset=DuskenUser.objects.all())
    order = serializers.SlugRelatedField(allow_null=True, slug_field="uuid", queryset=Order.objects.all())
    member_card = serializers.SlugRelatedField(slug_field="card_number", queryset=MemberCard.objects.all())
    transaction_id = serializers.CharField(allow_null=True, required=False)

    def validate(self, data):
        user = data.get("user")
        order = data.get("order")
        member_card = data.get("member_card")
        if member_card.registered:
            raise ValidationError("Card is already registered")
        if not (user or order):
            raise ValidationError("Need user or order")
        return data
