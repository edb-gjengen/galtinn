# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('dusken', '0004_auto_20150906_1409'),
    ]

    operations = [
        migrations.DeleteModel(
            name='PaymentType',
        ),
        migrations.AlterField(
            model_name='membership',
            name='user',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='memberships', blank=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='value',
            field=models.IntegerField(help_text='In øre'),
        ),
    ]
