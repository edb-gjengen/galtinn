# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-24 20:37
from __future__ import unicode_literals

import django.contrib.auth.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dusken', '0016_auto_20160417_1847'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='orgunit',
            managers=[
            ],
        ),
        migrations.AlterField(
            model_name='duskenuser',
            name='username',
            field=models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username'),
        ),
    ]
