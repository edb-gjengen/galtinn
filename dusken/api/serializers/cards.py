from rest_framework import serializers

from dusken.models import MemberCard


class MemberCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberCard
        # fields = ('')
