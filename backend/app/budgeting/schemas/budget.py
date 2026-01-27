"""Budget and version schemas."""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class BudgetType(str, Enum):
    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    MONTHLY = "monthly"
    PROJECT = "project"
    DEPARTMENTAL = "departmental"


class BudgetStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ACTIVE = "active"
    CLOSED = "closed"


class BudgetCreate(BaseModel):
    """Create budget."""
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    budget_type: BudgetType = BudgetType.ANNUAL
    fiscal_year: int = Field(..., ge=2000, le=2100)
    start_date: date
    end_date: date
    department_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    currency: str = Field(default="USD", max_length=3)
    requires_approval: bool = True
    allow_overspend: bool = False

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date <= self.start_date:
            raise ValueError("End date must be after start date")
        return self


class BudgetUpdate(BaseModel):
    """Update budget."""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    requires_approval: Optional[bool] = None
    allow_overspend: Optional[bool] = None


class BudgetResponse(BaseModel):
    """Budget response."""
    id: UUID
    budget_code: str
    name: str
    description: Optional[str]
    budget_type: BudgetType
    fiscal_year: int
    start_date: date
    end_date: date
    currency: str
    status: BudgetStatus
    total_revenue: Decimal
    total_expenses: Decimal
    total_net_income: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class BudgetSummary(BaseModel):
    """Budget summary for lists."""
    id: UUID
    budget_code: str
    name: str
    budget_type: BudgetType
    fiscal_year: int
    status: BudgetStatus
    total_revenue: Decimal
    total_expenses: Decimal
    total_net_income: Decimal

    class Config:
        from_attributes = True


class VersionCreate(BaseModel):
    """Create budget version."""
    version_name: str = Field(..., max_length=100)
    description: Optional[str] = None
    version_type: str = "original"
    parent_version_id: Optional[UUID] = None


class VersionResponse(BaseModel):
    """Budget version response."""
    id: UUID
    budget_id: UUID
    version_number: int
    version_name: str
    version_type: str
    total_revenue: Decimal
    total_expenses: Decimal
    total_net_income: Decimal
    status: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
