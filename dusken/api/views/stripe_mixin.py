import logging

import stripe
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException
from stripe import CardError, InvalidRequestError

STRIPE_ERRORS = {
    "incorrect_number": _("The card number is incorrect."),
    "invalid_number": _("The card number is not a valid credit card number."),
    "invalid_expiry_month": _("The card's expiration month is invalid."),
    "invalid_expiry_year": _("The card's expiration year is invalid."),
    "invalid_cvc": _("The card's security code is invalid."),
    "expired_card": _("The card has expired."),
    "incorrect_cvc": _("The card's security code is incorrect."),
    "incorrect_zip": _("The card's zip code failed validation."),
    "card_declined": _("The card was declined."),
    "missing": _("There is no card on a customer that is being charged."),
    "processing_error": _("An error occurred while processing the card."),
    "rate_limit": _(
        "An error occurred due to requests hitting the API too quickly. Please let us know if you're consistently running into this error.",
    ),
}

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeAPIMixin:
    def _create_stripe_customer(self, stripe_token):
        try:
            return stripe.Customer.create(email=stripe_token["email"], card=stripe_token["id"])
        except InvalidRequestError as e:
            logger.warning("Invalid Stripe request! %s", str(e))

            raise APIException(_("Stripe charge failed with API error.")) from e
        except CardError as e:
            logger.info("stripe.Customer.create did not succeed: %s", e)
            raise APIException(STRIPE_ERRORS.get(e.code, _("Your card has been declined."))) from e

    def _update_stripe_customer(self, customer, stripe_token):
        try:
            return stripe.Customer.modify(customer.id, email=stripe_token["email"], source=stripe_token["id"])
        except InvalidRequestError as e:
            logger.warning("Invalid Stripe request! %s", str(e))

            raise APIException(_("Stripe charge failed with API error.")) from e
        except CardError as e:
            logger.info("stripe.Customer.modify did not succeed: %s", e)
            raise APIException(STRIPE_ERRORS.get(e.code, _("Your card has been declined."))) from e

    def _create_stripe_charge(self, customer, amount, description, currency):
        try:
            return stripe.Charge.create(
                customer=customer.id,
                amount=amount,
                currency=currency,
                description=description,
            )
        except InvalidRequestError as e:
            logger.warning("Invalid Stripe request! %s", str(e))

            raise APIException("Stripe charge failed with API error.") from e
        except CardError as e:
            logger.info("stripe.Charge.create did not succeed: %s", e)
            raise APIException(STRIPE_ERRORS.get(e.code, _("Your card has been declined."))) from e

    def _get_stripe_customer(self, stripe_customer_id):
        try:
            return stripe.Customer.retrieve(stripe_customer_id)
        except InvalidRequestError as e:
            logger.warning("Invalid Stripe request! %s", str(e))
            raise APIException(_("Stripe charge failed with API error.")) from e
