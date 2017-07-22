from rest_framework import serializers

from dusken.models import MemberCard, Order


class MemberCardSerializer(serializers.ModelSerializer):
    orders = serializers.SlugRelatedField(
        read_only=True,
        many=True,
        slug_field='uuid')

    class Meta:
        model = MemberCard
        fields = ('card_number', 'registered', 'is_active', 'user', 'created', 'orders')
