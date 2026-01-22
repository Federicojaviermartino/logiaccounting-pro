"""
AI Invoice OCR Routes
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from pydantic import BaseModel

from app.utils.auth import get_current_user, require_roles
from ..services.invoice import InvoiceOCR, InvoiceExtractor, InvoiceCategorizer
from ..models.scanned_invoice import ScannedInvoice

router = APIRouter()
ocr_service = InvoiceOCR()
extractor = InvoiceExtractor()
categorizer = InvoiceCategorizer()


class ScanResponse(BaseModel):
    """Scan response"""
    id: str
    ocr_confidence: Optional[float]
    extracted_data: dict
    category: Optional[str]
    category_confidence: Optional[float]
    suggested_gl_account: Optional[str]
    validation_status: str
    validation_errors: Optional[list]


@router.post("/scan", response_model=ScanResponse)
async def scan_invoice(
    file: UploadFile = File(...),
    use_llm: bool = Form(True),
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """
    Scan and extract data from invoice image/PDF

    - Performs OCR on the document
    - Extracts structured data using AI
    - Auto-categorizes the invoice
    - Suggests GL account mapping
    """
    try:
        tenant_id = current_user.get("tenant_id", "default")

        # Read file
        content = await file.read()
        filename = file.filename

        # Determine file type and extract text
        if filename and filename.lower().endswith('.pdf'):
            ocr_text, confidence = ocr_service.extract_from_pdf(content)
        else:
            ocr_text, confidence = ocr_service.extract_text(content)

        # Extract structured data
        scan = await extractor.extract(
            ocr_text=ocr_text,
            tenant_id=tenant_id,
            filename=filename,
            use_llm=use_llm,
        )
        scan.ocr_confidence = confidence

        # Categorize
        scan = await categorizer.categorize(scan, use_llm=use_llm)

        return ScanResponse(
            id=scan.id,
            ocr_confidence=scan.ocr_confidence,
            extracted_data=scan.extracted_data,
            category=scan.category,
            category_confidence=scan.category_confidence,
            suggested_gl_account=scan.suggested_gl_account,
            validation_status=scan.validation_status,
            validation_errors=scan.validation_errors,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invoice scan failed: {str(e)}"
        )


@router.get("/scans")
async def get_scans(
    status: Optional[str] = None,
    limit: int = 20,
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """Get scanned invoices"""
    tenant_id = current_user.get("tenant_id", "default")
    scans = ScannedInvoice.get_by_tenant(tenant_id, status, limit)
    return [s.to_dict() for s in scans]


@router.get("/scans/{scan_id}")
async def get_scan(
    scan_id: str,
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """Get scan by ID"""
    tenant_id = current_user.get("tenant_id", "default")
    scan = ScannedInvoice.get_by_id(scan_id, tenant_id)

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )

    return scan.to_dict()


class CorrectionRequest(BaseModel):
    """Correction request"""
    corrected_data: dict


@router.put("/scans/{scan_id}/correct")
async def correct_scan(
    scan_id: str,
    request: CorrectionRequest,
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """Submit corrections for a scan"""
    tenant_id = current_user.get("tenant_id", "default")
    scan = ScannedInvoice.get_by_id(scan_id, tenant_id)

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )

    from datetime import datetime
    scan.corrected_data = request.corrected_data
    scan.validation_status = 'corrected'
    scan.validated_at = datetime.utcnow()
    scan.validated_by = current_user.get("id")
    scan.save()

    return scan.to_dict()


@router.post("/scans/{scan_id}/approve")
async def approve_scan(
    scan_id: str,
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """Approve a scan for invoice creation"""
    tenant_id = current_user.get("tenant_id", "default")
    scan = ScannedInvoice.get_by_id(scan_id, tenant_id)

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )

    from datetime import datetime
    scan.validation_status = 'approved'
    scan.validated_at = datetime.utcnow()
    scan.validated_by = current_user.get("id")
    scan.save()

    return scan.to_dict()


@router.get("/categories")
async def get_categories():
    """Get available invoice categories"""
    return {
        "categories": ScannedInvoice.CATEGORIES
    }
