from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from dusken.api.serializers.memberships import MembershipSerializer
from dusken.models import Membership, MembershipType, Order


class OrderSerializer(serializers.ModelSerializer):
    member_card = serializers.SlugRelatedField(slug_field='card_number', read_only=True)
    product = MembershipSerializer()

    class Meta:
        model = Order
        fields = ('uuid', 'price_nok', 'user', 'product', 'payment_method',
                  'transaction_id', 'phone_number', 'member_card')


class StripeOrderChargeSerializer(serializers.ModelSerializer):
    membership_type = serializers.SlugRelatedField(
        write_only=True,
        slug_field='slug',
        queryset=MembershipType.objects.filter(is_active=True),)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def validate_membership_type(self, value):
        # FIXME(nikolark): validate membership_type, only active users get active product
        return value

    def create(self, validated_data, **kwargs):
        user = validated_data.get('user')

        with transaction.atomic():
            membership = self._create_membership(user, validated_data.get('membership_type'))
            order = self._create_order(membership, validated_data.get('transaction_id'))

        return order

    def _create_order(self, membership, transaction_id):
        order = Order.objects.create(
            payment_method=Order.BY_CARD,
            transaction_id=transaction_id,
            price_nok=membership.membership_type.price,
            product=membership,
            user=membership.user)
        return order

    def _create_membership(self, user, mt):
        start_date = timezone.now()
        membership = Membership.objects.create(
            start_date=start_date,
            end_date=start_date + mt.duration,
            membership_type=mt,
            user=user)
        return membership

    class Meta:
        model = Order
        fields = ('user', 'membership_type')


class StripeOrderChargeRenewSerializer(StripeOrderChargeSerializer):
    def validate(self, attrs):
        # TODO: Implement business logic
        # TODO: Can't renew membership if has existing expiring in more than 1 month
        # TODO: Can't renew if existing lifelong
        return attrs

    def create(self, validated_data, **kwargs):
        user = validated_data.get('user')

        with transaction.atomic():
            membership = self._create_membership(user, validated_data.get('membership_type'))
            order = self._create_order(membership, validated_data.get('transaction_id'))

        return order
