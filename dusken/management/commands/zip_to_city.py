import csv
import os

import requests
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Ref: https://www.bring.no/radgivning/sende-noe/adressetjenester/postnummer"""

    help = "Update zip code to city map"

    def handle(self, *args, **options):
        url = "https://www.bring.no/radgivning/sende-noe/adressetjenester/postnummer/_attachment/615728?_download=true&_ts=1595e62daf0"
        lines = []

        r = requests.get(url)
        r.encoding = "ISO-8859-1"
        reader = csv.reader(r.text.split("\n"), delimiter="\t")
        for row in reader:
            if not row:
                continue

            lines.append(f'    "{row[0]}": "{row[1]}",\n')  # f.ex '0559': 'OSLO',

        with open(os.path.join(settings.BASE_DIR, "dusken/zip_to_city.py"), "w+") as out:
            out.write("ZIP_TO_CITY_MAP = {\n")
            out.writelines(lines)
            out.write("}\n")
