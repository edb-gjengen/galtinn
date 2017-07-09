# coding: utf-8
from __future__ import unicode_literals

from django.db import models
import datetime


class Action(models.Model):
    connection_name = 'inside'

    name = models.CharField(unique=True, max_length=50)
    text = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'din_action'


class ActionGroupRelationship(models.Model):
    connection_name = 'inside'

    action = models.ForeignKey(Action)
    group = models.ForeignKey('inside.InsideGroup')

    class Meta:
        managed = False
        db_table = 'din_actiongrouprelationship'


class BugReport(models.Model):
    connection_name = 'inside'

    date = models.DateTimeField()
    type = models.CharField(max_length=45)
    filename = models.CharField(max_length=45)
    query = models.TextField()
    referer = models.TextField()
    useragent = models.CharField(max_length=255)
    user_id = models.IntegerField(blank=True, null=True)
    comment = models.TextField()
    title = models.CharField(max_length=50)
    active = models.IntegerField()
    status_comment = models.TextField()

    class Meta:
        managed = False
        db_table = 'din_bugreport'


class Division(models.Model):
    connection_name = 'inside'

    name = models.CharField(unique=True, max_length=50)
    nicename = models.CharField(max_length=20)
    text = models.TextField()
    phone = models.CharField(max_length=8)
    email = models.CharField(max_length=120)
    office = models.CharField(max_length=3)
    user_id_contact = models.ForeignKey('inside.InsideUser', db_column='user_id_contact')
    url = models.CharField(max_length=120)
    divisioncategory = models.ForeignKey('inside.DivisionCategory')
    picture = models.CharField(max_length=7)
    hidden = models.IntegerField()
    updated = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'din_division'


class DivisionCategory(models.Model):
    connection_name = 'inside'

    title = models.CharField(unique=True, max_length=50)
    text = models.TextField()

    class Meta:
        managed = False
        db_table = 'din_divisioncategory'


class Document(models.Model):
    connection_name = 'inside'

    type = models.CharField(max_length=60)
    name = models.CharField(max_length=120)
    size = models.BigIntegerField()
    date = models.DateTimeField()
    documentcategory = models.ForeignKey('inside.DocumentCategory')
    tags = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'din_document'


class DocumentCategory(models.Model):
    connection_name = 'inside'

    title = models.CharField(unique=True, max_length=50)
    text = models.TextField()

    class Meta:
        managed = False
        db_table = 'din_documentcategory'


class DocumentData(models.Model):
    connection_name = 'inside'

    data = models.BinaryField()
    document = models.ForeignKey(Document)

    class Meta:
        managed = False
        db_table = 'din_documentdata'


class InsideGroup(models.Model):
    connection_name = 'inside'

    name = models.CharField(unique=True, max_length=50)
    text = models.TextField()
    division = models.ForeignKey(Division, blank=True, null=True)
    admin = models.CharField(max_length=1)
    mailinglist = models.CharField(max_length=50)
    posix_group = models.CharField(max_length=128)

    def __str__(self):
        if self.posix_group == '':
            return self.name

        return '{} ({})'.format(self.name, self.posix_group)

    class Meta:
        managed = False
        db_table = 'din_group'


class MemberCard(models.Model):
    connection_name = 'inside'

    userid = models.IntegerField(db_column='userId', blank=True, null=True)  # Field name made lowercase.
    ordered = models.DateTimeField(blank=True, null=True)
    produced = models.DateTimeField(blank=True, null=True)
    delivered = models.DateTimeField(blank=True, null=True)
    active = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'din_membercard'


class InsideOrder(models.Model):
    connection_name = 'inside'

    user = models.ForeignKey('inside.InsideUser')
    timestamp = models.DateTimeField()
    order_status = models.ForeignKey('inside.OrderStatus')
    order_deliverystatus_id = models.IntegerField()
    comment = models.TextField()

    class Meta:
        managed = False
        db_table = 'din_order'


class OrderDeliveryStatus(models.Model):
    connection_name = 'inside'

    order_deliverystatus_id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'din_order_deliverystatus'


class OrderItem(models.Model):
    connection_name = 'inside'

    product = models.ForeignKey('inside.Product')
    quantity = models.IntegerField()
    order = models.ForeignKey('inside.InsideOrder')
    discount = models.IntegerField()
    comment = models.TextField()

    class Meta:
        managed = False
        db_table = 'din_order_item'


class OrderStatus(models.Model):
    connection_name = 'inside'

    value = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'din_order_status'


class Position(models.Model):
    connection_name = 'inside'

    name = models.CharField(max_length=50)
    division = models.ForeignKey('inside.Division')
    text = models.TextField()

    class Meta:
        managed = False
        db_table = 'din_position'


class InsidePostalCode(models.Model):
    connection_name = 'inside'

    postnummer = models.CharField(primary_key=True, max_length=4)
    poststed = models.CharField(max_length=32)
    kommunenr = models.CharField(max_length=4)
    kommunenavn = models.CharField(max_length=30)
    kategori = models.CharField(max_length=1)

    class Meta:
        managed = False
        db_table = 'din_postnummer'


class Product(models.Model):
    connection_name = 'inside'

    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.IntegerField()
    allow_comment = models.IntegerField()
    display_in_shop = models.IntegerField()
    picture = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'din_product'


class InsideSettings(models.Model):
    connection_name = 'inside'

    name = models.CharField(primary_key=True, max_length=45)
    value = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'din_settings'


class SmsReceived(models.Model):
    connection_name = 'inside'

    smsid = models.IntegerField(primary_key=True)
    userid = models.IntegerField(blank=True, null=True)
    gsm = models.CharField(max_length=15)
    codeword = models.CharField(max_length=20)
    message = models.CharField(max_length=160)
    operator = models.CharField(max_length=20)
    shortno = models.CharField(max_length=15)
    action = models.CharField(max_length=30)
    ip = models.CharField(db_column='IP', max_length=15)  # Field name made lowercase.
    date = models.DateTimeField()
    simulation = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'din_sms_received'


class SmsSent(models.Model):
    connection_name = 'inside'

    smsid = models.IntegerField(primary_key=True)
    response_to = models.IntegerField()
    msgid = models.IntegerField()
    sender = models.CharField(max_length=15)
    receiver = models.CharField(max_length=15)
    countrycode = models.IntegerField()
    message = models.CharField(max_length=160)
    operator = models.CharField(max_length=20, blank=True)
    codeword = models.CharField(max_length=20, blank=True)
    billing_price = models.IntegerField()
    use_dlr = models.IntegerField()
    date = models.DateTimeField()
    simulation = models.IntegerField()
    activation_code = models.CharField(max_length=10, blank=True)

    class Meta:
        managed = False
        db_table = 'din_sms_sent'


class Transaction(models.Model):
    connection_name = 'inside'

    id_string = models.CharField(max_length=25)
    user = models.ForeignKey('inside.InsideUser')
    order = models.ForeignKey('inside.InsideOrder')
    timestamp = models.DateTimeField()
    status = models.CharField(max_length=8, blank=True)
    amount = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'din_transaction'


class TransactionCheck(models.Model):
    connection_name = 'inside'

    order_id = models.IntegerField(primary_key=True)
    inserted = models.DateTimeField()
    order_ref = models.CharField(max_length=255)
    order_ref2 = models.CharField(max_length=255, blank=True)

    class Meta:
        managed = False
        db_table = 'din_transaction_check'


class UsedCardNo(models.Model):
    connection_name = 'inside'

    date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'din_usedcardno'


class InsideUser(models.Model):
    connection_name = 'inside'

    cardno = models.IntegerField(unique=True, blank=True, null=True)
    username = models.CharField(unique=True, max_length=12)
    password = models.CharField(max_length=50)
    first_name = models.CharField(max_length=120, db_column='firstname')
    last_name = models.CharField(max_length=120, db_column='lastname')
    addresstype = models.CharField(max_length=3)
    valid_address = models.IntegerField()
    email = models.CharField(unique=True, max_length=120)
    birthdate = models.DateField()
    placeofstudy = models.ForeignKey('inside.InsidePlaceOfStudy', db_column='placeOfStudy')
    passwordreset = models.CharField(db_column='passwordReset', max_length=1)  # Field name made lowercase.
    expires = models.DateField(blank=True, null=True)
    division_id_request = models.ForeignKey('inside.Division', db_column='division_id_request', blank=True, null=True)
    cardproduced = models.IntegerField(db_column='cardProduced')  # Field name made lowercase.
    carddelivered = models.IntegerField(db_column='cardDelivered')  # Field name made lowercase.
    laststicker = models.CharField(db_column='lastSticker', max_length=9)  # Field name made lowercase.
    migrated = models.DateTimeField(blank=True, null=True)
    ldap_username = models.CharField(unique=True, max_length=20, blank=True)
    source = models.CharField(max_length=255)
    registration_status = models.CharField(max_length=255)
    created = models.DateTimeField(blank=True, null=True)
    membership_trial = models.CharField(max_length=255)
    ldap_password = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        if not self.ldap_username:
            return 'User {}'.format(self.pk)

        return '{} ({})'.format(self.ldap_username, self.pk)

    class Meta:
        managed = False
        db_table = 'din_user'


class UserAddressInt(models.Model):
    connection_name = 'inside'

    user = models.OneToOneField('inside.InsideUser', primary_key=True)
    street = models.CharField(max_length=255)
    zipcode = models.CharField(max_length=10)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    country = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'din_useraddressint'


class UserAddressNo(models.Model):
    connection_name = 'inside'

    user = models.OneToOneField('inside.InsideUser', primary_key=True)
    street = models.CharField(max_length=255)
    zipcode = models.ForeignKey('inside.PostalCode', db_column='zipcode')

    class Meta:
        managed = False
        db_table = 'din_useraddressno'


class UserGroupRelationship(models.Model):
    connection_name = 'inside'

    user = models.ForeignKey('inside.InsideUser', related_name='group_rels')
    group = models.ForeignKey('inside.InsideGroup', related_name='user_rels')

    class Meta:
        managed = False
        db_table = 'din_usergrouprelationship'


class UserPhoneNumber(models.Model):
    connection_name = 'inside'

    user = models.OneToOneField('inside.InsideUser', primary_key=True)
    number = models.CharField(max_length=16)
    validated = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'din_userphonenumber'


class UserUpdate(models.Model):
    connection_name = 'inside'

    date = models.DateTimeField(auto_now_add=True)
    user_updated = models.ForeignKey(
        'inside.InsideUser',
        db_column='user_id_updated',
        related_name='updates')
    comment = models.CharField(max_length=255)
    user_updated_by = models.ForeignKey(
        'inside.InsideUser',
        db_column='user_id_updated_by',
        blank=True,
        null=True,
        related_name='admin_updates')

    class Meta:
        managed = False
        db_table = 'din_userupdate'


class AuthLog(models.Model):
    connection_name = 'inside'

    username = models.CharField(max_length=80)
    password = models.IntegerField()
    time = models.DateTimeField()
    error = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'inside_auth_log'


class PostalCode(models.Model):
    connection_name = 'inside'

    postnummer = models.CharField(primary_key=True, max_length=4)
    poststed = models.CharField(max_length=32)
    kommunenr = models.CharField(max_length=4)
    kommunenavn = models.CharField(max_length=30)
    kategori = models.CharField(max_length=1)

    class Meta:
        managed = False
        db_table = 'postnummer'


class InsidePlaceOfStudy(models.Model):
    connection_name = 'inside'

    navn = models.CharField(unique=True, max_length=120)

    class Meta:
        managed = False
        db_table = 'studiesteder'


class InsideCard(models.Model):
    connection_name = 'inside'

    card_number = models.IntegerField(unique=True)
    user = models.ForeignKey('inside.InsideUser', models.DO_NOTHING, blank=True, null=True)
    registered = models.DateTimeField(blank=True, null=True)
    created = models.DateTimeField()
    is_active = models.IntegerField()
    owner_phone_number = models.CharField(max_length=32, blank=True, null=True)
    owner_membership_trial = models.CharField(max_length=254, blank=True, null=True)

    def __str__(self):
        return str(self.card_number)

    class Meta:
        managed = False
        db_table = 'din_card'
