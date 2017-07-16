from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from dusken.api.serializers.users import NewDuskenUserSerializer
from dusken.models import Membership, MembershipType, Order


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('uuid', 'price_nok', 'user', 'product', 'payment_method',
                  'transaction_id', 'extra_data')


class OrderChargeSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=MembershipType.objects.filter(is_active=True))
    user = NewDuskenUserSerializer()

    def validate_product(self, value):
        # FIXME(nikolark): validate membership_type, only active users get active product
        return value

    def create(self, validated_data, **kwargs):
        with transaction.atomic():
            user = self._create_user(validated_data.get('user'), validated_data.get('stripe_customer_id'))
            membership = self._create_membership(user, validated_data.get('product'))
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

    def _create_user(self, user_data, stripe_customer_id):
        # FIXME: Easier way?
        user_data['stripe_customer_id'] = stripe_customer_id
        user_serializer = NewDuskenUserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        return user_serializer.save()

    class Meta:
        model = Order
        fields = ('user', 'product')


class OrderChargeRenewSerializer(OrderChargeSerializer):
    user = NewDuskenUserSerializer(read_only=True)

    def validate(self, attrs):
        # TODO: Implement business logic
        # TODO: Can't renew membership if has existing expiring in more than 1 month
        # TODO: Can't renew if existing lifelong
        return attrs

    def create(self, validated_data, **kwargs):
        logged_in_user = validated_data.get('logged_in_user')

        with transaction.atomic():
            membership = self._create_membership(logged_in_user, validated_data.get('product'))
            order = self._create_order(membership, validated_data.get('transaction_id'))

        return order
