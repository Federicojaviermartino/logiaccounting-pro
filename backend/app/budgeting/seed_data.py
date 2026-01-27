"""Seed data for budgeting module."""
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.budgeting.models.distribution import DistributionPattern


def seed_distribution_patterns(db: Session, customer_id: str):
    """Create default distribution patterns."""

    patterns = [
        {
            "name": "Equal Distribution",
            "description": "Distribute equally across all months",
            "jan_percent": Decimal("8.33"),
            "feb_percent": Decimal("8.33"),
            "mar_percent": Decimal("8.33"),
            "apr_percent": Decimal("8.33"),
            "may_percent": Decimal("8.33"),
            "jun_percent": Decimal("8.33"),
            "jul_percent": Decimal("8.33"),
            "aug_percent": Decimal("8.33"),
            "sep_percent": Decimal("8.33"),
            "oct_percent": Decimal("8.33"),
            "nov_percent": Decimal("8.33"),
            "dec_percent": Decimal("8.37"),
            "is_default": True,
        },
        {
            "name": "Q4 Heavy",
            "description": "Higher allocation in Q4 (retail pattern)",
            "jan_percent": Decimal("6.00"),
            "feb_percent": Decimal("6.00"),
            "mar_percent": Decimal("7.00"),
            "apr_percent": Decimal("7.00"),
            "may_percent": Decimal("7.00"),
            "jun_percent": Decimal("8.00"),
            "jul_percent": Decimal("8.00"),
            "aug_percent": Decimal("8.00"),
            "sep_percent": Decimal("9.00"),
            "oct_percent": Decimal("10.00"),
            "nov_percent": Decimal("12.00"),
            "dec_percent": Decimal("12.00"),
            "is_default": False,
        },
        {
            "name": "Summer Peak",
            "description": "Higher allocation in summer months",
            "jan_percent": Decimal("5.00"),
            "feb_percent": Decimal("5.00"),
            "mar_percent": Decimal("7.00"),
            "apr_percent": Decimal("8.00"),
            "may_percent": Decimal("10.00"),
            "jun_percent": Decimal("12.00"),
            "jul_percent": Decimal("14.00"),
            "aug_percent": Decimal("12.00"),
            "sep_percent": Decimal("10.00"),
            "oct_percent": Decimal("8.00"),
            "nov_percent": Decimal("5.00"),
            "dec_percent": Decimal("4.00"),
            "is_default": False,
        },
    ]

    created = []
    for pattern_data in patterns:
        pattern = DistributionPattern(
            id=uuid4(),
            customer_id=customer_id,
            **pattern_data
        )
        db.add(pattern)
        created.append(pattern)

    db.commit()
    return created


if __name__ == "__main__":
    # Example usage
    print("Run this from your application context:")
    print("  from app.budgeting.seed_data import seed_distribution_patterns")
    print("  seed_distribution_patterns(db, customer_id)")
