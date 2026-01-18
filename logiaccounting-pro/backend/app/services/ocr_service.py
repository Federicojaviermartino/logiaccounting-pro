"""
Smart Invoice OCR + Auto-Categorization Service
Uses Tesseract for local OCR and OpenAI Vision for enhanced extraction
"""

import os
import re
import base64
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
import json

# Optional imports - gracefully handle missing dependencies
try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import fitz  # PyMuPDF for PDF processing
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


@dataclass
class InvoiceData:
    """Extracted invoice data structure"""
    vendor_name: Optional[str] = None
    vendor_tax_id: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    currency: str = "USD"
    line_items: List[Dict[str, Any]] = None
    raw_text: Optional[str] = None
    confidence_score: float = 0.0
    suggested_category_id: Optional[str] = None
    suggested_category_name: Optional[str] = None
    suggested_project_id: Optional[str] = None
    suggested_project_code: Optional[str] = None
    extraction_method: str = "unknown"

    def __post_init__(self):
        if self.line_items is None:
            self.line_items = []

    def to_dict(self) -> Dict:
        return asdict(self)


class OCRService:
    """
    Intelligent OCR service for invoice processing
    Supports: PDF, PNG, JPG, JPEG, TIFF, BMP
    """

    SUPPORTED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'}

    # Common patterns for invoice data extraction
    PATTERNS = {
        'invoice_number': [
            r'(?:invoice|inv|factura|nro?\.?)\s*[#:№]?\s*([A-Z0-9\-]+)',
            r'(?:number|numero)\s*[#:№]?\s*([A-Z0-9\-]+)',
        ],
        'date': [
            r'(?:date|fecha|dated?)\s*[:\s]\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            r'(\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})',
        ],
        'amount': [
            r'(?:total|amount|monto|importe)\s*[:\s]?\s*\$?\s*([\d,]+\.?\d*)',
            r'\$\s*([\d,]+\.?\d{2})',
            r'([\d,]+\.?\d{2})\s*(?:USD|EUR|ARS)',
        ],
        'tax': [
            r'(?:tax|iva|vat|impuesto)\s*[:\s]?\s*\$?\s*([\d,]+\.?\d*)',
            r'(?:21%|10\.5%)\s*[:\s]?\s*\$?\s*([\d,]+\.?\d*)',
        ],
        'tax_id': [
            r'(?:cuit|rfc|nit|tax\s*id|vat)\s*[:\s]?\s*([\d\-]+)',
            r'(\d{2}\-\d{8}\-\d)',  # CUIT Argentina format
        ],
    }

    def __init__(self):
        self.openai_client = None
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            self.openai_client = OpenAI()

    def extract_from_file(self, file_path: str) -> InvoiceData:
        """
        Extract invoice data from a file (PDF or image)
        """
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}")

        # Try OpenAI Vision first for best results
        if self.openai_client:
            try:
                return self._extract_with_openai_vision(file_path)
            except Exception as e:
                print(f"OpenAI Vision failed, falling back to Tesseract: {e}")

        # Fallback to Tesseract OCR
        if TESSERACT_AVAILABLE:
            return self._extract_with_tesseract(file_path)

        raise RuntimeError("No OCR engine available. Install pytesseract or configure OpenAI API key.")

    def extract_from_bytes(self, file_bytes: bytes, filename: str) -> InvoiceData:
        """
        Extract invoice data from file bytes
        """
        import tempfile
        ext = os.path.splitext(filename)[1].lower()

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            return self.extract_from_file(tmp_path)
        finally:
            os.unlink(tmp_path)

    def _extract_with_tesseract(self, file_path: str) -> InvoiceData:
        """
        Extract text using Tesseract OCR and parse invoice data
        """
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.pdf':
            text = self._pdf_to_text(file_path)
        else:
            image = Image.open(file_path)
            # Preprocess image for better OCR
            image = self._preprocess_image(image)
            text = pytesseract.image_to_string(image, lang='eng+spa')

        invoice_data = self._parse_text_to_invoice(text)
        invoice_data.extraction_method = "tesseract"
        invoice_data.raw_text = text

        return invoice_data

    def _extract_with_openai_vision(self, file_path: str) -> InvoiceData:
        """
        Extract invoice data using OpenAI Vision API
        """
        ext = os.path.splitext(file_path)[1].lower()

        # Convert PDF to image if needed
        if ext == '.pdf':
            images = self._pdf_to_images(file_path)
            if not images:
                raise ValueError("Could not extract images from PDF")
            image_data = images[0]  # Use first page
        else:
            with open(file_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

        # Determine media type
        media_type = "image/png" if ext == '.pdf' else f"image/{ext.lstrip('.')}"
        if ext in ['.jpg', '.jpeg']:
            media_type = "image/jpeg"

        prompt = """Analyze this invoice image and extract the following information in JSON format:
{
    "vendor_name": "Company name of the vendor/supplier",
    "vendor_tax_id": "Tax ID, CUIT, RFC, or VAT number",
    "invoice_number": "Invoice number or reference",
    "invoice_date": "Date in YYYY-MM-DD format",
    "due_date": "Due date in YYYY-MM-DD format if present",
    "subtotal": numeric value without currency symbol,
    "tax_amount": numeric value for tax/IVA/VAT,
    "total_amount": numeric total value,
    "currency": "USD", "EUR", "ARS", etc.,
    "line_items": [
        {"description": "item description", "quantity": number, "unit_price": number, "total": number}
    ],
    "confidence_score": 0.0 to 1.0 based on image clarity and data completeness
}

Return ONLY the JSON object, no additional text. Use null for missing values."""

        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_data}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000
        )

        # Parse JSON response
        json_text = response.choices[0].message.content.strip()
        # Clean up markdown code blocks if present
        if json_text.startswith("```"):
            json_text = re.sub(r'^```(?:json)?\n?', '', json_text)
            json_text = re.sub(r'\n?```$', '', json_text)

        data = json.loads(json_text)

        invoice_data = InvoiceData(
            vendor_name=data.get("vendor_name"),
            vendor_tax_id=data.get("vendor_tax_id"),
            invoice_number=data.get("invoice_number"),
            invoice_date=data.get("invoice_date"),
            due_date=data.get("due_date"),
            subtotal=data.get("subtotal"),
            tax_amount=data.get("tax_amount"),
            total_amount=data.get("total_amount"),
            currency=data.get("currency", "USD"),
            line_items=data.get("line_items", []),
            confidence_score=data.get("confidence_score", 0.8),
            extraction_method="openai_vision"
        )

        return invoice_data

    def _preprocess_image(self, image: "Image.Image") -> "Image.Image":
        """
        Preprocess image for better OCR results
        """
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')

        # Resize if too small
        min_dimension = 1000
        if min(image.size) < min_dimension:
            ratio = min_dimension / min(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        return image

    def _pdf_to_text(self, pdf_path: str) -> str:
        """
        Extract text from PDF using PyMuPDF
        """
        if not PDF_AVAILABLE:
            raise RuntimeError("PyMuPDF not installed. Run: pip install pymupdf")

        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text

    def _pdf_to_images(self, pdf_path: str) -> List[str]:
        """
        Convert PDF pages to base64 images
        """
        if not PDF_AVAILABLE:
            raise RuntimeError("PyMuPDF not installed. Run: pip install pymupdf")

        doc = fitz.open(pdf_path)
        images = []
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
            img_bytes = pix.tobytes("png")
            images.append(base64.b64encode(img_bytes).decode('utf-8'))
        doc.close()
        return images

    def _parse_text_to_invoice(self, text: str) -> InvoiceData:
        """
        Parse raw text to extract invoice fields using regex patterns
        """
        text_lower = text.lower()

        invoice_data = InvoiceData()
        confidence_factors = []

        # Extract invoice number
        for pattern in self.PATTERNS['invoice_number']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_data.invoice_number = match.group(1).strip()
                confidence_factors.append(0.2)
                break

        # Extract dates
        dates_found = []
        for pattern in self.PATTERNS['date']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates_found.extend(matches)

        if dates_found:
            # Try to parse and assign dates
            parsed_dates = []
            for date_str in dates_found[:2]:
                parsed = self._parse_date(date_str)
                if parsed:
                    parsed_dates.append(parsed)

            if parsed_dates:
                invoice_data.invoice_date = parsed_dates[0]
                confidence_factors.append(0.15)
                if len(parsed_dates) > 1:
                    invoice_data.due_date = parsed_dates[1]

        # Extract amounts
        amounts = []
        for pattern in self.PATTERNS['amount']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches:
                try:
                    amount = float(m.replace(',', ''))
                    if amount > 0:
                        amounts.append(amount)
                except ValueError:
                    pass

        if amounts:
            # Assume largest amount is total
            amounts.sort(reverse=True)
            invoice_data.total_amount = amounts[0]
            confidence_factors.append(0.25)
            if len(amounts) > 1:
                invoice_data.subtotal = amounts[1]

        # Extract tax
        for pattern in self.PATTERNS['tax']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    invoice_data.tax_amount = float(match.group(1).replace(',', ''))
                    confidence_factors.append(0.1)
                except ValueError:
                    pass
                break

        # Extract tax ID
        for pattern in self.PATTERNS['tax_id']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_data.vendor_tax_id = match.group(1).strip()
                confidence_factors.append(0.1)
                break

        # Try to extract vendor name (first line that looks like a company name)
        lines = text.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if len(line) > 3 and len(line) < 100:
                # Skip lines that look like addresses or dates
                if not re.search(r'\d{2}[\/\-]\d{2}[\/\-]\d{2,4}', line):
                    if not re.search(r'invoice|factura|date|total|subtotal', line.lower()):
                        invoice_data.vendor_name = line
                        confidence_factors.append(0.2)
                        break

        # Calculate overall confidence
        invoice_data.confidence_score = min(sum(confidence_factors), 1.0)

        return invoice_data

    def _parse_date(self, date_str: str) -> Optional[str]:
        """
        Parse various date formats to YYYY-MM-DD
        """
        date_formats = [
            '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d',
            '%d-%m-%Y', '%m-%d-%Y', '%Y-%m-%d',
            '%d.%m.%Y', '%m.%d.%Y', '%Y.%m.%d',
            '%d/%m/%y', '%m/%d/%y',
        ]

        for fmt in date_formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return parsed.strftime('%Y-%m-%d')
            except ValueError:
                continue

        return None


class AutoCategorizationService:
    """
    Auto-categorizes expenses based on vendor patterns and historical data
    """

    # Default category keywords mapping
    CATEGORY_KEYWORDS = {
        'office_supplies': ['staples', 'office depot', 'paper', 'toner', 'printer', 'stationery'],
        'utilities': ['electricity', 'water', 'gas', 'internet', 'phone', 'telecom', 'edenor', 'metrogas'],
        'raw_materials': ['steel', 'aluminum', 'metal', 'lumber', 'wood', 'plastic', 'chemical'],
        'equipment': ['machine', 'tool', 'equipment', 'hardware', 'computer', 'laptop'],
        'services': ['consulting', 'service', 'maintenance', 'repair', 'cleaning'],
        'transport': ['shipping', 'freight', 'logistics', 'transport', 'fedex', 'ups', 'dhl'],
        'labor': ['salary', 'wages', 'contractor', 'freelance', 'payroll'],
    }

    def __init__(self, db):
        """
        Initialize with database reference for historical pattern learning
        """
        self.db = db
        self.vendor_category_cache: Dict[str, str] = {}

    def suggest_category(self, invoice_data: InvoiceData) -> Tuple[Optional[str], Optional[str]]:
        """
        Suggest a category based on invoice data
        Returns: (category_id, category_name)
        """
        # Check vendor cache first
        if invoice_data.vendor_name:
            vendor_lower = invoice_data.vendor_name.lower()

            # Check if we've categorized this vendor before
            if vendor_lower in self.vendor_category_cache:
                cat_id = self.vendor_category_cache[vendor_lower]
                cat = self.db.categories.find_by_id(cat_id)
                if cat:
                    return cat["id"], cat["name"]

            # Look for historical transactions from this vendor
            for tx in self.db.transactions._data:
                if tx.get("vendor_name", "").lower() == vendor_lower and tx.get("category_id"):
                    self.vendor_category_cache[vendor_lower] = tx["category_id"]
                    cat = self.db.categories.find_by_id(tx["category_id"])
                    if cat:
                        return cat["id"], cat["name"]

        # Keyword-based categorization
        search_text = " ".join([
            invoice_data.vendor_name or "",
            " ".join(item.get("description", "") for item in invoice_data.line_items)
        ]).lower()

        # Find matching category by keywords
        categories = self.db.categories.find_all({"type": "expense"})

        for cat in categories:
            cat_name_lower = cat["name"].lower().replace(" ", "_")
            keywords = self.CATEGORY_KEYWORDS.get(cat_name_lower, [])

            for keyword in keywords:
                if keyword in search_text:
                    if invoice_data.vendor_name:
                        self.vendor_category_cache[invoice_data.vendor_name.lower()] = cat["id"]
                    return cat["id"], cat["name"]

        # Default to first expense category if no match
        if categories:
            return categories[0]["id"], categories[0]["name"]

        return None, None

    def suggest_project(self, invoice_data: InvoiceData) -> Tuple[Optional[str], Optional[str]]:
        """
        Suggest a project based on invoice data and historical patterns
        Returns: (project_id, project_code)
        """
        if not invoice_data.vendor_name:
            return None, None

        vendor_lower = invoice_data.vendor_name.lower()

        # Look for historical transactions from this vendor
        for tx in self.db.transactions._data:
            if tx.get("vendor_name", "").lower() == vendor_lower and tx.get("project_id"):
                project = self.db.projects.find_by_id(tx["project_id"])
                if project and project.get("status") == "active":
                    return project["id"], project["code"]

        return None, None

    def learn_from_transaction(self, vendor_name: str, category_id: str, project_id: Optional[str] = None):
        """
        Learn from a confirmed transaction to improve future suggestions
        """
        if vendor_name:
            self.vendor_category_cache[vendor_name.lower()] = category_id


# Service instances
ocr_service = OCRService()
