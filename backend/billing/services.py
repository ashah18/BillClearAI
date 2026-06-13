import logging
from datetime import datetime, timezone as dt_timezone

import stripe
from django.conf import settings
from django.utils import timezone

from .models import BillUploadUsage, Subscription

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

# Free tier limits
FREE_BILL_UPLOAD_LIMIT = 3
FREE_CHAT_MESSAGE_LIMIT = 5

# Maps Stripe subscription statuses to our Subscription.STATUS_CHOICES
_STRIPE_STATUS_MAP = {
    "active": "active",
    "trialing": "active",
    "past_due": "past_due",
}


def get_or_create_subscription(user):
    """Return the user's Subscription, creating a default free one if missing."""
    subscription, _ = Subscription.objects.get_or_create(user=user)
    return subscription


def user_is_pro(user):
    """True if the user currently has an active Pro subscription."""
    return get_or_create_subscription(user).is_pro


def current_month():
    """Return the first day of the current calendar month."""
    return timezone.localdate().replace(day=1)


def get_current_month_usage(user):
    """Return (creating if needed) this user's BillUploadUsage row for the current month."""
    usage, _ = BillUploadUsage.objects.get_or_create(
        user=user, month=current_month(), defaults={"count": 0}
    )
    return usage


def increment_bill_upload_usage(user):
    """Increment and return this user's bill upload count for the current month."""
    usage = get_current_month_usage(user)
    usage.count += 1
    usage.save(update_fields=["count"])
    return usage


def _to_datetime(timestamp):
    """Convert a Stripe unix timestamp to an aware UTC datetime (or None)."""
    if not timestamp:
        return None
    return datetime.fromtimestamp(timestamp, tz=dt_timezone.utc)


def _field(stripe_object, key, default=None):
    """Read a field from a Stripe SDK object.

    Stripe's StripeObject no longer subclasses dict, so it has no .get() —
    fields are accessed via attributes, which __getattr__ resolves from the
    underlying data (raising AttributeError if absent).
    """
    return getattr(stripe_object, key, default)


def create_checkout_session(user, success_url, cancel_url):
    """Create a Stripe Checkout session for the Pro subscription."""
    subscription = get_or_create_subscription(user)

    params = {
        "mode": "subscription",
        "line_items": [{"price": settings.STRIPE_PRO_PRICE_ID, "quantity": 1}],
        "success_url": success_url,
        "cancel_url": cancel_url,
        "client_reference_id": str(user.id),
    }
    if subscription.stripe_customer_id:
        params["customer"] = subscription.stripe_customer_id
    else:
        params["customer_email"] = user.email

    return stripe.checkout.Session.create(**params)


def create_portal_session(user, return_url):
    """Create a Stripe Customer Portal session, or None if the user has no Stripe customer yet."""
    subscription = get_or_create_subscription(user)
    if not subscription.stripe_customer_id:
        return None
    return stripe.billing_portal.Session.create(
        customer=subscription.stripe_customer_id,
        return_url=return_url,
    )


def handle_checkout_completed(session):
    """checkout.session.completed — activate the user's Pro subscription."""
    from users.models import User

    user_id = _field(session, "client_reference_id")
    if not user_id:
        logger.warning("[BILLING] checkout.session.completed missing client_reference_id")
        return

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.warning("[BILLING] checkout.session.completed: no user with id=%s", user_id)
        return

    subscription = get_or_create_subscription(user)
    subscription.stripe_customer_id = _field(session, "customer") or subscription.stripe_customer_id
    stripe_subscription_id = _field(session, "subscription")
    subscription.stripe_subscription_id = stripe_subscription_id or subscription.stripe_subscription_id
    subscription.plan = "pro"
    subscription.status = "active"

    if stripe_subscription_id:
        stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
        subscription.current_period_end = _to_datetime(_field(stripe_sub, "current_period_end"))

    subscription.save()
    logger.info("[BILLING] Activated Pro subscription for %s", user.email)


def handle_subscription_updated(stripe_subscription):
    """customer.subscription.updated — sync status and current_period_end."""
    subscription_id = _field(stripe_subscription, "id")
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
    except Subscription.DoesNotExist:
        logger.warning("[BILLING] subscription.updated: no local subscription for %s", subscription_id)
        return

    stripe_status = _field(stripe_subscription, "status")
    subscription.status = _STRIPE_STATUS_MAP.get(stripe_status, "canceled")
    subscription.current_period_end = _to_datetime(_field(stripe_subscription, "current_period_end"))
    if subscription.status == "active":
        subscription.plan = "pro"
    subscription.save()
    logger.info("[BILLING] Synced subscription %s -> status=%s", subscription_id, subscription.status)


def handle_subscription_deleted(stripe_subscription):
    """customer.subscription.deleted — downgrade the user to Free."""
    subscription_id = _field(stripe_subscription, "id")
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
    except Subscription.DoesNotExist:
        logger.warning("[BILLING] subscription.deleted: no local subscription for %s", subscription_id)
        return

    subscription.plan = "free"
    subscription.status = "canceled"
    subscription.current_period_end = None
    subscription.save()
    logger.info("[BILLING] Downgraded subscription %s to free", subscription_id)
