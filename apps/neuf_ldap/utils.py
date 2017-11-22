# coding: utf-8
import logging
import os
import pprint

from datetime import datetime
from django.conf import settings
from django.db.utils import ConnectionDoesNotExist
from passlib.hash import ldap_salted_sha1

logger = logging.getLogger(__name__)


def ldap_create_password(raw_password):
    return ldap_salted_sha1.encrypt(raw_password)


def ldap_validate_password(raw_password, challenge_password):
    # challenge_password is hash from db
    # raw_password is the cleartext password.
    return ldap_salted_sha1.validate(raw_password, challenge_password)


def set_ldap_password(username, raw_password):
    # TODO: Allow LDAP to be down
    from .models import LdapUser
    try:
        # Lookup the Ldap user with the identical username (1-to-1).
        user = LdapUser.objects.get(username=username)
        user.set_password(raw_password)
    except LdapUser.DoesNotExist:
        logger.warning('Could not set password in LDAP for user with username {}'.format(username))


def ldap_user_group_exists(username):
    from .models import LdapGroup

    return LdapGroup.objects.filter(name=username).exists()


def ldap_username_exists(username):
    from .models import LdapUser

    return LdapUser.objects.filter(username=username).exists()


def create_ldap_user(user, dry_run=False):
    from .models import LdapUser, LdapGroup

    def _get_next_uid():
        # Get user id order desc by id
        logger.debug('{} Getting next available UID'.format(datetime.utcnow()))
        users = LdapUser.objects.order_by('-id').values_list('id', flat=True)

        if len(users) == 0:
            return settings.LDAP_UID_MIN

        if users[0] >= settings.LDAP_UID_MAX:
            logger.exception("UID larger than LDAP_UID_MAX")

        return users[0] + 1

    def _get_next_user_gid():
        logger.debug('{} Getting next available GID for user group'.format(datetime.utcnow()))
        # Get user group ids order desc by id
        user_groups = LdapGroup.objects.order_by('-gid').values_list('gid', flat=True)

        if len(user_groups) == 0:
            return settings.LDAP_USER_GID_MIN

        if user_groups[0] >= settings.LDAP_USER_GID_MAX:
            logger.exception("UID larger than LDAP_USER_GID_MAX")

        return user_groups[0] + 1

    # User
    full_name = '{} {}'.format(user['first_name'], user['last_name'])
    user_data = {
        'first_name': user['first_name'],
        'last_name': user['last_name'],
        'full_name': full_name,
        'display_name': full_name,
        'gecos': user['username'],
        'email': user['email'],
        'username': user['username'],
        'id': _get_next_uid(),
        'group': _get_next_user_gid(),
        'home_directory': os.path.join(settings.LDAP_HOME_DIRECTORY_PREFIX, user['username'])
    }
    ldap_user = LdapUser(**user_data)

    # User password
    if user.get('password') is not None:
        ldap_user.set_password(user['password'], commit=False)  # Raw
        pwd_type = 'raw'
    elif user.get('ldap_password') is not None:
        ldap_user.set_password(user['ldap_password'], commit=False, prehashed=True)  # Hashed
        pwd_type = 'hashed'
    else:
        # No password
        logger.error("User {} has no ldap_password (hashed) or password (unhashed), bailing!".format(user['username']))
        return False

    if not dry_run:
        ldap_user.save()
    logger.debug('User saved with data: {} and password type \'{}\'.'.format(pprint.pformat(user_data), pwd_type))

    # Add user group
    ldap_user_group = LdapGroup(name=user['username'], gid=user_data['group'], members=[user['username']])
    if not dry_run:
        ldap_user_group.save()
    logger.debug('User group {} created'.format(user['username']))

    # Add groups
    ldap_groups = LdapGroup.objects.filter(name__in=user['groups'])
    for g in ldap_groups:
        if user['username'] not in g.members:
            g.members.append(user['username'])
            if not dry_run:
                g.save()
            logger.debug('User {} added to group {}'.format(user['username'], g.name))

    # Finito!
    return True


def ldap_update_user_details(dusken_user, dry_run=False):
    from .models import LdapUser
    ldap_user = LdapUser.objects.get(username=dusken_user['username'])

    ldap_user.email = dusken_user['email']

    name_changed = dusken_user['first_name'] != ldap_user.first_name or dusken_user['last_name'] != ldap_user.last_name
    if name_changed:
        full_name = '{} {}'.format(dusken_user['first_name'], dusken_user['last_name'])
        name_data = {
            'first_name': dusken_user['first_name'],
            'last_name': dusken_user['last_name'],
            'full_name': full_name,
            'display_name': full_name,
        }
        for key, value in name_data.items():
            setattr(ldap_user, key, value)

    if not dry_run:
        ldap_user.save()
    logger.debug('User details updated for {}'.format(dusken_user['username']))


def ldap_update_user_groups(dusken_user, ldap_user_diffable, dry_run=False, delete_group_memberships=False):
    from .models import LdapUser, LdapGroup
    ldap_user = LdapUser.objects.get(username=dusken_user['username'])

    missing_groups = set(dusken_user['groups']).difference(set(ldap_user_diffable['groups']))
    stale_groups = set(ldap_user_diffable['groups']).difference(set(dusken_user['groups']))

    if not dry_run:
        for g in LdapGroup.objects.filter(name__in=missing_groups):
            g.members.append(ldap_user.username)
            g.save()
        if delete_group_memberships:
            for g in LdapGroup.objects.filter(name__in=stale_groups):
                g.members.remove(ldap_user.username)
                g.save()

    if len(missing_groups) > 0:
        logger.debug('Group memberships added: {}'.format(','.join(missing_groups)))

    if len(stale_groups) > 0 and delete_group_memberships:
        logger.debug('Group memberships removed: {}'.format(','.join(stale_groups)))


def create_ldap_automount(username, dry_run=False):
    from .models import LdapAutomountHome

    if LdapAutomountHome.objects.filter(username=username).exists():
        # Bail if it already exists
        return True

    automount = LdapAutomountHome(username=username)
    automount.set_automount_info()

    if not dry_run:
        automount.save()
    logger.debug('Automount {} added for user {}'.format(automount.automountInformation, username))

    return True


def delete_ldap_automount(username):
    from .models import LdapAutomountHome
    LdapAutomountHome.objects.filter(username=username).delete()


def delete_ldap_user_groups(username):
    from .models import LdapGroup
    groups_with_memberships = LdapGroup.objects.filter(members__contains=username)

    for g in groups_with_memberships:
        g.members.remove(username)
        g.save()


def delete_ldap_user(username):
    from .models import LdapUser, LdapGroup
    try:
        logger.info('Deleting LDAP user {}'.format(username))

        if ldap_user_group_exists(username):
            LdapGroup.objects.filter(name=username).delete()

        delete_ldap_automount(username)
        delete_ldap_user_groups(username)

        if ldap_username_exists(username):
            LdapUser.objects.filter(username=username).delete()
    except ConnectionDoesNotExist:
        logger.warning('Skipping deletion of LDAP user {}, since the LDAP connection does not exist'.format(username))
