# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-14 13:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("neuf_auth", "0002_auto_20170803_1607"),
    ]

    operations = [
        migrations.AddField(
            model_name="authprofile",
            name="username_updated",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
