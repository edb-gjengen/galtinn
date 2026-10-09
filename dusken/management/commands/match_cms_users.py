import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from dusken.models import DuskenUser

EXTRA_FIELDS = ["match", "candidate_ids", "galtinn_username", "galtinn_email", "galtinn_name", "email_confirmed"]


class Command(BaseCommand):
    help = (
        "Suggest a Galtinn user for each row of a CMS user export (galtinn_users export in dnscms). "
        "Writes the CSV to stdout with galtinn_id filled in on an email match, for manual review."
    )

    def add_arguments(self, parser):
        parser.add_argument("csv_file")
        parser.add_argument("--group", help="Add an in_group column for membership of this group")

    def handle(self, *_args, **options):
        group = options["group"]
        with Path(options["csv_file"]).open(newline="") as f:
            reader = csv.DictReader(f)
            fields = [*reader.fieldnames, *EXTRA_FIELDS, *(["in_group"] if group else [])]
            writer = csv.DictWriter(self.stdout, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            for row in reader:
                writer.writerow({**row, **self.match(row, group)})

    def match(self, row, group):
        if row.get("galtinn_id"):
            match, users = "linked", list(DuskenUser.objects.filter(pk=row["galtinn_id"]))
        else:
            by_email = DuskenUser.objects.filter(email__iexact=row["email"]).first() if row["email"] else None
            by_username = DuskenUser.objects.filter(username__iexact=row["username"]).first()
            users = list(dict.fromkeys(user for user in (by_email, by_username) if user))
            if not users:
                match = "none"
            elif len(users) > 1:
                match = "conflict"
            elif by_email and by_username:
                match = "email+username"
            else:
                match = "email" if by_email else "username"

        result = {"match": match, "candidate_ids": " ".join(str(user.pk) for user in users)}
        if len(users) != 1:
            return result
        user = users[0]
        result |= {
            "galtinn_username": user.username,
            "galtinn_email": user.email,
            "galtinn_name": user.get_full_name(),
            "email_confirmed": int(user.email_is_confirmed),
        }
        # A username alone is too weak to prefill; the reviewer copies the candidate over
        if match.startswith("email"):
            result["galtinn_id"] = user.pk
        if group:
            result["in_group"] = int(user.groups.filter(name=group).exists())
        return result
