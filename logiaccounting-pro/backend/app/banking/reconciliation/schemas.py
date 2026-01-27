"""
Bank Reconciliation Schemas
Pydantic schemas for reconciliation
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

from app.banking.reconciliation.models import ReconciliationStatus, MatchType, LineStatus


class ReconciliationCreate(BaseModel):
    """Schema for creating a reconciliation"""
    account_id: UUID
    period_start: date
    period_end: date
    statement_opening_balance: Decimal
    statement_closing_balance: Decimal
    notes: Optional[str] = None


class ReconciliationUpdate(BaseModel):
    """Schema for updating reconciliation"""
    statement_opening_balance: Optional[Decimal] = None
    statement_closing_balance: Optional[Decimal] = None
    notes: Optional[str] = None


class ReconciliationLineCreate(BaseModel):
    """Schema for creating a reconciliation line"""
    transaction_id: Optional[UUID] = None
    journal_line_id: Optional[UUID] = None
    match_type: MatchType = MatchType.MANUAL
    statement_amount: Optional[Decimal] = None
    book_amount: Optional[Decimal] = None
    notes: Optional[str] = None


class ReconciliationLineResponse(BaseModel):
    """Schema for reconciliation line response"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reconciliation_id: UUID
    transaction_id: Optional[UUID] = None
    journal_line_id: Optional[UUID] = None
    match_type: Optional[str] = None
    statement_amount: Optional[Decimal] = None
    book_amount: Optional[Decimal] = None
    difference: Optional[Decimal] = None
    confidence_score: Optional[Decimal] = None
    status: str
    notes: Optional[str] = None
    matched_at: datetime


class ReconciliationResponse(BaseModel):
    """Schema for reconciliation response"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    reconciliation_number: str

    period_start: date
    period_end: date

    statement_opening_balance: Decimal
    statement_closing_balance: Decimal
    book_opening_balance: Decimal
    book_closing_balance: Decimal

    total_matched: Decimal
    total_unmatched_statement: Decimal
    total_unmatched_book: Decimal
    outstanding_deposits: int
    outstanding_withdrawals: int
    reconciling_difference: Decimal

    status: str
    is_balanced: bool

    completed_by: Optional[UUID] = None
    completed_at: Optional[datetime] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None

    notes: Optional[str] = None
    created_at: datetime


class ReconciliationDetailResponse(ReconciliationResponse):
    """Reconciliation with lines"""
    lines: List[ReconciliationLineResponse] = []


class ReconciliationSummary(BaseModel):
    """Brief reconciliation summary"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reconciliation_number: str
    period_start: date
    period_end: date
    statement_closing_balance: Decimal
    reconciling_difference: Decimal
    status: str
    is_balanced: bool


class MatchingRuleCreate(BaseModel):
    """Schema for creating a matching rule"""
    rule_name: str = Field(..., max_length=100)
    description: Optional[str] = None
    match_criteria: dict
    match_action: dict
    priority: int = Field(100, ge=1, le=1000)


class MatchingRuleResponse(BaseModel):
    """Schema for matching rule response"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rule_name: str
    description: Optional[str] = None
    match_criteria: dict
    match_action: dict
    priority: int
    is_active: bool
    times_matched: int
    last_matched_at: Optional[datetime] = None
    created_at: datetime


class AutoMatchRequest(BaseModel):
    """Request for auto-matching"""
    reconciliation_id: UUID
    apply_rules: bool = True
    match_threshold: Decimal = Field(Decimal("0.8"), ge=0, le=1)


class AutoMatchResult(BaseModel):
    """Result of auto-matching"""
    total_transactions: int
    matched_count: int
    suggested_count: int
    unmatched_count: int
    matches: List[dict]
