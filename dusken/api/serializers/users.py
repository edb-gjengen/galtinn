from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from dusken.models import DuskenUser
from dusken.api.serializers.cards import MemberCardSerializer
from dusken.api.serializers.memberships import MembershipSerializer
from dusken.utils import generate_username, phone_number_exist, email_exists
from dusken.validators import phone_number_validator, email_validator


class DuskenUserSerializer(serializers.ModelSerializer):
    active_member_card = MemberCardSerializer()
    last_membership = MembershipSerializer()

    class Meta:
        model = DuskenUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'phone_number',
                  'date_of_birth', 'legacy_id', 'place_of_study', 'active_member_card',
                  'is_volunteer', 'is_member', 'last_membership')
        read_only_fields = ('id', 'legacy_id', 'username', 'active_member_card',
                            'is_volunteer', 'is_member', 'last_membership')


class DuskenUserRegisterSerializer(serializers.ModelSerializer):
    auth_token = serializers.SlugRelatedField(read_only=True, slug_field='key')
    active_member_card = MemberCardSerializer(read_only=True)
    last_membership = MembershipSerializer(read_only=True)

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data['username'] = generate_username(validated_data['first_name'], validated_data['last_name'])
        obj = super().create(validated_data)

        obj.set_password(password)
        obj.save()
        obj.set_ldap_hash(password)

        Token.objects.create(user=obj)

        return obj

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_phone_number(self, value):
        phone_number_validator(value)
        if phone_number_exist(value):
            raise ValidationError(_('Phone number already in use'))

        return value

    def validate_email(self, value):
        email_validator(value)
        if email_exists(value):
            raise ValidationError(_('Email already in use'))

        return value

    class Meta:
        model = DuskenUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'phone_number', 'password',
                  'date_of_birth', 'legacy_id', 'place_of_study', 'active_member_card',
                  'is_volunteer', 'is_member', 'last_membership', 'auth_token')
        read_only_fields = ('id', 'legacy_id', 'username', 'active_member_card', 'date_of_birth', 'place_of_study',
                            'is_volunteer', 'is_member', 'last_membership', 'auth_token')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
            'phone_number': {'required': True},
            'password': {'required': True, 'write_only': True}
        }
