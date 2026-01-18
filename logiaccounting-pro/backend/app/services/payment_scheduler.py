"""
Intelligent Payment Scheduler Service
Optimizes payment dates to maximize discounts and minimize penalties
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

# Optional optimization imports
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from scipy.optimize import linear_sum_assignment, minimize
    SCIPY_OPTIMIZE_AVAILABLE = True
except ImportError:
    SCIPY_OPTIMIZE_AVAILABLE = False


@dataclass
class PaymentRecommendation:
    """Recommended payment action"""
    payment_id: str
    reference: str
    amount: float
    original_due_date: str
    recommended_date: str
    action: str  # pay_now, pay_early, pay_on_time, delay_if_possible
    priority: int  # 1 = highest priority
    reason: str
    potential_savings: float
    penalty_risk: float
    discount_available: float


@dataclass
class PaymentSchedule:
    """Optimized payment schedule"""
    generated_at: str
    total_pending: float
    total_potential_savings: float
    total_penalty_risk: float
    cash_required_7_days: float
    cash_required_30_days: float
    recommendations: List[Dict]
    daily_schedule: List[Dict]
    optimization_notes: List[str]

    def to_dict(self) -> Dict:
        return asdict(self)


class PaymentScheduler:
    """
    Intelligent Payment Optimization Engine

    Features:
    - Early payment discount optimization
    - Late payment penalty avoidance
    - Cash flow balancing
    - Priority-based scheduling
    - Vendor relationship consideration
    """

    # Default discount/penalty parameters
    EARLY_PAYMENT_DISCOUNT_RATE = 0.02  # 2% discount for early payment
    EARLY_PAYMENT_DAYS = 10  # Days before due for discount
    LATE_PENALTY_RATE = 0.015  # 1.5% penalty per month late
    GRACE_PERIOD_DAYS = 3  # Days after due before penalty

    def __init__(self, db):
        self.db = db

    def optimize_schedule(
        self,
        available_cash: Optional[float] = None,
        optimize_for: str = "balanced"  # balanced, minimize_cost, maximize_discount, prioritize_vendors
    ) -> PaymentSchedule:
        """
        Generate optimized payment schedule

        Args:
            available_cash: Current available cash (if None, assumes unlimited)
            optimize_for: Optimization strategy
                - balanced: Balance between discounts and cash preservation
                - minimize_cost: Minimize total cost (penalties + missed discounts)
                - maximize_discount: Capture all possible discounts
                - prioritize_vendors: Pay strategic vendors first

        Returns:
            PaymentSchedule with optimized recommendations
        """
        payments = self.db.payments.find_all()
        pending = [p for p in payments if p.get("status") in ["pending", "overdue"]]

        if not pending:
            return PaymentSchedule(
                generated_at=datetime.utcnow().isoformat(),
                total_pending=0,
                total_potential_savings=0,
                total_penalty_risk=0,
                cash_required_7_days=0,
                cash_required_30_days=0,
                recommendations=[],
                daily_schedule=[],
                optimization_notes=["No pending payments"]
            )

        # Calculate current cash if not provided
        if available_cash is None:
            available_cash = self._calculate_available_cash()

        # Generate recommendations for each payment
        recommendations = []
        for payment in pending:
            rec = self._analyze_payment(payment, optimize_for)
            recommendations.append(rec)

        # Sort by priority
        recommendations.sort(key=lambda x: x.priority)

        # Apply cash constraints if limited
        if available_cash < sum(r.amount for r in recommendations):
            recommendations = self._apply_cash_constraints(recommendations, available_cash)

        # Generate daily schedule
        daily_schedule = self._generate_daily_schedule(recommendations)

        # Calculate totals
        total_pending = sum(p.get("amount", 0) for p in pending)
        total_savings = sum(r.potential_savings for r in recommendations if r.action in ["pay_now", "pay_early"])
        total_risk = sum(r.penalty_risk for r in recommendations)

        # Cash requirements
        today = datetime.utcnow().date()
        week_end = today + timedelta(days=7)
        month_end = today + timedelta(days=30)

        cash_7_days = sum(
            r.amount for r in recommendations
            if r.recommended_date and datetime.fromisoformat(r.recommended_date).date() <= week_end
        )
        cash_30_days = sum(
            r.amount for r in recommendations
            if r.recommended_date and datetime.fromisoformat(r.recommended_date).date() <= month_end
        )

        # Generate optimization notes
        notes = self._generate_notes(recommendations, optimize_for, available_cash)

        return PaymentSchedule(
            generated_at=datetime.utcnow().isoformat(),
            total_pending=round(total_pending, 2),
            total_potential_savings=round(total_savings, 2),
            total_penalty_risk=round(total_risk, 2),
            cash_required_7_days=round(cash_7_days, 2),
            cash_required_30_days=round(cash_30_days, 2),
            recommendations=[r.__dict__ if hasattr(r, '__dict__') else asdict(r) for r in recommendations],
            daily_schedule=daily_schedule,
            optimization_notes=notes
        )

    def _analyze_payment(self, payment: Dict, optimize_for: str) -> PaymentRecommendation:
        """
        Analyze a single payment and generate recommendation
        """
        today = datetime.utcnow().date()
        amount = payment.get("amount", 0)
        due_date_str = payment.get("due_date", "")[:10]

        try:
            due_date = datetime.fromisoformat(due_date_str).date()
        except (ValueError, TypeError):
            due_date = today + timedelta(days=30)  # Default 30 days if no due date

        days_until_due = (due_date - today).days
        is_overdue = days_until_due < 0

        # Calculate potential discount (early payment)
        discount_eligible = days_until_due > self.EARLY_PAYMENT_DAYS
        discount_amount = amount * self.EARLY_PAYMENT_DISCOUNT_RATE if discount_eligible else 0

        # Calculate penalty risk
        if is_overdue:
            days_overdue = abs(days_until_due)
            penalty_months = max(0, (days_overdue - self.GRACE_PERIOD_DAYS) / 30)
            penalty_risk = amount * self.LATE_PENALTY_RATE * penalty_months
        else:
            penalty_risk = 0

        # Determine action and priority
        if is_overdue:
            action = "pay_now"
            priority = 1
            reason = f"OVERDUE by {abs(days_until_due)} days - pay immediately to avoid further penalties"
            recommended_date = today.isoformat()
        elif days_until_due <= self.GRACE_PERIOD_DAYS:
            action = "pay_now"
            priority = 2
            reason = f"Due in {days_until_due} days - pay now to avoid late penalties"
            recommended_date = today.isoformat()
        elif discount_eligible and optimize_for in ["maximize_discount", "minimize_cost"]:
            action = "pay_early"
            priority = 3
            # Pay early enough to get discount
            early_date = due_date - timedelta(days=self.EARLY_PAYMENT_DAYS)
            recommended_date = max(early_date, today).isoformat()
            reason = f"Pay early for {self.EARLY_PAYMENT_DISCOUNT_RATE*100}% discount (${discount_amount:.2f} savings)"
        elif days_until_due <= 7:
            action = "pay_on_time"
            priority = 4
            recommended_date = (due_date - timedelta(days=1)).isoformat()
            reason = f"Due in {days_until_due} days - schedule payment"
        else:
            action = "delay_if_possible"
            priority = 5
            recommended_date = (due_date - timedelta(days=2)).isoformat()
            reason = f"Not urgent - can delay until closer to due date ({due_date_str})"

        # Adjust priority for strategic vendors
        if optimize_for == "prioritize_vendors":
            supplier_id = payment.get("supplier_id")
            if supplier_id and self._is_strategic_vendor(supplier_id):
                priority = min(priority, 2)
                reason += " [Strategic vendor - prioritized]"

        return PaymentRecommendation(
            payment_id=payment["id"],
            reference=payment.get("reference") or payment.get("description", "N/A")[:50],
            amount=amount,
            original_due_date=due_date_str,
            recommended_date=recommended_date,
            action=action,
            priority=priority,
            reason=reason,
            potential_savings=discount_amount,
            penalty_risk=penalty_risk,
            discount_available=discount_amount
        )

    def _apply_cash_constraints(
        self,
        recommendations: List[PaymentRecommendation],
        available_cash: float
    ) -> List[PaymentRecommendation]:
        """
        Adjust recommendations based on cash constraints
        """
        running_total = 0
        constrained = []

        for rec in recommendations:
            if running_total + rec.amount <= available_cash:
                running_total += rec.amount
                constrained.append(rec)
            else:
                # Can't afford now - delay or partial
                if rec.action in ["pay_now"]:
                    # Must pay overdue - add warning
                    rec.reason += " [INSUFFICIENT FUNDS - prioritize this payment]"
                    constrained.append(rec)
                else:
                    # Delay further
                    rec.action = "delay_if_possible"
                    rec.reason = f"Delayed due to cash constraints (need ${rec.amount:.2f}, available ${available_cash - running_total:.2f})"
                    constrained.append(rec)

        return constrained

    def _generate_daily_schedule(self, recommendations: List[PaymentRecommendation]) -> List[Dict]:
        """
        Generate day-by-day payment schedule
        """
        by_date = defaultdict(list)

        for rec in recommendations:
            if rec.recommended_date:
                by_date[rec.recommended_date].append({
                    "payment_id": rec.payment_id,
                    "reference": rec.reference,
                    "amount": rec.amount,
                    "action": rec.action
                })

        # Sort and format
        schedule = []
        for date in sorted(by_date.keys()):
            payments = by_date[date]
            schedule.append({
                "date": date,
                "payments": payments,
                "total_amount": sum(p["amount"] for p in payments),
                "payment_count": len(payments)
            })

        return schedule

    def _calculate_available_cash(self) -> float:
        """
        Calculate current available cash from transactions
        """
        transactions = self.db.transactions.find_all()
        payments = self.db.payments.find_all()

        income = sum(t.get("amount", 0) for t in transactions if t.get("type") == "income")
        expenses = sum(t.get("amount", 0) for t in transactions if t.get("type") == "expense")

        paid_out = sum(p.get("amount", 0) for p in payments
                      if p.get("type") == "payable" and p.get("status") == "paid")
        received = sum(p.get("amount", 0) for p in payments
                      if p.get("type") == "receivable" and p.get("status") == "paid")

        return income + received - expenses - paid_out

    def _is_strategic_vendor(self, supplier_id: str) -> bool:
        """
        Determine if a vendor is strategic (high transaction volume or value)
        """
        transactions = self.db.transactions.find_all()
        vendor_txs = [t for t in transactions if t.get("supplier_id") == supplier_id]

        if len(vendor_txs) >= 10:  # High frequency
            return True

        total = sum(t.get("amount", 0) for t in vendor_txs)
        if total > 50000:  # High value
            return True

        return False

    def _generate_notes(
        self,
        recommendations: List[PaymentRecommendation],
        strategy: str,
        available_cash: float
    ) -> List[str]:
        """
        Generate optimization notes and warnings
        """
        notes = []

        # Strategy note
        strategy_names = {
            "balanced": "Balanced optimization (cost vs. cash preservation)",
            "minimize_cost": "Minimize total cost",
            "maximize_discount": "Maximize early payment discounts",
            "prioritize_vendors": "Prioritize strategic vendors"
        }
        notes.append(f"Strategy: {strategy_names.get(strategy, strategy)}")

        # Overdue warning
        overdue = [r for r in recommendations if r.action == "pay_now" and "OVERDUE" in r.reason]
        if overdue:
            total_overdue = sum(r.amount for r in overdue)
            notes.append(f"WARNING: {len(overdue)} overdue payment(s) totaling ${total_overdue:,.2f}")

        # Discount opportunities
        discounts = [r for r in recommendations if r.discount_available > 0]
        if discounts:
            total_discount = sum(r.discount_available for r in discounts)
            notes.append(f"Potential early payment savings: ${total_discount:,.2f}")

        # Cash flow note
        total_pending = sum(r.amount for r in recommendations)
        if available_cash < total_pending:
            notes.append(f"Cash constraint: ${available_cash:,.2f} available, ${total_pending:,.2f} pending")

        return notes

    def get_payment_insights(self, payment_id: str) -> Dict:
        """
        Get detailed insights for a specific payment
        """
        payment = self.db.payments.find_by_id(payment_id)
        if not payment:
            return {"error": "Payment not found"}

        rec = self._analyze_payment(payment, "balanced")

        # Historical payment patterns for vendor
        vendor_history = []
        if payment.get("supplier_id"):
            transactions = self.db.transactions.find_all()
            vendor_txs = [t for t in transactions if t.get("supplier_id") == payment["supplier_id"]]
            vendor_history = [{
                "amount": t.get("amount"),
                "date": t.get("date") or t.get("created_at", "")[:10]
            } for t in vendor_txs[-5:]]

        return {
            "payment": payment,
            "recommendation": asdict(rec),
            "vendor_history": vendor_history,
            "optimal_payment_window": {
                "earliest_for_discount": (datetime.fromisoformat(payment.get("due_date", "")[:10]) -
                                         timedelta(days=self.EARLY_PAYMENT_DAYS)).isoformat()
                                         if payment.get("due_date") else None,
                "latest_without_penalty": payment.get("due_date", "")[:10]
            }
        }


# Service instance factory
def create_payment_scheduler(db) -> PaymentScheduler:
    return PaymentScheduler(db)
