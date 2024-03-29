# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-31 22:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mailchimp", "0002_auto_20170801_0012"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="mailchimpsubscription",
            name="mailchimp_id",
        ),
        migrations.AlterField(
            model_name="mailchimpsubscription",
            name="status",
            field=models.CharField(
                choices=[
                    ("subscribed", "subscribed"),
                    ("pending", "pending"),
                    ("unsubscribed", "unsubscribed"),
                    ("cleaned", "cleaned"),
                ],
                default="subscribed",
                max_length=15,
                verbose_name="status",
            ),
        ),
    ]
