"""
Fiscal Periods and Bank Reconciliation API Routes
"""

from typing import List, Optional
from uuid import UUID
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User

from app.accounting.periods import (
    PeriodService,
    YearEndClosingService,
)
from app.accounting.reconciliation import (
    ReconciliationService,
    StatementImporter,
    TransactionMatcher,
)

router = APIRouter(tags=["Fiscal Periods & Reconciliation"])


# ============== Fiscal Years ==============

@router.get("/fiscal-years")
async def list_fiscal_years(
    include_closed: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all fiscal years."""
    service = PeriodService(db)

    years = service.get_fiscal_years(
        customer_id=current_user.customer_id,
        include_closed=include_closed,
    )

    return [y.to_dict() for y in years]


@router.post("/fiscal-years")
async def create_fiscal_year(
    start_date: date,
    end_date: Optional[date] = None,
    name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new fiscal year with periods."""
    service = PeriodService(db)

    try:
        year = service.create_fiscal_year(
            customer_id=current_user.customer_id,
            start_date=start_date,
            end_date=end_date,
            name=name,
            created_by=current_user.id,
        )
        return year.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/fiscal-years/current-period")
async def get_current_period(
    as_of_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current open fiscal period."""
    service = PeriodService(db)

    period = service.get_current_period(
        customer_id=current_user.customer_id,
        as_of_date=as_of_date,
    )

    if not period:
        raise HTTPException(status_code=404, detail="No open period found")

    return period.to_dict()


@router.post("/periods/{period_id}/close")
async def close_period(
    period_id: UUID,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Close a fiscal period."""
    service = PeriodService(db)

    try:
        period = service.close_period(
            period_id=period_id,
            closed_by=current_user.id,
            notes=notes,
        )
        return period.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/fiscal-years/{year_id}/close")
async def close_fiscal_year(
    year_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Perform year-end closing."""
    service = YearEndClosingService(db)

    try:
        result = service.perform_year_end_closing(
            fiscal_year_id=year_id,
            closed_by=current_user.id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============== Bank Reconciliation ==============

@router.get("/bank-accounts")
async def list_bank_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List bank accounts."""
    from app.accounting.reconciliation.models import BankAccount

    accounts = db.query(BankAccount).filter(
        BankAccount.customer_id == current_user.customer_id,
        BankAccount.is_active == True
    ).all()

    return [
        {
            "id": str(a.id),
            "bank_name": a.bank_name,
            "account_number": a.account_number,
            "gl_account_id": str(a.account_id),
            "current_balance": float(a.current_balance),
            "last_reconciled_date": a.last_reconciled_date.isoformat() if a.last_reconciled_date else None,
        }
        for a in accounts
    ]


@router.post("/bank-accounts")
async def create_bank_account(
    gl_account_id: UUID,
    bank_name: str,
    account_number: Optional[str] = None,
    routing_number: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a bank account."""
    service = ReconciliationService(db)

    account = service.create_bank_account(
        customer_id=current_user.customer_id,
        gl_account_id=gl_account_id,
        bank_name=bank_name,
        account_number=account_number,
        routing_number=routing_number,
    )

    return {"id": str(account.id), "message": "Bank account created"}


@router.post("/bank-accounts/{bank_account_id}/import")
async def import_bank_statement(
    bank_account_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import bank statement from file."""
    importer = StatementImporter(db)

    content = await file.read()

    if file.filename.endswith(".csv"):
        statement = importer.import_csv(
            bank_account_id=bank_account_id,
            file_content=content.decode("utf-8"),
            column_mapping={
                "date": "Date",
                "amount": "Amount",
                "description": "Description",
            },
            created_by=current_user.id,
        )
    elif file.filename.endswith((".ofx", ".qfx")):
        statement = importer.import_ofx(
            bank_account_id=bank_account_id,
            file_content=content,
            created_by=current_user.id,
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format")

    return {
        "statement_id": str(statement.id),
        "transactions_imported": len(statement.transactions),
    }


@router.post("/reconciliations")
async def start_reconciliation(
    bank_account_id: UUID,
    statement_balance: Decimal,
    reconciliation_date: Optional[date] = None,
    statement_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start a new reconciliation session."""
    service = ReconciliationService(db)

    try:
        recon = service.start_reconciliation(
            bank_account_id=bank_account_id,
            statement_id=statement_id,
            statement_balance=statement_balance,
            reconciliation_date=reconciliation_date,
            created_by=current_user.id,
        )
        return service.get_reconciliation_summary(recon.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reconciliations/{recon_id}")
async def get_reconciliation(
    recon_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get reconciliation summary."""
    service = ReconciliationService(db)

    try:
        return service.get_reconciliation_summary(recon_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/reconciliations/{recon_id}/auto-match")
async def auto_match_transactions(
    recon_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Auto-match bank transactions."""
    from app.accounting.reconciliation.models import Reconciliation

    recon = db.query(Reconciliation).get(recon_id)
    if not recon or not recon.statement_id:
        raise HTTPException(status_code=404, detail="Reconciliation not found")

    matcher = TransactionMatcher(db)
    result = matcher.auto_match_statement(recon.statement_id)

    return result


@router.post("/reconciliations/{recon_id}/match")
async def manual_match(
    recon_id: UUID,
    transaction_id: UUID,
    line_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually match a transaction to a journal line."""
    matcher = TransactionMatcher(db)

    try:
        matcher.manual_match(transaction_id, line_id)
        return {"message": "Match created"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reconciliations/{recon_id}/complete")
async def complete_reconciliation(
    recon_id: UUID,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Complete a reconciliation session."""
    service = ReconciliationService(db)

    try:
        recon = service.complete_reconciliation(
            reconciliation_id=recon_id,
            completed_by=current_user.id,
            notes=notes,
        )
        return {
            "status": recon.status,
            "difference": float(recon.difference),
            "completed_at": recon.completed_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
