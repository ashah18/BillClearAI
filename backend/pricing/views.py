from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status


class PriceLookupView(APIView):
    """
    Public endpoint returning Medicare rate + fair-market range for a CPT/HCPCS code.

    Query parameters:
        zip  — 5-digit patient ZIP code (optional; falls back to national average)
        facility — "1" to use facility (hospital) rates; defaults to non-facility

    Response fields:
        cpt_code          — the requested code
        status            — "priced" | status code for non-priceable codes
        medicare_rate     — calculated Medicare payment (null if not priced)
        fair_market_low   — 1.5× Medicare rate (null if not priced)
        fair_market_high  — 3.0× Medicare rate (null if not priced)
        locality          — locality description used for calculation
        message           — explanation for non-priceable codes (null if priced)
        short_description — procedure description from RVU table
    """

    permission_classes = [AllowAny]

    def get(self, request, cpt_code):
        from pricing.services import calculate_medicare_rate
        from pricing.models import ProcedureRVU

        zip_code = request.query_params.get("zip", "").strip()
        facility = request.query_params.get("facility", "0") == "1"

        result = calculate_medicare_rate(cpt_code, zip_code, facility=facility)
        if result is None:
            return Response(
                {"detail": f"No pricing data found for code {cpt_code}."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Add short description from ProcedureRVU
        rvu = ProcedureRVU.objects.filter(hcpc=cpt_code.strip().upper()).first()
        result["cpt_code"] = cpt_code
        result["short_description"] = rvu.short_description if rvu else None

        return Response(result)
