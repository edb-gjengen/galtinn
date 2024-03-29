# Generated by Django 1.11.3 on 2017-07-31 20:29

from typing import List, Tuple

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies: List[Tuple[str, str]] = []

    operations = [
        migrations.CreateModel(
            name="MailChimpSubscription",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                ("email", models.EmailField(max_length=254, verbose_name="email")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("subscribed", "subscribed"),
                            ("pending", "pending"),
                            ("unsubscribed", "unsubscribed"),
                        ],
                        default="subscribed",
                        max_length=15,
                        verbose_name="status",
                    ),
                ),
                ("mailchimp_id", models.CharField(max_length=50, unique=True)),
            ],
            options={
                "verbose_name": "mailchimp user",
                "verbose_name_plural": "mailchimp users",
            },
        ),
    ]
