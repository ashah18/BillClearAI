from rest_framework import serializers
from .models import Bill, ChatMessage, LineItem


class LineItemSerializer(serializers.ModelSerializer):
    """Serializer for individual bill line items."""

    class Meta:
        model = LineItem
        fields = [
            "id",
            "cpt_code",
            "hcpcs_code",
            "icd10_codes",
            "description_raw",
            "description_plain",
            "quantity",
            "charged_amount",
            "allowed_amount",
            "regional_average",
            "risk_level",
            "error_type",
            "flag_explanation",
            "confidence",
        ]


class BillSerializer(serializers.ModelSerializer):
    """Serializer for bill objects, optionally including nested line items."""

    line_items = LineItemSerializer(many=True, read_only=True)

    class Meta:
        model = Bill
        fields = [
            "id",
            "provider_name",
            "facility_type",
            "date_of_service",
            "total_charged",
            "total_allowed",
            "patient_responsibility",
            "status",
            "error_message",
            "parse_status",
            "parse_message",
            "original_file",
            "created_at",
            "line_items",
        ]
        read_only_fields = ["id", "created_at", "original_file"]


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages associated with a bill."""

    class Meta:
        model = ChatMessage
        fields = ["id", "role", "content", "created_at"]
        read_only_fields = ["id", "role", "created_at"]
