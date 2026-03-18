import os

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from dusken.models import MembershipType


class Command(BaseCommand):
    help = "Connect to Stripe and sync Product and Price to MembershipType objects"

    def handle(self, *_args, **_options):
        if not os.getenv("DJANGO_SETTINGS_MODULE", "").endswith(".dev"):
            self.stderr.write("This command should only be run in development environment.")
            return

        # Fetch all active products from Stripe
        url = "https://api.stripe.com/v1/products?active=true&limit=100"
        r = requests.get(url, auth=(settings.STRIPE_SECRET_KEY, ""), timeout=10)
        r.raise_for_status()
        data = r.json()

        for item in data["data"]:
            self.stdout.write(f"Processing product: {item['name']}")
            if item["metadata"].get("django_model", "") != "MembershipType":  # Click-opsed this to the Product metadata
                continue

            # Fetch prices
            price_url = f"https://api.stripe.com/v1/prices?product={item['id']}&active=true&limit=100"
            price_response = requests.get(price_url, auth=(settings.STRIPE_SECRET_KEY, ""), timeout=10)
            price_response.raise_for_status()
            price_data = price_response.json()
            for price in price_data["data"]:
                MembershipType.objects.update_or_create(
                    slug=price["lookup_key"],
                    defaults={
                        "name": price["nickname"] or price["lookup_key"],
                        "price": price["unit_amount"],
                        "stripe_price_id": price["id"],
                        "slug": price["lookup_key"],
                    },
                )
