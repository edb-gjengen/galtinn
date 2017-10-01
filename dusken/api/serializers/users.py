from pprint import pprint

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from dusken.models import DuskenUser
from dusken.api.serializers.cards import MemberCardSerializer
from dusken.api.serializers.memberships import MembershipSerializer
from dusken.utils import generate_username


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
    # TODO: Auth token
    # TODO: You are here
    active_member_card = MemberCardSerializer(read_only=True)
    last_membership = MembershipSerializer(read_only=True)

    def create(self, validated_data):
        # TODO Validate uniqueness?
        password = validated_data.pop('password')
        validated_data['username'] = generate_username(validated_data['first_name'], validated_data['last_name'])
        obj = super().create(validated_data)

        obj.set_password(password)
        obj.save()
        obj.set_ldap_hash(password)

        return obj

    def validate_password(self, value):
        validate_password(value)
        return value

    class Meta:
        model = DuskenUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'phone_number', 'password',
                  'date_of_birth', 'legacy_id', 'place_of_study', 'active_member_card',
                  'is_volunteer', 'is_member', 'last_membership')
        read_only_fields = ('id', 'legacy_id', 'username', 'active_member_card', 'date_of_birth', 'place_of_study',
                            'is_volunteer', 'is_member', 'last_membership')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
            'phone_number': {'required': True},
            'password': {'required': True, 'write_only': True}
        }
