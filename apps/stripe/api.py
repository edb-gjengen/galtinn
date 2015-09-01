from django.conf import settings
import stripe


def charge(amount, card_token, description, meta_data):
    stripe.api_key = settings.STRIPE_API_KEY

    charge_res = stripe.Charge.create(
        amount=amount,
        currency="NOK",
        card=card_token,  # obtained with Stripe.js
        description=description,
        meta_data=meta_data
    )
    # TODO: Look at https://github.com/eldarion/django-stripe-payments
    return charge_res
