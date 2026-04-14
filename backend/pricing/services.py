"""
Pricing services for BillClear AI.

Implements the CMS Medicare Physician Fee Schedule payment formula to calculate
fair-market rates for CPT/HCPCS procedure codes by geographic region.

Formula:
    Non-Facility Rate = [(Work RVU × Work GPCI) + (Non-Fac PE RVU × PE GPCI) + (MP RVU × MP GPCI)] × CF
    Facility Rate    = [(Work RVU × Work GPCI) + (Fac PE RVU × PE GPCI)     + (MP RVU × MP GPCI)] × CF

Where CF = $33.4009 (2026 non-QP conversion factor).
"""

import logging
from decimal import Decimal, ROUND_HALF_UP

from pricing.models import LocalityGPCI, ProcedureRVU, ZipToLocality

logger = logging.getLogger(__name__)

DEFAULT_YEAR = 2026
NATIONAL_LOCALITY = "0000000"  # CMS "NATIONAL" locality used as fallback

# proc_stat values that have real PFS pricing
PRICEABLE_STATS = {"A", "R", "T"}

# Human-readable messages for non-priceable status codes
STATUS_MESSAGES = {
    "X": "Priced under Clinical Lab Fee Schedule — PFS comparison not available.",
    "B": "This charge may be bundled with another procedure.",
    "C": "Carrier-priced — no national rate available.",
    "E": "Excluded from PFS.",
    "I": "Not valid for Medicare purposes.",
    "M": "Measurement code — not separately priced.",
    "N": "Non-covered by Medicare.",
    "P": "Bundled/excluded code.",
}


def calculate_medicare_rate(
    cpt_code: str,
    zip_code: str,
    facility: bool = False,
    year: int = DEFAULT_YEAR,
) -> dict | None:
    """
    Calculate the Medicare Physician Fee Schedule rate for a CPT/HCPCS code
    at the location indicated by the patient's ZIP code.

    Returns a dict with:
        status          — "priced" | "clfs" | "bundled" | "not_found" | (other status msg key)
        medicare_rate   — calculated dollar amount (Decimal), only when status="priced"
        fair_market_low — 1.5× Medicare rate (Decimal), only when status="priced"
        fair_market_high— 3.0× Medicare rate (Decimal), only when status="priced"
        locality        — locality description string (e.g. "SAN FRANCISCO-OAKLAND-BERKELEY")
        message         — human-readable explanation for non-priced codes

    Returns None if the CPT code is not in the database at all.

    Args:
        cpt_code: CPT or HCPCS code string (e.g. "99214", "G0008").
        zip_code: Patient 5-digit ZIP code string.
        facility: True for hospital/ASC procedures (uses facility PE RVU).
        year: Fee schedule year (default: 2026).
    """
    if not cpt_code:
        return None

    cpt_code = cpt_code.strip().upper()
    zip_code = (zip_code or "").strip()[:5]

    # ── 1. Look up RVUs ───────────────────────────────────────────────────────
    # Try the base code (no modifier) first; fall back to any modifier variant.
    rvu = (
        ProcedureRVU.objects.filter(hcpc=cpt_code, modifier="", year=year).first()
        or ProcedureRVU.objects.filter(hcpc=cpt_code, year=year).first()
    )
    if rvu is None:
        logger.debug("CPT %s not found in ProcedureRVU for year %s", cpt_code, year)
        return None

    # ── 2. Check proc_stat ────────────────────────────────────────────────────
    if rvu.proc_stat not in PRICEABLE_STATS:
        msg = STATUS_MESSAGES.get(rvu.proc_stat, f"Not priced under PFS (status: {rvu.proc_stat}).")
        return {
            "status": rvu.proc_stat,
            "message": msg,
            "medicare_rate": None,
            "fair_market_low": None,
            "fair_market_high": None,
            "locality": None,
        }

    # ── 3. Resolve ZIP → carrier + locality_code ─────────────────────────────
    gpci = None
    locality_desc = None

    if zip_code:
        try:
            zip_row = ZipToLocality.objects.get(zip_code=zip_code, year=year)
            full_locality = zip_row.carrier + zip_row.locality_code
            gpci = LocalityGPCI.objects.filter(locality=full_locality, year=year).first()
            if gpci:
                locality_desc = gpci.loc_description
        except ZipToLocality.DoesNotExist:
            logger.debug("ZIP %s not found in ZipToLocality for year %s", zip_code, year)

    # ── 4. Fall back to national GPCI if ZIP lookup failed ───────────────────
    if gpci is None:
        gpci = LocalityGPCI.objects.filter(locality=NATIONAL_LOCALITY, year=year).first()
        if gpci:
            locality_desc = "National Average"

    if gpci is None:
        logger.warning("No GPCI data found for year %s (not even national)", year)
        return None

    # ── 5. Apply Medicare payment formula ─────────────────────────────────────
    pe_rvu = float(rvu.full_fac_pe if facility else rvu.full_nfac_pe)
    work_component = float(rvu.rvu_work) * float(gpci.gpci_work)
    pe_component = pe_rvu * float(gpci.gpci_pe)
    mp_component = float(rvu.rvu_mp) * float(gpci.gpci_mp)
    rate = (work_component + pe_component + mp_component) * float(rvu.conv_fact)

    medicare_rate = Decimal(str(rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    fair_low = (medicare_rate * Decimal("1.5")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    fair_high = (medicare_rate * Decimal("3.0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "status": "priced",
        "medicare_rate": medicare_rate,
        "fair_market_low": fair_low,
        "fair_market_high": fair_high,
        "locality": locality_desc,
        "message": None,
    }


def enrich_line_items_with_pricing(bill_instance, year: int = DEFAULT_YEAR) -> None:
    """
    Look up the Medicare rate for each line item on a bill and set regional_average.
    Also escalates risk_level based on how far the charged amount exceeds the Medicare rate:

        ≤ 3× Medicare  → keep existing risk level (green is within fair-market range)
        3–5× Medicare  → yellow (above fair-market high, warrants review)
        > 5× Medicare  → red (likely error or extreme overcharge)

    Uses the patient's ZIP code for geographic adjustment. Falls back to the
    national GPCI if the ZIP is not in the database.

    Args:
        bill_instance: A bills.models.Bill instance with related LineItem objects.
        year: Fee schedule year (default: DEFAULT_YEAR).
    """
    zip_code = (getattr(bill_instance.user, "zip_code", None) or "").strip()
    is_facility = bill_instance.facility_type == "hospital"

    line_items = list(bill_instance.line_items.all())
    updated = []

    for item in line_items:
        code = (item.cpt_code or item.hcpcs_code or "").strip()
        if not code:
            continue

        result = calculate_medicare_rate(code, zip_code, facility=is_facility, year=year)
        if result is None:
            continue  # code not in database

        if result["status"] != "priced":
            # Non-priceable code: annotate flag_explanation if not already set
            if not item.flag_explanation and result.get("message"):
                item.flag_explanation = result["message"]
                item.save(update_fields=["flag_explanation"])
            continue

        medicare_rate = result["medicare_rate"]
        item.regional_average = medicare_rate

        # Risk escalation based on charged-to-Medicare ratio
        charged = float(item.charged_amount)
        rate = float(medicare_rate)
        if rate > 0:
            ratio = charged / rate
            if ratio > 5.0 and item.risk_level != "red":
                item.risk_level = "red"
                if not item.flag_explanation:
                    item.flag_explanation = (
                        f"You were charged ${charged:,.2f} — more than 5× the Medicare "
                        f"rate (${rate:,.2f}) for this service. This is well above the "
                        f"typical commercial range (${float(result['fair_market_low']):,.2f}–"
                        f"${float(result['fair_market_high']):,.2f})."
                    )
            elif ratio > 3.0 and item.risk_level == "green":
                item.risk_level = "yellow"
                if not item.flag_explanation:
                    item.flag_explanation = (
                        f"You were charged ${charged:,.2f} — above the typical commercial "
                        f"range of ${float(result['fair_market_low']):,.2f}–"
                        f"${float(result['fair_market_high']):,.2f} "
                        f"(Medicare rate: ${rate:,.2f})."
                    )

        updated.append(item)

    if updated:
        for item in updated:
            item.save(update_fields=["regional_average", "risk_level", "flag_explanation"])

    logger.info(
        "Enriched %d/%d line items with CMS pricing for bill %s",
        len(updated),
        len(line_items),
        bill_instance.pk,
    )
