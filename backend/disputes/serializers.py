from rest_framework import serializers
from bills.serializers import LineItemSerializer
from .models import Dispute


class DisputeSerializer(serializers.ModelSerializer):
    """Serializer for dispute objects including the generated letter content."""

    line_items = LineItemSerializer(many=True, read_only=True)

    class Meta:
        model = Dispute
        fields = [
            "id",
            "bill",
            "line_items",
            "status",
            "letter_content",
            "letter_pdf",
            "sent_at",
            "resolved_at",
            "savings_amount",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "letter_content", "letter_pdf"]
