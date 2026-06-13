import logging

import stripe
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .serializers import SubscriptionSerializer

logger = logging.getLogger(__name__)


class SubscriptionStatusView(APIView):
    """Return the authenticated user's current plan, status, and usage this month."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        subscription = services.get_or_create_subscription(request.user)
        usage = services.get_current_month_usage(request.user)
        data = {
            "plan": subscription.plan,
            "status": subscription.status,
            "is_pro": subscription.is_pro,
            "current_period_end": subscription.current_period_end,
            "bill_uploads_used": usage.count,
            "bill_uploads_limit": None if subscription.is_pro else services.FREE_BILL_UPLOAD_LIMIT,
        }
        return Response(SubscriptionSerializer(data).data)


class CreateCheckoutSessionView(APIView):
    """Create a Stripe Checkout session for upgrading to Pro."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        subscription = services.get_or_create_subscription(request.user)
        if subscription.is_pro:
            return Response(
                {"detail": "You already have an active Pro subscription."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        success_url = f"{settings.FRONTEND_URL}/upgrade?checkout=success"
        cancel_url = f"{settings.FRONTEND_URL}/upgrade?checkout=canceled"

        try:
            session = services.create_checkout_session(request.user, success_url, cancel_url)
        except stripe.error.StripeError:
            logger.exception("[BILLING] Failed to create checkout session for %s", request.user.email)
            return Response(
                {"detail": "Could not start checkout. Please try again."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"url": session.url})


class CreatePortalSessionView(APIView):
    """Create a Stripe Customer Portal session for managing an existing subscription."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        return_url = f"{settings.FRONTEND_URL}/profile"

        try:
            portal_session = services.create_portal_session(request.user, return_url)
        except stripe.error.StripeError:
            logger.exception("[BILLING] Failed to create portal session for %s", request.user.email)
            return Response(
                {"detail": "Could not open the billing portal. Please try again."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if portal_session is None:
            return Response(
                {"detail": "No billing account found for this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"url": portal_session.url})


class StripeWebhookView(APIView):
    """Receives and verifies Stripe webhook events to sync subscription state."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        except (ValueError, stripe.error.SignatureVerificationError):
            logger.warning("[BILLING] Webhook signature verification failed")
            return Response(status=status.HTTP_400_BAD_REQUEST)

        event_type = event["type"]
        data_object = event["data"]["object"]
        logger.info("[BILLING] Received webhook event: %s", event_type)

        if event_type == "checkout.session.completed":
            services.handle_checkout_completed(data_object)
        elif event_type == "customer.subscription.updated":
            services.handle_subscription_updated(data_object)
        elif event_type == "customer.subscription.deleted":
            services.handle_subscription_deleted(data_object)

        return Response(status=status.HTTP_200_OK)
