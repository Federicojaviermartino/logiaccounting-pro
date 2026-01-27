"""
Bank Reconciliation API Routes
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.banking.reconciliation.service import BankReconciliationService
from app.banking.reconciliation.schemas import (
    ReconciliationCreate, ReconciliationUpdate, ReconciliationResponse,
    ReconciliationDetailResponse, ReconciliationLineCreate, ReconciliationLineResponse,
    MatchingRuleCreate, MatchingRuleResponse, AutoMatchRequest, AutoMatchResult
)
from app.banking.reconciliation.models import ReconciliationStatus

router = APIRouter(prefix="/reconciliation", tags=["Bank Reconciliation"])

DEMO_CUSTOMER_ID = UUID("00000000-0000-0000-0000-000000000001")
DEMO_USER_ID = UUID("00000000-0000-0000-0000-000000000002")


def get_customer_id() -> UUID:
    return DEMO_CUSTOMER_ID


def get_user_id() -> UUID:
    return DEMO_USER_ID


@router.get("", response_model=dict)
def list_reconciliations(
    account_id: Optional[UUID] = None,
    status: Optional[ReconciliationStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List reconciliations with filtering"""
    service = BankReconciliationService(db, get_customer_id())

    reconciliations, total = service.get_reconciliations(
        account_id=account_id,
        status=status,
        skip=skip,
        limit=limit
    )

    return {
        "items": [ReconciliationResponse.model_validate(r) for r in reconciliations],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("", response_model=ReconciliationResponse, status_code=status.HTTP_201_CREATED)
def create_reconciliation(
    data: ReconciliationCreate,
    db: Session = Depends(get_db)
):
    """Create a new reconciliation session"""
    service = BankReconciliationService(db, get_customer_id())
    try:
        reconciliation = service.create_reconciliation(data, get_user_id())
        return ReconciliationResponse.model_validate(reconciliation)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{reconciliation_id}", response_model=ReconciliationDetailResponse)
def get_reconciliation(
    reconciliation_id: UUID,
    db: Session = Depends(get_db)
):
    """Get reconciliation details with lines"""
    service = BankReconciliationService(db, get_customer_id())
    try:
        reconciliation = service.get_reconciliation_by_id(reconciliation_id)
        return ReconciliationDetailResponse.model_validate(reconciliation)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{reconciliation_id}/lines", response_model=ReconciliationLineResponse)
def add_reconciliation_line(
    reconciliation_id: UUID,
    data: ReconciliationLineCreate,
    db: Session = Depends(get_db)
):
    """Add a line to reconciliation"""
    service = BankReconciliationService(db, get_customer_id())
    try:
        line = service.add_reconciliation_line(
            reconciliation_id,
            data,
            get_user_id()
        )
        return ReconciliationLineResponse.model_validate(line)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{reconciliation_id}/lines/{line_id}")
def remove_reconciliation_line(
    reconciliation_id: UUID,
    line_id: UUID,
    db: Session = Depends(get_db)
):
    """Remove a line from reconciliation"""
    service = BankReconciliationService(db, get_customer_id())
    try:
        service.remove_reconciliation_line(line_id)
        return {"message": "Line removed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{reconciliation_id}/auto-match", response_model=AutoMatchResult)
def auto_match_transactions(
    reconciliation_id: UUID,
    apply_rules: bool = True,
    match_threshold: float = 0.8,
    db: Session = Depends(get_db)
):
    """Automatically match transactions"""
    from decimal import Decimal
    service = BankReconciliationService(db, get_customer_id())
    try:
        result = service.auto_match_transactions(
            reconciliation_id,
            apply_rules=apply_rules,
            match_threshold=Decimal(str(match_threshold))
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{reconciliation_id}/complete", response_model=ReconciliationResponse)
def complete_reconciliation(
    reconciliation_id: UUID,
    db: Session = Depends(get_db)
):
    """Complete and finalize reconciliation"""
    service = BankReconciliationService(db, get_customer_id())
    try:
        reconciliation = service.complete_reconciliation(
            reconciliation_id,
            get_user_id()
        )
        return ReconciliationResponse.model_validate(reconciliation)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
