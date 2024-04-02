from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser
from strawberry.printer import print_schema

from dusken.api.graphql import schema as schema_symbol


class Command(BaseCommand):
    help = " Write graphql schema to file or stdout"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("--filename", default="schema.graphql", help="`-` prints to stdout")

    def handle(self, *_args, filename=None, **_options):
        schema_output = print_schema(schema_symbol)
        if filename != "-":
            with Path(settings.BASE_DIR, filename).open("w+") as fp:
                fp.write(schema_output)
            self.stdout.write(self.style.SUCCESS("OK"))
        else:
            print(schema_output)  # noqa: T201
