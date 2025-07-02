import logging

import stripe
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from dusken.models.orders import Membership, MembershipType, Order, StripePayment
from dusken.utils import redirect_see_other

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripePaymentSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    membership_type = serializers.SlugRelatedField(
        slug_field="slug", queryset=MembershipType.objects.filter(is_active=True)
    )

    class Meta:
        model = StripePayment
        fields = ["id", "user", "stripe_id", "membership_type"]
        read_only_fields = ["stripe_id"]


class StripeBaseAPIView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = StripePaymentSerializer

    customer: stripe.Customer
    membership_type: MembershipType
    redirect_on_exception = False

    def get_response(self) -> HttpResponse:
        raise NotImplementedError

    def stripe_customer_get_or_create(self, user) -> stripe.Customer:
        # Lookup using existing Customer ID
        if user.stripe_customer_id:
            customer = stripe.Customer.retrieve(user.stripe_customer_id)
            # Update email
            customer.modify(customer.id, email=user.email)
        else:
            customer = stripe.Customer.create(email=user.email)
            user.stripe_customer_id = customer.id
            user.save()

        return customer

    def post(self, request):
        self.serializer = self.serializer_class(data=request.data, context={"request": request})
        self.serializer.is_valid(raise_exception=True)
        self.membership_type = self.serializer.validated_data.get("membership_type")
        try:
            self.customer = self.stripe_customer_get_or_create(request.user)
        except stripe.InvalidRequestError as e:
            logger.exception("Stripe Customer API request failed", exc_info=e)
            if self.redirect_on_exception:
                home_url = f"{settings.SITE_URL}{reverse('home')}"
                return redirect_see_other(f"{home_url}?payment_failed=1&error=tryagainlater")

            raise APIException(_("Payment failed with a Stripe API error")) from e

        return self.get_response()


# FIXME: Test failed and cancelled payments
class StripeCheckoutSessionView(StripeBaseAPIView):
    def get_response(self):
        # Create checkout session
        home_url = f"{settings.SITE_URL}{reverse('home')}"
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=[{"price": self.membership_type.stripe_price_id, "quantity": 1}],
                mode="payment",
                success_url=f"{home_url}?payment_success=1",
                # TODO: verify flow canceled state
                cancel_url=f"{home_url}?payment_canceled=1",
                customer=self.customer.id,
            )
        except stripe.InvalidRequestError as e:
            logger.exception("Stripe checkout.Session.create API request failed", exc_info=e)
            # FIXME: Show error to user in HTML template
            return redirect_see_other(f"{home_url}?payment_failed=1&error=tryagainlater")

        # Save local checkout session with a stripe ID reference
        self.serializer.save(stripe_id=checkout_session.id)

        return redirect_see_other(checkout_session.url)


class StripePaymentSheetView(StripeBaseAPIView):
    CURRENCY = "nok"

    def get_response(self):
        # Create ephemeral key and payment intent for app payment sheet use
        try:
            ephemeral_key = stripe.EphemeralKey.create(customer=self.customer.id, stripe_version="2018-05-21")
            payment_intent = stripe.PaymentIntent.create(
                amount=self.membership_type.price,
                currency=self.CURRENCY,
                customer=self.customer.id,
                automatic_payment_methods={"enabled": True},
            )
        except stripe.InvalidRequestError as e:
            logger.exception("Stripe PaymentIntent.create API request failed", exc_info=e)
            raise APIException(_("Payment failed with a Stripe API error")) from e

        # Save local payment intent with a stripe ID reference
        self.serializer.save(
            stripe_id=payment_intent.id,
            stripe_model=StripePayment.StripeModel.PAYMENT_INTENT,
            source=Order.PaymentSource.APP,
        )

        return Response(
            {
                "paymentIntent": payment_intent.client_secret,
                "ephemeralKey": ephemeral_key.secret,
                "customer": self.customer.id,
                "publishableKey": settings.STRIPE_PUBLIC_KEY,
            }
        )


class StripeWebhookView(GenericAPIView):
    permission_classes = [AllowAny]  # Rely on signature verification

    def _verify_signature(self, request):
        try:
            signature_header = request.headers.get("stripe-signature")
            event = stripe.Webhook.construct_event(
                request.body, signature_header, settings.STRIPE_WEBHOOK_SIGNING_SECRET
            )
        except ValueError as err:
            raise ValidationError("Invalid stripe webhook payload") from err
        except stripe.SignatureVerificationError as err:
            raise ValidationError("Invalid stripe webhook signature") from err

        return event

    def _get_stripe_payment(self, stripe_id: str, stripe_model: StripePayment.StripeModel, suppress_exception=False):
        try:
            return StripePayment.objects.get(
                stripe_id=stripe_id, stripe_model=stripe_model, status=StripePayment.Status.OPEN
            )
        except StripePayment.DoesNotExist as err:
            if suppress_exception:
                return None
            raise ValidationError(
                f"StripePayment({stripe_id=},stripe_model='{stripe_model}',status='open') does not exist"
            ) from err

    def _create_order(self, stripe_payment: StripePayment):
        # FIXME: reduce duplication. This is copied from legacy serializer
        user = stripe_payment.user
        membership_type = stripe_payment.membership_type
        payment_method = Order.BY_APP if stripe_payment.source == Order.PaymentSource.APP else Order.BY_CARD
        with transaction.atomic():
            start_date = Membership.start_date_for_user(user)
            membership = Membership.objects.create(
                start_date=start_date,
                end_date=start_date + membership_type.duration,
                user=user,
                membership_type=membership_type,
            )
            order = Order.objects.create(
                price_nok=membership_type.price,
                product=membership,
                user=membership.user,
                payment_method=payment_method,
                payment_source=stripe_payment.source,
                transaction_id=stripe_payment.stripe_id,
            )
            stripe_payment.status = StripePayment.Status.COMPLETE
            stripe_payment.save()

        return order

    def handle_payment_intent_succeeded(self, event):
        stripe_payment = self._get_stripe_payment(
            event["data"]["object"]["id"], StripePayment.StripeModel.PAYMENT_INTENT, suppress_exception=True
        )
        # This is OK since rely on this event for app payments and checkout.session.completed for web.
        # This means we also get this event for payments via web, but we simply ignore them.
        if not stripe_payment:
            stripe_id = event["data"]["object"]["id"]
            logger.info(f"Skipping order creation for payment_intent.succeeded event with {stripe_id=}")
            return

        self._create_order(stripe_payment)

    def handle_checkout_session_complete(self, event):
        stripe_payment = self._get_stripe_payment(
            event["data"]["object"]["id"], StripePayment.StripeModel.CHECKOUT_SESSION
        )
        self._create_order(stripe_payment)
        # TODO: Send and email with a reciept

    def post(self, request: Request):
        event = self._verify_signature(request)
        handled = False
        handlers = {
            "checkout.session.completed": self.handle_checkout_session_complete,
            "payment_intent.succeeded": self.handle_payment_intent_succeeded,
        }

        if event["type"] in handlers:
            try:
                handlers[event["type"]](event)
                handled = True
            except ValidationError as err:
                logger.warning(f"Could not handle {event['type']} event: {err}", exc_info=err)
                raise
        else:
            logger.warning(f"Received unhandled stripe event type {event['type']}")

        return Response({"handled": handled, "event_type": event["type"]})
