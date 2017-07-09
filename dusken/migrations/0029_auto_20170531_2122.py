# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-31 19:22
from __future__ import unicode_literals

from django.db import migrations, models
import django_countries.fields
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('dusken', '0028_auto_20170412_2234'),
    ]

    operations = [
        migrations.AlterField(
            model_name='duskenuser',
            name='country',
            field=django_countries.fields.CountryField(blank=True, default='NO', max_length=2, verbose_name='country'),
        ),
        migrations.AlterField(
            model_name='duskenuser',
            name='phone_number',
            field=phonenumber_field.modelfields.PhoneNumberField(blank=True, default='', max_length=128, verbose_name='phone number'),
        ),
        migrations.AlterField(
            model_name='order',
            name='price_nok',
            field=models.IntegerField(help_text='Price in øre'),
        ),
    ]
