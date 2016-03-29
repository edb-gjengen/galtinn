# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-28 17:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0007_alter_validators_add_error_messages'),
        ('dusken', '0011_duskenuser_phone_number_validated'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='placeofstudy',
            name='from_date',
        ),
        migrations.RemoveField(
            model_name='placeofstudy',
            name='institution',
        ),
        migrations.AddField(
            model_name='orgunit',
            name='admin_groups',
            field=models.ManyToManyField(blank=True, related_name='admin_orgunits', to='auth.Group'),
        ),
        migrations.AddField(
            model_name='placeofstudy',
            name='name',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='placeofstudy',
            name='short_name',
            field=models.CharField(default='', max_length=16),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='orgunit',
            name='groups',
            field=models.ManyToManyField(blank=True, related_name='member_orgunits', to='auth.Group'),
        ),
        migrations.DeleteModel(
            name='Institution',
        ),
    ]
