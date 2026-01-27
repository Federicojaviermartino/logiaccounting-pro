"""
AI Extraction Service - Phase 13
AI-powered data extraction from documents using OpenAI/Anthropic
"""

from typing import Optional, Dict, Any, List
import os
import json
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class AIExtractionService:
    """AI-powered document data extraction"""

    # Extraction schemas for different document types
    EXTRACTION_SCHEMAS = {
        'invoice': {
            'vendor_name': 'string',
            'vendor_address': 'string',
            'vendor_tax_id': 'string',
            'invoice_number': 'string',
            'invoice_date': 'date',
            'due_date': 'date',
            'customer_name': 'string',
            'customer_address': 'string',
            'customer_tax_id': 'string',
            'line_items': [{
                'description': 'string',
                'quantity': 'number',
                'unit_price': 'number',
                'amount': 'number',
            }],
            'subtotal': 'number',
            'tax_rate': 'number',
            'tax_amount': 'number',
            'total': 'number',
            'currency': 'string',
            'payment_terms': 'string',
            'notes': 'string',
        },
        'receipt': {
            'merchant_name': 'string',
            'merchant_address': 'string',
            'receipt_number': 'string',
            'date': 'date',
            'time': 'string',
            'items': [{
                'description': 'string',
                'quantity': 'number',
                'price': 'number',
            }],
            'subtotal': 'number',
            'tax': 'number',
            'total': 'number',
            'payment_method': 'string',
            'currency': 'string',
        },
        'contract': {
            'title': 'string',
            'contract_number': 'string',
            'effective_date': 'date',
            'expiration_date': 'date',
            'parties': [{
                'name': 'string',
                'role': 'string',
                'address': 'string',
            }],
            'terms_summary': 'string',
            'payment_terms': 'string',
            'total_value': 'number',
            'currency': 'string',
        },
        'statement': {
            'account_holder': 'string',
            'account_number': 'string',
            'statement_period_start': 'date',
            'statement_period_end': 'date',
            'opening_balance': 'number',
            'closing_balance': 'number',
            'total_deposits': 'number',
            'total_withdrawals': 'number',
            'transactions': [{
                'date': 'date',
                'description': 'string',
                'amount': 'number',
                'type': 'string',
            }],
            'currency': 'string',
        },
    }

    def __init__(self):
        self._openai_client = None
        self._anthropic_client = None
        self.provider = os.getenv('AI_EXTRACTION_PROVIDER', 'openai')

    @property
    def openai_client(self):
        """Lazy load OpenAI client"""
        if self._openai_client is None:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                try:
                    from openai import OpenAI
                    self._openai_client = OpenAI(api_key=api_key)
                except ImportError:
                    logger.warning("OpenAI not installed")
        return self._openai_client

    @property
    def anthropic_client(self):
        """Lazy load Anthropic client"""
        if self._anthropic_client is None:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                try:
                    from anthropic import Anthropic
                    self._anthropic_client = Anthropic(api_key=api_key)
                except ImportError:
                    logger.warning("Anthropic not installed")
        return self._anthropic_client

    def extract_data(
        self,
        text: str,
        document_type: str = None,
        custom_fields: Dict[str, str] = None,
        use_vision: bool = False,
        image_data: bytes = None
    ) -> Dict[str, Any]:
        """
        Extract structured data from document text

        Args:
            text: OCR extracted text
            document_type: Document type for schema selection
            custom_fields: Additional fields to extract
            use_vision: Use vision API for image analysis
            image_data: Image bytes for vision analysis

        Returns:
            Dict with extracted data
        """
        if not text and not image_data:
            return {
                'success': False,
                'error': 'No text or image provided'
            }

        # Get extraction schema
        schema = self.EXTRACTION_SCHEMAS.get(document_type, {})
        if custom_fields:
            schema.update(custom_fields)

        try:
            if self.provider == 'anthropic' and self.anthropic_client:
                return self._extract_with_anthropic(text, schema, document_type)
            elif self.openai_client:
                if use_vision and image_data:
                    return self._extract_with_openai_vision(image_data, schema, document_type)
                return self._extract_with_openai(text, schema, document_type)
            else:
                # Fallback to regex-based extraction
                return self._extract_with_patterns(text, document_type)

        except Exception as e:
            logger.error(f"AI extraction failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_data': self._extract_with_patterns(text, document_type).get('data', {})
            }

    def _extract_with_openai(
        self,
        text: str,
        schema: Dict,
        document_type: str
    ) -> Dict[str, Any]:
        """Extract data using OpenAI GPT"""
        prompt = self._build_extraction_prompt(text, schema, document_type)

        response = self.openai_client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            messages=[
                {
                    "role": "system",
                    "content": "You are a document data extraction assistant. Extract structured data from documents accurately. Return only valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        return {
            'success': True,
            'data': result,
            'provider': 'openai',
            'model': os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
        }

    def _extract_with_openai_vision(
        self,
        image_data: bytes,
        schema: Dict,
        document_type: str
    ) -> Dict[str, Any]:
        """Extract data using OpenAI Vision"""
        import base64

        base64_image = base64.b64encode(image_data).decode('utf-8')

        prompt = self._build_vision_prompt(schema, document_type)

        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.1,
            max_tokens=4096
        )

        result_text = response.choices[0].message.content

        # Try to parse JSON from response
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = {'raw_response': result_text}

        return {
            'success': True,
            'data': result,
            'provider': 'openai_vision',
            'model': 'gpt-4o',
        }

    def _extract_with_anthropic(
        self,
        text: str,
        schema: Dict,
        document_type: str
    ) -> Dict[str, Any]:
        """Extract data using Anthropic Claude"""
        prompt = self._build_extraction_prompt(text, schema, document_type)

        response = self.anthropic_client.messages.create(
            model=os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307'),
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            system="You are a document data extraction assistant. Extract structured data from documents accurately. Return only valid JSON."
        )

        result_text = response.content[0].text

        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = {'raw_response': result_text}

        return {
            'success': True,
            'data': result,
            'provider': 'anthropic',
            'model': os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307'),
        }

    def _build_extraction_prompt(
        self,
        text: str,
        schema: Dict,
        document_type: str
    ) -> str:
        """Build extraction prompt"""
        schema_desc = self._schema_to_description(schema)

        prompt = f"""Extract the following data from this {document_type or 'document'}:

{schema_desc}

Document text:
---
{text[:8000]}
---

Return a JSON object with the extracted fields. Use null for fields that cannot be found.
For dates, use ISO format (YYYY-MM-DD).
For numbers, use numeric values (not strings).
"""
        return prompt

    def _build_vision_prompt(
        self,
        schema: Dict,
        document_type: str
    ) -> str:
        """Build vision extraction prompt"""
        schema_desc = self._schema_to_description(schema)

        prompt = f"""Analyze this {document_type or 'document'} image and extract the following data:

{schema_desc}

Return a JSON object with the extracted fields. Use null for fields that cannot be found.
For dates, use ISO format (YYYY-MM-DD).
For numbers, use numeric values (not strings).
"""
        return prompt

    def _schema_to_description(self, schema: Dict) -> str:
        """Convert schema to human-readable description"""
        lines = []
        for field, field_type in schema.items():
            if isinstance(field_type, list) and len(field_type) > 0:
                if isinstance(field_type[0], dict):
                    subfields = ', '.join(field_type[0].keys())
                    lines.append(f"- {field}: array of objects with ({subfields})")
                else:
                    lines.append(f"- {field}: array of {field_type[0]}")
            elif isinstance(field_type, dict):
                subfields = ', '.join(field_type.keys())
                lines.append(f"- {field}: object with ({subfields})")
            else:
                lines.append(f"- {field}: {field_type}")
        return '\n'.join(lines)

    def _extract_with_patterns(
        self,
        text: str,
        document_type: str
    ) -> Dict[str, Any]:
        """Fallback regex-based extraction"""
        data = {}

        # Common patterns
        patterns = {
            'date': [
                (r'(?:date|fecha)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'date'),
                (r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})', 'date'),
            ],
            'total': [
                (r'(?:total|amount)[:\s]*[\$\u20ac\u00a3]?\s*([0-9,]+\.?\d*)', 'total'),
            ],
            'invoice_number': [
                (r'(?:invoice|factura|ref)[#:\s]*([A-Z0-9-]+)', 'invoice_number'),
            ],
            'vendor_name': [
                (r'^([A-Z][A-Za-z\s]+(?:Inc|LLC|Ltd|Corp|Company|Co)\.?)', 'vendor_name'),
            ],
            'tax_id': [
                (r'(?:tax id|vat|nif|cif|rfc)[:\s]*([A-Z0-9-]+)', 'tax_id'),
            ],
        }

        for field, field_patterns in patterns.items():
            for pattern, _ in field_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    value = match.group(1).strip()
                    if field == 'total':
                        try:
                            value = float(value.replace(',', ''))
                        except ValueError:
                            pass
                    data[field] = value
                    break

        return {
            'success': True,
            'data': data,
            'provider': 'pattern_matching',
        }

    def classify_document(
        self,
        text: str,
        image_data: bytes = None
    ) -> Dict[str, Any]:
        """
        Classify document type using AI

        Args:
            text: OCR extracted text
            image_data: Optional image for vision classification

        Returns:
            Dict with document_type and confidence
        """
        document_types = list(self.EXTRACTION_SCHEMAS.keys()) + ['other']

        try:
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
                    messages=[
                        {
                            "role": "system",
                            "content": f"Classify the document type. Return JSON with 'document_type' (one of: {', '.join(document_types)}) and 'confidence' (0-1)."
                        },
                        {
                            "role": "user",
                            "content": f"Classify this document:\n\n{text[:4000]}"
                        }
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )

                result = json.loads(response.choices[0].message.content)

                return {
                    'success': True,
                    'document_type': result.get('document_type', 'other'),
                    'confidence': result.get('confidence', 0.5),
                    'provider': 'openai',
                }

        except Exception as e:
            logger.error(f"Classification failed: {e}")

        # Fallback to pattern-based classification
        return self._classify_with_patterns(text)

    def _classify_with_patterns(self, text: str) -> Dict[str, Any]:
        """Pattern-based document classification"""
        text_lower = text.lower()

        scores = {
            'invoice': 0,
            'receipt': 0,
            'contract': 0,
            'statement': 0,
            'other': 0,
        }

        # Invoice patterns
        if re.search(r'\b(invoice|factura|bill)\b', text_lower):
            scores['invoice'] += 2
        if re.search(r'\b(qty|quantity|cantidad)\b', text_lower):
            scores['invoice'] += 1
        if re.search(r'\b(unit price|precio unitario)\b', text_lower):
            scores['invoice'] += 1

        # Receipt patterns
        if re.search(r'\b(receipt|recibo)\b', text_lower):
            scores['receipt'] += 2
        if re.search(r'\b(cash|change|efectivo|cambio)\b', text_lower):
            scores['receipt'] += 1

        # Contract patterns
        if re.search(r'\b(contract|agreement|contrato)\b', text_lower):
            scores['contract'] += 2
        if re.search(r'\b(parties|party|parte)\b', text_lower):
            scores['contract'] += 1

        # Statement patterns
        if re.search(r'\b(statement|estado de cuenta)\b', text_lower):
            scores['statement'] += 2
        if re.search(r'\b(balance|saldo)\b', text_lower):
            scores['statement'] += 1

        best_type = max(scores, key=scores.get)
        max_score = scores[best_type]

        if max_score == 0:
            best_type = 'other'
            confidence = 0.3
        else:
            confidence = min(max_score / 5, 1.0)

        return {
            'success': True,
            'document_type': best_type,
            'confidence': confidence,
            'provider': 'pattern_matching',
        }

    def summarize_document(
        self,
        text: str,
        max_length: int = 200
    ) -> Dict[str, Any]:
        """
        Generate a brief summary of the document

        Args:
            text: Document text
            max_length: Maximum summary length

        Returns:
            Dict with summary
        """
        try:
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
                    messages=[
                        {
                            "role": "system",
                            "content": f"Summarize the document in {max_length} characters or less. Be concise and factual."
                        },
                        {
                            "role": "user",
                            "content": text[:6000]
                        }
                    ],
                    temperature=0.3,
                    max_tokens=100
                )

                summary = response.choices[0].message.content

                return {
                    'success': True,
                    'summary': summary[:max_length],
                    'provider': 'openai',
                }

        except Exception as e:
            logger.error(f"Summarization failed: {e}")

        # Fallback: first sentences
        sentences = re.split(r'[.!?]\s+', text)
        summary = '. '.join(sentences[:3])

        if len(summary) > max_length:
            summary = summary[:max_length-3] + '...'

        return {
            'success': True,
            'summary': summary,
            'provider': 'truncation',
        }


# Global service instance
ai_extraction_service = AIExtractionService()
