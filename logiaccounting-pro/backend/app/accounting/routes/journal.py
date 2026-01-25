"""
Journal Entry API Routes
"""

from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User

from app.accounting.journal import (
    JournalEntryService,
    JournalEntryCreate,
    JournalEntryUpdate,
    JournalEntryResponse,
    JournalEntryFilter,
    EntrySubmitRequest,
    EntryApprovalRequest,
    EntryReversalRequest,
    EntryVoidRequest,
    BatchPostRequest,
)

router = APIRouter(prefix="/journal", tags=["Journal Entries"])


@router.get("")
async def list_journal_entries(
    search: Optional[str] = None,
    entry_type: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    account_id: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List journal entries with filtering."""
    service = JournalEntryService(db)

    filters = JournalEntryFilter(
        search=search,
        entry_type=entry_type,
        status=status,
        start_date=start_date,
        end_date=end_date,
        account_id=account_id,
    )

    entries, total, total_debit, total_credit = service.get_entries(
        customer_id=current_user.customer_id,
        filters=filters,
        page=page,
        page_size=page_size,
    )

    return {
        "entries": [e.to_dict(include_lines=False) for e in entries],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_debit": float(total_debit),
        "total_credit": float(total_credit),
    }


@router.post("", response_model=JournalEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_journal_entry(
    data: JournalEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new journal entry."""
    service = JournalEntryService(db)

    try:
        entry = service.create_entry(
            customer_id=current_user.customer_id,
            data=data,
            created_by=current_user.id,
        )
        return entry.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{entry_id}", response_model=JournalEntryResponse)
async def get_journal_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get journal entry details."""
    service = JournalEntryService(db)
    entry = service.get_entry_by_id(entry_id)

    if not entry or entry.customer_id != current_user.customer_id:
        raise HTTPException(status_code=404, detail="Entry not found")

    return entry.to_dict()


@router.put("/{entry_id}", response_model=JournalEntryResponse)
async def update_journal_entry(
    entry_id: UUID,
    data: JournalEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a draft journal entry."""
    service = JournalEntryService(db)

    entry = service.get_entry_by_id(entry_id)
    if not entry or entry.customer_id != current_user.customer_id:
        raise HTTPException(status_code=404, detail="Entry not found")

    try:
        entry = service.update_entry(entry_id, data)
        return entry.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{entry_id}")
async def delete_journal_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a draft journal entry."""
    service = JournalEntryService(db)

    entry = service.get_entry_by_id(entry_id)
    if not entry or entry.customer_id != current_user.customer_id:
        raise HTTPException(status_code=404, detail="Entry not found")

    try:
        service.delete_entry(entry_id)
        return {"message": "Entry deleted"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{entry_id}/submit")
async def submit_entry(
    entry_id: UUID,
    data: EntrySubmitRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit entry for approval."""
    service = JournalEntryService(db)

    try:
        entry = service.submit_for_approval(
            entry_id,
            submitted_by=current_user.id,
            notes=data.notes if data else None,
        )
        return entry.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{entry_id}/approve")
async def approve_entry(
    entry_id: UUID,
    data: EntryApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve or reject an entry."""
    service = JournalEntryService(db)

    try:
        if data.approved:
            entry = service.approve_entry(
                entry_id,
                approved_by=current_user.id,
                notes=data.notes,
            )
        else:
            entry = service.reject_entry(
                entry_id,
                rejected_by=current_user.id,
                notes=data.notes,
            )
        return entry.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{entry_id}/post")
async def post_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Post an approved entry to the ledger."""
    service = JournalEntryService(db)

    try:
        entry = service.post_entry(entry_id, posted_by=current_user.id)
        return entry.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{entry_id}/reverse")
async def reverse_entry(
    entry_id: UUID,
    data: EntryReversalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reverse a posted entry."""
    service = JournalEntryService(db)

    try:
        reversal = service.reverse_entry(
            entry_id,
            reversal_data=data,
            reversed_by=current_user.id,
        )
        return reversal.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{entry_id}/void")
async def void_entry(
    entry_id: UUID,
    data: EntryVoidRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Void an unposted entry."""
    service = JournalEntryService(db)

    try:
        entry = service.void_entry(
            entry_id,
            voided_by=current_user.id,
            reason=data.reason,
        )
        return entry.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch/post")
async def batch_post_entries(
    data: BatchPostRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Post multiple entries at once."""
    service = JournalEntryService(db)

    result = service.batch_post(
        entry_ids=data.entry_ids,
        posted_by=current_user.id,
    )

    return result
