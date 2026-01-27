"""
Document Processor
Core document processing and data extraction
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
import logging
import io

logger = logging.getLogger(__name__)


@dataclass
class LineItem:
    """Invoice line item."""
    description: str = ""
    quantity: float = 1.0
    unit_price: float = 0.0
    amount: float = 0.0
    category: str = ""

    def to_dict(self) -> Dict:
        return {
            "description": self.description,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "amount": self.amount,
            "category": self.category,
        }


@dataclass
class ExtractedInvoice:
    """Extracted invoice data."""
    document_id: str = field(default_factory=lambda: f"doc_{uuid4().hex[:12]}")

    # Vendor info
    vendor_name: str = ""
    vendor_address: str = ""
    vendor_tax_id: str = ""

    # Invoice details
    invoice_number: str = ""
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    po_number: str = ""

    # Amounts
    subtotal: float = 0.0
    tax_amount: float = 0.0
    tax_rate: float = 0.0
    discount: float = 0.0
    total: float = 0.0
    currency: str = "USD"

    # Line items
    line_items: List[LineItem] = field(default_factory=list)

    # Payment info
    payment_terms: str = ""
    bank_info: str = ""

    # Metadata
    confidence: float = 0.0
    extracted_at: datetime = field(default_factory=datetime.utcnow)
    raw_text: str = ""
    status: str = "needs_review"

    def to_dict(self) -> Dict:
        return {
            "document_id": self.document_id,
            "vendor": {
                "name": self.vendor_name,
                "address": self.vendor_address,
                "tax_id": self.vendor_tax_id,
            },
            "invoice_number": self.invoice_number,
            "invoice_date": self.invoice_date,
            "due_date": self.due_date,
            "po_number": self.po_number,
            "subtotal": self.subtotal,
            "tax_amount": self.tax_amount,
            "tax_rate": self.tax_rate,
            "discount": self.discount,
            "total": self.total,
            "currency": self.currency,
            "line_items": [item.to_dict() for item in self.line_items],
            "payment_terms": self.payment_terms,
            "bank_info": self.bank_info,
            "confidence": self.confidence,
            "extracted_at": self.extracted_at.isoformat(),
            "status": self.status,
        }


class DocumentProcessor:
    """Processes documents for data extraction."""

    def __init__(self):
        self._processed_documents: Dict[str, ExtractedInvoice] = {}

    async def process(
        self,
        file_data: bytes,
        filename: str,
        customer_id: str,
    ) -> ExtractedInvoice:
        """Process a document and extract data."""
        logger.info(f"Processing document: {filename}")

        # Determine file type
        file_type = self._detect_file_type(file_data, filename)

        # Convert to image if PDF
        if file_type == "pdf":
            images = await self._pdf_to_images(file_data)
            image_data = images[0] if images else None
        else:
            image_data = file_data

        # Create document record
        doc = ExtractedInvoice()
        doc.raw_text = ""

        # Store for later retrieval
        self._processed_documents[doc.document_id] = doc

        return doc

    def _detect_file_type(self, file_data: bytes, filename: str) -> str:
        """Detect file type from content and filename."""
        # Check magic bytes
        if file_data[:4] == b'%PDF':
            return "pdf"
        elif file_data[:8] == b'\x89PNG\r\n\x1a\n':
            return "png"
        elif file_data[:2] == b'\xff\xd8':
            return "jpeg"

        # Fall back to extension
        ext = filename.lower().split(".")[-1]
        if ext in ["pdf"]:
            return "pdf"
        elif ext in ["png"]:
            return "png"
        elif ext in ["jpg", "jpeg"]:
            return "jpeg"

        return "unknown"

    async def _pdf_to_images(self, pdf_data: bytes) -> List[bytes]:
        """Convert PDF pages to images."""
        images = []
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(stream=pdf_data, filetype="pdf")
            for page in doc:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_data = pix.tobytes("png")
                images.append(img_data)
            doc.close()
        except ImportError:
            logger.warning("PyMuPDF not available, returning raw PDF data")
            images = [pdf_data]
        except Exception as e:
            logger.error(f"PDF conversion error: {e}")
            images = [pdf_data]

        return images

    def get_document(self, document_id: str) -> Optional[ExtractedInvoice]:
        """Get a processed document."""
        return self._processed_documents.get(document_id)

    def update_document(self, document_id: str, updates: Dict) -> Optional[ExtractedInvoice]:
        """Update a processed document."""
        doc = self._processed_documents.get(document_id)
        if not doc:
            return None

        for key, value in updates.items():
            if hasattr(doc, key):
                setattr(doc, key, value)

        return doc

    def approve_document(self, document_id: str) -> Optional[ExtractedInvoice]:
        """Approve a document for processing."""
        doc = self._processed_documents.get(document_id)
        if not doc:
            return None

        doc.status = "completed"
        return doc

    def get_customer_documents(self, customer_id: str, limit: int = 50) -> List[Dict]:
        """Get documents for a customer."""
        # In real implementation, this would query from database
        return [doc.to_dict() for doc in list(self._processed_documents.values())[:limit]]


# Global processor instance
document_processor = DocumentProcessor()
