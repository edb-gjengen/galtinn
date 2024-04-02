import csv
import json
import sys

from django.core.management.base import BaseCommand

from dusken.models import DuskenUser


class Command(BaseCommand):
    """The CSV file should have the following headers with the exact column names.
    attributes (optional) should be a valid JSON string with double escaped quotes.

    Example:
    -------
    email,name,attributes
    user1@mail.com,"User One","{""age"": 42, ""planet"": ""Mars""}"
    user2@mail.com,"User Two","{""age"": 24, ""job"": ""Time Traveller""}"

    """

    help = "Export users with an active membership and volunteer status as CSV"

    def handle(self, *_args, **_options):
        exportable = []
        members = DuskenUser.objects.with_valid_membership()
        for member in members:
            if (member.is_volunteer and member.is_lifelong_member) or not member.is_lifelong_member:
                exportable.append(
                    {
                        "email": member.email,
                        "name": f"{member.first_name} {member.last_name}",
                        "attributes": json.dumps({"user_id": member.id}),
                    },
                )
        writer = csv.DictWriter(sys.stdout, fieldnames=["email", "name", "attributes"])
        writer.writeheader()
        for row in exportable:
            writer.writerow(row)
