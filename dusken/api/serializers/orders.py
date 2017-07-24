from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework.serializers import ValidationError

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


class BaseMembershipOrder(object):
    def _create_order(self, membership, transaction_id, phone_number=None, member_card=None):
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

    def _validate_user_can_renew(self, user):
        if user.is_lifelong_member:
            raise ValidationError('Cannot renew a lifelong membership')
        elif user.is_member:
            if not user.last_membership.expires_in_less_than_one_month:
                raise ValidationError(
                    'Cannot renew a membership that expires in more than one month')


class StripeOrderSerializer(BaseMembershipOrder, serializers.ModelSerializer):
    membership_type = serializers.SlugRelatedField(
        write_only=True,
        slug_field='slug',
        queryset=MembershipType.objects.filter(is_active=True),)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def validate_membership_type(self, value):
        if not value or value.slug not in ('standard', 'active'):
            raise ValidationError('Invalid membership type')
        # FIXME(nikolark): validate membership_type, only active users get active product
        return value

    def validate(self, data):
        self._validate_user_can_renew(data.get('user'))
        return data

    def create(self, validated_data, **kwargs):
        user = validated_data.get('user')
        start_date = self._get_start_date(user)

        with transaction.atomic():
            membership = self._create_membership(
                user=user,
                start_date=start_date,
                membership_type=validated_data.get('membership_type'))
            order = self._create_order(
                membership=membership,
                transaction_id=validated_data.get('transaction_id'))

        return order

    def _get_start_date(self, user):
        if user and user.is_member:
            return user.last_membership.end_date + timezone.timedelta(days=1)
        return timezone.now().date()

    class Meta:
        model = Order
        fields = ('user', 'membership_type')


class KassaOrderSerializer(BaseMembershipOrder, serializers.ModelSerializer):
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
        user = data.get('user')
        phone_number = data.get('phone_number')
        member_card = data.get('member_card')
        if not user and not (phone_number or member_card):
            raise ValidationError('Need user, phone_number or member_card')
        if member_card and user and member_card.registered and member_card.user != user:
            raise ValidationError('Member card already registered to a different user')
        if user:
            self._validate_user_can_renew(user)
        else:
            last_order = self._get_past_orders(phone_number, member_card).first()
            if last_order and not last_order.product.expires_in_less_than_one_month:
                raise ValidationError(
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
                transaction_id=validated_data.get('transaction_id'))
            if user and member_card and not user.member_cards.filter(pk=member_card.pk).exists():
                member_card.register(user=user)
            elif not user and member_card and not member_card.registered:
                member_card.register(order=order)

        return order

    def _get_start_date(self, user, phone_number, member_card):
        if user and user.is_member:
            return user.last_membership.end_date + timezone.timedelta(days=1)
        elif not user:
            last_order = self._get_past_orders(phone_number, member_card).first()
            if last_order and last_order.product.is_valid:
                return last_order.product.end_date + timezone.timedelta(days=1)
        return timezone.now().date()

    def _get_past_orders(self, phone_number, member_card):
        return Order.objects.filter(
            Q(phone_number__isnull=False, phone_number=phone_number) |
            Q(member_card__isnull=False, member_card=member_card)).order_by('-created')

    class Meta:
        model = Order
        fields = ('user', 'membership_type', 'phone_number', 'member_card', 'transaction_id')
