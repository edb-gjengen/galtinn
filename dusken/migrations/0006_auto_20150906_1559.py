# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dusken', '0005_auto_20150906_1504'),
    ]

    operations = [
        migrations.AddField(
            model_name='duskenuser',
            name='stripe_customer_id',
            field=models.CharField(max_length=254, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='membershiptype',
            name='price',
            field=models.IntegerField(default=0, help_text='Price in øre'),
        ),
    ]
