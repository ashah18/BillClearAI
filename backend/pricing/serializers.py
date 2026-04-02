from rest_framework import serializers
from .models import CPTPriceCache


class CPTPriceSerializer(serializers.ModelSerializer):
    """Serializer for CPT code price cache entries."""

    class Meta:
        model = CPTPriceCache
        fields = ["cpt_code", "description", "national_average", "created_at"]
