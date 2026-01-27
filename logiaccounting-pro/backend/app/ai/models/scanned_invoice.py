"""
Scanned Invoice Model
Store OCR scan results
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import uuid


# In-memory storage
scanned_invoices_db: Dict[str, 'ScannedInvoice'] = {}


@dataclass
class ScannedInvoice:
    """Scanned invoice record"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ''
    document_id: Optional[str] = None
    original_filename: Optional[str] = None
    file_type: Optional[str] = None
    ocr_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    extracted_data: Dict = field(default_factory=dict)
    category: Optional[str] = None
    category_confidence: Optional[float] = None
    suggested_gl_account: Optional[str] = None
    suggested_cost_center: Optional[str] = None
    validation_status: str = 'pending'
    validation_errors: Optional[List[Dict]] = None
    corrected_data: Optional[Dict] = None
    created_invoice_id: Optional[str] = None
    processing_time_ms: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    validated_at: Optional[datetime] = None
    validated_by: Optional[str] = None

    CATEGORIES = [
        'Office Supplies',
        'Software & Subscriptions',
        'Professional Services',
        'Travel & Entertainment',
        'Utilities',
        'Marketing & Advertising',
        'Equipment',
        'Inventory Purchase',
        'Shipping & Logistics',
        'Insurance',
        'Rent & Facilities',
        'Payroll & Benefits',
        'Other',
    ]

    @property
    def final_data(self) -> Dict[str, Any]:
        """Get final data (corrected if available)"""
        if self.corrected_data:
            return self.corrected_data
        return self.extracted_data

    def save(self):
        scanned_invoices_db[self.id] = self

    @classmethod
    def get_by_id(cls, scan_id: str, tenant_id: str) -> Optional['ScannedInvoice']:
        """Get scanned invoice by ID"""
        scan = scanned_invoices_db.get(scan_id)
        if scan and scan.tenant_id == tenant_id:
            return scan
        return None

    @classmethod
    def get_by_tenant(
        cls,
        tenant_id: str,
        status: str = None,
        limit: int = 20
    ) -> List['ScannedInvoice']:
        """Get scanned invoices for tenant"""
        scans = [s for s in scanned_invoices_db.values() if s.tenant_id == tenant_id]
        if status and status != 'all':
            scans = [s for s in scans if s.validation_status == status]
        scans.sort(key=lambda x: x.created_at, reverse=True)
        return scans[:limit]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'ocr_confidence': self.ocr_confidence,
            'extracted_data': self.extracted_data,
            'category': self.category,
            'category_confidence': self.category_confidence,
            'suggested_gl_account': self.suggested_gl_account,
            'suggested_cost_center': self.suggested_cost_center,
            'validation_status': self.validation_status,
            'validation_errors': self.validation_errors,
            'corrected_data': self.corrected_data,
            'created_invoice_id': self.created_invoice_id,
            'processing_time_ms': self.processing_time_ms,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
