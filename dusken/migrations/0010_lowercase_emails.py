from django.db import migrations
from django.db.models import Q
from django.db.models.functions import Lower


def lowercase_emails(apps, _schema_editor):
    # A bulk update, so DuskenUser.save() doesn't reset the confirmation or send validation emails
    DuskenUser = apps.get_model("dusken", "DuskenUser")
    DuskenUser.objects.filter(~Q(email=Lower("email"))).update(email=Lower("email"))
    DuskenUser.objects.filter(~Q(username=Lower("username"))).update(username=Lower("username"))


class Migration(migrations.Migration):
    dependencies = [
        ("dusken", "0009_order_payment_source_stripepayment"),
    ]

    operations = [
        migrations.RunPython(lowercase_emails, migrations.RunPython.noop),
    ]
