import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from disputes.models import Dispute
from disputes.serializers import DisputeSerializer
from .models import Bill, ChatMessage, LineItem
from .serializers import BillSerializer, ChatMessageSerializer
from . import services

logger = logging.getLogger(__name__)


class BillListView(APIView):
    """List all bills belonging to the authenticated user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        bills = Bill.objects.filter(user=request.user)
        serializer = BillSerializer(bills, many=True)
        return Response(serializer.data)


class BillUploadView(APIView):
    """Upload a new bill file and trigger AI parsing pipeline."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"detail": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

        bill = Bill.objects.create(user=request.user, original_file=file)

        try:
            parsed_data = services.parse_bill(bill)

            # Create LineItem objects from parsed data
            for item_data in parsed_data.get("line_items", []):
                LineItem.objects.create(
                    bill=bill,
                    cpt_code=item_data.get("cpt_code"),
                    hcpcs_code=item_data.get("hcpcs_code"),
                    icd10_codes=item_data.get("icd10_codes", []),
                    description_raw=item_data.get("description_raw", ""),
                    quantity=item_data.get("quantity", 1),
                    charged_amount=item_data.get("charged_amount", 0),
                    allowed_amount=item_data.get("allowed_amount"),
                )

            services.analyze_line_items(bill)

        except Exception as exc:
            logger.exception("Error processing bill %s: %s", bill.pk, exc)
            # Bill is saved; AI analysis failed but we still return the bill
            return Response(
                {
                    "detail": "Bill uploaded but AI analysis failed. You can retry analysis.",
                    "bill": BillSerializer(bill).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(BillSerializer(bill).data, status=status.HTTP_201_CREATED)


class BillDetailView(APIView):
    """Retrieve full detail for a single bill including its line items."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        bill = get_object_or_404(Bill, pk=pk, user=request.user)
        serializer = BillSerializer(bill)
        return Response(serializer.data)


class BillAnalyzeView(APIView):
    """Re-run AI analysis on an existing bill's line items."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        bill = get_object_or_404(Bill, pk=pk, user=request.user)

        try:
            services.analyze_line_items(bill)
        except Exception as exc:
            logger.exception("Error re-analyzing bill %s: %s", bill.pk, exc)
            return Response(
                {"detail": "Analysis failed. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(BillSerializer(bill).data)


class BillDisputeView(APIView):
    """Generate a dispute letter for flagged line items on a bill."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        bill = get_object_or_404(Bill, pk=pk, user=request.user)

        line_item_ids = request.data.get("line_item_ids", [])
        if not line_item_ids:
            # Default: include all red-flagged items
            flagged_items = bill.line_items.filter(risk_level="red")
        else:
            flagged_items = bill.line_items.filter(pk__in=line_item_ids)

        if not flagged_items.exists():
            return Response(
                {"detail": "No line items selected for dispute."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        dispute = Dispute.objects.create(bill=bill, status="draft")
        dispute.line_items.set(flagged_items)

        try:
            services.generate_dispute_letter(dispute)
        except Exception as exc:
            logger.exception("Error generating dispute letter for bill %s: %s", bill.pk, exc)
            return Response(
                {"detail": "Failed to generate dispute letter."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        bill.status = "disputed"
        bill.save(update_fields=["status"])

        return Response(DisputeSerializer(dispute).data, status=status.HTTP_201_CREATED)


class ChatView(APIView):
    """Send and receive chat messages about a bill."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Return the full chat history for a bill."""
        bill = get_object_or_404(Bill, pk=pk, user=request.user)
        messages = ChatMessage.objects.filter(bill=bill)
        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data)

    def post(self, request, pk):
        """Send a user message and get an AI response."""
        bill = get_object_or_404(Bill, pk=pk, user=request.user)

        user_message = request.data.get("message", "").strip()
        if not user_message:
            return Response(
                {"detail": "Message cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Save the user message
        ChatMessage.objects.create(
            bill=bill,
            user=request.user,
            role="user",
            content=user_message,
        )

        try:
            assistant_reply = services.chat_with_bill(bill, user_message)
        except Exception as exc:
            logger.exception("Chat error for bill %s: %s", bill.pk, exc)
            return Response(
                {"detail": "AI response failed. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Save the assistant message
        assistant_msg = ChatMessage.objects.create(
            bill=bill,
            user=request.user,
            role="assistant",
            content=assistant_reply,
        )

        return Response(ChatMessageSerializer(assistant_msg).data, status=status.HTTP_201_CREATED)
