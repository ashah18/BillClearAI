from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Dispute
from .serializers import DisputeSerializer


class DisputeDetailView(APIView):
    """Retrieve the detail of a specific dispute for a bill."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk, dispute_id):
        dispute = get_object_or_404(
            Dispute,
            pk=dispute_id,
            bill__pk=pk,
            bill__user=request.user,
        )
        serializer = DisputeSerializer(dispute)
        return Response(serializer.data)
