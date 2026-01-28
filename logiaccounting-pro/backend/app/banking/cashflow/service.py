"""
Cash Flow Forecasting Service
Business logic for cash flow forecasting
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.utils.datetime_utils import utc_now

from app.banking.cashflow.models import (
    CashFlowForecast, CashFlowForecastLine, PlannedCashTransaction, CashPosition,
    ForecastStatus, Granularity, TransactionType, RecurrencePattern
)
from app.banking.cashflow.schemas import (
    ForecastCreate, ForecastUpdate, PlannedTransactionCreate,
    PlannedTransactionUpdate, ForecastSummary
)
from app.banking.accounts.models import BankAccount


class CashFlowService:
    """Service for cash flow forecasting operations"""

    def __init__(self, db: Session, customer_id: UUID = None):
        self.db = db
        self.customer_id = customer_id

    def create_forecast(
        self,
        data: ForecastCreate,
        created_by: UUID
    ) -> CashFlowForecast:
        """Create a new cash flow forecast"""
        forecast = CashFlowForecast(
            customer_id=self.customer_id,
            forecast_name=data.forecast_name,
            description=data.description,
            period_start=data.period_start,
            period_end=data.period_end,
            granularity=data.granularity.value,
            include_ar=data.include_ar,
            include_ap=data.include_ap,
            include_recurring=data.include_recurring,
            include_planned=data.include_planned,
            bank_account_ids=[str(aid) for aid in data.bank_account_ids] if data.bank_account_ids else None,
            created_by=created_by
        )

        self.db.add(forecast)
        self.db.commit()
        self.db.refresh(forecast)

        return forecast

    def get_forecast_by_id(self, forecast_id: UUID) -> CashFlowForecast:
        """Get forecast by ID"""
        result = self.db.execute(
            select(CashFlowForecast).where(CashFlowForecast.id == forecast_id)
        )
        forecast = result.scalar_one_or_none()

        if not forecast:
            raise ValueError(f"Forecast {forecast_id} not found")

        return forecast

    def get_forecasts(
        self,
        status: ForecastStatus = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[CashFlowForecast], int]:
        """Get forecasts with filtering"""
        query = select(CashFlowForecast).where(
            CashFlowForecast.customer_id == self.customer_id
        )

        if status:
            query = query.where(CashFlowForecast.status == status.value)

        # Count total
        count_result = self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        # Get paginated results
        query = query.order_by(CashFlowForecast.created_at.desc())
        query = query.offset(skip).limit(limit)

        result = self.db.execute(query)
        forecasts = list(result.scalars().all())

        return forecasts, total

    def generate_forecast(
        self,
        forecast_id: UUID,
        generated_by: UUID
    ) -> CashFlowForecast:
        """Generate or regenerate forecast lines"""
        forecast = self.get_forecast_by_id(forecast_id)

        # Clear existing lines
        self.db.execute(
            CashFlowForecastLine.__table__.delete().where(
                CashFlowForecastLine.forecast_id == forecast_id
            )
        )

        # Get current cash position
        current_cash = self._get_current_cash_position()

        # Generate periods based on granularity
        periods = self._generate_periods(
            forecast.period_start,
            forecast.period_end,
            Granularity(forecast.granularity)
        )

        opening_balance = current_cash

        for period_start, period_end, label in periods:
            # Calculate inflows
            ar_collections = Decimal("0")
            planned_inflows = Decimal("0")

            if forecast.include_ar:
                ar_collections = self._estimate_ar_collections(period_start, period_end)

            if forecast.include_planned:
                planned_inflows = self._get_planned_inflows(period_start, period_end)

            total_inflows = ar_collections + planned_inflows

            # Calculate outflows
            ap_payments = Decimal("0")
            planned_outflows = Decimal("0")

            if forecast.include_ap:
                ap_payments = self._estimate_ap_payments(period_start, period_end)

            if forecast.include_planned:
                planned_outflows = self._get_planned_outflows(period_start, period_end)

            total_outflows = ap_payments + planned_outflows

            # Calculate closing balance
            net_cash_flow = total_inflows - total_outflows
            closing_balance = opening_balance + net_cash_flow

            # Create line
            line = CashFlowForecastLine(
                forecast_id=forecast_id,
                period_date=period_start,
                period_label=label,
                opening_balance=opening_balance,
                ar_collections=ar_collections,
                planned_inflows=planned_inflows,
                total_inflows=total_inflows,
                ap_payments=ap_payments,
                planned_outflows=planned_outflows,
                total_outflows=total_outflows,
                net_cash_flow=net_cash_flow,
                closing_balance=closing_balance
            )

            self.db.add(line)

            # Update opening balance for next period
            opening_balance = closing_balance

        forecast.status = ForecastStatus.ACTIVE.value
        forecast.last_generated_at = utc_now()
        forecast.generated_by = generated_by

        self.db.commit()
        self.db.refresh(forecast)

        return forecast

    def create_planned_transaction(
        self,
        data: PlannedTransactionCreate,
        created_by: UUID
    ) -> PlannedCashTransaction:
        """Create a planned transaction"""
        transaction = PlannedCashTransaction(
            customer_id=self.customer_id,
            description=data.description,
            category=data.category,
            transaction_type=data.transaction_type.value,
            amount=data.amount,
            currency=data.currency,
            bank_account_id=data.bank_account_id,
            scheduled_date=data.scheduled_date,
            is_recurring=data.is_recurring,
            recurrence_pattern=data.recurrence_pattern.value if data.recurrence_pattern else None,
            recurrence_end_date=data.recurrence_end_date,
            notes=data.notes,
            created_by=created_by
        )

        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)

        return transaction

    def get_planned_transactions(
        self,
        start_date: date = None,
        end_date: date = None,
        transaction_type: TransactionType = None,
        is_active: bool = True,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[PlannedCashTransaction], int]:
        """Get planned transactions"""
        query = select(PlannedCashTransaction).where(
            PlannedCashTransaction.customer_id == self.customer_id
        )

        if start_date:
            query = query.where(PlannedCashTransaction.scheduled_date >= start_date)

        if end_date:
            query = query.where(PlannedCashTransaction.scheduled_date <= end_date)

        if transaction_type:
            query = query.where(PlannedCashTransaction.transaction_type == transaction_type.value)

        if is_active is not None:
            query = query.where(PlannedCashTransaction.is_active == is_active)

        # Count total
        count_result = self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        # Get paginated results
        query = query.order_by(PlannedCashTransaction.scheduled_date)
        query = query.offset(skip).limit(limit)

        result = self.db.execute(query)
        transactions = list(result.scalars().all())

        return transactions, total

    def update_planned_transaction(
        self,
        transaction_id: UUID,
        data: PlannedTransactionUpdate
    ) -> PlannedCashTransaction:
        """Update a planned transaction"""
        result = self.db.execute(
            select(PlannedCashTransaction).where(PlannedCashTransaction.id == transaction_id)
        )
        transaction = result.scalar_one_or_none()

        if not transaction:
            raise ValueError(f"Planned transaction {transaction_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(transaction, field, value)

        self.db.commit()
        self.db.refresh(transaction)

        return transaction

    def create_cash_position_snapshot(self) -> CashPosition:
        """Create a daily cash position snapshot"""
        # Get all active bank accounts
        result = self.db.execute(
            select(BankAccount).where(
                and_(
                    BankAccount.customer_id == self.customer_id,
                    BankAccount.is_active == True
                )
            )
        )
        accounts = list(result.scalars().all())

        total_cash = Decimal("0")
        cash_by_currency = {}
        cash_by_account = []

        for acc in accounts:
            total_cash += acc.current_balance

            if acc.currency not in cash_by_currency:
                cash_by_currency[acc.currency] = Decimal("0")
            cash_by_currency[acc.currency] += acc.current_balance

            cash_by_account.append({
                "account_id": str(acc.id),
                "account_name": acc.account_name,
                "balance": float(acc.current_balance),
                "currency": acc.currency
            })

        # Convert Decimal to float for JSON storage
        cash_by_currency = {k: float(v) for k, v in cash_by_currency.items()}

        position = CashPosition(
            customer_id=self.customer_id,
            snapshot_date=date.today(),
            total_cash=total_cash,
            cash_by_currency=cash_by_currency,
            cash_by_account=cash_by_account
        )

        self.db.add(position)
        self.db.commit()
        self.db.refresh(position)

        return position

    def get_forecast_summary(self) -> ForecastSummary:
        """Get cash flow forecast summary for dashboard"""
        current_cash = self._get_current_cash_position()

        # Get active forecast
        result = self.db.execute(
            select(CashFlowForecast).where(
                and_(
                    CashFlowForecast.customer_id == self.customer_id,
                    CashFlowForecast.status == ForecastStatus.ACTIVE.value
                )
            ).order_by(CashFlowForecast.last_generated_at.desc()).limit(1)
        )
        forecast = result.scalar_one_or_none()

        projected_30 = current_cash
        projected_60 = current_cash
        projected_90 = current_cash
        expected_ar = Decimal("0")
        expected_ap = Decimal("0")

        if forecast:
            # Get projections from forecast lines
            today = date.today()
            day_30 = today + timedelta(days=30)
            day_60 = today + timedelta(days=60)
            day_90 = today + timedelta(days=90)

            lines_result = self.db.execute(
                select(CashFlowForecastLine).where(
                    CashFlowForecastLine.forecast_id == forecast.id
                ).order_by(CashFlowForecastLine.period_date)
            )
            lines = list(lines_result.scalars().all())

            for line in lines:
                if line.period_date <= day_30:
                    projected_30 = line.closing_balance
                if line.period_date <= day_60:
                    projected_60 = line.closing_balance
                if line.period_date <= day_90:
                    projected_90 = line.closing_balance

                expected_ar += line.ar_collections
                expected_ap += line.ap_payments

        return ForecastSummary(
            current_cash=current_cash,
            projected_cash_30_days=projected_30,
            projected_cash_60_days=projected_60,
            projected_cash_90_days=projected_90,
            expected_ar_collections=expected_ar,
            expected_ap_payments=expected_ap
        )

    def _get_current_cash_position(self) -> Decimal:
        """Get current total cash position"""
        result = self.db.execute(
            select(func.sum(BankAccount.current_balance)).where(
                and_(
                    BankAccount.customer_id == self.customer_id,
                    BankAccount.is_active == True
                )
            )
        )
        total = result.scalar()
        return total or Decimal("0")

    def _generate_periods(
        self,
        start_date: date,
        end_date: date,
        granularity: Granularity
    ) -> List[Tuple[date, date, str]]:
        """Generate period ranges based on granularity"""
        periods = []
        current = start_date

        while current <= end_date:
            if granularity == Granularity.DAILY:
                period_end = current
                label = current.strftime("%Y-%m-%d")
                next_start = current + timedelta(days=1)
            elif granularity == Granularity.WEEKLY:
                period_end = min(current + timedelta(days=6), end_date)
                label = f"Week of {current.strftime('%b %d')}"
                next_start = current + timedelta(days=7)
            else:  # MONTHLY
                # Get last day of month
                if current.month == 12:
                    period_end = date(current.year + 1, 1, 1) - timedelta(days=1)
                else:
                    period_end = date(current.year, current.month + 1, 1) - timedelta(days=1)
                period_end = min(period_end, end_date)
                label = current.strftime("%B %Y")
                if current.month == 12:
                    next_start = date(current.year + 1, 1, 1)
                else:
                    next_start = date(current.year, current.month + 1, 1)

            periods.append((current, period_end, label))
            current = next_start

        return periods

    def _estimate_ar_collections(self, start_date: date, end_date: date) -> Decimal:
        """Estimate AR collections for a period (simplified)"""
        # In production, this would analyze open invoices and payment patterns
        return Decimal("0")

    def _estimate_ap_payments(self, start_date: date, end_date: date) -> Decimal:
        """Estimate AP payments for a period (simplified)"""
        # In production, this would analyze open bills and due dates
        return Decimal("0")

    def _get_planned_inflows(self, start_date: date, end_date: date) -> Decimal:
        """Get planned inflows for a period"""
        result = self.db.execute(
            select(func.sum(PlannedCashTransaction.amount)).where(
                and_(
                    PlannedCashTransaction.customer_id == self.customer_id,
                    PlannedCashTransaction.transaction_type == TransactionType.INFLOW.value,
                    PlannedCashTransaction.scheduled_date >= start_date,
                    PlannedCashTransaction.scheduled_date <= end_date,
                    PlannedCashTransaction.is_active == True,
                    PlannedCashTransaction.is_completed == False
                )
            )
        )
        total = result.scalar()
        return total or Decimal("0")

    def _get_planned_outflows(self, start_date: date, end_date: date) -> Decimal:
        """Get planned outflows for a period"""
        result = self.db.execute(
            select(func.sum(PlannedCashTransaction.amount)).where(
                and_(
                    PlannedCashTransaction.customer_id == self.customer_id,
                    PlannedCashTransaction.transaction_type == TransactionType.OUTFLOW.value,
                    PlannedCashTransaction.scheduled_date >= start_date,
                    PlannedCashTransaction.scheduled_date <= end_date,
                    PlannedCashTransaction.is_active == True,
                    PlannedCashTransaction.is_completed == False
                )
            )
        )
        total = result.scalar()
        return total or Decimal("0")
