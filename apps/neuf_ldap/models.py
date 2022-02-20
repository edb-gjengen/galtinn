from datetime import datetime

import ldapdb.models
from django.conf import settings
from ldapdb.models.fields import CharField, ImageField, IntegerField, ListField

from .utils import ldap_create_password, ldap_validate_password


class LdapUser(ldapdb.models.Model):
    """
    Represents an LDAP posixAccount, inetOrgPerson, shadowAccount entry.
    Ref: http://www.zytrax.com/books/ldap/apa/types.html
    """

    connection_name = "ldap"

    # LDAP meta-data
    base_dn = settings.LDAP_USER_DN
    object_classes = ["inetOrgPerson", "posixAccount", "shadowAccount"]

    # inetOrgPerson
    first_name = CharField(db_column="givenName")
    last_name = CharField(db_column="sn")
    full_name = CharField(db_column="cn")
    email = CharField(db_column="mail")
    phone = CharField(db_column="telephoneNumber", blank=True)
    mobile_phone = CharField(db_column="mobile", blank=True)
    photo = ImageField(db_column="jpegPhoto")

    # posixAccount
    id = IntegerField(db_column="uidNumber", unique=True)  # referenced in reset password form
    group = IntegerField(db_column="gidNumber")
    gecos = CharField(db_column="gecos")
    display_name = CharField(db_column="displayname")
    home_directory = CharField(db_column="homeDirectory")
    login_shell = CharField(db_column="loginShell", default=settings.LDAP_LOGIN_SHELL)
    username = CharField(db_column="uid", primary_key=True)

    # shadowAccount
    password = CharField(db_column="userPassword")
    shadowLastChange = IntegerField(db_column="shadowLastChange", default=settings.LDAP_SHADOW_LAST_CHANGE)
    shadowMin = IntegerField(db_column="shadowMin", default=settings.LDAP_SHADOW_MIN)
    shadowMax = IntegerField(db_column="shadowMax", default=settings.LDAP_SHADOW_MAX)
    shadowWarning = IntegerField(db_column="shadowWarning", default=settings.LDAP_SHADOW_WARNING)
    shadowInactive = IntegerField(db_column="shadowInactive")
    shadowExpire = IntegerField(db_column="shadowExpire", default=settings.LDAP_SHADOW_EXPIRE)
    shadowFlag = IntegerField(db_column="shadowFlag", default=settings.LDAP_SHADOW_FLAG)

    # core
    description = CharField(db_column="description")

    @staticmethod
    def _days_since_epoch():
        return (datetime.utcnow() - datetime(1970, 1, 1)).days

    def set_password(self, raw_password, commit=True, prehashed=False):
        self.password = raw_password if prehashed else ldap_create_password(raw_password)
        # Update last changed password date
        self.shadowLastChange = LdapUser._days_since_epoch()

        if commit:
            self.save()

    def check_password(self, raw_password):
        return ldap_validate_password(raw_password, self.password)

    def __str__(self):
        return self.username

    class Meta:
        managed = False


class LdapGroup(ldapdb.models.Model):
    """Represents an LDAP posixGroup entry."""

    connection_name = "ldap"

    # LDAP meta-data
    base_dn = settings.LDAP_GROUP_DN
    object_classes = ["posixGroup"]

    # posixGroup attributes
    gid = IntegerField(db_column="gidNumber", unique=True)
    name = CharField(db_column="cn", max_length=200, primary_key=True)
    members = ListField(db_column="memberUid")

    def __str__(self):
        return self.name

    class Meta:
        managed = False


class LdapAutomountMap(ldapdb.models.Model):
    """
    Represents an LDAP automountMap
    Ref: http://www.openldap.org/faq/data/cache/599.html
    """

    connection_name = "ldap"

    # LDAP meta-data
    base_dn = settings.LDAP_AUTOMOUNT_DN
    object_classes = ["automountMap"]

    ou = CharField(db_column="ou", primary_key=True)  # F.ex auto.home

    def __str__(self):
        return self.ou

    class Meta:
        managed = False


class LdapAutomountHome(ldapdb.models.Model):
    """
    Represents an LDAP automount with hardcoded 'auto.home' in the base_dn (!)
    Ref: http://www.openldap.org/faq/data/cache/599.html
    Ref: http://lists.bolloretelecom.eu/pipermail/django-ldapdb/2012-April/000113.html
    """

    connection_name = "ldap"

    # LDAP meta-data
    base_dn = "ou=auto.home,{}".format(settings.LDAP_AUTOMOUNT_DN)
    object_classes = ["automount"]

    username = CharField(db_column="cn", primary_key=True)
    automountInformation = CharField(db_column="automountInformation")

    def set_automount_info(self, username=None):
        krb5_automount_info = "-fstype=nfs4,rw,sec=krb5 {}:{}/{}".format(
            settings.FILESERVER_HOST, settings.FILESERVER_HOME_PATH, username if username is not None else self.username
        )

        self.automountInformation = krb5_automount_info

    def __str__(self):
        return self.username

    class Meta:
        managed = False
