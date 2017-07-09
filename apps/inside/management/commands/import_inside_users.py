# coding: utf-8
import random
import re
from datetime import timedelta, datetime
from pprint import pprint

from django.core.management.base import BaseCommand
from django.utils import timezone
from signal_disabler import signal_disabler

from apps.common.utils import log_time
from apps.inside.models import InsideUser, InsideCard
from dusken.models import DuskenUser, Membership, MemberCard, MembershipType, Order, UserLogMessage
from dusken.zip_to_city import ZIP_TO_CITY_MAP


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

        'created': 'date_joined',  # FIXME: Does not work?
    }

    def __init__(self):
        super().__init__()

        # No email notifications
        signal_disabler.disable().disconnect_all()

        self.inside_users = InsideUser.objects.order_by('pk')

        self.zip_to_city_map = ZIP_TO_CITY_MAP

        self.life_long_users = InsideUser.objects.filter(expires=None).values_list('pk', flat=True)

        m1, c = MembershipType.objects.get_or_create(pk=1, defaults={'name': 'Membership'})
        m2, c = MembershipType.objects.get_or_create(pk=2,
                                                     expiry_type=MembershipType.EXPIRY_NEVER,
                                                     defaults={'name': 'Life long'})
        m3, c = MembershipType.objects.get_or_create(pk=3,
                                                     expiry_type=MembershipType.EXPIRY_END_OF_YEAR,
                                                     defaults={'name': 'Trial membership'})
        self.membership_types = {
            'standard': m1,
            'life_long': m2,
            'trial': m3,
        }

    def _get_city_from_postal_code(self, postal_code):
        return self.zip_to_city_map.get(postal_code)

    def _get_start_date(self, user, is_life_long):
        if is_life_long:
            return timezone.now()  # Manually fix this later

        if user.get('expires') is not None:
            return user.get('expires') - timedelta(days=365)

        return None

    def _get_membership_type(self, is_life_long):
        if is_life_long:
            return self.membership_types['life_long']

        return self.membership_types['standard']

    def _get_last_valid_membership(self, user):
        is_life_long = user.get('pk') in self.life_long_users

        if user.get('expires') is None and not is_life_long:
            return None

        _type = 'life_long' if is_life_long else 'standard'
        membership_type = self.membership_types[_type]

        end_date = user.get('expires')
        start_date = self._get_start_date(user, is_life_long)

        return {
            'end_date': end_date,
            'start_date': start_date,
            'membership_type': membership_type
        }

    def _generate_username(self, firstname, lastname):
        firstname = re.sub(r'[^\w]', '', firstname)
        firstname = firstname.lower()[:5]

        lastname = re.sub(r'[^\w]', '', lastname)
        lastname = lastname.lower()[:2]
        rand = random.randint(10000, 100000)

        random_username = '{}{}{}'.format(firstname, lastname, rand).encode('ascii', 'ignore').decode('utf-8')
        return random_username

    @log_time('Fetching user data...')
    def get_user_data(self):
        skip_usernames = ['ukjent']
        more_fields = ['addresstype', 'registration_status', 'source', 'placeofstudy', 'expires', 'created',
                       'ldap_password', 'username']
        fields = list(self.USER_FIELD_MAP.keys()) + more_fields

        i_users = self.inside_users.order_by('pk').reverse().values(*fields)
        d_users = []
        for u in i_users:
            if u['username'] in skip_usernames:
                continue

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
                    new_user['city'] = self.zip_to_city_map.get(u.get('useraddressno__zipcode'), '')

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
                    new_val = self._generate_username(u.get('first_name'), u.get('last_name'))

                if dst_field == 'date_joined':
                    new_val = timezone.now()

                if dst_field == 'phone_number' and (new_val is None or new_val == '-'):
                    new_val = ''

                # Clean
                if dst_field in ['email', 'username']:
                    new_val = new_val.lower()

                if dst_field == 'phone_number_validated':
                    new_val = bool(new_val)

                new_user[dst_field] = new_val

            # Last valid membership
            last_valid_membership = self._get_last_valid_membership(u)

            new_user['memberships'] = []
            if last_valid_membership is not None:
                new_user['memberships'] = [last_valid_membership]

            d_users.append(new_user)

        return d_users

    @log_time('Fetching group data...')
    def get_group_data(self):
        # TODO

        return []

    def _get_card_end_date(self, card):
        if not card['owner_membership_trial']:
            return card['registered'] + timedelta(days=365)

        return datetime(year=card['registered'].year + 1, month=1, day=1)

    @log_time('Fetching member card data...')
    def get_member_card_data(self):
        cards_fields = ['registered', 'is_active', 'user', 'created', 'card_number']
        fields = ['owner_membership_trial', 'owner_phone_number'] + cards_fields
        cards = list(InsideCard.objects.values(*fields))
        ret = {
            'cards': [],
            'memberships': []
        }

        # Cards
        for c in cards:
            _c = {}
            for f in cards_fields:
                if f == 'user':
                    _c['legacy_user_id'] = c[f]
                else:
                    _c[f] = c[f]
            ret['cards'].append(_c)

            # Memberships (only handle those without users)
            if c['owner_phone_number'] and c['user'] is None:
                is_trial = c['owner_membership_trial']
                _type = 'standard' if not is_trial else 'trial'
                m = {
                    'start_date': c['registered'],
                    'end_date': self._get_card_end_date(c),
                    'payment_method': Order.BY_PHYSICAL_CARD,
                    'extra_data': {'phone_number': c['owner_phone_number'], 'card_number': c['card_number']},
                    'membership_type': self.membership_types[_type],
                    'price_nok': 25000 if not is_trial else 0

                }
                ret['memberships'].append(m)

        return ret

    @log_time('Creating database...')
    def create_database(self, users, member_cards_data):
        # Create users first, use legacy_id to reference later
        for u in users:
            memberships = u.pop('memberships')
            new_user = DuskenUser.objects.create(**u)
            message = 'Imported user_id={} from Inside'.format(new_user.legacy_id)
            UserLogMessage.objects.create(user=new_user, message=message)
            for m_data in memberships:
                m_data['user_id'] = new_user.pk
                m = Membership.objects.create(**m_data)
                # TODO: Price
                # TODO: Payment method
                Order.objects.create(product=m, user=new_user, price_nok=0)

        for c in member_cards_data['cards']:
            if c['legacy_user_id'] is not None:
                c['user'] = DuskenUser.objects.get(legacy_id=c.pop('legacy_user_id'))
            MemberCard.objects.create(**c)

        for m in member_cards_data['memberships']:
            order_data = {
                'extra_data': m.pop('extra_data'),
                'payment_method': m.pop('payment_method'),
                'price_nok': m.pop('price_nok')
            }
            m = Membership.objects.create(**m)
            Order.objects.create(product=m, **order_data)

    def handle(self, *args, **options):
        # TODO: Get list of org units
        # TODO: Get list of groups
        # Note: Keep concept of admin_group

        group_data = self.get_group_data()
        users = self.get_user_data()

        member_cards_data = self.get_member_card_data()
        # pprint(member_cards_data['cards'][0])

        self.create_database(users, member_cards_data)
