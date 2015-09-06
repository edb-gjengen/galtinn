# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dusken', '0003_auto_20150905_1858'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='transaction_id',
            field=models.CharField(max_length=254, help_text='Stripe token ID, Kassa ID, SMS ID or App ID', blank=True, null=True),
        ),
    ]
