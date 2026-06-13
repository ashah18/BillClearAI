from django.urls import path
from .views import (
    CreateCheckoutSessionView,
    CreatePortalSessionView,
    StripeWebhookView,
    SubscriptionStatusView,
)

urlpatterns = [
    path("subscription/", SubscriptionStatusView.as_view(), name="billing-subscription"),
    path("create-checkout-session/", CreateCheckoutSessionView.as_view(), name="billing-create-checkout-session"),
    path("create-portal-session/", CreatePortalSessionView.as_view(), name="billing-create-portal-session"),
    path("webhook/", StripeWebhookView.as_view(), name="billing-webhook"),
]
