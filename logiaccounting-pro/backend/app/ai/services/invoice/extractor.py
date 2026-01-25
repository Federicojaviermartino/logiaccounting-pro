"""
Invoice Data Extractor
Extract structured data from OCR text using LLM
"""

import logging
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
import re
import json

from ...config import get_ai_config
from ...models.scanned_invoice import ScannedInvoice
from ..llm_client import get_llm_client, ModelTier

logger = logging.getLogger(__name__)


EXTRACTION_SCHEMA = """
{
    "vendor_name": "string - company/vendor name",
    "vendor_address": "string - vendor address",
    "vendor_tax_id": "string - tax ID/VAT number",
    "invoice_number": "string - invoice/document number",
    "invoice_date": "string - date in YYYY-MM-DD format",
    "due_date": "string - due date in YYYY-MM-DD format",
    "currency": "string - 3-letter currency code",
    "subtotal": "number - subtotal before tax",
    "tax_amount": "number - total tax amount",
    "total_amount": "number - total amount due",
    "line_items": [
        {
            "description": "string",
            "quantity": "number",
            "unit_price": "number",
            "amount": "number"
        }
    ],
    "payment_terms": "string - payment terms if mentioned",
    "purchase_order": "string - PO number if referenced"
}
"""


class InvoiceExtractor:
    """Extract structured invoice data using LLM"""

    def __init__(self):
        self.config = get_ai_config()
        self.llm = get_llm_client()

    def _extract_with_regex(self, text: str) -> Dict[str, Any]:
        """Extract basic fields using regex patterns"""
        data = {}

        # Invoice number patterns
        inv_patterns = [
            r'invoice\s*#?\s*:?\s*([A-Z0-9-]+)',
            r'inv\s*#?\s*:?\s*([A-Z0-9-]+)',
            r'factura\s*#?\s*:?\s*([A-Z0-9-]+)',
        ]
        for pattern in inv_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['invoice_number'] = match.group(1)
                break

        # Date patterns
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
        ]
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            dates.extend(matches)
        if dates:
            data['invoice_date_raw'] = dates[0]

        # Amount patterns
        amount_patterns = [
            r'total\s*:?\s*\$?\s*([\d,]+\.?\d*)',
            r'\$\s*([\d,]+\.?\d*)',
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    data['total_amount'] = float(amount_str)
                except ValueError:
                    pass
                break

        # Tax ID patterns
        tax_patterns = [
            r'tax\s*id\s*:?\s*([A-Z0-9-]+)',
            r'vat\s*:?\s*([A-Z0-9-]+)',
            r'rfc\s*:?\s*([A-Z0-9-]+)',
        ]
        for pattern in tax_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data['vendor_tax_id'] = match.group(1)
                break

        return data

    async def extract(
        self,
        ocr_text: str,
        tenant_id: str,
        filename: Optional[str] = None,
        use_llm: bool = True,
    ) -> ScannedInvoice:
        """
        Extract structured data from OCR text

        Args:
            ocr_text: OCR extracted text
            tenant_id: Tenant ID
            filename: Original filename
            use_llm: Whether to use LLM for extraction

        Returns:
            ScannedInvoice with extracted data
        """
        start_time = time.time()

        # Start with regex extraction
        extracted_data = self._extract_with_regex(ocr_text)

        # Enhance with LLM if enabled
        if use_llm and ocr_text.strip():
            try:
                llm_data = await self._llm_extract(ocr_text, tenant_id)
                # Merge LLM data, preferring LLM results
                for key, value in llm_data.items():
                    if value is not None and value != "":
                        extracted_data[key] = value
            except Exception as e:
                logger.warning(f"LLM extraction failed: {e}")

        processing_time = int((time.time() - start_time) * 1000)

        # Create scanned invoice record
        scan = ScannedInvoice(
            tenant_id=tenant_id,
            original_filename=filename,
            file_type=self._detect_file_type(filename),
            ocr_text=ocr_text,
            extracted_data=extracted_data,
            validation_status='pending',
            processing_time_ms=processing_time,
        )

        # Validate extracted data
        validation_errors = self._validate_extraction(extracted_data)
        if validation_errors:
            scan.validation_status = 'needs_review'
            scan.validation_errors = validation_errors
        else:
            scan.validation_status = 'validated'

        scan.save()
        return scan

    async def _llm_extract(self, ocr_text: str, tenant_id: str) -> Dict[str, Any]:
        """Extract data using LLM"""
        prompt = f"""Extract structured invoice data from the following OCR text.
Return valid JSON matching the schema provided.

OCR Text:
{ocr_text}

Extract all available fields. Use null for missing fields.
Ensure dates are in YYYY-MM-DD format.
Ensure amounts are numbers without currency symbols."""

        try:
            result = await self.llm.extract_json(
                prompt=prompt,
                schema_hint=EXTRACTION_SCHEMA,
                tier=ModelTier.FAST,
                tenant_id=tenant_id,
                feature='invoice_extraction',
            )
            return result
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM extraction result")
            return {}

    def _validate_extraction(self, data: Dict[str, Any]) -> List[Dict]:
        """Validate extracted data"""
        errors = []

        # Check required fields
        if not data.get('invoice_number'):
            errors.append({
                'field': 'invoice_number',
                'error': 'Invoice number not found',
                'severity': 'warning',
            })

        if not data.get('total_amount'):
            errors.append({
                'field': 'total_amount',
                'error': 'Total amount not found',
                'severity': 'error',
            })

        if not data.get('invoice_date') and not data.get('invoice_date_raw'):
            errors.append({
                'field': 'invoice_date',
                'error': 'Invoice date not found',
                'severity': 'warning',
            })

        if not data.get('vendor_name'):
            errors.append({
                'field': 'vendor_name',
                'error': 'Vendor name not found',
                'severity': 'warning',
            })

        # Validate amounts
        total = data.get('total_amount', 0)
        subtotal = data.get('subtotal', 0)
        tax = data.get('tax_amount', 0)

        if subtotal and tax and total:
            expected_total = subtotal + tax
            if abs(expected_total - total) > 0.01:
                errors.append({
                    'field': 'total_amount',
                    'error': f'Total ({total}) does not match subtotal ({subtotal}) + tax ({tax})',
                    'severity': 'warning',
                })

        return errors

    def _detect_file_type(self, filename: Optional[str]) -> str:
        """Detect file type from filename"""
        if not filename:
            return 'unknown'

        filename_lower = filename.lower()
        if filename_lower.endswith('.pdf'):
            return 'pdf'
        elif filename_lower.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')):
            return 'image'
        else:
            return 'unknown'
