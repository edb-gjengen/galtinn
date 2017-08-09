# coding: utf-8
import html
import random
import re
from collections import defaultdict
from datetime import timedelta, date, datetime
from pprint import pprint

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from signal_disabler import signal_disabler

from apps.common.utils import log_time
from apps.inside.models import InsideUser, InsideCard, InsideGroup, Division, InsidePlaceOfStudy, UserUpdate
from apps.kassa.models import KassaEvent
from apps.neuf_auth.models import AuthProfile
from apps.tekstmelding.models import TekstmeldingEvent
from dusken.hashers import Argon2WrappedMySQL41PasswordHasher
from dusken.models import (DuskenUser, Membership, MemberCard, MembershipType, Order, UserLogMessage, GroupProfile,
                           OrgUnit, OrgUnitLogMessage, PlaceOfStudy)
from dusken.zip_to_city import ZIP_TO_CITY_MAP


class Command(BaseCommand):
    """ Imports users from Inside (in a one off ninja-style way)
        - Group
        - OrgUnit
        - User
        - Membership
        - Group membership
        - Physical cards / Membership cards
        - Place of study
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Dry run importing, does not save anything.')

    def __init__(self):
        super().__init__()
        # No email notifications or any post_save or pre_save signals
        signal_disabler.disable().disconnect_all()

        self.zip_to_city_map = ZIP_TO_CITY_MAP
        self.life_long_users = InsideUser.objects.filter(expires=None).values_list('pk', flat=True)

        m1, c = MembershipType.objects.get_or_create(pk=1,
                                                     slug='standard',
                                                     is_default=True,
                                                     defaults={'name': 'Membership'})
        m2, c = MembershipType.objects.get_or_create(pk=2,
                                                     slug='lifelong',
                                                     expiry_type=MembershipType.EXPIRY_NEVER,
                                                     defaults={'name': 'Life long'})
        m3, c = MembershipType.objects.get_or_create(pk=3,
                                                     slug='trial',
                                                     expiry_type=MembershipType.EXPIRY_END_OF_YEAR,
                                                     defaults={'name': 'Trial membership'})
        m4, c = MembershipType.objects.get_or_create(pk=4,
                                                     duration=timedelta(days=365*5),
                                                     slug='five_year',
                                                     defaults={'name': 'Five year membership'})
        self.membership_types = {
            'standard': m1,
            'life_long': m2,
            'trial': m3,
            'five_year': m4,
        }

        # Create places of study and legacy mapping
        self.pos_map = {}
        for ipos in InsidePlaceOfStudy.objects.all():
            pos, _ = PlaceOfStudy.objects.get_or_create(name=ipos.navn)
            self.pos_map[ipos.pk] = pos.pk

        # User id to groups
        self.group_rel_map = defaultdict(list)
        rels = InsideGroup.objects.all().values_list('user_rels__user__pk', 'pk')
        for user, group in rels:
            if user is not None:
                self.group_rel_map[user].append(group)

        self.log_map = {}
        uus = UserUpdate.objects.order_by('date').values_list('user_updated__pk', 'date')
        for user, ts in uus:
            if user not in self.log_map:
                self.log_map[user] = ts

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

    def _hash_password(self, sha1sha1_hash):
        hasher = Argon2WrappedMySQL41PasswordHasher()
        salt = hasher.salt()
        password = hasher.encode_sha1_sha1_hash(sha1sha1_hash, salt)
        return password

    def _get_unusable_password(self):
        return make_password(None)  # Same as User.set_unusable_password()

    @log_time('Fetching user log data...')
    def get_user_update_log(self):
        field_mapping = {
            'date': 'created',
            'comment': 'message',
            'user_updated_by': 'legacy_changed_by',
            'user_updated': 'legacy_user',
        }
        updates = UserUpdate.objects.all().values(*field_mapping.keys())
        user_log = []
        for update in updates:
            message = {}
            for src, dst in field_mapping.items():
                message[dst] = update[src]
            user_log.append(message)

        return user_log

    def _format_int_country(self, country):
        country = country.strip()
        if len(country) == 2 or len(country) == 0:
            return country

        country = country.lower()
        maps = {
            'norway': 'NO', 'norge': 'NO',
            'usa': 'US', 'united states': 'US',
            'sverige': 'SE', 'sweden': 'SE',
            'danmark': 'DK', 'denmark': 'DK',
            'france': 'FR', 'frankrike': 'FR',
            'canada': 'CA',
            'tyskland': 'DE',
            'england': 'GB', 'storbritannia': 'GB',
            'spain': 'ES',
            'españa': 'ES',
            'finland': 'FI',
            'italy': 'IT', 'italia': 'IT',
            'belgia': 'BE', 'belgium': 'BE', 'belgique': 'BE',
            'australia': 'AU',
            'the netherlands': 'NL', 'holland': 'NL',
            'island': 'IS', 'ísland': 'IS',
            'irland': 'IE',
            'india': 'IN',
            'czech republic': 'CZ',
            'sveits': 'CH',
            'brazil': 'BR',
            'argentina': 'AR',
            'estland': 'EE',
            'korea, republikken': 'KR'
        }

        if country in maps:
            return maps[country]

        return ''  # bail

    def _is_spam_user(self, u):
        if u.get('expires') is not None:
            return False

        if u.get('password') == '*6646454122E5FB2D3FC7F699120332D623083A57':
            return True
        if u.get('email').endswith('@163.com'):
            return True
        if u.get('last_name') in ['OLIVIER', 'Holland', 'ken', 'vigorda']:
            return True

        return False

    def get_snapporder_membership(self, user):
        log_strings_query = (Q(comment='Medlemskap fornyet via snapporder.')
                             | Q(comment='Medlemskap registrert via snapporder.'))
        iu = InsideUser.objects.get(pk=user.legacy_id)
        purchase_date = iu.expires - timedelta(days=365)
        purchase_datetime = datetime(
            year=purchase_date.year, month=purchase_date.month, day=purchase_date.day, tzinfo=timezone.utc)
        has_snapporder_membership = UserUpdate.objects.filter(
            user_updated=iu,
            date__gte=purchase_datetime).filter(log_strings_query).exists()

        if not has_snapporder_membership:
            return None

        return {
            'start_date': iu.expires - timedelta(days=365),
            'end_date': iu.expires,
            'payment_method': Order.BY_APP,
            'membership_type': self.membership_types['standard'],
            'phone_number': user.phone_number,
            'price_nok': 25000,
            'user': user
        }

    def _create_unknown_membership(self, membership, user):
        # No memberships registered, create the last one for reference (assume 1 year membership)
        order_data = {
            'payment_method': Order.PAYMENT_METHOD_OTHER,
            'price_nok': 0,
            'user': user
        }
        m_obj = Membership.objects.create(user=user, **membership)
        Order.objects.create(product=m_obj, **order_data)

    @log_time('Fetching user data...')
    def get_user_data(self):
        user_field_map = {
            'pk': 'legacy_id',
            'first_name': 'first_name',
            'last_name': 'last_name',
            'ldap_username': 'username',
            'email': 'email',
            'birthdate': 'date_of_birth',
            'placeofstudy': 'place_of_study_id',
            'password': 'password',
            'ldap_password': 'ldap_password',

            'userphonenumber__number': 'phone_number',
            'userphonenumber__validated': 'phone_number_confirmed',

            'useraddressno__street': 'street_address',
            'useraddressno__zipcode': 'postal_code',

            'useraddressint__street': 'street_address',
            'useraddressint__zipcode': 'postal_code',
            'useraddressint__country': 'country',
            'useraddressint__city': 'city',

            'created': 'date_joined',
        }
        skip_usernames = ['ukjent']
        more_fields = ['addresstype', 'registration_status', 'source', 'expires', 'username']
        fields = list(user_field_map.keys()) + more_fields

        i_users = InsideUser.objects.order_by('pk').values(*fields)
        d_users = []
        for u in i_users:
            # Skip unwanted users
            if u['username'] in skip_usernames:
                continue
            if self._is_spam_user(u):
                continue

            new_user = {}
            for src_field, dst_field in user_field_map.items():
                # Address
                if u.get('addresstype') == 'no' and dst_field == 'country':
                    new_user[dst_field] = 'NO'
                    continue
                if u.get('addresstype') == 'int' and dst_field == 'country':
                    new_user[dst_field] = self._format_int_country(u.get(src_field))
                    continue

                if u.get('addresstype') == 'no' and src_field.startswith('useraddressint'):
                    continue
                if u.get('addresstype') == 'int' and src_field.startswith('useraddressno'):
                    continue

                if u.get('addresstype') == 'no' and dst_field == 'postal_code':
                    new_user['city'] = self.zip_to_city_map.get(u.get('useraddressno__zipcode'), '')

                # Values
                new_val = u.get(src_field)

                if dst_field == 'username' and new_val is None:
                    new_val = self._generate_username(u.get('first_name'), u.get('last_name'))

                if dst_field == 'date_joined':
                    if new_val is None:
                        # First log entry ts
                        if u['pk'] in self.log_map:
                            new_val = self.log_map[u['pk']]
                        else:
                            new_val = timezone.now()

                if dst_field == 'place_of_study_id':
                    new_val = self.pos_map.get(new_val)
                    if not new_val:
                        continue

                if dst_field == 'phone_number' and (new_val is None or new_val == '-'):
                    new_val = ''

                if dst_field == 'password':
                    # Note: All mysql PASSWORD() hashes are 41 chars
                    if len(new_val) == 41:
                        new_val = self._hash_password(new_val)
                    else:
                        # Throw away all old hashes and unset ldap_password
                        new_val = self._get_unusable_password()
                        new_user['ldap_password'] = ''

                # Clean
                if dst_field in ['email', 'username']:
                    new_val = new_val.lower().strip()

                if dst_field in ['first_name', 'last_name']:
                    new_val = new_val.strip()

                if dst_field == 'phone_number_confirmed':
                    new_val = bool(new_val)

                if dst_field == 'street_address':
                    if new_val is None or new_val == '-':
                        new_val = ''

                    new_val = new_val.replace('\r\n', '\n').strip()
                    new_val = new_val.replace('\n', ' ')

                new_user[dst_field] = new_val

            # Last valid membership (lifelong are added right away, the others are cross referencing kassa stuff later)
            last_valid_membership = self._get_last_valid_membership(u)

            new_user['memberships'] = []
            if last_valid_membership is not None:
                new_user['memberships'] = [last_valid_membership]

            # Groups
            new_user['legacy_group_ids'] = self.group_rel_map[u['pk']]

            d_users.append(new_user)

        return d_users

    @log_time('Fetching org unit data...')
    def get_org_units_data(self):
        field_map = {
            'email': 'email',
            'phone': 'phone_number',
            'name': 'name',
            'nicename': 'slug',
            'text': 'description',
            'url': 'website',
            'id': 'legacy_id',
            'user_id_contact': 'legacy_contact_id'
        }
        divisions = list(Division.objects.values(*field_map.keys()))

        org_units = []
        for d in divisions:
            org_unit = {}
            for src_key, dst_key in field_map.items():
                if dst_key == 'phone_number' and len(d[src_key]) == 8:
                    org_unit[dst_key] = '+47{}'.format(d[src_key])
                elif dst_key == 'description':
                    new_val = html.unescape(d[src_key]).replace(u'\xa0', u' ').replace('\\"', '"').replace('\\\'', '\'')
                    new_val = new_val.strip()
                    new_val = re.sub("(<!--.*?-->)", "", new_val)
                    org_unit[dst_key] = new_val
                else:
                    org_unit[dst_key] = d[src_key]

            org_units.append(org_unit)

        return org_units

    @log_time('Fetching group data...')
    def get_group_data(self):
        field_map = {
            'name': 'name',
            'posix_group': 'posix_name',
            'text': 'description',
            'division_id': 'legacy_division_id',
            'admin': 'is_admin_group',
            'id': 'legacy_id'

        }
        groups = list(InsideGroup.objects.values(*field_map.keys()))

        group_data = []
        for g in groups:
            group = {}
            for src_key, dst_key in field_map.items():
                if dst_key == 'description':
                    group[dst_key] = g[src_key].replace('...', '')
                elif dst_key == 'is_admin_group':
                    group[dst_key] = g[src_key] == '1'
                else:
                    group[dst_key] = g[src_key]

            group_data.append(group)

        return group_data

    def _get_card_end_date(self, card):
        if not card['owner_membership_trial']:
            return card['registered'].date() + timedelta(days=365)

        return date(year=card['registered'].year + 1, month=1, day=1)

    @log_time('Fetching member card data...')
    def get_member_card_data(self):
        fields = ['registered', 'is_active', 'user', 'created', 'card_number']
        cards = list(InsideCard.objects.values(*fields))
        all_card_data = []

        # Cards
        for c in cards:
            card_data = {}
            for field in fields:
                if field == 'user':
                    card_data['legacy_user'] = c[field]
                else:
                    card_data[field] = c[field]
            all_card_data.append(card_data)

        return all_card_data

    @log_time('Fetching SMS membership data...')
    def get_sms_memberships(self):
        memberships = []

        query = Q(action=TekstmeldingEvent.NEW_MEMBERSHIP_DELIVERED) \
            | Q(action=TekstmeldingEvent.RENEW_MEMBERSHIP_DELIVERED)

        # New and renewal memberships
        fields = ['pk', 'action', 'timestamp', 'incoming', 'incoming__msisdn']
        charged_memberships = TekstmeldingEvent.objects.filter(query).values(*fields)
        for m in charged_memberships:
            action = TekstmeldingEvent.NEW_MEMBERSHIP
            if m['action'] == TekstmeldingEvent.RENEW_MEMBERSHIP_DELIVERED:
                action = TekstmeldingEvent.RENEW_MEMBERSHIP
            try:
                charge_message = TekstmeldingEvent.objects.get(action=action, incoming=m['incoming'])
            except TekstmeldingEvent.DoesNotExist:
                continue  # Note: This happens with only two memberships, which have been refunded

            msisdn = str(m['incoming__msisdn'])[:-2]  # work around floatfield
            m_data = {
                'start_date': m['timestamp'].date(),
                'end_date': m['timestamp'].date() + timedelta(days=365),
                'payment_method': Order.BY_SMS,
                'phone_number': '+{}'.format(msisdn),
                'membership_type': self.membership_types['standard'],
                'price_nok': charge_message.outgoing.pricegroup,
            }
            if charge_message.action == TekstmeldingEvent.RENEW_MEMBERSHIP:
                m_data['legacy_user'] = charge_message.user.pk
            else:
                # Look for new membercard events with an outgoing message to the same number
                # and within the not expired range
                member_card = TekstmeldingEvent.objects.filter(
                    action=TekstmeldingEvent.NEW_MEMBERSHIP_CARD,
                    outgoing__destination=msisdn,
                    timestamp__lte=m['timestamp'] + timedelta(days=365)).first()
                if member_card:
                    m_data['card_number'] = member_card.activation_code

            memberships.append(m_data)

        return memberships

    @log_time('Fetching Kassa membership data...')
    def get_kassa_memberships(self, users):
        memberships = []

        # Prepare user lookup
        users_by_legacy_id = {}
        for u in users:
            users_by_legacy_id[u['legacy_id']] = u

        fields = ['user_inside_id', 'event', 'card_number', 'user_phone_number', 'created']
        query = (Q(event=KassaEvent.ADD_OR_RENEW) | Q(event=KassaEvent.NEW_CARD_MEMBERSHIP)
                 | Q(event=KassaEvent.RENEW_ONLY) | Q(event=KassaEvent.MEMBERSHIP_TRIAL))
        purchase_events = KassaEvent.objects.filter(query).values(*fields)

        for m in purchase_events:
            end_date = m['created'].date() + timedelta(days=365)
            if m['event'] == KassaEvent.MEMBERSHIP_TRIAL:
                end_date = date(year=m['created'].year + 1, month=1, day=1)

            mtype = 'standard' if m['event'] != KassaEvent.MEMBERSHIP_TRIAL else 'trial'
            m_data = {
                'start_date': m['created'].date(),
                'end_date': end_date,
                'payment_method': Order.BY_CASH_REGISTER,
                'membership_type': self.membership_types[mtype],
                'phone_number': m['user_phone_number'],
                'price_nok': 25000,
                'legacy_user': m['user_inside_id']
            }

            # Is it tied to a user and does the end date differ from latest set din_user.expires?
            if m_data.get('legacy_user'):
                user = users_by_legacy_id[m_data['legacy_user']]
                user_end_date = user['memberships'][0]['end_date']
                if user_end_date is not None and m_data['end_date'] != user_end_date:
                    diff_days = (user_end_date - m_data['end_date']).days
                    if 363 > diff_days > 1:
                        # Replace our dates
                        m_data['end_date'] = user_end_date
                        m_data['start_date'] = user_end_date - timedelta(days=365)

            memberships.append(m_data)

        return memberships

    @log_time('Creating database...\n')
    def create_database(self, users, member_cards_data, org_unit_data, group_data, user_log_messages, sms_memberships,
                        kassa_memberships):
        # Maps of old ID's to new
        group_map = {}
        ou_map = {}
        ou_contact_map = {}  # From legacy user contact id to org unit id

        unhandled_memberships = []

        # Create org units
        print("\tCreating org units...")
        for ou in org_unit_data:
            ou_legacy_id = ou.pop('legacy_id')
            ou_contact_id = ou.pop('legacy_contact_id')
            o = OrgUnit.objects.create(**ou)

            message = 'Imported from Inside (division_id={})'.format(ou_legacy_id)
            OrgUnitLogMessage.objects.create(org_unit=o, message=message)
            ou_map[ou_legacy_id] = o.pk
            if ou_contact_id:
                ou_contact_map[ou_contact_id] = o.pk

        # Create groups
        print("\tCreating groups...")
        for g in group_data:
            gp_data = {
                'description': g.pop('description'),
                'posix_name': g.pop('posix_name')
            }
            legacy_division_id = g.pop('legacy_division_id')
            legacy_id = g.pop('legacy_id')
            is_admin_group = g.pop('is_admin_group')

            g = Group.objects.create(**g)
            group_map[legacy_id] = g.pk
            GroupProfile.objects.create(group=g, **gp_data)

            # Add ou admin group or member group
            if legacy_division_id:
                _ou = OrgUnit.objects.get(pk=ou_map[legacy_division_id])
                # Note: This overwrites when there are multiple groups tied to same division
                if is_admin_group:
                    _ou.admin_group = g
                else:
                    _ou.group = g
                _ou.save()

        # Create users, use legacy_id to reference later
        print("\tCreating users...")
        _legacy_users_map = {}
        for u in users:
            memberships = u.pop('memberships')
            ldap_password = u.pop('ldap_password')

            group_ids = [group_map[g] for g in u.pop('legacy_group_ids')]
            groups = Group.objects.filter(pk__in=group_ids)
            new_user = DuskenUser.objects.create(**u)
            _legacy_users_map[new_user.legacy_id] = new_user.pk
            new_user.groups.add(*groups)

            # Add org unit contact
            if new_user.legacy_id in ou_contact_map:
                ou = OrgUnit.objects.get(pk=ou_contact_map[new_user.legacy_id])
                ou.contact_person = new_user
                ou.save()

            # Add LDAP password
            if ldap_password:
                AuthProfile.objects.create(user=new_user, ldap_password=ldap_password)

            message = 'Imported from Inside (user_id={})'.format(new_user.legacy_id)
            UserLogMessage.objects.create(user=new_user, message=message)
            for m_data in memberships:
                # Only add life long memberships here
                if m_data['membership_type'].expiry_type == MembershipType.EXPIRY_NEVER:
                    m_data['user_id'] = new_user.pk
                    Membership.objects.create(**m_data)
                else:
                    unhandled_memberships.append([new_user, m_data])

        # Create user log messages
        print("\tCreating user log messages...")
        for m in user_log_messages:
            legacy_user = m.pop('legacy_user')
            legacy_changed_by = m.pop('legacy_changed_by')
            if legacy_user not in _legacy_users_map:
                continue  # Spam users

            m['user_id'] = _legacy_users_map[legacy_user]
            if legacy_changed_by is not None:
                m['changed_by_id'] = _legacy_users_map[legacy_changed_by]
            UserLogMessage.objects.create(**m)

        # Create membercards and relate to users
        print("\tCreating member cards...")
        for c in member_cards_data:
            legacy_user = c.pop('legacy_user')
            if legacy_user is not None:
                c['user_id'] = _legacy_users_map[legacy_user]
            MemberCard.objects.create(**c)

        # Create memberships and orders from kassa data
        print("\tCreating kassa memberships...")
        for m in kassa_memberships:
            order_data = {
                'phone_number': m.pop('phone_number'),
                'payment_method': m.pop('payment_method'),
                'price_nok': m.pop('price_nok')
            }

            legacy_user = m.pop('legacy_user')
            if legacy_user:
                _user_id = _legacy_users_map[legacy_user]
                order_data['user_id'] = _user_id
                m['user_id'] = _user_id

            m = Membership.objects.create(**m)
            Order.objects.create(product=m, **order_data)

        # Create SMS memberships
        print("\tCreating SMS memberships...")
        for m in sms_memberships:
            order_data = {
                'phone_number': m.pop('phone_number'),
                'payment_method': m.pop('payment_method'),
                'price_nok': m.pop('price_nok'),
            }

            if 'legacy_user' in m:
                m['user'] = DuskenUser.objects.get(pk=_legacy_users_map[m.pop('legacy_user')])
            elif 'card_number' in m:
                order_data['member_card'] = MemberCard.objects.get(card_number=m.pop('card_number'))

            membership = Membership.objects.create(**m)
            Order.objects.create(product=membership, **order_data)

        # Creating two 5-year memberships
        print("\tCreating two 5-year memberships...")
        for u in DuskenUser.objects.filter(pk__in=[_legacy_users_map.get(10709), _legacy_users_map.get(16430)]):
            end_date = date(year=2018, month=8, day=1)
            m = {
                'start_date': end_date - timedelta(days=365*5),
                'end_date': end_date,
                'membership_type': self.membership_types['standard'],
                'user': u
            }
            m_obj = Membership.objects.create(**m)

            order_data = {
                'payment_method': Order.PAYMENT_METHOD_OTHER,
                'price_nok': 25000,
                'user': u,
                'product': m_obj,
            }

            Order.objects.create(**order_data)

        # Claim memberships (after order creation)
        print("\tClaiming SMS and card memberships...")
        for user in DuskenUser.objects.no_valid_membership():
            user.claim_orders(ignore_confirmed_state=True)

        # Create unhandled memberships if none exists or
        print("\tCreating unhandled memberships")
        for user, membership in unhandled_memberships:
            user.refresh_from_db()
            now = timezone.now().date()
            inside_membership_valid = membership['end_date'] >= now
            if inside_membership_valid and not user.is_member:
                m = self.get_snapporder_membership(user)

                if m:
                    order_data = {
                        'phone_number': m.pop('phone_number'),
                        'payment_method': m.pop('payment_method'),
                        'price_nok': m.pop('price_nok'),
                        'user': m['user']
                    }
                    m_obj = Membership.objects.create(**m)
                    Order.objects.create(product=m_obj, **order_data)
                else:
                    # Should have a valid membership, but no
                    print("Missing valid membership", user.legacy_id)
                    self._create_unknown_membership(membership, user)

            elif not user.memberships.exists():
                self._create_unknown_membership(membership, user)

        # Delete users with no memberships
        print("\tDelete users with no memberships")
        users_with_no_memberships = DuskenUser.objects.filter(memberships__isnull=True).exclude(is_superuser=True)
        for u in users_with_no_memberships:
            print('Deleting user {} with legacy_id={}'.format(u.get_full_name(), u.legacy_id))
        users_with_no_memberships.delete()

    def handle(self, *args, **options):
        # Get data
        org_units_data = self.get_org_units_data()
        group_data = self.get_group_data()
        users = self.get_user_data()
        user_log_messages = self.get_user_update_log()
        member_cards_data = self.get_member_card_data()

        # Get membership data
        kassa_memberships = self.get_kassa_memberships(users)
        sms_memberships = self.get_sms_memberships()

        if not options['dry_run']:
            # Create database
            with transaction.atomic():
                self.create_database(
                    users, member_cards_data, org_units_data, group_data, user_log_messages, sms_memberships,
                    kassa_memberships)
