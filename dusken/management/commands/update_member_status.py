import json
import logging
from argparse import ArgumentParser
from datetime import datetime, timedelta
from pathlib import Path

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction

from dusken.models import DuskenUser

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Updates is_member status based on group membership and saves the state to a JSON file"

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "--groups",
            nargs="+",
            type=str,
            help="List of group names that should be considered for member status",
        )
        parser.add_argument(
            "--output_file",
            type=str,
            default="member_status.json",
            help="Path to the output JSON file. Is also read if it exists to get previous state.",
        )
        parser.add_argument(
            "--duration_days",
            type=int,
            default=365,
            help="Duration of membership in days (default: 365)",
        )

    def _read_previous_state(self, output_file: Path) -> dict:
        if not output_file.exists():
            return {}
        try:
            with output_file.open() as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Could not parse {output_file}, starting fresh")
            return {}

    def _update_user_membership(self, user: DuskenUser, is_member: bool, duration_days: int) -> None:  # noqa: FBT001
        if is_member and not user.last_membership:
            from dusken.models import Membership, MembershipType

            membership_type = MembershipType.get_default()
            start_date = datetime.now().date()  # noqa: DTZ005
            end_date = start_date + timedelta(days=duration_days)
            Membership.objects.create(
                user=user, membership_type=membership_type, start_date=start_date, end_date=end_date
            )
        elif not is_member and user.last_membership:
            user.last_membership.delete()

    def _get_user_data(self, user: DuskenUser, is_member: bool) -> dict:  # noqa: FBT001
        return {
            "username": user.username,
            "email": user.email,
            "groups": list(user.groups.values_list("name", flat=True)),
            "is_member": is_member,
            "last_membership": {
                "start_date": str(user.last_membership.start_date) if user.last_membership else None,
                "end_date": str(user.last_membership.end_date) if user.last_membership else None,
            }
            if user.last_membership
            else None,
        }

    def handle(self, **options):
        group_names = options["groups"]
        output_file = Path(options["output_file"])
        duration_days = options["duration_days"]

        if not group_names:
            logger.error("Please provide at least one group name")
            return

        groups = Group.objects.filter(name__in=group_names)
        if not groups.exists():
            logger.error(f"No groups found with names: {group_names}")
            return

        previous_state = self._read_previous_state(output_file)
        if previous_state:
            logger.info(f"Read previous state from {output_file}")

        users = DuskenUser.objects.all()
        user_data = []

        with transaction.atomic():
            for user in users:
                is_member = any(group.name in group_names for group in user.groups.all())

                if previous_state and "users" in previous_state:
                    for prev_user in previous_state["users"]:
                        if prev_user["username"] == user.username and prev_user["is_member"] and not is_member:
                            logger.info(
                                f"User {user.username} was previously a member but has been removed from groups"
                            )
                            if user.last_membership:
                                user.last_membership.delete()
                            break

                if is_member != user.is_member:
                    logger.info(f"Updating {user.username} member status from {user.is_member} to {is_member}")
                    self._update_user_membership(user, is_member, duration_days)

                user_data.append(self._get_user_data(user, is_member))

        with output_file.open("w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),  # noqa: DTZ005
                    "groups": group_names,
                    "duration_days": duration_days,
                    "users": user_data,
                },
                f,
                indent=2,
            )

        logger.info(f"Successfully updated member status and saved to {output_file}")
