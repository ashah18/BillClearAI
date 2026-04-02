"""
Bill processing services for BillClear AI.

This module contains all AI-powered logic for parsing, analyzing, and chatting
about medical bills using the Anthropic Claude API.
"""

import json
import base64
import logging

import anthropic
from django.conf import settings

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"


def _get_client() -> anthropic.Anthropic:
    """Return a configured Anthropic client."""
    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def parse_bill(bill_instance) -> dict:
    """
    Parse a medical bill file using Claude's vision capability.

    Sends the uploaded bill image/PDF to Claude with a structured extraction
    prompt. Returns a dict of extracted data and updates the Bill model fields.

    Args:
        bill_instance: A bills.models.Bill instance with an uploaded original_file.

    Returns:
        A dict containing the parsed bill data as extracted by Claude.
    """
    client = _get_client()

    # Read the uploaded file and encode it for the API
    bill_instance.original_file.open("rb")
    file_bytes = bill_instance.original_file.read()
    bill_instance.original_file.close()

    file_name = bill_instance.original_file.name.lower()
    if file_name.endswith(".pdf"):
        media_type = "application/pdf"
    elif file_name.endswith(".png"):
        media_type = "image/png"
    elif file_name.endswith((".jpg", ".jpeg")):
        media_type = "image/jpeg"
    else:
        media_type = "image/jpeg"

    encoded_file = base64.standard_b64encode(file_bytes).decode("utf-8")

    system_prompt = """You are a medical billing expert. Your task is to extract structured data
from a medical bill or Explanation of Benefits (EOB) document.

Return ONLY valid JSON with this exact structure:
{
  "provider_name": "string",
  "facility_type": "hospital|clinic|lab|pharmacy|specialist|other",
  "date_of_service": "YYYY-MM-DD or null",
  "total_charged": number or null,
  "total_allowed": number or null,
  "patient_responsibility": number or null,
  "line_items": [
    {
      "cpt_code": "5-digit string or null",
      "hcpcs_code": "string or null",
      "icd10_codes": ["list", "of", "codes"],
      "description_raw": "exact text from bill",
      "quantity": integer,
      "charged_amount": number,
      "allowed_amount": number or null
    }
  ]
}

Rules:
- CPT codes must be exactly 5 digits. Set to null if not clearly identifiable.
- Extract ALL line items visible on the bill.
- If a field is not present, use null.
- Do not include any text outside the JSON object."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": encoded_file,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Please extract all billing information from this medical bill.",
                    },
                ],
            }
        ],
    )

    raw_text = response.content[0].text.strip()

    # Strip markdown code fences if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1]
        raw_text = raw_text.rsplit("```", 1)[0]

    parsed_data = json.loads(raw_text)

    # Update bill instance fields
    bill_instance.provider_name = parsed_data.get("provider_name") or ""
    bill_instance.facility_type = parsed_data.get("facility_type") or "other"
    bill_instance.total_charged = parsed_data.get("total_charged")
    bill_instance.total_allowed = parsed_data.get("total_allowed")
    bill_instance.patient_responsibility = parsed_data.get("patient_responsibility")

    date_str = parsed_data.get("date_of_service")
    if date_str:
        from datetime import date
        try:
            bill_instance.date_of_service = date.fromisoformat(date_str)
        except ValueError:
            bill_instance.date_of_service = None

    bill_instance.save()

    return parsed_data


def analyze_line_items(bill_instance) -> None:
    """
    Analyze line items on a bill for errors, overcharges, and risk levels.

    Uses Claude to translate CPT/HCPCS codes into plain English, detect
    potential billing errors (duplicates, upcoding, unbundling, balance billing),
    and assign a risk level (green/yellow/red) to each line item.

    Args:
        bill_instance: A bills.models.Bill instance with related LineItem objects.
    """
    client = _get_client()

    line_items = list(bill_instance.line_items.all())
    if not line_items:
        logger.warning("No line items found for bill %s", bill_instance.pk)
        return

    items_data = [
        {
            "id": item.pk,
            "cpt_code": item.cpt_code,
            "hcpcs_code": item.hcpcs_code,
            "description_raw": item.description_raw,
            "quantity": item.quantity,
            "charged_amount": float(item.charged_amount),
            "allowed_amount": float(item.allowed_amount) if item.allowed_amount else None,
        }
        for item in line_items
    ]

    system_prompt = """You are a medical billing auditor with expertise in CPT codes, HCPCS codes,
and common medical billing errors.

Analyze the provided line items and return ONLY valid JSON with this structure:
{
  "line_items": [
    {
      "id": integer,
      "description_plain": "plain English explanation of what this charge is for",
      "risk_level": "green|yellow|red",
      "error_type": "duplicate|unbundled|upcoded|balance_billing|null"
    }
  ]
}

Risk level guide:
- green: Charge appears reasonable and correct
- yellow: Charge warrants review (unusual quantity, slightly high, unclear code)
- red: Likely error or overcharge (duplicate, known upcoding pattern, balance billing)

Error types:
- duplicate: Same service billed more than once
- unbundled: Services that should be billed together are split to inflate cost
- upcoded: Service billed at a higher complexity/cost than documented
- balance_billing: Patient charged more than the allowed amount
- null: No apparent error

Return null for error_type when risk_level is green."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": json.dumps({"line_items": items_data}),
            }
        ],
    )

    raw_text = response.content[0].text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1]
        raw_text = raw_text.rsplit("```", 1)[0]

    analysis = json.loads(raw_text)

    # Build a lookup map for quick access
    analysis_map = {item["id"]: item for item in analysis.get("line_items", [])}

    for item in line_items:
        if item.pk in analysis_map:
            result = analysis_map[item.pk]
            item.description_plain = result.get("description_plain", "")
            item.risk_level = result.get("risk_level", "green")
            item.error_type = result.get("error_type") or None
            item.save()

    # Update bill status from new to reviewed
    if bill_instance.status == "new":
        bill_instance.status = "reviewed"
        bill_instance.save(update_fields=["status"])


def generate_dispute_letter(dispute_instance) -> str:
    """
    Generate a formal dispute letter for a set of flagged line items.

    Uses Claude to compose a professional, patient-facing dispute letter
    suitable for submission to the healthcare provider or insurance company.
    The letter content is saved to the dispute instance.

    Args:
        dispute_instance: A disputes.models.Dispute instance with related line items.

    Returns:
        The generated dispute letter as a string.
    """
    client = _get_client()

    bill = dispute_instance.bill
    line_items = list(dispute_instance.line_items.all())

    items_summary = "\n".join(
        f"- Code: {item.cpt_code or item.hcpcs_code or 'N/A'}, "
        f"Description: {item.description_plain or item.description_raw}, "
        f"Charged: ${item.charged_amount}, "
        f"Issue: {item.error_type or 'overcharge'}"
        for item in line_items
    )

    system_prompt = """You are a patient advocate specializing in medical billing disputes.
Write a formal, professional dispute letter that a patient can send to their healthcare provider
or insurance company. The letter should be clear, factual, and reference the specific billing issues.
Include placeholders like [PATIENT NAME] and [DATE] where appropriate."""

    user_message = f"""Please write a dispute letter for the following medical bill issues:

Provider: {bill.provider_name or "Healthcare Provider"}
Date of Service: {bill.date_of_service or "Unknown"}
Total Charged: ${bill.total_charged or "Unknown"}

Disputed Line Items:
{items_summary}

Write a complete, ready-to-send dispute letter."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    letter_content = response.content[0].text.strip()

    dispute_instance.letter_content = letter_content
    dispute_instance.save(update_fields=["letter_content"])

    return letter_content


def chat_with_bill(bill_instance, user_message: str) -> str:
    """
    Respond to a user's question about a specific medical bill.

    Provides context about the bill's line items and any identified issues,
    then answers the user's question in plain, helpful language.

    Args:
        bill_instance: A bills.models.Bill instance to provide context.
        user_message: The user's question or message as a string.

    Returns:
        The assistant's response as a string.
    """
    client = _get_client()

    line_items = list(bill_instance.line_items.all())

    items_context = "\n".join(
        f"- {item.description_plain or item.description_raw}: "
        f"${item.charged_amount} (Risk: {item.risk_level}"
        + (f", Issue: {item.error_type}" if item.error_type else "")
        + ")"
        for item in line_items
    )

    # Fetch conversation history
    from bills.models import ChatMessage

    history = ChatMessage.objects.filter(bill=bill_instance).order_by("created_at")
    conversation = [
        {"role": msg.role, "content": msg.content}
        for msg in history
    ]

    system_prompt = f"""You are a helpful medical billing assistant for BillClear AI.
You help patients understand their medical bills, identify potential errors, and take action.

Here is the context for the current bill:
- Provider: {bill_instance.provider_name or "Unknown"}
- Date of Service: {bill_instance.date_of_service or "Unknown"}
- Total Charged: ${bill_instance.total_charged or "Unknown"}
- Status: {bill_instance.status}

Line Items:
{items_context if items_context else "No line items have been extracted yet."}

Answer questions clearly and in plain language. If you identify potential billing errors,
explain them simply. Always recommend the patient verify information with their provider."""

    # Append the new user message
    conversation.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=conversation,
    )

    return response.content[0].text.strip()
