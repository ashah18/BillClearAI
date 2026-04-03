from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bills.models import Bill
from .models import Dispute
from .serializers import DisputeSerializer


class DisputeListView(APIView):
    """List all disputes for a specific bill."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        bill = get_object_or_404(Bill, pk=pk, user=request.user)
        disputes = Dispute.objects.filter(bill=bill)
        serializer = DisputeSerializer(disputes, many=True)
        return Response(serializer.data)


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


class DisputeDownloadView(APIView):
    """Download the dispute letter as a .docx file."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk, dispute_id):
        dispute = get_object_or_404(
            Dispute,
            pk=dispute_id,
            bill__pk=pk,
            bill__user=request.user,
        )
        if not dispute.letter_pdf:
            return Response(
                {"detail": "Document not yet generated."},
                status=status.HTTP_404_NOT_FOUND,
            )
        file_handle = dispute.letter_pdf.open("rb")
        response = FileResponse(
            file_handle,
            content_type=(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ),
        )
        response["Content-Disposition"] = (
            f'attachment; filename="dispute-letter-{dispute_id}.docx"'
        )
        return response
