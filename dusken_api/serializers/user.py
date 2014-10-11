from dusken_api.models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'username', 'password', 'email', 'first_name', 'last_name',           # django.contrib.auth.User
            'phone_number', 'date_of_birth', 'legacy_id', 'address', 'place_of_study',  # dusken_api.Member
        )
        read_only_fields = ('id', 'username',)
        write_only_fields = ('password',)
