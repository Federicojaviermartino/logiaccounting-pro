"""
Payment Processing API Routes
"""

from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.banking.payments.service import PaymentService
from app.banking.payments.schemas import (
    PaymentBatchCreate, PaymentBatchUpdate, PaymentBatchResponse,
    PaymentBatchDetailResponse, PaymentInstructionCreate, PaymentInstructionResponse,
    ApprovalRequest, PaymentHistoryResponse
)
from app.banking.payments.models import BatchStatus, BatchType

router = APIRouter(prefix="/payments", tags=["Payment Processing"])

DEMO_CUSTOMER_ID = UUID("00000000-0000-0000-0000-000000000001")
DEMO_USER_ID = UUID("00000000-0000-0000-0000-000000000002")


def get_customer_id() -> UUID:
    return DEMO_CUSTOMER_ID


def get_user_id() -> UUID:
    return DEMO_USER_ID


@router.get("/batches", response_model=dict)
def list_payment_batches(
    status: Optional[BatchStatus] = None,
    batch_type: Optional[BatchType] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List payment batches with filtering"""
    service = PaymentService(db, get_customer_id())

    batches, total = service.get_batches(
        status=status,
        batch_type=batch_type,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )

    return {
        "items": [PaymentBatchResponse.model_validate(b) for b in batches],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("/batches", response_model=PaymentBatchResponse, status_code=status.HTTP_201_CREATED)
def create_payment_batch(
    data: PaymentBatchCreate,
    db: Session = Depends(get_db)
):
    """Create a new payment batch"""
    service = PaymentService(db, get_customer_id())
    try:
        batch = service.create_batch(data, get_user_id())
        return PaymentBatchResponse.model_validate(batch)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/batches/{batch_id}", response_model=PaymentBatchDetailResponse)
def get_payment_batch(
    batch_id: UUID,
    db: Session = Depends(get_db)
):
    """Get payment batch details with instructions"""
    service = PaymentService(db, get_customer_id())
    try:
        batch = service.get_batch_by_id(batch_id)
        return PaymentBatchDetailResponse.model_validate(batch)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/batches/{batch_id}", response_model=PaymentBatchResponse)
def update_payment_batch(
    batch_id: UUID,
    data: PaymentBatchUpdate,
    db: Session = Depends(get_db)
):
    """Update payment batch"""
    service = PaymentService(db, get_customer_id())
    try:
        batch = service.update_batch(batch_id, data)
        return PaymentBatchResponse.model_validate(batch)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batches/{batch_id}/instructions", response_model=PaymentInstructionResponse)
def add_payment_instruction(
    batch_id: UUID,
    data: PaymentInstructionCreate,
    db: Session = Depends(get_db)
):
    """Add a payment instruction to a batch"""
    service = PaymentService(db, get_customer_id())
    try:
        instruction = service.add_instruction(batch_id, data)
        return PaymentInstructionResponse.model_validate(instruction)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/batches/{batch_id}/instructions/{instruction_id}")
def remove_payment_instruction(
    batch_id: UUID,
    instruction_id: UUID,
    db: Session = Depends(get_db)
):
    """Remove a payment instruction from a batch"""
    service = PaymentService(db, get_customer_id())
    try:
        service.remove_instruction(instruction_id)
        return {"message": "Instruction removed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batches/{batch_id}/submit", response_model=PaymentBatchResponse)
def submit_for_approval(
    batch_id: UUID,
    db: Session = Depends(get_db)
):
    """Submit batch for approval"""
    service = PaymentService(db, get_customer_id())
    try:
        batch = service.submit_for_approval(batch_id)
        return PaymentBatchResponse.model_validate(batch)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batches/{batch_id}/approve", response_model=PaymentBatchResponse)
def approve_batch(
    batch_id: UUID,
    data: ApprovalRequest,
    db: Session = Depends(get_db)
):
    """Approve or reject a batch"""
    service = PaymentService(db, get_customer_id())
    try:
        batch = service.approve_batch(
            batch_id,
            approved=data.approved,
            approved_by=get_user_id(),
            notes=data.notes
        )
        return PaymentBatchResponse.model_validate(batch)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batches/{batch_id}/process", response_model=PaymentBatchResponse)
def process_batch(
    batch_id: UUID,
    db: Session = Depends(get_db)
):
    """Process an approved batch"""
    service = PaymentService(db, get_customer_id())
    try:
        batch = service.process_batch(batch_id)
        return PaymentBatchResponse.model_validate(batch)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batches/{batch_id}/generate-file")
def generate_payment_file(
    batch_id: UUID,
    file_format: str = Query("nacha", pattern="^(nacha|csv)$"),
    db: Session = Depends(get_db)
):
    """Generate payment file for bank submission"""
    service = PaymentService(db, get_customer_id())
    try:
        file_content = service.generate_payment_file(batch_id, file_format)
        return {
            "file_content": file_content,
            "file_format": file_format
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batches/{batch_id}/mark-sent", response_model=PaymentBatchResponse)
def mark_batch_sent(
    batch_id: UUID,
    db: Session = Depends(get_db)
):
    """Mark batch as sent to bank"""
    service = PaymentService(db, get_customer_id())
    try:
        batch = service.mark_batch_sent(batch_id)
        return PaymentBatchResponse.model_validate(batch)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batches/{batch_id}/complete", response_model=PaymentBatchResponse)
def complete_batch(
    batch_id: UUID,
    db: Session = Depends(get_db)
):
    """Mark batch as completed"""
    service = PaymentService(db, get_customer_id())
    try:
        batch = service.complete_batch(batch_id)
        return PaymentBatchResponse.model_validate(batch)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batches/{batch_id}/cancel", response_model=PaymentBatchResponse)
def cancel_batch(
    batch_id: UUID,
    db: Session = Depends(get_db)
):
    """Cancel a batch"""
    service = PaymentService(db, get_customer_id())
    try:
        batch = service.cancel_batch(batch_id)
        return PaymentBatchResponse.model_validate(batch)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
