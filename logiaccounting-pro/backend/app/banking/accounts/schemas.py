"""
Bank Account Schemas
Pydantic schemas for bank accounts
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
from uuid import UUID

from app.banking.accounts.models import AccountType


class BankAddressSchema(BaseModel):
    """Bank address details"""
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = Field(None, max_length=3)


class BankAccountCreate(BaseModel):
    """Schema for creating a bank account"""
    account_code: str = Field(..., min_length=1, max_length=20)
    account_name: str = Field(..., min_length=1, max_length=200)

    # Bank details
    bank_name: str = Field(..., min_length=1, max_length=200)
    bank_code: Optional[str] = Field(None, max_length=20)
    branch_code: Optional[str] = Field(None, max_length=20)
    branch_name: Optional[str] = Field(None, max_length=200)

    # Account numbers
    account_number: str = Field(..., min_length=1, max_length=50)
    iban: Optional[str] = Field(None, max_length=50)
    routing_number: Optional[str] = Field(None, max_length=50)
    sort_code: Optional[str] = Field(None, max_length=20)

    # Currency and type
    currency: str = Field("USD", max_length=3)
    account_type: AccountType = AccountType.CHECKING

    # Limits
    overdraft_limit: Decimal = Field(default=Decimal("0"), ge=0)
    daily_limit: Optional[Decimal] = Field(None, ge=0)

    # Opening balance
    opening_balance: Decimal = Field(default=Decimal("0"))

    # GL Integration
    gl_account_id: Optional[UUID] = None

    # Contact
    contact_name: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=200)

    # Bank address
    bank_address: Optional[BankAddressSchema] = None

    is_primary: bool = False
    notes: Optional[str] = None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        return v.upper()

    @field_validator("iban")
    @classmethod
    def validate_iban(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.replace(" ", "").upper()
            if len(v) < 15 or len(v) > 34:
                raise ValueError("Invalid IBAN length")
        return v


class BankAccountUpdate(BaseModel):
    """Schema for updating a bank account"""
    account_name: Optional[str] = Field(None, max_length=200)

    # Bank details
    bank_name: Optional[str] = Field(None, max_length=200)
    bank_code: Optional[str] = Field(None, max_length=20)
    branch_code: Optional[str] = Field(None, max_length=20)
    branch_name: Optional[str] = Field(None, max_length=200)

    # Account numbers
    iban: Optional[str] = Field(None, max_length=50)
    routing_number: Optional[str] = Field(None, max_length=50)
    sort_code: Optional[str] = Field(None, max_length=20)

    # Limits
    overdraft_limit: Optional[Decimal] = Field(None, ge=0)
    daily_limit: Optional[Decimal] = Field(None, ge=0)

    # GL Integration
    gl_account_id: Optional[UUID] = None

    # Contact
    contact_name: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=200)

    # Bank address
    bank_address: Optional[BankAddressSchema] = None

    is_active: Optional[bool] = None
    is_primary: Optional[bool] = None
    notes: Optional[str] = None


class BankAccountResponse(BaseModel):
    """Schema for bank account response"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_code: str
    account_name: str

    # Bank details
    bank_name: str
    bank_code: Optional[str] = None
    branch_code: Optional[str] = None
    branch_name: Optional[str] = None

    # Account numbers (masked for security)
    account_number_masked: Optional[str] = Field(None, alias="masked_account_number")
    iban: Optional[str] = None
    routing_number: Optional[str] = None

    # Currency and type
    currency: str
    account_type: str

    # Limits
    overdraft_limit: Decimal
    daily_limit: Optional[Decimal] = None

    # Balances
    current_balance: Decimal
    available_balance: Decimal
    last_balance_date: Optional[date] = None

    # GL Integration
    gl_account_id: Optional[UUID] = None

    # Reconciliation
    last_reconciled_date: Optional[date] = None
    last_reconciled_balance: Optional[Decimal] = None

    # Status
    is_active: bool
    is_primary: bool
    is_online_enabled: bool

    # Contact
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None

    notes: Optional[str] = None

    created_at: datetime
    updated_at: datetime


class BankAccountSummary(BaseModel):
    """Brief bank account summary for dropdowns"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_code: str
    account_name: str
    bank_name: str
    currency: str
    current_balance: Decimal
    is_primary: bool


class BankAccountFilter(BaseModel):
    """Filter options for bank accounts"""
    search: Optional[str] = None
    currency: Optional[str] = None
    account_type: Optional[AccountType] = None
    is_active: Optional[bool] = None
    is_primary: Optional[bool] = None


class BankBalanceResponse(BaseModel):
    """Daily balance response"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    balance_date: date
    opening_balance: Decimal
    total_debits: Decimal
    total_credits: Decimal
    closing_balance: Decimal
    net_change: Decimal
    debit_count: int
    credit_count: int
    is_reconciled: bool


class BankBalanceHistoryRequest(BaseModel):
    """Request for balance history"""
    account_id: UUID
    start_date: date
    end_date: date


class CashPositionResponse(BaseModel):
    """Cash position across all accounts"""
    total_cash: Decimal
    total_cash_base_currency: Decimal
    base_currency: str
    accounts: List[BankAccountSummary]
    by_currency: dict
    snapshot_date: date
