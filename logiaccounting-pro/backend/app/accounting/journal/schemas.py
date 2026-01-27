"""
Journal Entry Schemas
Pydantic schemas for validation and serialization
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, validator, model_validator


class EntryTypeEnum(str, Enum):
    STANDARD = "standard"
    INVOICE = "invoice"
    BILL = "bill"
    PAYMENT = "payment"
    RECEIPT = "receipt"
    ADJUSTMENT = "adjustment"
    CLOSING = "closing"
    REVERSAL = "reversal"
    OPENING = "opening"
    DEPRECIATION = "depreciation"
    ACCRUAL = "accrual"
    TRANSFER = "transfer"


class EntryStatusEnum(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    POSTED = "posted"
    REVERSED = "reversed"
    VOIDED = "voided"


# ============== Line Schemas ==============

class JournalLineBase(BaseModel):
    account_id: UUID
    debit_amount: Decimal = Field(default=Decimal("0"), ge=0)
    credit_amount: Decimal = Field(default=Decimal("0"), ge=0)
    description: Optional[str] = None
    memo: Optional[str] = None
    tax_code: Optional[str] = None
    tax_amount: Optional[Decimal] = None
    cost_center: Optional[str] = None
    department: Optional[str] = None
    project_id: Optional[UUID] = None

    @model_validator(mode='after')
    def validate_amounts(self):
        if self.debit_amount > 0 and self.credit_amount > 0:
            raise ValueError("Line cannot have both debit and credit amounts")
        if self.debit_amount == 0 and self.credit_amount == 0:
            raise ValueError("Line must have either debit or credit amount")
        return self


class JournalLineCreate(JournalLineBase):
    pass


class JournalLineUpdate(BaseModel):
    account_id: Optional[UUID] = None
    debit_amount: Optional[Decimal] = None
    credit_amount: Optional[Decimal] = None
    description: Optional[str] = None
    memo: Optional[str] = None
    tax_code: Optional[str] = None
    tax_amount: Optional[Decimal] = None
    cost_center: Optional[str] = None
    project_id: Optional[UUID] = None


class JournalLineResponse(JournalLineBase):
    id: UUID
    entry_id: UUID
    line_number: int
    account_code: Optional[str] = None
    account_name: Optional[str] = None
    currency: str
    exchange_rate: Decimal
    base_debit: Decimal
    base_credit: Decimal
    is_reconciled: bool

    class Config:
        from_attributes = True


# ============== Entry Schemas ==============

class JournalEntryBase(BaseModel):
    entry_date: date
    entry_type: EntryTypeEnum = EntryTypeEnum.STANDARD
    description: Optional[str] = None
    memo: Optional[str] = None
    reference: Optional[str] = None
    currency: str = "USD"
    exchange_rate: Decimal = Decimal("1")


class JournalEntryCreate(JournalEntryBase):
    lines: List[JournalLineCreate] = Field(..., min_length=2)
    source_type: Optional[str] = None
    source_id: Optional[UUID] = None
    fiscal_period_id: Optional[UUID] = None

    @validator("lines")
    def validate_balanced(cls, lines):
        total_debit = sum(l.debit_amount for l in lines)
        total_credit = sum(l.credit_amount for l in lines)

        if total_debit != total_credit:
            raise ValueError(
                f"Entry is not balanced: Debits ({total_debit}) != Credits ({total_credit})"
            )

        return lines


class JournalEntryUpdate(BaseModel):
    entry_date: Optional[date] = None
    description: Optional[str] = None
    memo: Optional[str] = None
    reference: Optional[str] = None
    lines: Optional[List[JournalLineCreate]] = None

    @validator("lines")
    def validate_balanced(cls, lines):
        if lines is None:
            return lines

        if len(lines) < 2:
            raise ValueError("Entry must have at least 2 lines")

        total_debit = sum(l.debit_amount for l in lines)
        total_credit = sum(l.credit_amount for l in lines)

        if total_debit != total_credit:
            raise ValueError(
                f"Entry is not balanced: Debits ({total_debit}) != Credits ({total_credit})"
            )

        return lines


class JournalEntryResponse(JournalEntryBase):
    id: UUID
    customer_id: UUID
    entry_number: str
    status: EntryStatusEnum
    fiscal_period_id: Optional[UUID]
    source_type: Optional[str]
    source_id: Optional[UUID]
    total_debit: Decimal
    total_credit: Decimal
    is_balanced: bool
    is_reversing: bool
    reversed_entry_id: Optional[UUID]
    lines: List[JournalLineResponse] = []
    created_at: datetime
    updated_at: datetime
    posted_at: Optional[datetime]

    class Config:
        from_attributes = True


class JournalEntrySummary(BaseModel):
    """Summary for list views."""
    id: UUID
    entry_number: str
    entry_date: date
    entry_type: EntryTypeEnum
    status: EntryStatusEnum
    description: Optional[str]
    total_debit: Decimal
    total_credit: Decimal
    line_count: int
    created_at: datetime


# ============== Action Schemas ==============

class EntrySubmitRequest(BaseModel):
    notes: Optional[str] = None


class EntryApprovalRequest(BaseModel):
    approved: bool
    notes: Optional[str] = None


class EntryReversalRequest(BaseModel):
    reversal_date: date
    description: Optional[str] = None


class EntryVoidRequest(BaseModel):
    reason: str


# ============== Query Schemas ==============

class JournalEntryFilter(BaseModel):
    search: Optional[str] = None
    entry_type: Optional[EntryTypeEnum] = None
    status: Optional[EntryStatusEnum] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    fiscal_period_id: Optional[UUID] = None
    account_id: Optional[UUID] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    source_type: Optional[str] = None
    unposted_only: bool = False


class JournalEntryListResponse(BaseModel):
    entries: List[JournalEntrySummary]
    total: int
    page: int
    page_size: int
    total_debit: Decimal
    total_credit: Decimal


# ============== Batch Operations ==============

class BatchPostRequest(BaseModel):
    entry_ids: List[UUID]


class BatchPostResult(BaseModel):
    success: bool
    posted_count: int
    failed_count: int
    errors: List[dict] = []
