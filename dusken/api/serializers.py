from dusken.models import Membership, DuskenUser
from rest_framework import serializers


class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = ('id', 'start_date', 'end_date', 'payment', 'user', 'membership_type')


class DuskenUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = DuskenUser
        fields = (
            'id', 'username', 'password', 'email', 'first_name', 'last_name',
            'phone_number', 'date_of_birth', 'legacy_id', 'place_of_study',
        )
        read_only_fields = ('id', 'username',)
        write_only_fields = ('password',)
