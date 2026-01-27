"""
Invoice Extractor
AI-powered data extraction from invoice images
"""

from typing import Dict, Any, List, Optional
import json
import logging
import re
from datetime import datetime

from app.ai.client import ai_client
from app.ai.config import get_model_config
from app.ai.ocr.processor import ExtractedInvoice, LineItem

logger = logging.getLogger(__name__)


EXTRACTION_PROMPT = """You are an expert document analyzer. Extract all invoice data from this image accurately.

Extract the following information and return it as valid JSON:

{
    "vendor": {
        "name": "Company name on the invoice",
        "address": "Full address",
        "tax_id": "Tax ID, VAT number, or EIN if visible"
    },
    "invoice_number": "Invoice/Bill number",
    "invoice_date": "Date in YYYY-MM-DD format",
    "due_date": "Due date in YYYY-MM-DD format if shown",
    "po_number": "Purchase order number if shown",
    "line_items": [
        {
            "description": "Item description",
            "quantity": 1.0,
            "unit_price": 0.00,
            "amount": 0.00
        }
    ],
    "subtotal": 0.00,
    "tax_rate": 0.00,
    "tax_amount": 0.00,
    "discount": 0.00,
    "total": 0.00,
    "currency": "USD",
    "payment_terms": "Net 30, etc if shown",
    "bank_info": "Bank details if shown",
    "confidence": 0.95
}

Important:
- Use null for fields not found
- Amounts should be numbers, not strings
- Dates must be in YYYY-MM-DD format
- Return ONLY the JSON, no other text
"""


class InvoiceExtractor:
    """Extracts invoice data using AI vision."""

    def __init__(self):
        self.model_config = get_model_config("vision")

    async def extract(self, image_data: bytes) -> ExtractedInvoice:
        """Extract invoice data from image."""
        logger.info("Extracting invoice data from image")

        try:
            # Call AI vision API
            response = await ai_client.vision(
                image_data=image_data,
                prompt=EXTRACTION_PROMPT,
                model_config=self.model_config,
            )

            # Parse response
            extracted = self._parse_response(response)

            return extracted

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            # Return empty invoice with low confidence
            invoice = ExtractedInvoice()
            invoice.confidence = 0.0
            invoice.status = "failed"
            return invoice

    def _parse_response(self, response: str) -> ExtractedInvoice:
        """Parse AI response into ExtractedInvoice."""
        try:
            # Clean response - extract JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if not json_match:
                raise ValueError("No JSON found in response")

            data = json.loads(json_match.group())

            invoice = ExtractedInvoice()

            # Vendor info
            vendor = data.get("vendor", {})
            invoice.vendor_name = vendor.get("name", "") or ""
            invoice.vendor_address = vendor.get("address", "") or ""
            invoice.vendor_tax_id = vendor.get("tax_id", "") or ""

            # Invoice details
            invoice.invoice_number = data.get("invoice_number", "") or ""
            invoice.invoice_date = data.get("invoice_date")
            invoice.due_date = data.get("due_date")
            invoice.po_number = data.get("po_number", "") or ""

            # Amounts
            invoice.subtotal = float(data.get("subtotal", 0) or 0)
            invoice.tax_rate = float(data.get("tax_rate", 0) or 0)
            invoice.tax_amount = float(data.get("tax_amount", 0) or 0)
            invoice.discount = float(data.get("discount", 0) or 0)
            invoice.total = float(data.get("total", 0) or 0)
            invoice.currency = data.get("currency", "USD") or "USD"

            # Line items
            for item_data in data.get("line_items", []):
                item = LineItem(
                    description=item_data.get("description", ""),
                    quantity=float(item_data.get("quantity", 1) or 1),
                    unit_price=float(item_data.get("unit_price", 0) or 0),
                    amount=float(item_data.get("amount", 0) or 0),
                )
                invoice.line_items.append(item)

            # Other info
            invoice.payment_terms = data.get("payment_terms", "") or ""
            invoice.bank_info = data.get("bank_info", "") or ""

            # Confidence
            invoice.confidence = float(data.get("confidence", 0.8) or 0.8)
            invoice.status = "needs_review" if invoice.confidence < 0.9 else "completed"

            return invoice

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            invoice = ExtractedInvoice()
            invoice.confidence = 0.0
            invoice.status = "failed"
            return invoice

    async def extract_from_text(self, text: str) -> ExtractedInvoice:
        """Extract invoice data from OCR text."""
        logger.info("Extracting invoice data from text")

        prompt = f"""Extract invoice data from this text and return as JSON:

{text}

{EXTRACTION_PROMPT}"""

        try:
            response = await ai_client.complete(prompt)
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            invoice = ExtractedInvoice()
            invoice.confidence = 0.0
            invoice.status = "failed"
            return invoice


# Global extractor instance
invoice_extractor = InvoiceExtractor()
