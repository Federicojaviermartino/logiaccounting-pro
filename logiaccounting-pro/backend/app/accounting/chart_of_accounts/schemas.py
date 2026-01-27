"""
Chart of Accounts Schemas
Pydantic schemas for validation and serialization
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, validator


class AccountTypeEnum(str, Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class NormalBalanceEnum(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"


# ============== Account Type Schemas ==============

class AccountTypeBase(BaseModel):
    name: str
    display_name: str
    normal_balance: NormalBalanceEnum
    display_order: int = 0
    description: Optional[str] = None


class AccountTypeResponse(AccountTypeBase):
    id: UUID
    report_type: str

    class Config:
        from_attributes = True


# ============== Account Schemas ==============

class AccountBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    account_type_id: UUID
    parent_id: Optional[UUID] = None
    currency: str = Field(default="USD", max_length=3)
    is_reconcilable: bool = False
    is_header: bool = False
    tax_code: Optional[str] = None
    default_tax_rate: Optional[Decimal] = None
    cost_center: Optional[str] = None
    department: Optional[str] = None
    notes: Optional[str] = None

    @validator("code")
    def validate_code(cls, v):
        if not v.replace(".", "").replace("-", "").isalnum():
            raise ValueError("Account code must be alphanumeric")
        return v.upper()


class AccountCreate(AccountBase):
    opening_balance: Decimal = Decimal("0")


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    is_reconcilable: Optional[bool] = None
    is_header: Optional[bool] = None
    tax_code: Optional[str] = None
    default_tax_rate: Optional[Decimal] = None
    cost_center: Optional[str] = None
    department: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class AccountResponse(AccountBase):
    id: UUID
    customer_id: UUID
    level: int
    path: Optional[str]
    is_active: bool
    is_system: bool
    opening_balance: Decimal
    current_balance: Decimal
    created_at: datetime
    updated_at: datetime
    account_type: Optional[AccountTypeResponse] = None

    class Config:
        from_attributes = True


class AccountTreeNode(BaseModel):
    id: UUID
    code: str
    name: str
    full_name: str
    type: Optional[str]
    balance: float
    is_header: bool
    is_active: bool
    level: int
    has_children: bool
    children: List["AccountTreeNode"] = []

    class Config:
        from_attributes = True


AccountTreeNode.model_rebuild()


class AccountSummary(BaseModel):
    """Simplified account for dropdowns."""
    id: UUID
    code: str
    name: str
    full_name: str
    type: str
    can_post: bool


class AccountBalanceUpdate(BaseModel):
    """For updating account balance."""
    debit_amount: Decimal = Decimal("0")
    credit_amount: Decimal = Decimal("0")


# ============== Import/Export Schemas ==============

class AccountImportRow(BaseModel):
    code: str
    name: str
    type: AccountTypeEnum
    parent_code: Optional[str] = None
    description: Optional[str] = None
    opening_balance: Decimal = Decimal("0")
    is_header: bool = False


class AccountImportRequest(BaseModel):
    template_name: Optional[str] = None  # Use predefined template
    accounts: Optional[List[AccountImportRow]] = None  # Or provide list


class AccountImportResult(BaseModel):
    success: bool
    accounts_created: int
    accounts_updated: int
    errors: List[str] = []


# ============== Filter/Query Schemas ==============

class AccountFilter(BaseModel):
    search: Optional[str] = None
    account_type: Optional[AccountTypeEnum] = None
    is_active: Optional[bool] = None
    is_header: Optional[bool] = None
    parent_id: Optional[UUID] = None
    has_balance: Optional[bool] = None


class AccountListResponse(BaseModel):
    accounts: List[AccountResponse]
    total: int
    page: int
    page_size: int
