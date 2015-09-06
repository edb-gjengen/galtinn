# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dusken', '0006_auto_20150906_1559'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='transaction_id',
            field=models.CharField(null=True, max_length=254, help_text='Stripe charge ID, Kassa event ID, SMS event ID or App event ID', blank=True),
        ),
    ]
