"""
OCR Service
High-level service for document processing
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

from app.ai.base import AIResult
from app.ai.ocr.processor import DocumentProcessor, ExtractedInvoice, document_processor
from app.ai.ocr.extractor import InvoiceExtractor, invoice_extractor
from app.ai.ocr.classifier import DocumentClassifier, DuplicateDetector, document_classifier, duplicate_detector

logger = logging.getLogger(__name__)


class OCRService:
    """Service layer for OCR and document processing."""

    def __init__(
        self,
        processor: DocumentProcessor = None,
        extractor: InvoiceExtractor = None,
        classifier: DocumentClassifier = None,
        dup_detector: DuplicateDetector = None,
    ):
        self.processor = processor or document_processor
        self.extractor = extractor or invoice_extractor
        self.classifier = classifier or document_classifier
        self.dup_detector = dup_detector or duplicate_detector

    async def process_document(
        self,
        file_data: bytes,
        filename: str,
        customer_id: str,
    ) -> AIResult:
        """Process a document and extract data."""
        logger.info(f"Processing document {filename} for customer {customer_id}")

        try:
            # Initial processing
            doc = await self.processor.process(file_data, filename, customer_id)

            # Extract data using AI
            extracted = await self.extractor.extract(file_data)

            # Copy extracted data to document
            doc.vendor_name = extracted.vendor_name
            doc.vendor_address = extracted.vendor_address
            doc.vendor_tax_id = extracted.vendor_tax_id
            doc.invoice_number = extracted.invoice_number
            doc.invoice_date = extracted.invoice_date
            doc.due_date = extracted.due_date
            doc.po_number = extracted.po_number
            doc.subtotal = extracted.subtotal
            doc.tax_rate = extracted.tax_rate
            doc.tax_amount = extracted.tax_amount
            doc.discount = extracted.discount
            doc.total = extracted.total
            doc.currency = extracted.currency
            doc.line_items = extracted.line_items
            doc.payment_terms = extracted.payment_terms
            doc.bank_info = extracted.bank_info
            doc.confidence = extracted.confidence
            doc.status = extracted.status

            # Check for duplicates
            duplicate_check = self.dup_detector.check_duplicate(
                customer_id=customer_id,
                invoice_number=doc.invoice_number,
                vendor_name=doc.vendor_name,
                total=doc.total,
                date=doc.invoice_date or "",
            )

            # Classify expense category
            suggested_category = None
            if doc.line_items:
                desc = " ".join([item.description for item in doc.line_items])
                category, _ = self.classifier.classify_expense(desc, doc.vendor_name)
                suggested_category = category.value

            # Register document for duplicate detection
            if not duplicate_check.get("is_duplicate"):
                self.dup_detector.register_document(
                    customer_id=customer_id,
                    document_id=doc.document_id,
                    invoice_number=doc.invoice_number,
                    vendor_name=doc.vendor_name,
                    total=doc.total,
                    date=doc.invoice_date or "",
                )

            return AIResult.ok({
                "document_id": doc.document_id,
                "extracted_data": doc.to_dict(),
                "confidence": doc.confidence,
                "status": doc.status,
                "duplicate_check": duplicate_check,
                "suggested_category": suggested_category,
            })

        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return AIResult.fail(str(e))

    async def batch_process(
        self,
        files: List[Tuple[str, bytes]],
        customer_id: str,
    ) -> AIResult:
        """Process multiple documents."""
        results = []

        for filename, file_data in files:
            result = await self.process_document(file_data, filename, customer_id)
            results.append({
                "filename": filename,
                "success": result.success,
                "data": result.data if result.success else None,
                "error": result.error if not result.success else None,
            })

        successful = sum(1 for r in results if r["success"])

        return AIResult.ok({
            "total": len(files),
            "successful": successful,
            "failed": len(files) - successful,
            "results": results,
        })

    async def get_customer_documents(self, customer_id: str, limit: int = 50) -> List[Dict]:
        """Get processed documents for customer."""
        return self.processor.get_customer_documents(customer_id, limit)

    async def get_document(self, document_id: str) -> Optional[Dict]:
        """Get a specific document."""
        doc = self.processor.get_document(document_id)
        return doc.to_dict() if doc else None

    async def update_document(self, document_id: str, updates: Dict) -> AIResult:
        """Update document data."""
        doc = self.processor.update_document(document_id, updates)
        if not doc:
            return AIResult.fail("Document not found")
        return AIResult.ok(doc.to_dict())

    async def approve_document(self, document_id: str) -> AIResult:
        """Approve a document."""
        doc = self.processor.approve_document(document_id)
        if not doc:
            return AIResult.fail("Document not found")
        return AIResult.ok(doc.to_dict())


# Global service instance
ocr_service = OCRService()
