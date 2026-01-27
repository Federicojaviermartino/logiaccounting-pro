"""
Bank Account API Routes
"""

from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.banking.accounts.service import BankAccountService
from app.banking.accounts.schemas import (
    BankAccountCreate, BankAccountUpdate, BankAccountResponse,
    BankAccountSummary, BankAccountFilter, BankBalanceResponse,
    CashPositionResponse
)
from app.banking.accounts.models import AccountType

router = APIRouter(prefix="/accounts", tags=["Bank Accounts"])

# Mock customer ID for demo purposes
DEMO_CUSTOMER_ID = UUID("00000000-0000-0000-0000-000000000001")
DEMO_USER_ID = UUID("00000000-0000-0000-0000-000000000002")


def get_customer_id() -> UUID:
    """Get current customer ID"""
    return DEMO_CUSTOMER_ID


def get_user_id() -> UUID:
    """Get current user ID"""
    return DEMO_USER_ID


@router.get("", response_model=dict)
def list_bank_accounts(
    search: Optional[str] = None,
    currency: Optional[str] = None,
    account_type: Optional[AccountType] = None,
    is_active: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List bank accounts with filtering"""
    service = BankAccountService(db, get_customer_id())

    filters = BankAccountFilter(
        search=search,
        currency=currency,
        account_type=account_type,
        is_active=is_active
    )

    accounts, total = service.get_accounts(
        filters=filters,
        skip=skip,
        limit=limit
    )

    return {
        "items": [BankAccountResponse.model_validate(acc) for acc in accounts],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/summary", response_model=List[BankAccountSummary])
def get_accounts_summary(
    currency: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get account summary for dropdowns"""
    service = BankAccountService(db, get_customer_id())
    return service.get_accounts_summary(currency)


@router.get("/cash-position", response_model=CashPositionResponse)
def get_cash_position(
    base_currency: str = "USD",
    db: Session = Depends(get_db)
):
    """Get current cash position across all accounts"""
    service = BankAccountService(db, get_customer_id())
    return service.get_cash_position(base_currency)


@router.post("", response_model=BankAccountResponse, status_code=status.HTTP_201_CREATED)
def create_bank_account(
    data: BankAccountCreate,
    db: Session = Depends(get_db)
):
    """Create a new bank account"""
    service = BankAccountService(db, get_customer_id())
    try:
        account = service.create_account(data, get_user_id())
        return BankAccountResponse.model_validate(account)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{account_id}", response_model=BankAccountResponse)
def get_bank_account(
    account_id: UUID,
    db: Session = Depends(get_db)
):
    """Get bank account details"""
    service = BankAccountService(db, get_customer_id())
    try:
        account = service.get_account_by_id(account_id)
        return BankAccountResponse.model_validate(account)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{account_id}", response_model=BankAccountResponse)
def update_bank_account(
    account_id: UUID,
    data: BankAccountUpdate,
    db: Session = Depends(get_db)
):
    """Update bank account"""
    service = BankAccountService(db, get_customer_id())
    try:
        account = service.update_account(account_id, data)
        return BankAccountResponse.model_validate(account)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{account_id}/set-primary", response_model=BankAccountResponse)
def set_primary_account(
    account_id: UUID,
    db: Session = Depends(get_db)
):
    """Set account as primary"""
    service = BankAccountService(db, get_customer_id())
    try:
        account = service.set_primary_account(account_id)
        return BankAccountResponse.model_validate(account)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{account_id}/deactivate", response_model=BankAccountResponse)
def deactivate_account(
    account_id: UUID,
    db: Session = Depends(get_db)
):
    """Deactivate bank account"""
    service = BankAccountService(db, get_customer_id())
    try:
        account = service.deactivate_account(account_id)
        return BankAccountResponse.model_validate(account)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{account_id}/balances", response_model=List[BankBalanceResponse])
def get_balance_history(
    account_id: UUID,
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db: Session = Depends(get_db)
):
    """Get balance history for an account"""
    service = BankAccountService(db, get_customer_id())
    balances = service.get_balance_history(account_id, start_date, end_date)
    return [BankBalanceResponse.model_validate(b) for b in balances]
