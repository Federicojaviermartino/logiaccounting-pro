"""
Bank Transaction Schemas
Pydantic schemas for bank transactions
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

from app.banking.transactions.models import TransactionType, MatchStatus, Direction


class BankTransactionCreate(BaseModel):
    """Schema for creating a bank transaction"""
    account_id: UUID
    transaction_date: date
    value_date: Optional[date] = None
    transaction_type: TransactionType
    direction: Direction
    amount: Decimal = Field(..., gt=0)
    currency: str = Field("USD", max_length=3)

    payee_payer_name: Optional[str] = Field(None, max_length=200)
    payee_payer_account: Optional[str] = Field(None, max_length=50)
    payee_payer_bank: Optional[str] = Field(None, max_length=100)

    description: Optional[str] = None
    memo: Optional[str] = None
    check_number: Optional[str] = Field(None, max_length=20)
    category: Optional[str] = Field(None, max_length=50)
    transaction_ref: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class BankTransactionUpdate(BaseModel):
    """Schema for updating a bank transaction"""
    payee_payer_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    memo: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class BankTransactionResponse(BaseModel):
    """Schema for bank transaction response"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    transaction_ref: Optional[str] = None
    internal_ref: Optional[str] = None

    transaction_date: date
    value_date: Optional[date] = None
    transaction_type: str
    direction: str

    amount: Decimal
    currency: str
    running_balance: Optional[Decimal] = None

    payee_payer_name: Optional[str] = None
    payee_payer_account: Optional[str] = None
    payee_payer_bank: Optional[str] = None

    description: Optional[str] = None
    memo: Optional[str] = None
    check_number: Optional[str] = None
    category: Optional[str] = None

    match_status: str
    is_reconciled: bool
    is_posted: bool

    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BankTransactionFilter(BaseModel):
    """Filter options for bank transactions"""
    account_id: Optional[UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    transaction_type: Optional[TransactionType] = None
    direction: Optional[Direction] = None
    match_status: Optional[MatchStatus] = None
    is_reconciled: Optional[bool] = None
    category: Optional[str] = None
    search: Optional[str] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None


class StatementImportRequest(BaseModel):
    """Request for importing bank statement"""
    account_id: UUID
    file_format: str = Field(..., pattern="^(csv|ofx|qfx|mt940)$")


class StatementImportResponse(BaseModel):
    """Response for bank statement import"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    file_name: str
    file_format: Optional[str] = None
    status: str

    period_start: Optional[date] = None
    period_end: Optional[date] = None
    opening_balance: Optional[Decimal] = None
    closing_balance: Optional[Decimal] = None

    total_transactions: Optional[int] = None
    transactions_imported: int
    transactions_duplicates: int
    transactions_errors: int

    error_message: Optional[str] = None
    imported_at: datetime


class TransactionMatchRequest(BaseModel):
    """Request to match a transaction"""
    transaction_id: UUID
    match_type: str = Field(..., pattern="^(invoice|bill|journal|transfer)$")
    match_id: UUID


class TransactionCategorizeRequest(BaseModel):
    """Request to categorize transactions"""
    transaction_ids: List[UUID]
    category: str = Field(..., max_length=50)
