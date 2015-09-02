# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_countries.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dusken', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='duskenuser',
            options={},
        ),
        migrations.AlterField(
            model_name='duskenuser',
            name='city',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='duskenuser',
            name='country',
            field=django_countries.fields.CountryField(blank=True, max_length=2, null=True),
        ),
        migrations.AlterField(
            model_name='duskenuser',
            name='postal_code',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='duskenuser',
            name='street_address',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
