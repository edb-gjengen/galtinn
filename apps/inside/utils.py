# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
from neuf_ldap.utils import ldap_create
from passlib.hash import mysql41

from inside.models import InsideUser, UserUpdate


logger = logging.getLogger(__name__)


def mysql_create(raw_password):
    return mysql41.encrypt(raw_password)


def log_inside_userupdate(username, message):
    try:
        user = InsideUser.objects.get(ldap_username=username)
    except InsideUser.DoesNotExist:
        logger.warning('Could not log update in Inside for user with username {}'.format(username))
        return

    UserUpdate.objects.create(user_updated=user, comment=message, user_updated_by=user)


def set_inside_password(username, raw_password):
    ldap_hashed_password = ldap_create(raw_password)
    hashed_password = mysql_create(raw_password)

    try:
        user = InsideUser.objects.get(ldap_username=username)
    except InsideUser.DoesNotExist:
        logger.warning('Could not set password in Inside for user with username {}'.format(username))
        return

    user.password = hashed_password
    user.ldap_password = ldap_hashed_password
    user.save(update_fields=['password', 'ldap_password'])

    log_inside_userupdate(username, "Satt passord på nytt via brukerinfo.neuf.no.")