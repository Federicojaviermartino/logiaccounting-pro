# Phase 31: AI/ML Features - Part 3: Smart Invoice OCR

## Overview
This part covers the intelligent document processing system that extracts data from invoices and receipts using computer vision and AI.

---

## File 1: Document Processor
**Path:** `backend/app/ai/ocr/processor.py`

```python
"""
Document Processor
Main OCR processing pipeline
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import io
import logging
import base64
from uuid import uuid4

logger = logging.getLogger(__name__)


class DocumentType(str, Enum):
    """Supported document types."""
    INVOICE = "invoice"
    RECEIPT = "receipt"
    BILL = "bill"
    QUOTE = "quote"
    CREDIT_NOTE = "credit_note"
    PURCHASE_ORDER = "purchase_order"
    UNKNOWN = "unknown"


class ProcessingStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


@dataclass
class LineItem:
    """Extracted line item from document."""
    description: str
    quantity: float = 1.0
    unit_price: float = 0.0
    amount: float = 0.0
    tax_rate: Optional[float] = None
    product_code: Optional[str] = None
    confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "description": self.description,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "amount": self.amount,
            "tax_rate": self.tax_rate,
            "product_code": self.product_code,
            "confidence": self.confidence,
        }


@dataclass
class ExtractedInvoice:
    """Extracted invoice data."""
    document_id: str
    document_type: DocumentType = DocumentType.INVOICE
    status: ProcessingStatus = ProcessingStatus.COMPLETED
    confidence: float = 0.0
    
    # Vendor information
    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    vendor_tax_id: Optional[str] = None
    vendor_email: Optional[str] = None
    vendor_phone: Optional[str] = None
    
    # Invoice details
    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    purchase_order: Optional[str] = None
    
    # Customer information
    customer_name: Optional[str] = None
    customer_address: Optional[str] = None
    
    # Financial details
    currency: str = "USD"
    subtotal: float = 0.0
    tax_rate: Optional[float] = None
    tax_amount: float = 0.0
    discount: float = 0.0
    shipping: float = 0.0
    total: float = 0.0
    amount_paid: float = 0.0
    amount_due: float = 0.0
    
    # Line items
    line_items: List[LineItem] = field(default_factory=list)
    
    # Payment information
    payment_terms: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_routing: Optional[str] = None
    
    # Metadata
    raw_text: Optional[str] = None
    page_count: int = 1
    processed_at: datetime = field(default_factory=datetime.utcnow)
    field_confidences: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "document_id": self.document_id,
            "document_type": self.document_type.value,
            "status": self.status.value,
            "confidence": self.confidence,
            "vendor": {
                "name": self.vendor_name,
                "address": self.vendor_address,
                "tax_id": self.vendor_tax_id,
                "email": self.vendor_email,
                "phone": self.vendor_phone,
            },
            "invoice_number": self.invoice_number,
            "invoice_date": self.invoice_date.isoformat() if self.invoice_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "purchase_order": self.purchase_order,
            "customer": {
                "name": self.customer_name,
                "address": self.customer_address,
            },
            "currency": self.currency,
            "subtotal": self.subtotal,
            "tax_rate": self.tax_rate,
            "tax_amount": self.tax_amount,
            "discount": self.discount,
            "shipping": self.shipping,
            "total": self.total,
            "amount_paid": self.amount_paid,
            "amount_due": self.amount_due,
            "line_items": [item.to_dict() for item in self.line_items],
            "payment_terms": self.payment_terms,
            "bank_details": {
                "bank_name": self.bank_name,
                "account": self.bank_account,
                "routing": self.bank_routing,
            } if self.bank_name else None,
            "page_count": self.page_count,
            "processed_at": self.processed_at.isoformat(),
            "field_confidences": self.field_confidences,
        }


class DocumentProcessor:
    """Main document processing pipeline."""
    
    SUPPORTED_FORMATS = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.webp']
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self):
        self._processed_documents: Dict[str, ExtractedInvoice] = {}
    
    async def process(
        self,
        file_data: bytes,
        filename: str,
        customer_id: str,
        options: Dict = None,
    ) -> ExtractedInvoice:
        """Process a document and extract data."""
        import time
        start_time = time.time()
        
        options = options or {}
        document_id = f"doc_{uuid4().hex[:12]}"
        
        # Validate file
        self._validate_file(file_data, filename)
        
        # Determine file type
        file_ext = filename.lower().split('.')[-1]
        
        try:
            # Convert to image(s) if PDF
            if file_ext == 'pdf':
                images = await self._pdf_to_images(file_data)
            else:
                images = [file_data]
            
            # Process with AI vision
            from app.ai.ocr.extractor import InvoiceExtractor
            extractor = InvoiceExtractor()
            
            # Extract from all pages
            all_extractions = []
            for i, image in enumerate(images):
                extraction = await extractor.extract(image)
                all_extractions.append(extraction)
            
            # Merge multi-page results
            extracted = self._merge_extractions(all_extractions, document_id)
            
            # Classify document type
            from app.ai.ocr.classifier import DocumentClassifier
            classifier = DocumentClassifier()
            doc_type = await classifier.classify(extracted.raw_text or "")
            extracted.document_type = doc_type
            
            # Check for duplicates
            duplicate_check = await self._check_duplicate(extracted, customer_id)
            if duplicate_check["is_duplicate"]:
                extracted.status = ProcessingStatus.NEEDS_REVIEW
            
            # Calculate overall confidence
            extracted.confidence = self._calculate_confidence(extracted)
            
            # Validate extracted data
            validation_errors = self._validate_extraction(extracted)
            if validation_errors:
                extracted.status = ProcessingStatus.NEEDS_REVIEW
            
            extracted.page_count = len(images)
            
            # Store for reference
            self._processed_documents[document_id] = extracted
            
            logger.info(f"Document {document_id} processed in {time.time() - start_time:.2f}s")
            return extracted
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return ExtractedInvoice(
                document_id=document_id,
                status=ProcessingStatus.FAILED,
                confidence=0,
            )
    
    def _validate_file(self, file_data: bytes, filename: str):
        """Validate file format and size."""
        # Check size
        if len(file_data) > self.MAX_FILE_SIZE:
            raise ValueError(f"File too large. Maximum size is {self.MAX_FILE_SIZE // 1024 // 1024}MB")
        
        # Check format
        file_ext = f".{filename.lower().split('.')[-1]}"
        if file_ext not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format. Supported formats: {self.SUPPORTED_FORMATS}")
    
    async def _pdf_to_images(self, pdf_data: bytes) -> List[bytes]:
        """Convert PDF to images."""
        try:
            import fitz  # PyMuPDF
            
            images = []
            doc = fitz.open(stream=pdf_data, filetype="pdf")
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom
                img_data = pix.tobytes("png")
                images.append(img_data)
            
            doc.close()
            return images
            
        except ImportError:
            logger.warning("PyMuPDF not installed, trying pdf2image")
            try:
                from pdf2image import convert_from_bytes
                pil_images = convert_from_bytes(pdf_data, dpi=200)
                
                images = []
                for pil_img in pil_images:
                    img_bytes = io.BytesIO()
                    pil_img.save(img_bytes, format='PNG')
                    images.append(img_bytes.getvalue())
                
                return images
            except ImportError:
                raise ImportError("PDF processing requires PyMuPDF or pdf2image")
    
    def _merge_extractions(self, extractions: List[Dict], document_id: str) -> ExtractedInvoice:
        """Merge multi-page extraction results."""
        if not extractions:
            return ExtractedInvoice(document_id=document_id, status=ProcessingStatus.FAILED)
        
        if len(extractions) == 1:
            return extractions[0]
        
        # Use first page as base
        merged = extractions[0]
        merged.document_id = document_id
        
        # Merge line items from all pages
        for extraction in extractions[1:]:
            if hasattr(extraction, 'line_items'):
                merged.line_items.extend(extraction.line_items)
            
            # Use higher confidence values
            for field in ['vendor_name', 'invoice_number', 'total']:
                if hasattr(extraction, field):
                    curr_conf = merged.field_confidences.get(field, 0)
                    new_conf = extraction.field_confidences.get(field, 0)
                    if new_conf > curr_conf:
                        setattr(merged, field, getattr(extraction, field))
        
        return merged
    
    async def _check_duplicate(self, extracted: ExtractedInvoice, customer_id: str) -> Dict:
        """Check for duplicate invoices."""
        # In production: query database for similar invoices
        # Check by invoice number + vendor
        
        return {
            "is_duplicate": False,
            "similar_invoices": [],
        }
    
    def _calculate_confidence(self, extracted: ExtractedInvoice) -> float:
        """Calculate overall extraction confidence."""
        confidences = list(extracted.field_confidences.values())
        
        if not confidences:
            return 0.5
        
        # Weighted average (critical fields weighted higher)
        critical_fields = ['invoice_number', 'vendor_name', 'total', 'invoice_date']
        weights = []
        values = []
        
        for field, conf in extracted.field_confidences.items():
            weight = 2.0 if field in critical_fields else 1.0
            weights.append(weight)
            values.append(conf)
        
        return sum(w * v for w, v in zip(weights, values)) / sum(weights) if weights else 0.5
    
    def _validate_extraction(self, extracted: ExtractedInvoice) -> List[str]:
        """Validate extracted data."""
        errors = []
        
        # Required fields
        if not extracted.vendor_name:
            errors.append("Missing vendor name")
        
        if not extracted.invoice_number:
            errors.append("Missing invoice number")
        
        if extracted.total <= 0:
            errors.append("Invalid or missing total amount")
        
        # Consistency checks
        if extracted.line_items:
            line_total = sum(item.amount for item in extracted.line_items)
            if abs(line_total - extracted.subtotal) > 1:  # Allow $1 rounding difference
                errors.append(f"Line items total ({line_total}) doesn't match subtotal ({extracted.subtotal})")
        
        # Tax validation
        if extracted.tax_rate and extracted.subtotal > 0:
            expected_tax = extracted.subtotal * extracted.tax_rate
            if abs(expected_tax - extracted.tax_amount) > 1:
                errors.append("Tax amount doesn't match rate")
        
        return errors
    
    def get_document(self, document_id: str) -> Optional[ExtractedInvoice]:
        """Get processed document by ID."""
        return self._processed_documents.get(document_id)


# Global processor instance
document_processor = DocumentProcessor()
```

---

## File 2: AI Extractor
**Path:** `backend/app/ai/ocr/extractor.py`

```python
"""
Invoice Extractor
AI-powered field extraction from documents
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging
import re

from app.ai.client import ai_client, AIProvider
from app.ai.config import get_model_config
from app.ai.ocr.processor import ExtractedInvoice, LineItem, ProcessingStatus

logger = logging.getLogger(__name__)


EXTRACTION_PROMPT = """You are an expert document analyst specializing in invoice and receipt data extraction.

Analyze the provided image of a financial document and extract all relevant information.

Return a JSON object with the following structure:
{
    "document_type": "invoice|receipt|bill|quote|credit_note|purchase_order|unknown",
    "vendor": {
        "name": "Company name",
        "address": "Full address",
        "tax_id": "Tax/VAT ID if present",
        "email": "Email if present",
        "phone": "Phone if present"
    },
    "invoice_number": "Invoice/Receipt number",
    "invoice_date": "YYYY-MM-DD format",
    "due_date": "YYYY-MM-DD format if present",
    "purchase_order": "PO number if referenced",
    "customer": {
        "name": "Customer/Bill To name",
        "address": "Customer address"
    },
    "currency": "USD/EUR/GBP/etc",
    "line_items": [
        {
            "description": "Item description",
            "quantity": 1.0,
            "unit_price": 0.00,
            "amount": 0.00,
            "product_code": "SKU if present"
        }
    ],
    "subtotal": 0.00,
    "tax_rate": 0.10,
    "tax_amount": 0.00,
    "discount": 0.00,
    "shipping": 0.00,
    "total": 0.00,
    "amount_paid": 0.00,
    "amount_due": 0.00,
    "payment_terms": "Net 30, etc",
    "bank_details": {
        "bank_name": "Bank name if present",
        "account": "Account number",
        "routing": "Routing number"
    },
    "raw_text": "Full extracted text from document",
    "field_confidences": {
        "vendor_name": 0.95,
        "invoice_number": 0.90,
        ...
    }
}

Important guidelines:
1. Extract ALL visible text and numbers accurately
2. For amounts, remove currency symbols and convert to numbers
3. For dates, use YYYY-MM-DD format
4. If a field is not present or unclear, use null
5. Provide confidence scores (0-1) for each field
6. Include the full raw text extracted from the document
7. Pay special attention to:
   - Invoice/Receipt numbers (often near top)
   - Dates (invoice date, due date)
   - Total amounts (usually emphasized or at bottom)
   - Tax information (VAT, GST, sales tax)
   - Line item details

Return ONLY valid JSON, no additional text."""


class InvoiceExtractor:
    """Extracts invoice data using AI vision."""
    
    def __init__(self):
        self._model_config = get_model_config("vision")
    
    async def extract(self, image_data: bytes) -> ExtractedInvoice:
        """Extract invoice data from image."""
        try:
            # Call AI vision model
            response = await ai_client.vision(
                image_data=image_data,
                prompt=EXTRACTION_PROMPT,
                provider=AIProvider.ANTHROPIC,
                model_config=self._model_config,
            )
            
            # Parse JSON response
            extracted_data = self._parse_response(response)
            
            # Convert to ExtractedInvoice
            return self._build_invoice(extracted_data)
            
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return ExtractedInvoice(
                document_id="",
                status=ProcessingStatus.FAILED,
            )
    
    def _parse_response(self, response: str) -> Dict:
        """Parse AI response to extract JSON."""
        # Try to find JSON in response
        try:
            # Direct parse
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from markdown code block
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON object in text
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        logger.warning("Could not parse JSON from AI response")
        return {}
    
    def _build_invoice(self, data: Dict) -> ExtractedInvoice:
        """Build ExtractedInvoice from extracted data."""
        vendor = data.get("vendor", {}) or {}
        customer = data.get("customer", {}) or {}
        bank = data.get("bank_details", {}) or {}
        
        # Parse line items
        line_items = []
        for item in data.get("line_items", []) or []:
            line_items.append(LineItem(
                description=item.get("description", ""),
                quantity=float(item.get("quantity", 1) or 1),
                unit_price=float(item.get("unit_price", 0) or 0),
                amount=float(item.get("amount", 0) or 0),
                tax_rate=item.get("tax_rate"),
                product_code=item.get("product_code"),
                confidence=item.get("confidence", 0.8),
            ))
        
        # Parse dates
        invoice_date = self._parse_date(data.get("invoice_date"))
        due_date = self._parse_date(data.get("due_date"))
        
        invoice = ExtractedInvoice(
            document_id="",
            status=ProcessingStatus.COMPLETED,
            confidence=0,
            
            vendor_name=vendor.get("name"),
            vendor_address=vendor.get("address"),
            vendor_tax_id=vendor.get("tax_id"),
            vendor_email=vendor.get("email"),
            vendor_phone=vendor.get("phone"),
            
            invoice_number=data.get("invoice_number"),
            invoice_date=invoice_date,
            due_date=due_date,
            purchase_order=data.get("purchase_order"),
            
            customer_name=customer.get("name"),
            customer_address=customer.get("address"),
            
            currency=data.get("currency", "USD"),
            subtotal=float(data.get("subtotal", 0) or 0),
            tax_rate=data.get("tax_rate"),
            tax_amount=float(data.get("tax_amount", 0) or 0),
            discount=float(data.get("discount", 0) or 0),
            shipping=float(data.get("shipping", 0) or 0),
            total=float(data.get("total", 0) or 0),
            amount_paid=float(data.get("amount_paid", 0) or 0),
            amount_due=float(data.get("amount_due", 0) or 0),
            
            line_items=line_items,
            
            payment_terms=data.get("payment_terms"),
            bank_name=bank.get("bank_name"),
            bank_account=bank.get("account"),
            bank_routing=bank.get("routing"),
            
            raw_text=data.get("raw_text"),
            field_confidences=data.get("field_confidences", {}),
        )
        
        # Calculate amount_due if not provided
        if invoice.amount_due == 0 and invoice.total > 0:
            invoice.amount_due = invoice.total - invoice.amount_paid
        
        return invoice
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None
        
        from dateutil import parser
        
        try:
            return parser.parse(date_str)
        except:
            return None


class OCRTextExtractor:
    """Fallback OCR using Tesseract."""
    
    def __init__(self):
        self._tesseract_available = self._check_tesseract()
    
    def _check_tesseract(self) -> bool:
        """Check if Tesseract is available."""
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except:
            return False
    
    async def extract_text(self, image_data: bytes) -> str:
        """Extract text from image using OCR."""
        if not self._tesseract_available:
            return ""
        
        try:
            import pytesseract
            from PIL import Image
            import io
            
            image = Image.open(io.BytesIO(image_data))
            text = pytesseract.image_to_string(image)
            
            return text
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ""
    
    async def extract_with_boxes(self, image_data: bytes) -> List[Dict]:
        """Extract text with bounding boxes."""
        if not self._tesseract_available:
            return []
        
        try:
            import pytesseract
            from PIL import Image
            import io
            
            image = Image.open(io.BytesIO(image_data))
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            boxes = []
            for i in range(len(data['text'])):
                if data['text'][i].strip():
                    boxes.append({
                        'text': data['text'][i],
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i],
                        'confidence': data['conf'][i] / 100,
                    })
            
            return boxes
            
        except Exception as e:
            logger.error(f"OCR box extraction failed: {e}")
            return []
```

---

## File 3: Document Classifier
**Path:** `backend/app/ai/ocr/classifier.py`

```python
"""
Document Classifier
Classifies document types and suggests categories
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum
import re
import logging

from app.ai.client import ai_client
from app.ai.ocr.processor import DocumentType

logger = logging.getLogger(__name__)


class ExpenseCategory(str, Enum):
    """Expense categories for auto-categorization."""
    OFFICE_SUPPLIES = "office_supplies"
    SOFTWARE = "software"
    HARDWARE = "hardware"
    TRAVEL = "travel"
    MEALS = "meals"
    UTILITIES = "utilities"
    RENT = "rent"
    PROFESSIONAL_SERVICES = "professional_services"
    MARKETING = "marketing"
    SHIPPING = "shipping"
    INSURANCE = "insurance"
    MAINTENANCE = "maintenance"
    SUBSCRIPTIONS = "subscriptions"
    TELECOMMUNICATIONS = "telecommunications"
    OTHER = "other"


# Keywords for document type classification
DOCUMENT_TYPE_KEYWORDS = {
    DocumentType.INVOICE: [
        'invoice', 'inv', 'bill to', 'payment due', 'amount due',
        'invoice number', 'invoice date', 'net 30', 'net 60',
    ],
    DocumentType.RECEIPT: [
        'receipt', 'paid', 'thank you', 'payment received',
        'transaction', 'confirmation', 'order #',
    ],
    DocumentType.QUOTE: [
        'quote', 'quotation', 'estimate', 'proposal',
        'valid until', 'expires', 'accept',
    ],
    DocumentType.CREDIT_NOTE: [
        'credit note', 'credit memo', 'refund', 'return',
        'credit adjustment', 'negative invoice',
    ],
    DocumentType.PURCHASE_ORDER: [
        'purchase order', 'po number', 'p.o.', 'order form',
        'requisition', 'procurement',
    ],
    DocumentType.BILL: [
        'bill', 'statement', 'amount owed', 'balance due',
    ],
}

# Keywords for expense categorization
CATEGORY_KEYWORDS = {
    ExpenseCategory.OFFICE_SUPPLIES: [
        'paper', 'pens', 'staples', 'office depot', 'staples inc',
        'folders', 'envelopes', 'printer', 'toner', 'ink',
    ],
    ExpenseCategory.SOFTWARE: [
        'software', 'license', 'subscription', 'saas', 'cloud',
        'adobe', 'microsoft', 'google workspace', 'slack', 'zoom',
        'figma', 'notion', 'github', 'aws', 'azure',
    ],
    ExpenseCategory.HARDWARE: [
        'computer', 'laptop', 'monitor', 'keyboard', 'mouse',
        'hardware', 'electronics', 'apple', 'dell', 'lenovo',
        'server', 'networking', 'router',
    ],
    ExpenseCategory.TRAVEL: [
        'airline', 'flight', 'hotel', 'rental car', 'uber', 'lyft',
        'travel', 'booking', 'airbnb', 'expedia', 'marriott',
    ],
    ExpenseCategory.MEALS: [
        'restaurant', 'cafe', 'coffee', 'lunch', 'dinner',
        'catering', 'grubhub', 'doordash', 'uber eats',
    ],
    ExpenseCategory.UTILITIES: [
        'electric', 'gas', 'water', 'utility', 'power',
        'pg&e', 'con edison', 'national grid',
    ],
    ExpenseCategory.PROFESSIONAL_SERVICES: [
        'consulting', 'legal', 'accounting', 'attorney', 'lawyer',
        'cpa', 'audit', 'advisory', 'professional fees',
    ],
    ExpenseCategory.MARKETING: [
        'advertising', 'marketing', 'google ads', 'facebook ads',
        'promotion', 'branding', 'pr', 'media',
    ],
    ExpenseCategory.SHIPPING: [
        'shipping', 'fedex', 'ups', 'usps', 'dhl', 'freight',
        'postage', 'delivery', 'courier',
    ],
    ExpenseCategory.TELECOMMUNICATIONS: [
        'phone', 'mobile', 'wireless', 'internet', 'isp',
        'verizon', 'at&t', 't-mobile', 'comcast',
    ],
    ExpenseCategory.SUBSCRIPTIONS: [
        'subscription', 'monthly', 'annual', 'membership',
        'premium', 'pro plan',
    ],
}


class DocumentClassifier:
    """Classifies documents by type and category."""
    
    def __init__(self):
        pass
    
    async def classify(self, text: str) -> DocumentType:
        """Classify document type from text."""
        if not text:
            return DocumentType.UNKNOWN
        
        text_lower = text.lower()
        scores = {}
        
        for doc_type, keywords in DOCUMENT_TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            scores[doc_type] = score
        
        # Get highest scoring type
        if not scores or max(scores.values()) == 0:
            return DocumentType.UNKNOWN
        
        best_type = max(scores, key=scores.get)
        return best_type
    
    async def categorize_expense(self, text: str, vendor_name: str = None) -> Tuple[ExpenseCategory, float]:
        """Categorize expense based on text and vendor."""
        if not text and not vendor_name:
            return ExpenseCategory.OTHER, 0.0
        
        combined_text = f"{text or ''} {vendor_name or ''}".lower()
        scores = {}
        
        for category, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in combined_text)
            # Boost score if keyword appears in vendor name
            if vendor_name:
                vendor_lower = vendor_name.lower()
                score += sum(2 for kw in keywords if kw in vendor_lower)
            scores[category] = score
        
        if not scores or max(scores.values()) == 0:
            return ExpenseCategory.OTHER, 0.5
        
        best_category = max(scores, key=scores.get)
        max_score = scores[best_category]
        
        # Calculate confidence
        total_keywords = sum(len(kws) for kws in CATEGORY_KEYWORDS.values())
        confidence = min(1.0, max_score / 5)  # 5 matches = 100% confidence
        
        return best_category, confidence
    
    async def suggest_gl_account(self, category: ExpenseCategory) -> Optional[str]:
        """Suggest GL account based on category."""
        # Standard chart of accounts mapping
        gl_mapping = {
            ExpenseCategory.OFFICE_SUPPLIES: "6100",
            ExpenseCategory.SOFTWARE: "6200",
            ExpenseCategory.HARDWARE: "1500",
            ExpenseCategory.TRAVEL: "6300",
            ExpenseCategory.MEALS: "6310",
            ExpenseCategory.UTILITIES: "6400",
            ExpenseCategory.RENT: "6500",
            ExpenseCategory.PROFESSIONAL_SERVICES: "6600",
            ExpenseCategory.MARKETING: "6700",
            ExpenseCategory.SHIPPING: "6800",
            ExpenseCategory.INSURANCE: "6900",
            ExpenseCategory.MAINTENANCE: "7000",
            ExpenseCategory.SUBSCRIPTIONS: "6210",
            ExpenseCategory.TELECOMMUNICATIONS: "6410",
            ExpenseCategory.OTHER: "6999",
        }
        
        return gl_mapping.get(category, "6999")
    
    async def extract_vendor_from_text(self, text: str) -> Optional[str]:
        """Try to extract vendor name from document text."""
        if not text:
            return None
        
        lines = text.split('\n')
        
        # Usually vendor name is in first few lines
        for line in lines[:10]:
            line = line.strip()
            
            # Skip empty lines and common headers
            if not line or len(line) < 3:
                continue
            
            skip_patterns = [
                r'^invoice',
                r'^bill',
                r'^receipt',
                r'^date',
                r'^page',
                r'^\d+',
            ]
            
            if any(re.match(p, line.lower()) for p in skip_patterns):
                continue
            
            # Likely vendor name if it's a short line without numbers
            if len(line) < 50 and not re.search(r'\d{4,}', line):
                return line
        
        return None


class DuplicateDetector:
    """Detects duplicate documents."""
    
    def __init__(self):
        self._document_hashes: Dict[str, str] = {}
    
    def calculate_hash(self, invoice_number: str, vendor_name: str, total: float, date: str) -> str:
        """Calculate unique hash for document."""
        import hashlib
        
        key = f"{invoice_number or ''}{vendor_name or ''}{total}{date or ''}"
        return hashlib.md5(key.lower().encode()).hexdigest()
    
    async def check_duplicate(
        self,
        invoice_number: str,
        vendor_name: str,
        total: float,
        date: str,
        customer_id: str,
    ) -> Dict:
        """Check if document is a duplicate."""
        doc_hash = self.calculate_hash(invoice_number, vendor_name, total, date)
        
        # In production: check database
        # For now, check in-memory cache
        
        is_duplicate = doc_hash in self._document_hashes
        similar = []
        
        if is_duplicate:
            similar.append({
                "document_id": self._document_hashes[doc_hash],
                "match_score": 1.0,
            })
        
        return {
            "is_duplicate": is_duplicate,
            "similar_invoices": similar,
            "document_hash": doc_hash,
        }
    
    def register_document(self, document_id: str, invoice_number: str, vendor_name: str, total: float, date: str):
        """Register document hash."""
        doc_hash = self.calculate_hash(invoice_number, vendor_name, total, date)
        self._document_hashes[doc_hash] = document_id
```

---

## File 4: OCR Service
**Path:** `backend/app/ai/ocr/service.py`

```python
"""
OCR Service
High-level service for document processing
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.ai.ocr.processor import DocumentProcessor, ExtractedInvoice, ProcessingStatus, document_processor
from app.ai.ocr.classifier import DocumentClassifier, ExpenseCategory, DuplicateDetector
from app.ai.base import AIResult

logger = logging.getLogger(__name__)


class OCRService:
    """Service for document OCR and extraction."""
    
    def __init__(self):
        self.processor = document_processor
        self.classifier = DocumentClassifier()
        self.duplicate_detector = DuplicateDetector()
        self._processed_by_customer: Dict[str, List[str]] = {}
    
    async def process_document(
        self,
        file_data: bytes,
        filename: str,
        customer_id: str,
        options: Dict = None,
    ) -> AIResult:
        """Process a document and extract data."""
        import time
        start_time = time.time()
        
        try:
            # Process document
            extracted = await self.processor.process(
                file_data=file_data,
                filename=filename,
                customer_id=customer_id,
                options=options,
            )
            
            # Auto-categorize
            category, category_confidence = await self.classifier.categorize_expense(
                text=extracted.raw_text,
                vendor_name=extracted.vendor_name,
            )
            
            # Get GL account suggestion
            gl_account = await self.classifier.suggest_gl_account(category)
            
            # Check for duplicates
            duplicate_check = await self.duplicate_detector.check_duplicate(
                invoice_number=extracted.invoice_number,
                vendor_name=extracted.vendor_name,
                total=extracted.total,
                date=extracted.invoice_date.isoformat() if extracted.invoice_date else None,
                customer_id=customer_id,
            )
            
            # Register document
            if not duplicate_check["is_duplicate"]:
                self.duplicate_detector.register_document(
                    document_id=extracted.document_id,
                    invoice_number=extracted.invoice_number,
                    vendor_name=extracted.vendor_name,
                    total=extracted.total,
                    date=extracted.invoice_date.isoformat() if extracted.invoice_date else None,
                )
            
            # Track for customer
            if customer_id not in self._processed_by_customer:
                self._processed_by_customer[customer_id] = []
            self._processed_by_customer[customer_id].append(extracted.document_id)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return AIResult(
                success=True,
                data={
                    "document_id": extracted.document_id,
                    "status": extracted.status.value,
                    "confidence": extracted.confidence,
                    "extracted_data": extracted.to_dict(),
                    "suggested_category": category.value,
                    "category_confidence": category_confidence,
                    "suggested_gl_account": gl_account,
                    "duplicate_check": duplicate_check,
                },
                confidence=extracted.confidence,
                processing_time_ms=processing_time,
            )
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return AIResult(
                success=False,
                error=str(e),
            )
    
    async def get_document(self, document_id: str) -> Optional[Dict]:
        """Get processed document by ID."""
        extracted = self.processor.get_document(document_id)
        if extracted:
            return extracted.to_dict()
        return None
    
    async def update_document(self, document_id: str, updates: Dict) -> AIResult:
        """Update extracted document data (for corrections)."""
        extracted = self.processor.get_document(document_id)
        if not extracted:
            return AIResult(success=False, error="Document not found")
        
        # Apply updates
        for field, value in updates.items():
            if hasattr(extracted, field):
                setattr(extracted, field, value)
        
        # Mark as reviewed
        extracted.status = ProcessingStatus.COMPLETED
        
        return AIResult(
            success=True,
            data=extracted.to_dict(),
        )
    
    async def approve_document(self, document_id: str) -> AIResult:
        """Approve document for processing."""
        extracted = self.processor.get_document(document_id)
        if not extracted:
            return AIResult(success=False, error="Document not found")
        
        extracted.status = ProcessingStatus.COMPLETED
        
        return AIResult(
            success=True,
            data={"document_id": document_id, "status": "completed"},
        )
    
    async def get_customer_documents(self, customer_id: str, limit: int = 50) -> List[Dict]:
        """Get processed documents for customer."""
        doc_ids = self._processed_by_customer.get(customer_id, [])
        
        documents = []
        for doc_id in doc_ids[-limit:]:
            extracted = self.processor.get_document(doc_id)
            if extracted:
                documents.append({
                    "document_id": extracted.document_id,
                    "vendor_name": extracted.vendor_name,
                    "invoice_number": extracted.invoice_number,
                    "total": extracted.total,
                    "status": extracted.status.value,
                    "processed_at": extracted.processed_at.isoformat(),
                })
        
        return documents
    
    async def batch_process(
        self,
        files: List[tuple],  # List of (filename, file_data)
        customer_id: str,
    ) -> AIResult:
        """Process multiple documents."""
        results = []
        
        for filename, file_data in files:
            result = await self.process_document(
                file_data=file_data,
                filename=filename,
                customer_id=customer_id,
            )
            results.append({
                "filename": filename,
                "success": result.success,
                "document_id": result.data.get("document_id") if result.data else None,
                "error": result.error,
            })
        
        successful = sum(1 for r in results if r["success"])
        
        return AIResult(
            success=True,
            data={
                "total": len(files),
                "successful": successful,
                "failed": len(files) - successful,
                "results": results,
            },
        )


# Global service instance
ocr_service = OCRService()
```

---

## File 5: OCR Module Init
**Path:** `backend/app/ai/ocr/__init__.py`

```python
"""
OCR Module
Document processing and data extraction
"""

from app.ai.ocr.processor import (
    DocumentProcessor,
    DocumentType,
    ProcessingStatus,
    LineItem,
    ExtractedInvoice,
    document_processor,
)
from app.ai.ocr.extractor import InvoiceExtractor, OCRTextExtractor
from app.ai.ocr.classifier import (
    DocumentClassifier,
    ExpenseCategory,
    DuplicateDetector,
)
from app.ai.ocr.service import OCRService, ocr_service


__all__ = [
    'DocumentProcessor',
    'DocumentType',
    'ProcessingStatus',
    'LineItem',
    'ExtractedInvoice',
    'document_processor',
    'InvoiceExtractor',
    'OCRTextExtractor',
    'DocumentClassifier',
    'ExpenseCategory',
    'DuplicateDetector',
    'OCRService',
    'ocr_service',
]
```

---

## Summary Part 3

| File | Description | Lines |
|------|-------------|-------|
| `ocr/processor.py` | Document processing pipeline | ~380 |
| `ocr/extractor.py` | AI-powered field extraction | ~280 |
| `ocr/classifier.py` | Document type & expense classification | ~280 |
| `ocr/service.py` | OCR service layer | ~200 |
| `ocr/__init__.py` | Module initialization | ~35 |
| **Total** | | **~1,175 lines** |
