from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver


class Bill(models.Model):
    """Represents a single medical bill uploaded by a user."""

    FACILITY_TYPE_CHOICES = [
        ("hospital", "Hospital"),
        ("clinic", "Clinic"),
        ("lab", "Lab"),
        ("pharmacy", "Pharmacy"),
        ("specialist", "Specialist"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("new", "New"),
        ("reviewed", "Reviewed"),
        ("disputed", "Disputed"),
        ("resolved", "Resolved"),
        ("failed", "Failed"),
    ]

    PARSE_STATUS_CHOICES = [
        ("ok", "OK"),
        ("warning", "Warning"),
        ("error", "Error"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bills",
    )
    provider_name = models.CharField(max_length=255, blank=True, default="")
    facility_type = models.CharField(
        max_length=50,
        choices=FACILITY_TYPE_CHOICES,
        default="other",
    )
    date_of_service = models.DateField(null=True, blank=True)
    total_charged = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_allowed = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    patient_responsibility = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    parse_status = models.CharField(max_length=20, choices=PARSE_STATUS_CHOICES, default="ok")
    parse_message = models.TextField(blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    original_file = models.FileField(upload_to="bills/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Bill #{self.pk} — {self.provider_name or 'Unknown'} ({self.user.email})"


class LineItem(models.Model):
    """Represents a single line item on a medical bill."""

    RISK_LEVEL_CHOICES = [
        ("green", "Green"),
        ("yellow", "Yellow"),
        ("red", "Red"),
    ]

    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="line_items")
    cpt_code = models.CharField(max_length=10, blank=True, null=True)
    hcpcs_code = models.CharField(max_length=10, blank=True, null=True)
    icd10_codes = models.JSONField(default=list, blank=True)
    description_raw = models.TextField(blank=True, default="")
    description_plain = models.TextField(blank=True, default="")
    quantity = models.PositiveIntegerField(default=1)
    charged_amount = models.DecimalField(max_digits=10, decimal_places=2)
    allowed_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    regional_average = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, default="green")
    error_type = models.CharField(max_length=50, blank=True, null=True)
    flag_explanation = models.TextField(blank=True, default="")
    confidence = models.FloatField(default=1.0)

    def __str__(self):
        code = self.cpt_code or self.hcpcs_code or "N/A"
        return f"LineItem {code} — ${self.charged_amount}"


class ChatMessage(models.Model):
    """Stores conversation messages between a user and the AI about a specific bill."""

    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
    ]

    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="chat_messages")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_messages",
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.role}] {self.content[:60]}"


@receiver(post_delete, sender=Bill)
def delete_bill_file_on_delete(sender, instance, **kwargs):
    """Delete the original bill file from storage when the Bill record is deleted."""
    if instance.original_file:
        instance.original_file.delete(save=False)
