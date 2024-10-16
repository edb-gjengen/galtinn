# Generated by Django 1.11.7 on 2017-11-22 23:28

import django.db.models.deletion
import mptt.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dusken", "0001_squashed_0052_auto_20170920_2149"),
    ]

    operations = [
        migrations.AlterField(
            model_name="duskenuser",
            name="place_of_study",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="dusken.PlaceOfStudy",
                verbose_name="place of study",
            ),
        ),
        migrations.AlterField(
            model_name="membercard",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="member_cards",
                to=settings.AUTH_USER_MODEL,
                verbose_name="user",
            ),
        ),
        migrations.AlterField(
            model_name="membership",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="memberships",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="member_card",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="orders",
                to="dusken.MemberCard",
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="product",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="dusken.Membership",
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="orders",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="orgunit",
            name="admin_group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="admin_orgunits",
                to="auth.Group",
                verbose_name="admin group",
            ),
        ),
        migrations.AlterField(
            model_name="orgunit",
            name="group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="member_orgunits",
                to="auth.Group",
                verbose_name="group",
            ),
        ),
        migrations.AlterField(
            model_name="orgunit",
            name="parent",
            field=mptt.fields.TreeForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="children",
                to="dusken.OrgUnit",
                verbose_name="parent",
            ),
        ),
    ]
