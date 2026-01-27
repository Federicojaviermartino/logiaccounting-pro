"""
OCR Module
AI-powered document processing and data extraction
"""

from app.ai.ocr.processor import DocumentProcessor, ExtractedInvoice, LineItem
from app.ai.ocr.extractor import InvoiceExtractor
from app.ai.ocr.classifier import DocumentClassifier, ExpenseCategory, DuplicateDetector
from app.ai.ocr.service import ocr_service, OCRService


__all__ = [
    'DocumentProcessor',
    'ExtractedInvoice',
    'LineItem',
    'InvoiceExtractor',
    'DocumentClassifier',
    'ExpenseCategory',
    'DuplicateDetector',
    'ocr_service',
    'OCRService',
]
