"""
Ledger and Financial Statements API Routes
"""

from typing import Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User

from app.accounting.ledger import (
    GeneralLedgerService,
    TrialBalanceService,
)
from app.accounting.statements import (
    BalanceSheetGenerator,
    IncomeStatementGenerator,
    CashFlowGenerator,
)

router = APIRouter(prefix="/ledger", tags=["Ledger & Reports"])


# ============== General Ledger ==============

@router.get("/account/{account_id}")
async def get_account_ledger(
    account_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    include_unposted: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get account ledger (transaction history)."""
    service = GeneralLedgerService(db)

    try:
        return service.get_account_ledger(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            include_unposted=include_unposted,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/balances")
async def get_all_balances(
    as_of_date: Optional[date] = None,
    account_type: Optional[str] = None,
    with_activity_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get balances for all accounts."""
    service = GeneralLedgerService(db)

    return service.get_all_balances(
        customer_id=current_user.customer_id,
        as_of_date=as_of_date,
        account_type=account_type,
        with_activity_only=with_activity_only,
    )


# ============== Trial Balance ==============

@router.get("/trial-balance")
async def get_trial_balance(
    as_of_date: Optional[date] = None,
    include_zero_balances: bool = False,
    group_by_type: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate trial balance report."""
    service = TrialBalanceService(db)

    return service.generate_trial_balance(
        customer_id=current_user.customer_id,
        as_of_date=as_of_date,
        include_zero_balances=include_zero_balances,
        group_by_type=group_by_type,
    )


# ============== Financial Statements ==============

@router.get("/statements/balance-sheet")
async def get_balance_sheet(
    as_of_date: Optional[date] = None,
    comparative_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate balance sheet."""
    generator = BalanceSheetGenerator(db)

    return generator.generate(
        customer_id=current_user.customer_id,
        as_of_date=as_of_date,
        comparative_date=comparative_date,
    )


@router.get("/statements/income-statement")
async def get_income_statement(
    start_date: date,
    end_date: date,
    comparative_start: Optional[date] = None,
    comparative_end: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate income statement (P&L)."""
    generator = IncomeStatementGenerator(db)

    return generator.generate(
        customer_id=current_user.customer_id,
        start_date=start_date,
        end_date=end_date,
        comparative_start=comparative_start,
        comparative_end=comparative_end,
    )


@router.get("/statements/cash-flow")
async def get_cash_flow(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate cash flow statement."""
    generator = CashFlowGenerator(db)

    return generator.generate(
        customer_id=current_user.customer_id,
        start_date=start_date,
        end_date=end_date,
    )


# ============== Subsidiary Ledgers ==============

@router.get("/subsidiary/ar")
async def get_ar_ledger(
    as_of_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get accounts receivable subsidiary ledger."""
    service = GeneralLedgerService(db)

    return service.get_ar_ledger(
        customer_id=current_user.customer_id,
        as_of_date=as_of_date,
    )


@router.get("/subsidiary/ap")
async def get_ap_ledger(
    as_of_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get accounts payable subsidiary ledger."""
    service = GeneralLedgerService(db)

    return service.get_ap_ledger(
        customer_id=current_user.customer_id,
        as_of_date=as_of_date,
    )
