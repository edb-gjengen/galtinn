from rest_framework import serializers

from dusken.models import Membership


class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = ('id', 'start_date', 'end_date', 'order', 'user', 'membership_type')
