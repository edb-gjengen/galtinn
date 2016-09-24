from rest_framework import serializers

from dusken.models import Membership, DuskenUser
from dusken.utils import generate_username


class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = ('id', 'start_date', 'end_date', 'payment', 'user', 'membership_type')


class DuskenUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = DuskenUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'phone_number', 'date_of_birth', 'legacy_id',
                  'place_of_study',)
        read_only_fields = ('id', 'username',)
        write_only_fields = ('password',)


class SimpleDuskenUserSerializer(serializers.ModelSerializer):
    def validate(self, data):
        if not data.get('username', ''):
            data['username'] = generate_username(data['first_name'], data['last_name'])

        return data

    class Meta:
        model = DuskenUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'phone_number',)
        read_only_fields = ('id', 'username',)
        write_only_fields = ('password',)
