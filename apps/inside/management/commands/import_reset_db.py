from django.contrib.auth.models import Group
from django.core.management import BaseCommand

from dusken.models import DuskenUser, MemberCard, Order, Membership, OrgUnit, GroupProfile, PlaceOfStudy


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("WARNING: Destructive action, deleting everything!")

        answer = input("Are you sure? [y/N]")
        if answer.strip() not in ['y', 'Y', 'yes']:
            print("Bailed, did nothing.")
            return

        superusers = DuskenUser.objects.filter(is_superuser=True)
        DuskenUser.objects.exclude(pk__in=superusers).delete()
        MemberCard.objects.all().delete()
        Membership.objects.all().delete()
        Order.objects.all().delete()
        OrgUnit.objects.all().delete()
        GroupProfile.objects.all().delete()
        Group.objects.all().delete()
        PlaceOfStudy.objects.all().delete()

        print("All gone.")
