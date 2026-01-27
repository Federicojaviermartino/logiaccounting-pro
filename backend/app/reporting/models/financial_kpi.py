"""Financial KPI tracking model."""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import (
    String, Integer, ForeignKey, Date, Numeric,
    Enum as SQLEnum, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class KPIPeriodType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class FinancialKPISnapshot(Base):
    """Point-in-time snapshot of financial KPIs."""
    __tablename__ = "financial_kpi_snapshots"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    period_type: Mapped[KPIPeriodType] = mapped_column(SQLEnum(KPIPeriodType), nullable=False)
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    period_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Balance Sheet
    total_assets: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    current_assets: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    total_liabilities: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    current_liabilities: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    total_equity: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    
    # Liquidity Ratios
    current_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4))
    quick_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4))
    working_capital: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    
    # P&L
    total_revenue: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    total_expenses: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    gross_profit: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    operating_income: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    net_income: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    
    # Profitability Ratios
    gross_profit_margin: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4))
    operating_margin: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4))
    net_profit_margin: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4))
    return_on_assets: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4))
    return_on_equity: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4))
    
    # Efficiency
    days_sales_outstanding: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    days_payable_outstanding: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    
    # Leverage
    debt_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4))
    debt_to_equity: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4))
    
    # AR/AP
    accounts_receivable: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    accounts_payable: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    
    # Cash
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    
    additional_metrics: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("customer_id", "period_type", "period_year", "period_number", name="uq_kpi_snapshot"),
        Index("idx_kpi_snapshots_customer", "customer_id"),
        Index("idx_kpi_snapshots_date", "snapshot_date"),
    )
