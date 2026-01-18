"""
OCR Invoice Processing Routes
Smart Invoice OCR + Auto-Categorization API endpoints
"""

import os
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from pydantic import BaseModel

from app.utils.auth import get_current_user, require_roles
from app.models.store import db
from app.services.ocr_service import ocr_service, AutoCategorizationService, InvoiceData

router = APIRouter()

# Initialize auto-categorization service
auto_categorizer = AutoCategorizationService(db)

# Maximum file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024


class OCRResponse(BaseModel):
    """Response model for OCR extraction"""
    success: bool
    data: dict
    message: Optional[str] = None


class CreateTransactionFromOCR(BaseModel):
    """Request to create a transaction from OCR data"""
    vendor_name: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    subtotal: Optional[float] = None
    tax_amount: float = 0
    total_amount: float
    category_id: Optional[str] = None
    project_id: Optional[str] = None
    description: Optional[str] = None
    create_payment: bool = False


@router.post("/extract", response_model=OCRResponse)
async def extract_invoice_data(
    file: UploadFile = File(...),
    auto_categorize: bool = Form(default=True),
    current_user: dict = Depends(get_current_user)
):
    """
    Extract data from an invoice image or PDF

    Supports: PDF, PNG, JPG, JPEG, TIFF, BMP, GIF

    Returns extracted invoice data with optional auto-categorization
    """
    # Validate file type
    filename = file.filename or "unknown"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ocr_service.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {ext}. Supported: {', '.join(ocr_service.SUPPORTED_EXTENSIONS)}"
        )

    # Read file content
    content = await file.read()

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    try:
        # Extract invoice data
        invoice_data = ocr_service.extract_from_bytes(content, filename)

        # Auto-categorize if requested
        if auto_categorize:
            cat_id, cat_name = auto_categorizer.suggest_category(invoice_data)
            proj_id, proj_code = auto_categorizer.suggest_project(invoice_data)

            invoice_data.suggested_category_id = cat_id
            invoice_data.suggested_category_name = cat_name
            invoice_data.suggested_project_id = proj_id
            invoice_data.suggested_project_code = proj_code

        return OCRResponse(
            success=True,
            data=invoice_data.to_dict(),
            message=f"Invoice extracted successfully using {invoice_data.extraction_method}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR extraction failed: {str(e)}"
        )


@router.post("/extract-and-create")
async def extract_and_create_transaction(
    file: UploadFile = File(...),
    auto_create: bool = Form(default=False),
    create_payment: bool = Form(default=False),
    current_user: dict = Depends(get_current_user)
):
    """
    Extract invoice data and optionally create a transaction automatically

    If auto_create=True, creates the transaction immediately with suggested category/project.
    If auto_create=False, returns extracted data for user confirmation.
    """
    # First extract the data
    filename = file.filename or "unknown"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ocr_service.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {ext}"
        )

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large"
        )

    try:
        invoice_data = ocr_service.extract_from_bytes(content, filename)

        # Get category and project suggestions
        cat_id, cat_name = auto_categorizer.suggest_category(invoice_data)
        proj_id, proj_code = auto_categorizer.suggest_project(invoice_data)

        invoice_data.suggested_category_id = cat_id
        invoice_data.suggested_category_name = cat_name
        invoice_data.suggested_project_id = proj_id
        invoice_data.suggested_project_code = proj_code

        if not auto_create:
            return {
                "success": True,
                "auto_created": False,
                "extracted_data": invoice_data.to_dict(),
                "message": "Review and confirm to create transaction"
            }

        # Auto-create transaction
        if not invoice_data.total_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot auto-create: total amount not detected"
            )

        transaction_data = {
            "type": "expense",
            "amount": invoice_data.total_amount,
            "tax_amount": invoice_data.tax_amount or 0,
            "category_id": cat_id,
            "project_id": proj_id,
            "description": f"Invoice from {invoice_data.vendor_name or 'Unknown'}" +
                          (f" - {invoice_data.invoice_number}" if invoice_data.invoice_number else ""),
            "invoice_number": invoice_data.invoice_number,
            "date": invoice_data.invoice_date,
            "vendor_name": invoice_data.vendor_name,
            "created_by": current_user["id"],
            "ocr_extracted": True,
            "ocr_confidence": invoice_data.confidence_score
        }

        transaction = db.transactions.create(transaction_data)

        # Learn from this categorization
        if invoice_data.vendor_name and cat_id:
            auto_categorizer.learn_from_transaction(
                invoice_data.vendor_name,
                cat_id,
                proj_id
            )

        result = {
            "success": True,
            "auto_created": True,
            "transaction": transaction,
            "extracted_data": invoice_data.to_dict()
        }

        # Create payment if requested and due date exists
        if create_payment and invoice_data.due_date:
            payment_data = {
                "type": "payable",
                "amount": invoice_data.total_amount,
                "due_date": invoice_data.due_date,
                "description": f"Payment for invoice {invoice_data.invoice_number or 'N/A'}",
                "reference": invoice_data.invoice_number,
                "project_id": proj_id,
                "status": "pending",
                "related_transaction_id": transaction["id"]
            }
            payment = db.payments.create(payment_data)
            result["payment"] = payment

        # Create notification for admin
        if current_user["role"] != "admin":
            db.notifications.create({
                "type": "ocr_transaction",
                "title": "OCR Transaction Created",
                "message": f"Auto-created expense of ${invoice_data.total_amount:.2f} from scanned invoice",
                "target_role": "admin",
                "related_id": transaction["id"],
                "related_type": "transaction",
                "read": False
            })

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )


@router.post("/create-from-extracted")
async def create_transaction_from_extracted(
    data: CreateTransactionFromOCR,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a transaction from previously extracted OCR data (after user confirmation)
    """
    transaction_data = {
        "type": "expense",
        "amount": data.total_amount,
        "tax_amount": data.tax_amount,
        "category_id": data.category_id,
        "project_id": data.project_id,
        "description": data.description or f"Invoice from {data.vendor_name or 'Unknown'}",
        "invoice_number": data.invoice_number,
        "date": data.invoice_date,
        "vendor_name": data.vendor_name,
        "created_by": current_user["id"],
        "ocr_extracted": True
    }

    transaction = db.transactions.create(transaction_data)

    # Learn from this categorization
    if data.vendor_name and data.category_id:
        auto_categorizer.learn_from_transaction(
            data.vendor_name,
            data.category_id,
            data.project_id
        )

    result = {"success": True, "transaction": transaction}

    # Create payment if requested
    if data.create_payment and data.due_date:
        payment_data = {
            "type": "payable",
            "amount": data.total_amount,
            "due_date": data.due_date,
            "description": f"Payment for invoice {data.invoice_number or 'N/A'}",
            "reference": data.invoice_number,
            "project_id": data.project_id,
            "status": "pending",
            "related_transaction_id": transaction["id"]
        }
        payment = db.payments.create(payment_data)
        result["payment"] = payment

    return result


@router.get("/categories/suggestions")
async def get_category_suggestions(
    vendor_name: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get category suggestions for a vendor based on historical data
    """
    categories = db.categories.find_all({"type": "expense"})

    suggestions = []
    for cat in categories:
        suggestion = {
            "id": cat["id"],
            "name": cat["name"],
            "score": 0.0
        }

        if vendor_name:
            vendor_lower = vendor_name.lower()

            # Check if vendor matches cached category
            if vendor_lower in auto_categorizer.vendor_category_cache:
                if auto_categorizer.vendor_category_cache[vendor_lower] == cat["id"]:
                    suggestion["score"] = 1.0

            # Check keyword matches
            cat_name_lower = cat["name"].lower().replace(" ", "_")
            keywords = auto_categorizer.CATEGORY_KEYWORDS.get(cat_name_lower, [])
            for keyword in keywords:
                if keyword in vendor_lower:
                    suggestion["score"] = max(suggestion["score"], 0.7)

        suggestions.append(suggestion)

    # Sort by score descending
    suggestions.sort(key=lambda x: x["score"], reverse=True)

    return {"suggestions": suggestions}


@router.get("/status")
async def get_ocr_status():
    """
    Check OCR service status and available engines
    """
    from app.services.ocr_service import TESSERACT_AVAILABLE, OPENAI_AVAILABLE, PDF_AVAILABLE

    return {
        "tesseract_available": TESSERACT_AVAILABLE,
        "openai_vision_available": OPENAI_AVAILABLE and ocr_service.openai_client is not None,
        "pdf_support": PDF_AVAILABLE,
        "supported_formats": list(ocr_service.SUPPORTED_EXTENSIONS),
        "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024)
    }
