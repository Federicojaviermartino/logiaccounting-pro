"""
Bank Reconciliation routes
"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.reconciliation_service import reconciliation_service
from app.utils.auth import require_roles

router = APIRouter()


class ImportStatementRequest(BaseModel):
    bank_name: str
    account_number: str
    period_start: str
    period_end: str
    entries: List[dict]


class ManualMatchRequest(BaseModel):
    entry_id: str
    txn_id: str


@router.get("")
async def list_statements(current_user: dict = Depends(require_roles("admin"))):
    """List all bank statements"""
    return {"statements": reconciliation_service.list_statements()}


@router.post("/import")
async def import_statement(
    request: ImportStatementRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Import a bank statement"""
    return reconciliation_service.import_statement(
        bank_name=request.bank_name,
        account_number=request.account_number,
        period_start=request.period_start,
        period_end=request.period_end,
        entries=request.entries,
        imported_by=current_user["id"]
    )


@router.get("/{statement_id}")
async def get_statement(
    statement_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get a specific statement"""
    statement = reconciliation_service.get_statement(statement_id)
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")
    return statement


@router.post("/{statement_id}/auto-match")
async def auto_match(
    statement_id: str,
    tolerance_percent: float = 5,
    tolerance_days: int = 3,
    current_user: dict = Depends(require_roles("admin"))
):
    """Run auto-matching"""
    result = reconciliation_service.auto_match(statement_id, tolerance_percent, tolerance_days)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{statement_id}/match")
async def manual_match(
    statement_id: str,
    request: ManualMatchRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Manually match an entry"""
    result = reconciliation_service.manual_match(statement_id, request.entry_id, request.txn_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{statement_id}/unmatch/{entry_id}")
async def unmatch(
    statement_id: str,
    entry_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Unmatch an entry"""
    result = reconciliation_service.unmatch(statement_id, entry_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{statement_id}/complete")
async def complete_reconciliation(
    statement_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Complete reconciliation"""
    result = reconciliation_service.complete_reconciliation(statement_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/{statement_id}/unmatched-transactions")
async def get_unmatched_transactions(
    statement_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get unmatched transactions for a statement period"""
    statement = reconciliation_service.get_statement(statement_id)
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")

    transactions = reconciliation_service.get_unmatched_transactions(
        statement["period_start"],
        statement["period_end"]
    )
    return {"transactions": transactions}


@router.delete("/{statement_id}")
async def delete_statement(
    statement_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Delete a statement"""
    if reconciliation_service.delete_statement(statement_id):
        return {"message": "Statement deleted"}
    raise HTTPException(status_code=404, detail="Statement not found")
