"""
Bank Transaction API Routes
"""

from typing import List, Optional
from uuid import UUID
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.banking.transactions.service import BankTransactionService
from app.banking.transactions.schemas import (
    BankTransactionCreate, BankTransactionUpdate, BankTransactionResponse,
    BankTransactionFilter, StatementImportResponse, TransactionMatchRequest,
    TransactionCategorizeRequest
)
from app.banking.transactions.models import TransactionType, MatchStatus, Direction

router = APIRouter(prefix="/transactions", tags=["Bank Transactions"])

DEMO_CUSTOMER_ID = UUID("00000000-0000-0000-0000-000000000001")
DEMO_USER_ID = UUID("00000000-0000-0000-0000-000000000002")


def get_customer_id() -> UUID:
    return DEMO_CUSTOMER_ID


def get_user_id() -> UUID:
    return DEMO_USER_ID


@router.get("", response_model=dict)
def list_transactions(
    account_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    transaction_type: Optional[TransactionType] = None,
    direction: Optional[Direction] = None,
    match_status: Optional[MatchStatus] = None,
    is_reconciled: Optional[bool] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List bank transactions with filtering"""
    service = BankTransactionService(db, get_customer_id())

    filters = BankTransactionFilter(
        account_id=account_id,
        start_date=start_date,
        end_date=end_date,
        transaction_type=transaction_type,
        direction=direction,
        match_status=match_status,
        is_reconciled=is_reconciled,
        category=category,
        search=search,
        min_amount=min_amount,
        max_amount=max_amount
    )

    transactions, total = service.get_transactions(
        filters=filters,
        skip=skip,
        limit=limit
    )

    return {
        "items": [BankTransactionResponse.model_validate(t) for t in transactions],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("", response_model=BankTransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    data: BankTransactionCreate,
    db: Session = Depends(get_db)
):
    """Create a manual bank transaction"""
    service = BankTransactionService(db, get_customer_id())
    try:
        transaction = service.create_transaction(data, get_user_id())
        return BankTransactionResponse.model_validate(transaction)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/unmatched", response_model=List[BankTransactionResponse])
def get_unmatched_transactions(
    account_id: Optional[UUID] = None,
    days_back: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get unmatched transactions for reconciliation"""
    service = BankTransactionService(db, get_customer_id())
    transactions = service.get_unmatched_transactions(account_id, days_back)
    return [BankTransactionResponse.model_validate(t) for t in transactions]


@router.get("/{transaction_id}", response_model=BankTransactionResponse)
def get_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db)
):
    """Get transaction details"""
    service = BankTransactionService(db, get_customer_id())
    try:
        transaction = service.get_transaction_by_id(transaction_id)
        return BankTransactionResponse.model_validate(transaction)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{transaction_id}", response_model=BankTransactionResponse)
def update_transaction(
    transaction_id: UUID,
    data: BankTransactionUpdate,
    db: Session = Depends(get_db)
):
    """Update transaction details"""
    service = BankTransactionService(db, get_customer_id())
    try:
        transaction = service.update_transaction(transaction_id, data)
        return BankTransactionResponse.model_validate(transaction)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{transaction_id}/match", response_model=BankTransactionResponse)
def match_transaction(
    transaction_id: UUID,
    data: TransactionMatchRequest,
    db: Session = Depends(get_db)
):
    """Match a transaction to an invoice, bill, or journal entry"""
    service = BankTransactionService(db, get_customer_id())
    try:
        transaction = service.match_transaction(
            transaction_id,
            data.match_type,
            data.match_id
        )
        return BankTransactionResponse.model_validate(transaction)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{transaction_id}/unmatch", response_model=BankTransactionResponse)
def unmatch_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db)
):
    """Remove match from a transaction"""
    service = BankTransactionService(db, get_customer_id())
    try:
        transaction = service.unmatch_transaction(transaction_id)
        return BankTransactionResponse.model_validate(transaction)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/categorize", response_model=dict)
def categorize_transactions(
    data: TransactionCategorizeRequest,
    db: Session = Depends(get_db)
):
    """Categorize multiple transactions"""
    service = BankTransactionService(db, get_customer_id())
    count = service.categorize_transactions(data.transaction_ids, data.category)
    return {"categorized_count": count}


@router.post("/import/{account_id}", response_model=StatementImportResponse)
async def import_statement(
    account_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Import transactions from bank statement file"""
    service = BankTransactionService(db, get_customer_id())

    # Read file content
    content = await file.read()

    try:
        import_record = service.import_csv_statement(
            account_id=account_id,
            file_content=content,
            file_name=file.filename,
            imported_by=get_user_id()
        )
        return StatementImportResponse.model_validate(import_record)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
