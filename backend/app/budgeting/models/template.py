"""Budget template models."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import String, Boolean, Integer, ForeignKey, Text, Numeric, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base


class BudgetTemplate(Base):
    """Reusable budget template."""
    __tablename__ = "budget_templates"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Template type
    template_type: Mapped[str] = mapped_column(String(30), default="standard")  # standard, department, project, zero_based

    # Default settings
    period_type: Mapped[str] = mapped_column(String(20), default="annual")  # annual, quarterly, monthly
    default_distribution: Mapped[str] = mapped_column(String(20), default="equal")

    # Account filter (optional - which accounts to include)
    account_filter: Mapped[Optional[dict]] = mapped_column(JSONB)  # {"types": ["revenue", "expense"], "codes": ["4*", "5*"]}

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    created_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    items: Mapped[List["BudgetTemplateItem"]] = relationship("BudgetTemplateItem", back_populates="template", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("customer_id", "name", name="uq_budget_template_name"),
        Index("idx_budget_templates_customer", "customer_id"),
    )


class BudgetTemplateItem(Base):
    """Budget template line item."""
    __tablename__ = "budget_template_items"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    template_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("budget_templates.id", ondelete="CASCADE"), nullable=False)

    # Can be specific account or account type
    account_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("chart_of_accounts.id"))
    account_type: Mapped[Optional[str]] = mapped_column(String(20))  # Alternative: use account type

    # Default values
    default_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    growth_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))  # % growth from prior year

    # Period distribution (optional custom distribution)
    period_distribution: Mapped[Optional[List]] = mapped_column(JSONB)  # [8.33, 8.33, ..., 8.37]

    default_notes: Mapped[Optional[str]] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    template: Mapped["BudgetTemplate"] = relationship("BudgetTemplate", back_populates="items")

    __table_args__ = (
        Index("idx_budget_template_items_template", "template_id"),
    )
