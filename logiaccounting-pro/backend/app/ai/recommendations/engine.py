"""
Recommendations Engine
Generates actionable recommendations based on business data
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from uuid import uuid4
import logging

from app.ai.base import Recommendation

logger = logging.getLogger(__name__)


class RecommendationType:
    """Types of recommendations."""
    INVOICE_REMINDER = "invoice_reminder"
    PAYMENT_SCHEDULE = "payment_schedule"
    CASH_FLOW = "cash_flow"
    EXPENSE_OPTIMIZATION = "expense_optimization"
    CUSTOMER_RISK = "customer_risk"
    PROJECT_HEALTH = "project_health"
    PRICING = "pricing"


class RecommendationEngine:
    """Generates business recommendations."""

    def __init__(self):
        self._generated: Dict[str, List[Recommendation]] = {}

    async def generate_recommendations(
        self,
        customer_id: str,
        context: Dict,
    ) -> List[Recommendation]:
        """Generate recommendations based on context."""
        recommendations = []

        # Invoice reminders
        if context.get("overdue_invoices"):
            recommendations.extend(
                self._generate_invoice_reminders(context["overdue_invoices"])
            )

        # Cash flow recommendations
        if context.get("cashflow_forecast"):
            recommendations.extend(
                self._generate_cashflow_recommendations(context["cashflow_forecast"])
            )

        # Customer risk recommendations
        if context.get("customers"):
            recommendations.extend(
                self._generate_customer_recommendations(context["customers"])
            )

        # Project health recommendations
        if context.get("projects"):
            recommendations.extend(
                self._generate_project_recommendations(context["projects"])
            )

        # Sort by priority
        recommendations.sort(key=lambda r: r.priority, reverse=True)

        # Store for customer
        self._generated[customer_id] = recommendations

        return recommendations[:10]  # Top 10

    def _generate_invoice_reminders(self, invoices: List[Dict]) -> List[Recommendation]:
        """Generate invoice reminder recommendations."""
        recommendations = []

        for invoice in invoices:
            days_overdue = invoice.get("days_overdue", 0)
            amount = invoice.get("amount", 0)
            customer = invoice.get("customer_name", "Customer")

            if days_overdue > 30:
                priority = 9
                title = f"Escalate Collection: {customer}"
                description = f"Invoice ${amount:,.2f} is {days_overdue} days overdue. Consider escalating to collections or applying late fees."
            elif days_overdue > 14:
                priority = 7
                title = f"Send Final Reminder: {customer}"
                description = f"Invoice ${amount:,.2f} is {days_overdue} days overdue. Send a final payment reminder."
            else:
                priority = 5
                title = f"Send Payment Reminder: {customer}"
                description = f"Invoice ${amount:,.2f} is {days_overdue} days overdue. A friendly reminder may help."

            recommendations.append(Recommendation(
                id=f"rec_{uuid4().hex[:12]}",
                type=RecommendationType.INVOICE_REMINDER,
                title=title,
                description=description,
                priority=priority,
                confidence=0.9,
                potential_impact=f"Recover ${amount:,.2f}",
                actions=[
                    {"action": "send_reminder", "invoice_id": invoice.get("id")},
                    {"action": "view_invoice", "invoice_id": invoice.get("id")},
                ],
            ))

        return recommendations

    def _generate_cashflow_recommendations(self, forecast: Dict) -> List[Recommendation]:
        """Generate cash flow recommendations."""
        recommendations = []

        alerts = forecast.get("alerts", [])
        for alert in alerts:
            if alert.get("type") == "low_balance":
                recommendations.append(Recommendation(
                    id=f"rec_{uuid4().hex[:12]}",
                    type=RecommendationType.CASH_FLOW,
                    title="Prepare for Low Cash Period",
                    description=f"Cash balance may drop on {alert.get('date')}. Consider accelerating collections or delaying non-essential payments.",
                    priority=8,
                    confidence=0.8,
                    actions=[
                        {"action": "view_cashflow"},
                        {"action": "view_pending_invoices"},
                    ],
                ))

        summary = forecast.get("summary", {})
        if summary.get("trend") == "decreasing":
            recommendations.append(Recommendation(
                id=f"rec_{uuid4().hex[:12]}",
                type=RecommendationType.CASH_FLOW,
                title="Address Declining Cash Flow",
                description="Your cash flow trend is declining. Review revenue sources and expense patterns.",
                priority=7,
                confidence=0.75,
                actions=[
                    {"action": "view_cashflow"},
                    {"action": "view_expenses"},
                ],
            ))

        return recommendations

    def _generate_customer_recommendations(self, customers: List[Dict]) -> List[Recommendation]:
        """Generate customer-related recommendations."""
        recommendations = []

        for customer in customers:
            payment_days = customer.get("avg_payment_days", 30)
            outstanding = customer.get("outstanding_balance", 0)

            # Slow payers
            if payment_days > 45 and outstanding > 5000:
                recommendations.append(Recommendation(
                    id=f"rec_{uuid4().hex[:12]}",
                    type=RecommendationType.CUSTOMER_RISK,
                    title=f"Review Terms: {customer.get('name')}",
                    description=f"Customer averages {payment_days} days to pay with ${outstanding:,.2f} outstanding. Consider adjusting payment terms.",
                    priority=6,
                    confidence=0.85,
                    actions=[
                        {"action": "view_customer", "customer_id": customer.get("id")},
                    ],
                ))

        return recommendations

    def _generate_project_recommendations(self, projects: List[Dict]) -> List[Recommendation]:
        """Generate project recommendations."""
        recommendations = []

        for project in projects:
            margin = project.get("margin", 0)
            status = project.get("status", "")

            # Low margin projects
            if status == "active" and margin < 0.2:
                recommendations.append(Recommendation(
                    id=f"rec_{uuid4().hex[:12]}",
                    type=RecommendationType.PROJECT_HEALTH,
                    title=f"Low Margin: {project.get('name')}",
                    description=f"Project margin is only {margin:.1%}. Review costs and scope to improve profitability.",
                    priority=6,
                    confidence=0.9,
                    potential_impact="Improve project profitability",
                    actions=[
                        {"action": "view_project", "project_id": project.get("id")},
                    ],
                ))

            # Budget overrun
            if project.get("costs", 0) > project.get("budget", float('inf')) * 0.9:
                recommendations.append(Recommendation(
                    id=f"rec_{uuid4().hex[:12]}",
                    type=RecommendationType.PROJECT_HEALTH,
                    title=f"Budget Alert: {project.get('name')}",
                    description="Project is approaching or exceeding budget. Review remaining tasks and costs.",
                    priority=7,
                    confidence=0.95,
                    actions=[
                        {"action": "view_project", "project_id": project.get("id")},
                    ],
                ))

        return recommendations

    def get_customer_recommendations(self, customer_id: str) -> List[Recommendation]:
        """Get stored recommendations for customer."""
        recommendations = self._generated.get(customer_id, [])
        return [r for r in recommendations if r.expires_at is None or r.expires_at > datetime.utcnow()]


# Global engine instance
recommendation_engine = RecommendationEngine()
