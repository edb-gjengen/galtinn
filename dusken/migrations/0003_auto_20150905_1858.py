# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dusken', '0002_auto_20150902_2040'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='payment',
            name='payment_type',
        ),
        migrations.AddField(
            model_name='membershiptype',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='membershiptype',
            name='price',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='payment',
            name='payment_method',
            field=models.CharField(default='other', max_length=254, choices=[('app', 'Mobile app'), ('sms', 'SMS'), ('card', 'Credit card'), ('other', 'Other (cash register, bar, ...)')]),
        ),
        migrations.AlterField(
            model_name='membershiptype',
            name='name',
            field=models.CharField(max_length=254),
        ),
        migrations.AlterField(
            model_name='payment',
            name='transaction_id',
            field=models.IntegerField(blank=True, help_text='Stripe token ID, Kassa ID, SMS ID or App ID', null=True),
        ),
    ]
