from rest_framework import serializers

from dusken.models import DuskenUser
from dusken.api.serializers.cards import MemberCardSerializer
from dusken.api.serializers.memberships import MembershipSerializer


class DuskenUserSerializer(serializers.ModelSerializer):
    cards = MemberCardSerializer(source='member_cards', many=True)
    last_membership = MembershipSerializer()

    class Meta:
        model = DuskenUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'phone_number',
                  'date_of_birth', 'legacy_id', 'place_of_study', 'cards',
                  'has_valid_membership', 'last_membership')
        read_only_fields = ('id', 'legacy_id', 'username', 'cards',
                            'has_valid_membership', 'last_membership')
        write_only_fields = ('password',)
