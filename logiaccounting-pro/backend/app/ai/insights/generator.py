"""
Insights Generator
Generates business insights from data
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class InsightType(str, Enum):
    """Types of insights."""
    TREND = "trend"
    ALERT = "alert"
    OPPORTUNITY = "opportunity"
    BENCHMARK = "benchmark"
    PREDICTION = "prediction"


@dataclass
class Insight:
    """Generated insight."""
    id: str = field(default_factory=lambda: f"ins_{uuid4().hex[:8]}")
    type: InsightType = InsightType.TREND
    title: str = ""
    description: str = ""
    metric: str = ""
    current_value: float = 0.0
    comparison_value: float = 0.0
    change_percent: float = 0.0
    direction: str = ""  # up, down, stable
    significance: str = "medium"  # low, medium, high
    actions: List[Dict] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "metric": self.metric,
            "current_value": self.current_value,
            "comparison_value": self.comparison_value,
            "change_percent": self.change_percent,
            "direction": self.direction,
            "significance": self.significance,
            "actions": self.actions,
            "generated_at": self.generated_at.isoformat(),
        }


class InsightsGenerator:
    """Generates business insights from financial data."""

    def __init__(self):
        pass

    def generate_insights(self, data: Dict) -> List[Insight]:
        """Generate insights from business data."""
        insights = []

        # Revenue insights
        if "revenue" in data:
            insights.extend(self._analyze_revenue(data["revenue"]))

        # Expense insights
        if "expenses" in data:
            insights.extend(self._analyze_expenses(data["expenses"]))

        # Cash flow insights
        if "cashflow" in data:
            insights.extend(self._analyze_cashflow(data["cashflow"]))

        # Customer insights
        if "customers" in data:
            insights.extend(self._analyze_customers(data["customers"]))

        # Sort by significance
        significance_order = {"high": 0, "medium": 1, "low": 2}
        insights.sort(key=lambda i: significance_order.get(i.significance, 1))

        return insights[:10]  # Top 10 insights

    def _analyze_revenue(self, revenue_data: Dict) -> List[Insight]:
        """Analyze revenue data."""
        insights = []

        current = revenue_data.get("current_period", 0)
        previous = revenue_data.get("previous_period", 0)

        if previous > 0:
            change_pct = ((current - previous) / previous) * 100
            direction = "up" if change_pct > 0 else "down" if change_pct < 0 else "stable"

            significance = "high" if abs(change_pct) > 20 else "medium" if abs(change_pct) > 10 else "low"

            insights.append(Insight(
                type=InsightType.TREND,
                title=f"Revenue {'Increased' if direction == 'up' else 'Decreased' if direction == 'down' else 'Stable'}",
                description=f"Revenue is {direction} {abs(change_pct):.1f}% compared to the previous period",
                metric="revenue",
                current_value=current,
                comparison_value=previous,
                change_percent=change_pct,
                direction=direction,
                significance=significance,
                actions=[{"action": "view_revenue_report"}] if abs(change_pct) > 10 else [],
            ))

        return insights

    def _analyze_expenses(self, expense_data: Dict) -> List[Insight]:
        """Analyze expense data."""
        insights = []

        total = expense_data.get("total", 0)
        by_category = expense_data.get("by_category", {})
        previous_total = expense_data.get("previous_total", 0)

        # Overall expense trend
        if previous_total > 0:
            change_pct = ((total - previous_total) / previous_total) * 100

            if change_pct > 15:
                insights.append(Insight(
                    type=InsightType.ALERT,
                    title="Expenses Rising",
                    description=f"Total expenses increased {change_pct:.1f}% - review spending categories",
                    metric="expenses",
                    current_value=total,
                    comparison_value=previous_total,
                    change_percent=change_pct,
                    direction="up",
                    significance="high",
                    actions=[{"action": "view_expense_breakdown"}],
                ))

        # Category analysis
        if by_category:
            largest_category = max(by_category.items(), key=lambda x: x[1])
            if total > 0 and largest_category[1] / total > 0.4:
                insights.append(Insight(
                    type=InsightType.OPPORTUNITY,
                    title=f"High {largest_category[0].replace('_', ' ').title()} Spending",
                    description=f"{largest_category[0].replace('_', ' ').title()} represents {(largest_category[1]/total)*100:.0f}% of expenses",
                    metric=f"expense_{largest_category[0]}",
                    current_value=largest_category[1],
                    significance="medium",
                    actions=[{"action": "review_category", "category": largest_category[0]}],
                ))

        return insights

    def _analyze_cashflow(self, cashflow_data: Dict) -> List[Insight]:
        """Analyze cash flow data."""
        insights = []

        balance = cashflow_data.get("current_balance", 0)
        forecast_30 = cashflow_data.get("forecast_30_days", balance)
        runway_days = cashflow_data.get("runway_days", 0)

        # Low balance warning
        if balance < 10000:
            insights.append(Insight(
                type=InsightType.ALERT,
                title="Low Cash Balance",
                description=f"Current balance of ${balance:,.2f} may be insufficient for upcoming obligations",
                metric="cash_balance",
                current_value=balance,
                significance="high",
                actions=[{"action": "view_cashflow"}, {"action": "accelerate_collections"}],
            ))

        # Declining forecast
        if forecast_30 < balance * 0.8:
            change_pct = ((forecast_30 - balance) / balance) * 100
            insights.append(Insight(
                type=InsightType.PREDICTION,
                title="Cash Flow Declining",
                description=f"Cash is projected to decrease {abs(change_pct):.0f}% over the next 30 days",
                metric="cash_forecast",
                current_value=forecast_30,
                comparison_value=balance,
                change_percent=change_pct,
                direction="down",
                significance="high",
                actions=[{"action": "view_cashflow_forecast"}],
            ))

        return insights

    def _analyze_customers(self, customer_data: Dict) -> List[Insight]:
        """Analyze customer data."""
        insights = []

        total_ar = customer_data.get("total_receivables", 0)
        overdue = customer_data.get("overdue_amount", 0)
        overdue_count = customer_data.get("overdue_count", 0)

        # Overdue receivables
        if overdue > 0 and total_ar > 0:
            overdue_pct = (overdue / total_ar) * 100
            if overdue_pct > 20:
                insights.append(Insight(
                    type=InsightType.ALERT,
                    title="High Overdue Receivables",
                    description=f"${overdue:,.2f} ({overdue_pct:.0f}% of AR) is overdue across {overdue_count} invoices",
                    metric="overdue_ar",
                    current_value=overdue,
                    comparison_value=total_ar,
                    change_percent=overdue_pct,
                    significance="high",
                    actions=[{"action": "view_overdue_invoices"}, {"action": "send_reminders"}],
                ))

        return insights


# Global generator instance
insights_generator = InsightsGenerator()
