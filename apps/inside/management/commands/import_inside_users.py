# coding: utf-8
from datetime import timedelta
from django.core.management.base import BaseCommand

from apps.inside.models import InsideUser, PostalCode, InsideCard
from django.db.models import Q
from dusken.models import DuskenUser, Membership, MemberCard, MembershipType


class Command(BaseCommand):
    """ Imports users from Inside (in a one off ninja-style way)
        (1)
        * Grupper
        * Foreninger
        (2)
        * Brukere
        * Medlemskap (siste gyldige)
        * Gruppemedlemskap
        * Kort
        * Studiested
        * Brukerlogg
    """
    USER_FIELD_MAP = {
        'pk': 'legacy_id',
        'first_name': 'first_name',
        'last_name': 'last_name',
        'ldap_username': 'username',
        'email': 'email',
        'birthdate': 'date_of_birth',

        'userphonenumber__number': 'phone_number',
        'userphonenumber__validated': 'phone_number_validated',

        'useraddressno__street': 'street_address',
        'useraddressno__zipcode': 'postal_code',

        'useraddressint__street': 'street_address',
        'useraddressint__zipcode': 'postal_code',
        'useraddressint__country': 'country',
        'useraddressint__city': 'city',

        'created': 'date_joined',
    }

    def __init__(self):
        super().__init__()
        self.inside_users = InsideUser.objects.all()

        self.zip_to_city_map = dict(PostalCode.objects.values_list('postnummer', 'poststed'))

        self.life_long_users = InsideUser.objects.filter(expires=None).values_list('pk', flat=True)

        self.member_cards = InsideCard.objects.values()
        self.member_cards_with_user = list(filter(lambda c: c['user_id'] is not None, self.member_cards))

        m1, c = MembershipType.objects.get_or_create(pk=1)
        m2, c = MembershipType.objects.get_or_create(pk=2)
        m3, c = MembershipType.objects.get_or_create(pk=3)
        self.membership_types = {
            'standard': m1,
            'active': m2,  # FIXME: need this?
            'life_long': m3,
        }

    def _get_city_from_postal_code(self, postal_code):
        return self.zip_to_city_map.get(postal_code)

    def _get_start_date(self, user):
        if user.get('expires') is not None:
            return user.get('expires') - timedelta(days=365)

        return None

    def _get_membership_type(self, user):
        # FIXME: less hardcoding
        if user.get('pk') in self.life_long_users:
            return self.membership_types['life_long']

        return self.membership_types['standard']

    def _get_last_valid_membership(self, user):
        if user.get('expires') is None:
            return None
        membership_type = self._get_membership_type(user)
        # payment = Payment.objects.create()
        end_date = user.get('expires')
        start_date = self._get_start_date(user)

        return {
            'end_date': end_date,
            'start_date': start_date,
            'membership_type': membership_type
        }

    def _get_cards(self, user):
        cards = []
        for c in self.member_cards_with_user:
            if c['user_id'] == user.get('legacy_id'):
                cards.append(c)

        return cards

    def get_user_data(self):
        more_fields = ['addresstype', 'registration_status', 'source', 'placeofstudy', 'expires', 'created',
                       'ldap_password', 'username']
        fields = list(self.USER_FIELD_MAP.keys()) + more_fields

        i_users = self.inside_users.order_by('pk').reverse().values(*fields)
        d_users = []
        for u in i_users:
            new_user = {}
            for src_field, dst_field in self.USER_FIELD_MAP.items():
                # Address
                if u.get('addresstype') == 'no' and dst_field == 'country':
                    new_user[dst_field] = 'NO'
                    continue

                if u.get('addresstype') == 'no' and src_field.startswith('useraddressint'):
                    continue
                if u.get('addresstype') == 'int' and src_field.startswith('useraddressno'):
                    continue

                if u.get('addresstype') == 'no' and dst_field == 'postal_code':
                    new_user['city'] = self._get_city_from_postal_code(u.get('useraddressno__zipcode'))

                # Partially registered users (autogenerated username and no password set)
                if u.get('registration_status') == 'partial':
                    if dst_field == 'username':
                        new_user[dst_field] = u.get('username')

                        # hijack username key for active status
                        new_user['is_active'] = False
                        continue

                # Values
                new_val = u.get(src_field)

                if dst_field == 'username' and new_val is None:
                    # TODO generate username
                    pass

                # Clean
                if dst_field in ['email', 'username']:
                    new_val = new_val.lower()

                new_user[dst_field] = new_val

            # Last valid membership
            last_valid_membership = self._get_last_valid_membership(u)
            if last_valid_membership is not None:
                new_user['memberships'] = [last_valid_membership]
            else:
                new_user['memberships'] = []

            new_user['membercards'] = self._get_cards(u)

            d_users.append(new_user)

        return d_users

    def get_group_data(self):
        # TODO
        return None

    def handle(self, *args, **options):
        # TODO
        # Get list of org units
        # Get list of groups
        # Keep concept of admin_group
        group_data = self.get_group_data()

        # TODO
        # Get list of users
        # Join with phone number and address
        # Get current membership
        # Get historical memberships ( Ninja-SQL time!)
        users = self.get_user_data()

        import pprint
        pprint.pprint(list(filter(lambda x: x['username'] is None, users)))

        # for u in users:
        #     memberships = u.pop('memberships')
        #     membercards = u.pop('membercards')
        #     new_user = DuskenUser.objects.create(**u)
        #     for m in memberships:
        #         m['user_id'] = new_user.pk
        #         Membership.objects.create(**m)
        #
        #     for m in membercards:
        #         m['user_id'] = new_user.pk
        #         MemberCard.objects.create(**m)
        #
