from django.db import models
from bills.models import Bill, LineItem


class Dispute(models.Model):
    """Represents a formal billing dispute for a set of flagged line items."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("acknowledged", "Acknowledged"),
        ("resolved", "Resolved"),
        ("denied", "Denied"),
    ]

    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="disputes")
    line_items = models.ManyToManyField(LineItem, related_name="disputes", blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    letter_content = models.TextField(blank=True, default="")
    letter_pdf = models.FileField(upload_to="disputes/", blank=True, null=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    savings_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Dispute #{self.pk} — Bill #{self.bill_id} ({self.status})"
