from dusken_api.models import Member
from rest_framework import serializers

class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ('username', 'phone_number', 'date_of_birth', 'legacy_id', 'address', 'place_of_study')
