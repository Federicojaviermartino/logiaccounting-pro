"""
Fiscal Period Models
Fiscal years and periods for accounting
"""

from datetime import datetime, date
from typing import Optional
from enum import Enum
import uuid

from sqlalchemy import Column, String, Boolean, DateTime, Date, ForeignKey, Integer, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class FiscalYear(Base):
    """Fiscal year definition."""

    __tablename__ = "fiscal_years"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    name = Column(String(100), nullable=False)  # 'FY 2026'
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    is_closed = Column(Boolean, default=False)
    closed_at = Column(DateTime)
    closed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    periods = relationship("FiscalPeriod", back_populates="fiscal_year", order_by="FiscalPeriod.period_number")

    __table_args__ = (
        Index("idx_fiscal_years_customer", "customer_id"),
        Index("idx_fiscal_years_dates", "start_date", "end_date"),
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "is_closed": self.is_closed,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "periods": [p.to_dict() for p in self.periods],
        }


class FiscalPeriod(Base):
    """Fiscal period (month/quarter) within a year."""

    __tablename__ = "fiscal_periods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fiscal_year_id = Column(UUID(as_uuid=True), ForeignKey("fiscal_years.id"), nullable=False)

    name = Column(String(50), nullable=False)  # 'January 2026'
    period_number = Column(Integer, nullable=False)  # 1-12
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    is_closed = Column(Boolean, default=False)
    is_adjustment = Column(Boolean, default=False)  # Year-end adjustment period

    closed_at = Column(DateTime)
    closed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    close_notes = Column(Text)

    # Relationships
    fiscal_year = relationship("FiscalYear", back_populates="periods")
    journal_entries = relationship("JournalEntry", back_populates="fiscal_period")

    __table_args__ = (
        Index("idx_fiscal_periods_year", "fiscal_year_id"),
        Index("idx_fiscal_periods_dates", "start_date", "end_date"),
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "fiscal_year_id": str(self.fiscal_year_id),
            "name": self.name,
            "period_number": self.period_number,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "is_closed": self.is_closed,
            "is_adjustment": self.is_adjustment,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
        }
