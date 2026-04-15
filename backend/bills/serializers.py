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
    potential_savings = serializers.SerializerMethodField()
    confirmed_savings = serializers.SerializerMethodField()

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
            "potential_savings",
            "confirmed_savings",
        ]
        read_only_fields = ["id", "created_at", "original_file"]

    def get_potential_savings(self, obj):
        from .services import calculate_bill_savings
        from disputes.models import Dispute

        resolved_denied = Dispute.objects.filter(bill=obj, status__in=["resolved", "denied"])

        # Exclude handled line items from the remaining actionable savings calculation.
        handled_ids = set(resolved_denied.values_list("line_items__id", flat=True))
        handled_ids.discard(None)
        eligible = [item for item in obj.line_items.all() if item.id not in handled_ids]

        # Add confirmed savings back so potential savings reflects all identified
        # savings — both already recovered and still actionable.
        confirmed = sum(
            float(d.savings_amount)
            for d in resolved_denied.filter(status="resolved")
            if d.savings_amount is not None
        )
        return round(calculate_bill_savings(eligible) + confirmed, 2)

    def get_confirmed_savings(self, obj):
        from disputes.models import Dispute

        resolved = Dispute.objects.filter(bill=obj, status="resolved")
        total = sum(
            float(d.savings_amount) for d in resolved if d.savings_amount is not None
        )
        return round(total, 2)


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages associated with a bill."""

    class Meta:
        model = ChatMessage
        fields = ["id", "role", "content", "created_at"]
        read_only_fields = ["id", "role", "created_at"]
