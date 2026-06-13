from django.conf import settings
from django.db import models


class Subscription(models.Model):
    """Tracks a user's BillClear AI plan and Stripe billing state."""

    PLAN_CHOICES = [
        ("free", "Free"),
        ("pro", "Pro"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("canceled", "Canceled"),
        ("past_due", "Past Due"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    stripe_customer_id = models.CharField(max_length=255, blank=True, default="")
    stripe_subscription_id = models.CharField(max_length=255, blank=True, default="")
    plan = models.CharField(max_length=10, choices=PLAN_CHOICES, default="free")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    current_period_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_pro(self):
        return self.plan == "pro" and self.status == "active"

    def __str__(self):
        return f"{self.user.email} — {self.plan} ({self.status})"


class BillUploadUsage(models.Model):
    """Tracks how many bills a user has uploaded in a given calendar month."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bill_upload_usages",
    )
    month = models.DateField()
    count = models.IntegerField(default=0)

    class Meta:
        unique_together = ("user", "month")

    def __str__(self):
        return f"{self.user.email} — {self.month:%Y-%m}: {self.count}"
