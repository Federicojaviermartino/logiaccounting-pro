"""Distribution pattern model."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, Boolean, ForeignKey, Text, Numeric, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DistributionPattern(Base):
    """Seasonal distribution pattern."""
    __tablename__ = "distribution_patterns"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    jan_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("8.33"))
    feb_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("8.33"))
    mar_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("8.33"))
    apr_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("8.33"))
    may_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("8.33"))
    jun_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("8.33"))
    jul_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("8.33"))
    aug_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("8.33"))
    sep_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("8.33"))
    oct_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("8.33"))
    nov_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("8.33"))
    dec_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("8.37"))

    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("customer_id", "name", name="uq_distribution_pattern_name"),
        Index("idx_distribution_patterns_customer", "customer_id"),
    )

    def get_month_percent(self, month: int) -> Decimal:
        """Get percentage for a specific month (1-12)."""
        month_attrs = [
            'jan_percent', 'feb_percent', 'mar_percent', 'apr_percent',
            'may_percent', 'jun_percent', 'jul_percent', 'aug_percent',
            'sep_percent', 'oct_percent', 'nov_percent', 'dec_percent'
        ]
        if 1 <= month <= 12:
            return getattr(self, month_attrs[month - 1])
        return Decimal(0)
