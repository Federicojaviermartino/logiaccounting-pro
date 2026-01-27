"""
Document Classifier
Classify documents and detect duplicates
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib
import logging
from datetime import datetime

from app.ai.client import ai_client
from app.ai.config import get_model_config

logger = logging.getLogger(__name__)


class ExpenseCategory(str, Enum):
    """Expense categories."""
    OFFICE_SUPPLIES = "office_supplies"
    SOFTWARE = "software"
    HARDWARE = "hardware"
    TRAVEL = "travel"
    MEALS = "meals"
    UTILITIES = "utilities"
    RENT = "rent"
    PROFESSIONAL_SERVICES = "professional_services"
    MARKETING = "marketing"
    INSURANCE = "insurance"
    SHIPPING = "shipping"
    TELECOMMUNICATIONS = "telecommunications"
    MAINTENANCE = "maintenance"
    OTHER = "other"


CATEGORY_KEYWORDS = {
    ExpenseCategory.OFFICE_SUPPLIES: ["staples", "paper", "pen", "ink", "toner", "office depot", "staples"],
    ExpenseCategory.SOFTWARE: ["software", "license", "subscription", "saas", "cloud", "adobe", "microsoft", "google workspace"],
    ExpenseCategory.HARDWARE: ["computer", "laptop", "monitor", "keyboard", "mouse", "printer", "server"],
    ExpenseCategory.TRAVEL: ["airline", "hotel", "flight", "uber", "lyft", "rental car", "parking", "airbnb"],
    ExpenseCategory.MEALS: ["restaurant", "food", "meal", "lunch", "dinner", "catering", "doordash", "grubhub"],
    ExpenseCategory.UTILITIES: ["electric", "gas", "water", "utility", "power", "energy"],
    ExpenseCategory.RENT: ["rent", "lease", "property"],
    ExpenseCategory.PROFESSIONAL_SERVICES: ["consulting", "legal", "accounting", "attorney", "lawyer", "cpa"],
    ExpenseCategory.MARKETING: ["marketing", "advertising", "ads", "promotion", "facebook ads", "google ads"],
    ExpenseCategory.INSURANCE: ["insurance", "policy", "premium", "coverage"],
    ExpenseCategory.SHIPPING: ["shipping", "fedex", "ups", "usps", "freight", "delivery", "dhl"],
    ExpenseCategory.TELECOMMUNICATIONS: ["phone", "internet", "telecom", "at&t", "verizon", "comcast"],
    ExpenseCategory.MAINTENANCE: ["repair", "maintenance", "service", "fix"],
}


class DocumentClassifier:
    """Classifies documents and expenses."""

    def __init__(self):
        self.model_config = get_model_config("fast")

    def classify_expense(self, description: str, vendor_name: str = "") -> Tuple[ExpenseCategory, float]:
        """Classify expense category based on description and vendor."""
        text = f"{description} {vendor_name}".lower()

        # Score each category
        scores = {}
        for category, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in text)
            if score > 0:
                scores[category] = score

        if not scores:
            return ExpenseCategory.OTHER, 0.5

        # Return highest scoring category
        best_category = max(scores, key=scores.get)
        confidence = min(0.95, 0.6 + scores[best_category] * 0.1)

        return best_category, confidence

    async def classify_with_ai(self, description: str, vendor_name: str = "") -> Tuple[ExpenseCategory, float]:
        """Classify expense using AI."""
        prompt = f"""Classify this expense into one of these categories:
- office_supplies
- software
- hardware
- travel
- meals
- utilities
- rent
- professional_services
- marketing
- insurance
- shipping
- telecommunications
- maintenance
- other

Expense: {description}
Vendor: {vendor_name}

Return only the category name, nothing else."""

        try:
            response = await ai_client.complete(prompt, model_config=self.model_config)
            category_str = response.strip().lower().replace(" ", "_")

            try:
                category = ExpenseCategory(category_str)
                return category, 0.9
            except ValueError:
                # Fall back to keyword matching
                return self.classify_expense(description, vendor_name)

        except Exception as e:
            logger.error(f"AI classification failed: {e}")
            return self.classify_expense(description, vendor_name)

    def classify_document_type(self, text: str) -> Tuple[str, float]:
        """Classify document type from text."""
        text_lower = text.lower()

        type_keywords = {
            "invoice": ["invoice", "bill to", "due date", "payment due", "total due"],
            "receipt": ["receipt", "paid", "transaction", "payment received"],
            "quote": ["quote", "quotation", "estimate", "proposal"],
            "purchase_order": ["purchase order", "po number", "order"],
            "statement": ["statement", "balance due", "account summary"],
        }

        scores = {}
        for doc_type, keywords in type_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[doc_type] = score

        if not scores:
            return "unknown", 0.3

        best_type = max(scores, key=scores.get)
        confidence = min(0.95, 0.5 + scores[best_type] * 0.15)

        return best_type, confidence


class DuplicateDetector:
    """Detects duplicate documents."""

    def __init__(self):
        self._document_hashes: Dict[str, List[Dict]] = {}

    def compute_hash(self, invoice_number: str, vendor_name: str, total: float, date: str) -> str:
        """Compute document hash for duplicate detection."""
        content = f"{invoice_number}|{vendor_name}|{total:.2f}|{date}"
        return hashlib.md5(content.encode()).hexdigest()

    def check_duplicate(
        self,
        customer_id: str,
        invoice_number: str,
        vendor_name: str,
        total: float,
        date: str,
    ) -> Optional[Dict]:
        """Check if document is a duplicate."""
        doc_hash = self.compute_hash(invoice_number, vendor_name, total, date)

        customer_docs = self._document_hashes.get(customer_id, [])

        for doc in customer_docs:
            if doc["hash"] == doc_hash:
                return {
                    "is_duplicate": True,
                    "original_document_id": doc["document_id"],
                    "similarity": 1.0,
                }

            # Check partial match (same invoice number and vendor)
            if doc["invoice_number"] == invoice_number and doc["vendor_name"].lower() == vendor_name.lower():
                return {
                    "is_duplicate": True,
                    "original_document_id": doc["document_id"],
                    "similarity": 0.9,
                    "reason": "Same invoice number and vendor",
                }

        return {"is_duplicate": False}

    def register_document(
        self,
        customer_id: str,
        document_id: str,
        invoice_number: str,
        vendor_name: str,
        total: float,
        date: str,
    ):
        """Register a document for future duplicate detection."""
        doc_hash = self.compute_hash(invoice_number, vendor_name, total, date)

        if customer_id not in self._document_hashes:
            self._document_hashes[customer_id] = []

        self._document_hashes[customer_id].append({
            "document_id": document_id,
            "hash": doc_hash,
            "invoice_number": invoice_number,
            "vendor_name": vendor_name,
            "total": total,
            "date": date,
            "registered_at": datetime.utcnow().isoformat(),
        })


# Global instances
document_classifier = DocumentClassifier()
duplicate_detector = DuplicateDetector()
