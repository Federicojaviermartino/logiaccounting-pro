"""Financial statements API routes."""
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.reporting.services.financial_statement_service import FinancialStatementService
from app.reporting.schemas.financial_statements import (
    BalanceSheetData, IncomeStatementData, CashFlowData, TrialBalanceData
)

router = APIRouter(prefix="/financial-statements", tags=["Financial Statements"])


@router.get("/balance-sheet", response_model=BalanceSheetData)
async def get_balance_sheet(
    as_of_date: date = Query(..., description="Report date"),
    compare_prior_period: bool = Query(False, description="Include prior period comparison"),
    department_id: Optional[UUID] = Query(None, description="Filter by department"),
    show_zero_balances: bool = Query(False, description="Show accounts with zero balance"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate Balance Sheet report."""
    service = FinancialStatementService(db, current_user.customer_id)
    return await service.generate_balance_sheet(
        as_of_date=as_of_date,
        compare_prior_period=compare_prior_period,
        department_id=department_id,
        show_zero_balances=show_zero_balances
    )


@router.get("/income-statement", response_model=IncomeStatementData)
async def get_income_statement(
    start_date: date = Query(..., description="Period start date"),
    end_date: date = Query(..., description="Period end date"),
    compare_prior_period: bool = Query(False, description="Include prior period comparison"),
    department_id: Optional[UUID] = Query(None, description="Filter by department"),
    show_zero_balances: bool = Query(False, description="Show accounts with zero balance"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate Income Statement (P&L) report."""
    service = FinancialStatementService(db, current_user.customer_id)
    return await service.generate_income_statement(
        start_date=start_date,
        end_date=end_date,
        compare_prior_period=compare_prior_period,
        department_id=department_id,
        show_zero_balances=show_zero_balances
    )


@router.get("/cash-flow", response_model=CashFlowData)
async def get_cash_flow(
    start_date: date = Query(..., description="Period start date"),
    end_date: date = Query(..., description="Period end date"),
    department_id: Optional[UUID] = Query(None, description="Filter by department"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate Cash Flow Statement."""
    service = FinancialStatementService(db, current_user.customer_id)
    return await service.generate_cash_flow(
        start_date=start_date,
        end_date=end_date,
        department_id=department_id
    )


@router.get("/trial-balance", response_model=TrialBalanceData)
async def get_trial_balance(
    as_of_date: date = Query(..., description="Report date"),
    department_id: Optional[UUID] = Query(None, description="Filter by department"),
    show_zero_balances: bool = Query(False, description="Show accounts with zero balance"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate Trial Balance report."""
    service = FinancialStatementService(db, current_user.customer_id)
    return await service.generate_trial_balance(
        as_of_date=as_of_date,
        department_id=department_id,
        show_zero_balances=show_zero_balances
    )
