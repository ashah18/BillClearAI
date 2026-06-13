import logging
import os

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from billing.services import (
    FREE_BILL_UPLOAD_LIMIT,
    FREE_CHAT_MESSAGE_LIMIT,
    get_current_month_usage,
    increment_bill_upload_usage,
    user_is_pro,
)
from disputes.models import Dispute
from disputes.serializers import DisputeSerializer
from .models import Bill, ChatMessage, LineItem
from .serializers import BillSerializer, ChatMessageSerializer
from .throttles import BillUploadThrottle, ChatThrottle, DisputeThrottle, ReanalyzeThrottle
from . import services

logger = logging.getLogger(__name__)

# File upload constraints
_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png", "application/pdf"}


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
    throttle_classes = [BillUploadThrottle]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"detail": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Enforce the free-tier monthly bill analysis limit (Pro is unlimited)
        if not user_is_pro(request.user):
            usage = get_current_month_usage(request.user)
            if usage.count >= FREE_BILL_UPLOAD_LIMIT:
                return Response(
                    {
                        "detail": (
                            f"You've used your {FREE_BILL_UPLOAD_LIMIT} free bill analyses this month. "
                            "Upgrade to Pro for unlimited."
                        ),
                        "upgrade_required": True,
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Validate file size
        if file.size > _MAX_UPLOAD_BYTES:
            return Response(
                {"detail": "File too large. Maximum allowed size is 10 MB."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate file extension
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in _ALLOWED_EXTENSIONS:
            return Response(
                {"detail": "Unsupported file type. Please upload a JPG, PNG, or PDF."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate MIME type reported by the client
        if file.content_type not in _ALLOWED_CONTENT_TYPES:
            return Response(
                {"detail": "Unsupported file type. Please upload a JPG, PNG, or PDF."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bill = Bill.objects.create(user=request.user, original_file=file)

        if not user_is_pro(request.user):
            increment_bill_upload_usage(request.user)

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
                    confidence=float(item_data.get("confidence") or 1.0),
                )

            services.analyze_line_items(bill)

        except Exception as exc:
            logger.exception("Error processing bill %s: %s", bill.pk, exc)
            bill.refresh_from_db()
            # parse_bill raises after setting status=failed; any other exception needs the same
            if bill.status != "failed":
                bill.status = "failed"
                bill.error_message = (
                    "We had trouble reading this bill. This could be because the image is "
                    "blurry, at an angle, or doesn't contain itemized charges. Try uploading "
                    "a clearer photo or a PDF version of your itemized bill."
                )
                bill.save(update_fields=["status", "error_message"])
            return Response(BillSerializer(bill).data, status=status.HTTP_201_CREATED)

        return Response(BillSerializer(bill).data, status=status.HTTP_201_CREATED)


class BillDetailView(APIView):
    """Retrieve or delete a single bill."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        bill = get_object_or_404(Bill, pk=pk, user=request.user)
        serializer = BillSerializer(bill)
        return Response(serializer.data)

    def delete(self, request, pk):
        bill = get_object_or_404(Bill, pk=pk, user=request.user)
        bill.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BillAnalyzeView(APIView):
    """Re-run AI analysis on an existing bill's line items."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [ReanalyzeThrottle]

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
    throttle_classes = [DisputeThrottle]

    def post(self, request, pk):
        # Dispute letter generation is a Pro-only feature
        if not user_is_pro(request.user):
            return Response(
                {
                    "detail": "Dispute letter generation requires a Pro subscription",
                    "upgrade_required": True,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

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
    throttle_classes = [ChatThrottle]

    def get(self, request, pk):
        """Return the full chat history for a bill."""
        bill = get_object_or_404(Bill, pk=pk, user=request.user)
        messages = ChatMessage.objects.filter(bill=bill)
        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data)

    def post(self, request, pk):
        """Send a user message and get an AI response."""
        bill = get_object_or_404(Bill, pk=pk, user=request.user)

        # Enforce the free-tier chat message limit per bill (Pro is unlimited)
        if not user_is_pro(request.user):
            user_message_count = ChatMessage.objects.filter(bill=bill, role="user").count()
            if user_message_count >= FREE_CHAT_MESSAGE_LIMIT:
                return Response(
                    {
                        "detail": (
                            f"You've used your {FREE_CHAT_MESSAGE_LIMIT} free chat messages for this bill. "
                            "Upgrade to Pro for unlimited chat."
                        ),
                        "upgrade_required": True,
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

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
