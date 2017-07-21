from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from dusken.api.serializers.memberships import MembershipSerializer
from dusken.models import Membership, MembershipType, MemberCard, Order


class OrderSerializer(serializers.ModelSerializer):
    member_card = serializers.SlugRelatedField(
        slug_field='card_number',
        queryset=MemberCard.objects.all())
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


class KassaOrderSerializer(serializers.ModelSerializer):
    membership_type = serializers.SlugRelatedField(
        write_only=True,
        slug_field='slug',
        queryset=MembershipType.objects.filter(is_active=True),)
    member_card = serializers.SlugRelatedField(
        allow_null=True,
        required=False,
        slug_field='card_number',
        queryset=MemberCard.objects.all(),)

    def validate(self, data):
        user = data['user']
        if user and user.has_lifelong_membership:
            raise serializers.ValidationError('Cannot renew a lifelong membership')
        elif user and user.last_membership and user.last_membership.is_valid:
            if not user.last_membership.expires_in_less_than_one_month:
                raise serializers.ValidationError(
                    'Cannot renew a membership that expires in more than one month')
        return data

    def create(self, validated_data, **kwargs):
        user = validated_data.get('user')
        phone_number = validated_data.get('phone_number')
        member_card = validated_data.get('member_card')

        membership_start_date = self._get_start_date(user, phone_number, member_card)

        with transaction.atomic():
            membership = self._create_membership(
                user=user,
                start_date=membership_start_date,
                membership_type=validated_data.get('membership_type'))
            order = self._create_order(
                membership=membership,
                phone_number=phone_number if not user else None,
                member_card=member_card if not user else None,
                transaction_id=validated_data.get('transaction_id'))

        return order

    def _get_start_date(self, user, phone_number, member_card):
        if user and user.has_valid_membership:
            return user.last_membership.end_date + timezone.timedelta(days=1)
        if not user:
            # TODO: lookup order
            pass
        return timezone.now().date()

    def _create_order(self, membership, transaction_id, phone_number, member_card):
        order = Order.objects.create(
            payment_method=Order.BY_PHYSICAL_CARD,
            transaction_id=transaction_id,
            price_nok=membership.membership_type.price,
            product=membership,
            user=membership.user,
            phone_number=phone_number,
            member_card=member_card)
        return order

    def _create_membership(self, user, membership_type, start_date):
        membership = Membership.objects.create(
            start_date=start_date,
            end_date=start_date + membership_type.duration,
            membership_type=membership_type,
            user=user)
        return membership

    class Meta:
        model = Order
        fields = ('user', 'membership_type', 'phone_number', 'member_card')
