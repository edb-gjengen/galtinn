# Generated by Django 3.2.25 on 2024-04-17 13:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dusken', '0007_rename_discord_role_orgunit_discord_role_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupprofile',
            name='discord_role_id',
            field=models.IntegerField(blank=True, null=True, unique=True),
        ),
    ]
