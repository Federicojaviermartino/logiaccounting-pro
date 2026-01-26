"""
Depreciation calculation engine.

Supports multiple depreciation methods:
- Straight Line
- Declining Balance
- Double Declining Balance
- Sum of Years Digits
- Units of Production
"""
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Tuple
from uuid import UUID
from calendar import monthrange
from dataclasses import dataclass

from app.fixed_assets.models.asset import FixedAsset
from app.fixed_assets.models.category import DepreciationMethod


@dataclass
class DepreciationResult:
    """Result of depreciation calculation."""
    period_number: int
    period_year: int
    period_month: int
    period_start: date
    period_end: date

    depreciation_amount: Decimal
    accumulated_depreciation: Decimal
    opening_book_value: Decimal
    closing_book_value: Decimal

    units_this_period: Optional[Decimal] = None
    is_final_period: bool = False


class DepreciationEngine:
    """
    Calculates depreciation using various methods.
    """

    # Rounding precision
    PRECISION = Decimal("0.01")

    def __init__(self, asset: FixedAsset):
        self.asset = asset
        self.total_cost = asset.total_cost
        self.salvage_value = asset.salvage_value
        self.depreciable_amount = self.total_cost - self.salvage_value
        self.useful_life_months = asset.useful_life_months
        self.depreciation_method = asset.depreciation_method

        # For declining balance
        self.declining_rate = asset.declining_rate or self._calculate_declining_rate()

        # For units of production
        self.total_units = asset.total_estimated_units

    def _round(self, value: Decimal) -> Decimal:
        """Round to 2 decimal places."""
        return value.quantize(self.PRECISION, rounding=ROUND_HALF_UP)

    def _calculate_declining_rate(self) -> Decimal:
        """Calculate declining rate if not specified."""
        if self.useful_life_months == 0:
            return Decimal(0)

        useful_life_years = Decimal(self.useful_life_months) / 12

        if self.depreciation_method == DepreciationMethod.DOUBLE_DECLINING:
            # Double the straight-line rate
            return self._round((Decimal(2) / useful_life_years) * 100)
        else:
            # Standard declining (150%)
            return self._round((Decimal("1.5") / useful_life_years) * 100)

    # ==================== Main Calculation Methods ====================

    def calculate_monthly_depreciation(
        self,
        period_year: int,
        period_month: int,
        accumulated_depreciation: Decimal,
        units_produced: Optional[Decimal] = None
    ) -> Decimal:
        """
        Calculate depreciation for a single month.
        """
        current_book_value = self.total_cost - accumulated_depreciation

        # Already fully depreciated
        if current_book_value <= self.salvage_value:
            return Decimal(0)

        # Calculate based on method
        if self.depreciation_method == DepreciationMethod.STRAIGHT_LINE:
            depreciation = self._straight_line_monthly()

        elif self.depreciation_method in (
            DepreciationMethod.DECLINING_BALANCE,
            DepreciationMethod.DOUBLE_DECLINING
        ):
            depreciation = self._declining_balance_monthly(current_book_value)

        elif self.depreciation_method == DepreciationMethod.SUM_OF_YEARS:
            depreciation = self._sum_of_years_monthly(accumulated_depreciation)

        elif self.depreciation_method == DepreciationMethod.UNITS_OF_PRODUCTION:
            if units_produced is None:
                raise ValueError("Units produced required for units of production method")
            depreciation = self._units_of_production(units_produced)

        else:
            raise ValueError(f"Unsupported depreciation method: {self.depreciation_method}")

        # Don't depreciate below salvage value
        max_depreciation = current_book_value - self.salvage_value
        depreciation = min(depreciation, max_depreciation)

        return self._round(max(Decimal(0), depreciation))

    def generate_full_schedule(
        self,
        start_date: Optional[date] = None
    ) -> List[DepreciationResult]:
        """
        Generate complete depreciation schedule from start to end.
        """
        start_date = start_date or self.asset.depreciation_start_date or self.asset.in_service_date
        if not start_date:
            raise ValueError("Start date required for depreciation schedule")

        schedule = []
        accumulated = self.asset.accumulated_depreciation or Decimal(0)
        current_date = start_date
        period_number = 1

        # Calculate until fully depreciated or useful life ends
        max_periods = self.useful_life_months + 12  # Buffer for partial periods

        while period_number <= max_periods:
            book_value_before = self.total_cost - accumulated

            if book_value_before <= self.salvage_value:
                break

            # Calculate depreciation for this period
            depreciation = self.calculate_monthly_depreciation(
                period_year=current_date.year,
                period_month=current_date.month,
                accumulated_depreciation=accumulated
            )

            if depreciation <= 0:
                break

            accumulated += depreciation
            book_value_after = self.total_cost - accumulated

            # Period dates
            _, last_day = monthrange(current_date.year, current_date.month)
            period_start = date(current_date.year, current_date.month, 1)
            period_end = date(current_date.year, current_date.month, last_day)

            result = DepreciationResult(
                period_number=period_number,
                period_year=current_date.year,
                period_month=current_date.month,
                period_start=period_start,
                period_end=period_end,
                depreciation_amount=depreciation,
                accumulated_depreciation=accumulated,
                opening_book_value=book_value_before,
                closing_book_value=book_value_after,
                is_final_period=(book_value_after <= self.salvage_value)
            )

            schedule.append(result)

            # Move to next month
            if current_date.month == 12:
                current_date = date(current_date.year + 1, 1, 1)
            else:
                current_date = date(current_date.year, current_date.month + 1, 1)

            period_number += 1

        return schedule

    # ==================== Method-Specific Calculations ====================

    def _straight_line_monthly(self) -> Decimal:
        """
        Straight-line depreciation per month.

        Formula: (Cost - Salvage) / Useful Life Months
        """
        if self.useful_life_months == 0:
            return Decimal(0)

        return self.depreciable_amount / self.useful_life_months

    def _declining_balance_monthly(self, current_book_value: Decimal) -> Decimal:
        """
        Declining balance depreciation per month.

        Formula: Book Value x (Annual Rate / 12)
        """
        if self.declining_rate == 0:
            return Decimal(0)

        # Convert annual rate to monthly
        monthly_rate = self.declining_rate / 100 / 12

        depreciation = current_book_value * monthly_rate

        # Switch to straight-line if it gives higher depreciation
        remaining_life = self._get_remaining_life_months()
        if remaining_life > 0:
            remaining_depreciable = current_book_value - self.salvage_value
            straight_line = remaining_depreciable / remaining_life

            if straight_line > depreciation:
                depreciation = straight_line

        return depreciation

    def _sum_of_years_monthly(self, accumulated_depreciation: Decimal) -> Decimal:
        """
        Sum of years digits depreciation per month.

        Formula: (Cost - Salvage) x (Remaining Life / Sum of Years) / 12
        """
        useful_life_years = self.useful_life_months // 12
        if useful_life_years == 0:
            return Decimal(0)

        # Sum of years: n(n+1)/2
        sum_of_years = (useful_life_years * (useful_life_years + 1)) // 2

        # Determine current year
        current_year = self._get_current_depreciation_year(accumulated_depreciation)
        remaining_years = useful_life_years - current_year + 1

        if remaining_years <= 0 or sum_of_years == 0:
            return Decimal(0)

        # Annual depreciation for this year
        annual_depreciation = self.depreciable_amount * Decimal(remaining_years) / Decimal(sum_of_years)

        # Monthly portion
        return annual_depreciation / 12

    def _units_of_production(self, units_produced: Decimal) -> Decimal:
        """
        Units of production depreciation.

        Formula: (Cost - Salvage) / Total Units x Units This Period
        """
        if not self.total_units or self.total_units == 0:
            return Decimal(0)

        depreciation_per_unit = self.depreciable_amount / self.total_units

        return depreciation_per_unit * units_produced

    # ==================== Helper Methods ====================

    def _get_remaining_life_months(self) -> int:
        """Get remaining useful life in months."""
        if not self.asset.depreciation_start_date:
            return self.useful_life_months

        today = date.today()
        months_elapsed = (
            (today.year - self.asset.depreciation_start_date.year) * 12 +
            (today.month - self.asset.depreciation_start_date.month)
        )

        return max(0, self.useful_life_months - months_elapsed)

    def _get_current_depreciation_year(self, accumulated_depreciation: Decimal) -> int:
        """Determine which year of depreciation we're in."""
        if not self.asset.depreciation_start_date:
            return 1

        # Calculate based on accumulated depreciation
        annual_straight_line = self.depreciable_amount / (self.useful_life_months / 12)

        if annual_straight_line == 0:
            return 1

        years_completed = int(accumulated_depreciation / annual_straight_line)

        return min(years_completed + 1, self.useful_life_months // 12)

    # ==================== Partial Period Calculations ====================

    def calculate_partial_month(
        self,
        full_month_depreciation: Decimal,
        acquisition_date: date,
        period_year: int,
        period_month: int
    ) -> Decimal:
        """
        Calculate depreciation for partial first/last month.

        Uses daily proration.
        """
        _, days_in_month = monthrange(period_year, period_month)

        # First month (acquisition month)
        if (acquisition_date.year == period_year and
            acquisition_date.month == period_month):
            days_owned = days_in_month - acquisition_date.day + 1
            return self._round(full_month_depreciation * days_owned / days_in_month)

        return full_month_depreciation

    def calculate_mid_month_convention(
        self,
        full_month_depreciation: Decimal,
        acquisition_date: date,
        period_year: int,
        period_month: int
    ) -> Decimal:
        """
        Apply mid-month convention.

        Assets acquired before 15th: full month
        Assets acquired on/after 15th: half month
        """
        if (acquisition_date.year == period_year and
            acquisition_date.month == period_month):
            if acquisition_date.day >= 15:
                return self._round(full_month_depreciation / 2)

        return full_month_depreciation


class DepreciationCalculator:
    """
    High-level depreciation calculator for batch processing.
    """

    @staticmethod
    def calculate_for_asset(
        asset: FixedAsset,
        period_year: int,
        period_month: int,
        units_produced: Optional[Decimal] = None
    ) -> Tuple[Decimal, str]:
        """
        Calculate depreciation for an asset for a given period.

        Returns: (depreciation_amount, skip_reason or None)
        """
        # Validation checks
        if asset.status.value not in ("active", "fully_depreciated"):
            return Decimal(0), f"Asset status is {asset.status.value}"

        if asset.is_fully_depreciated:
            return Decimal(0), "Asset is fully depreciated"

        if asset.depreciation_suspended:
            return Decimal(0), f"Depreciation suspended: {asset.suspension_reason}"

        if not asset.depreciation_start_date:
            return Decimal(0), "No depreciation start date"

        # Check if period is before depreciation start
        period_date = date(period_year, period_month, 1)
        if period_date < asset.depreciation_start_date.replace(day=1):
            return Decimal(0), "Period before depreciation start"

        # Check if already depreciated this period
        if asset.last_depreciation_date:
            last_period = date(
                asset.last_depreciation_date.year,
                asset.last_depreciation_date.month,
                1
            )
            if period_date <= last_period:
                return Decimal(0), "Already depreciated for this period"

        # Calculate depreciation
        engine = DepreciationEngine(asset)

        try:
            depreciation = engine.calculate_monthly_depreciation(
                period_year=period_year,
                period_month=period_month,
                accumulated_depreciation=asset.accumulated_depreciation,
                units_produced=units_produced
            )

            return depreciation, None

        except Exception as e:
            return Decimal(0), f"Calculation error: {str(e)}"

    @staticmethod
    def generate_schedule(asset: FixedAsset) -> List[DepreciationResult]:
        """Generate full depreciation schedule for asset."""
        engine = DepreciationEngine(asset)
        return engine.generate_full_schedule()
