"""
Payment Scheduler Optimizer
Optimizes payment scheduling for cash flow
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from uuid import uuid4
import logging

from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


@dataclass
class PaymentItem:
    """Payment item to be scheduled."""
    id: str
    vendor: str
    amount: float
    due_date: datetime
    priority: int = 5  # 1-10, 10 being highest
    allows_early_discount: bool = False
    early_discount_percent: float = 0.0
    early_discount_days: int = 0
    allows_late_payment: bool = True
    late_fee_percent: float = 0.0


@dataclass
class ScheduledPayment:
    """Scheduled payment result."""
    id: str = field(default_factory=lambda: f"sched_{uuid4().hex[:8]}")
    payment_id: str = ""
    vendor: str = ""
    amount: float = 0.0
    original_due_date: str = ""
    scheduled_date: str = ""
    reason: str = ""
    savings: float = 0.0
    risk_notes: str = ""


class PaymentOptimizer:
    """Optimizes payment scheduling."""

    def __init__(self):
        self.min_balance_threshold = 5000  # Minimum cash to maintain

    def optimize_schedule(
        self,
        payments: List[PaymentItem],
        current_balance: float,
        expected_inflows: List[Dict] = None,
        optimization_goal: str = "balanced",
    ) -> Dict:
        """Optimize payment schedule."""
        logger.info(f"Optimizing {len(payments)} payments with balance ${current_balance:,.2f}")

        expected_inflows = expected_inflows or []
        scheduled = []

        # Sort by priority and due date
        sorted_payments = sorted(
            payments,
            key=lambda p: (-p.priority, p.due_date),
        )

        running_balance = current_balance
        today = utc_now().date()

        for payment in sorted_payments:
            due_date = payment.due_date.date() if isinstance(payment.due_date, datetime) else payment.due_date

            # Calculate best payment date
            best_date, reason, savings = self._find_best_date(
                payment,
                running_balance,
                expected_inflows,
                today,
                optimization_goal,
            )

            # Check if we can afford this payment
            if running_balance - payment.amount < self.min_balance_threshold:
                # Try to delay if possible
                if payment.allows_late_payment:
                    best_date = self._find_affordable_date(
                        payment,
                        running_balance,
                        expected_inflows,
                        today,
                    )
                    reason = "Delayed due to cash flow constraints"

            scheduled.append(ScheduledPayment(
                payment_id=payment.id,
                vendor=payment.vendor,
                amount=payment.amount,
                original_due_date=due_date.isoformat(),
                scheduled_date=best_date.isoformat(),
                reason=reason,
                savings=savings,
                risk_notes="" if best_date <= due_date else "Payment scheduled after due date",
            ))

            # Update running balance on scheduled date
            running_balance -= payment.amount

        # Calculate summary
        total_savings = sum(s.savings for s in scheduled)
        on_time = sum(1 for s in scheduled if s.scheduled_date <= s.original_due_date)
        delayed = len(scheduled) - on_time

        return {
            "scheduled_payments": [s.__dict__ for s in scheduled],
            "summary": {
                "total_payments": len(scheduled),
                "total_amount": sum(p.amount for p in payments),
                "on_time": on_time,
                "delayed": delayed,
                "total_savings": total_savings,
                "ending_balance_estimate": running_balance,
            },
            "recommendations": self._generate_recommendations(scheduled, running_balance),
        }

    def _find_best_date(
        self,
        payment: PaymentItem,
        balance: float,
        inflows: List[Dict],
        today: datetime.date,
        goal: str,
    ) -> tuple:
        """Find the best date to make a payment."""
        due_date = payment.due_date.date() if isinstance(payment.due_date, datetime) else payment.due_date

        # Early discount opportunity
        if payment.allows_early_discount and payment.early_discount_days > 0:
            early_date = due_date - timedelta(days=payment.early_discount_days)
            if early_date >= today and balance - payment.amount >= self.min_balance_threshold:
                savings = payment.amount * (payment.early_discount_percent / 100)
                return early_date, "Early payment discount", savings

        # Balance-based optimization
        if goal == "maximize_cash":
            # Pay as late as allowed
            return due_date, "Maximize cash on hand", 0.0

        elif goal == "minimize_fees":
            # Pay early if possible to avoid any risk
            best_date = max(today, due_date - timedelta(days=3))
            return best_date, "Early payment to avoid late fees", 0.0

        # Balanced approach - pay on due date
        return due_date, "Standard payment on due date", 0.0

    def _find_affordable_date(
        self,
        payment: PaymentItem,
        current_balance: float,
        inflows: List[Dict],
        today: datetime.date,
    ) -> datetime.date:
        """Find the earliest date we can afford this payment."""
        running_balance = current_balance
        check_date = today

        # Look up to 30 days ahead
        for _ in range(30):
            # Add any inflows on this date
            for inflow in inflows:
                inflow_date = datetime.fromisoformat(inflow["date"]).date() if isinstance(inflow["date"], str) else inflow["date"]
                if inflow_date == check_date:
                    running_balance += inflow.get("amount", 0)

            # Check if we can afford it
            if running_balance - payment.amount >= self.min_balance_threshold:
                return check_date

            check_date += timedelta(days=1)

        # Fall back to 30 days from now
        return today + timedelta(days=30)

    def _generate_recommendations(self, scheduled: List[ScheduledPayment], ending_balance: float) -> List[str]:
        """Generate recommendations based on the schedule."""
        recommendations = []

        delayed_count = sum(1 for s in scheduled if s.scheduled_date > s.original_due_date)
        if delayed_count > 0:
            recommendations.append(f"{delayed_count} payments scheduled after due date - consider accelerating collections")

        total_savings = sum(s.savings for s in scheduled)
        if total_savings > 0:
            recommendations.append(f"Early payment discounts could save ${total_savings:,.2f}")

        if ending_balance < self.min_balance_threshold * 2:
            recommendations.append("Cash balance will be low - consider delaying non-critical payments")

        return recommendations


# Global optimizer instance
payment_optimizer = PaymentOptimizer()
