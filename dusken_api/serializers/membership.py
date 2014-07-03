from dusken_api.models import Membership
from rest_framework import serializers

class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = ('start_date', 'end_date', 'payment', 'member', 'membership_type')

