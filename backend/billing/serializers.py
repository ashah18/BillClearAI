from rest_framework import serializers


class SubscriptionSerializer(serializers.Serializer):
    """Read-only summary of a user's subscription plan and current usage."""

    plan = serializers.CharField()
    status = serializers.CharField()
    is_pro = serializers.BooleanField()
    current_period_end = serializers.DateTimeField(allow_null=True)
    bill_uploads_used = serializers.IntegerField()
    bill_uploads_limit = serializers.IntegerField(allow_null=True)
