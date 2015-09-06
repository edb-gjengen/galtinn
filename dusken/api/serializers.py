import random
from dusken.models import Membership, DuskenUser
from rest_framework import serializers


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
    @staticmethod
    def _generate_username(first_name, last_name):
        random_number = random.randint(1, 9999)
        first_name = first_name.encode('ascii', 'ignore').lower()[:6].decode('utf-8')
        last_name = last_name.encode('ascii', 'ignore').lower()[:2].decode('utf-8')
        username = '{}{}{:04d}'.format(first_name, last_name, random_number)
        return username

    def validate(self, data):
        if not data.get('username', ''):
            data['username'] = SimpleDuskenUserSerializer._generate_username(data['first_name'], data['last_name'])

        return data

    class Meta:
        model = DuskenUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'phone_number',)
        read_only_fields = ('id', 'username',)
        write_only_fields = ('password',)
