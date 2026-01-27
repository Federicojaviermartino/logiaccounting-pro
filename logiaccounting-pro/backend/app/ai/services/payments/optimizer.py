"""
Payment Optimizer
AI-powered payment optimization recommendations
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from ...config import get_ai_config
from ...models.payment_recommendation import PaymentRecommendation

logger = logging.getLogger(__name__)


@dataclass
class Invoice:
    """Invoice data for optimization"""
    id: str
    vendor_name: str
    amount: float
    due_date: date
    payment_terms: Optional[str] = None
    early_payment_discount: Optional[float] = None
    discount_deadline: Optional[date] = None
    relationship_priority: str = 'normal'


class PaymentOptimizer:
    """Optimize payment timing and priorities"""

    def __init__(self):
        self.config = get_ai_config()

    def analyze_invoices(
        self,
        tenant_id: str,
        invoices: List[Dict[str, Any]],
        current_balance: float,
        expected_inflows: List[Dict[str, Any]] = None,
    ) -> List[PaymentRecommendation]:
        """
        Analyze invoices and generate payment recommendations

        Args:
            tenant_id: Tenant ID
            invoices: List of invoice data
            current_balance: Current cash balance
            expected_inflows: Expected incoming payments

        Returns:
            List of PaymentRecommendation
        """
        # Parse invoices
        parsed_invoices = [self._parse_invoice(inv) for inv in invoices]

        recommendations = []

        # Check for early payment discounts
        discount_recs = self._find_discount_opportunities(
            tenant_id, parsed_invoices, current_balance
        )
        recommendations.extend(discount_recs)

        # Check for batch payment opportunities
        batch_recs = self._find_batch_opportunities(tenant_id, parsed_invoices)
        recommendations.extend(batch_recs)

        # Check for delay opportunities (cash flow management)
        delay_recs = self._find_delay_opportunities(
            tenant_id, parsed_invoices, current_balance, expected_inflows or []
        )
        recommendations.extend(delay_recs)

        # Prioritize critical vendors
        priority_recs = self._identify_priority_payments(tenant_id, parsed_invoices)
        recommendations.extend(priority_recs)

        # Save all recommendations
        for rec in recommendations:
            rec.save()

        return recommendations

    def _parse_invoice(self, data: Dict[str, Any]) -> Invoice:
        """Parse invoice data into Invoice object"""
        due_date = data.get('due_date')
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date).date()

        discount_deadline = data.get('discount_deadline')
        if isinstance(discount_deadline, str):
            discount_deadline = datetime.fromisoformat(discount_deadline).date()

        return Invoice(
            id=data.get('id', ''),
            vendor_name=data.get('vendor_name', 'Unknown'),
            amount=float(data.get('amount', 0)),
            due_date=due_date or date.today(),
            payment_terms=data.get('payment_terms'),
            early_payment_discount=data.get('early_payment_discount'),
            discount_deadline=discount_deadline,
            relationship_priority=data.get('relationship_priority', 'normal'),
        )

    def _find_discount_opportunities(
        self,
        tenant_id: str,
        invoices: List[Invoice],
        current_balance: float,
    ) -> List[PaymentRecommendation]:
        """Find early payment discount opportunities"""
        recommendations = []
        today = date.today()

        for inv in invoices:
            if not inv.early_payment_discount or not inv.discount_deadline:
                continue

            if inv.discount_deadline < today:
                continue  # Discount deadline passed

            days_until_deadline = (inv.discount_deadline - today).days
            if days_until_deadline > 10:
                continue  # Too far out

            discount_amount = inv.amount * inv.early_payment_discount
            discounted_total = inv.amount - discount_amount

            if discounted_total > current_balance:
                continue  # Can't afford

            # Calculate annualized return
            days_early = (inv.due_date - inv.discount_deadline).days
            if days_early > 0:
                annualized_return = (inv.early_payment_discount / days_early) * 365
            else:
                annualized_return = inv.early_payment_discount * 12

            if annualized_return > 0.10:  # More than 10% annualized return
                rec = PaymentRecommendation(
                    tenant_id=tenant_id,
                    recommendation_type='early_discount',
                    invoice_ids=[inv.id],
                    title=f'Early payment discount: {inv.vendor_name}',
                    description=f'Pay by {inv.discount_deadline} to save ${discount_amount:,.2f} ({inv.early_payment_discount * 100:.1f}% discount)',
                    potential_savings=discount_amount,
                    cash_flow_impact=-discounted_total,
                    suggested_payment_date=inv.discount_deadline,
                    original_due_date=inv.due_date,
                    deadline=inv.discount_deadline,
                    priority='high' if annualized_return > 0.20 else 'medium',
                    confidence_score=0.95,
                    reasoning={
                        'discount_rate': inv.early_payment_discount,
                        'annualized_return': annualized_return,
                        'days_until_deadline': days_until_deadline,
                    },
                )
                recommendations.append(rec)

        return recommendations

    def _find_batch_opportunities(
        self,
        tenant_id: str,
        invoices: List[Invoice],
    ) -> List[PaymentRecommendation]:
        """Find opportunities to batch payments to same vendor"""
        recommendations = []

        # Group by vendor
        vendor_invoices = {}
        for inv in invoices:
            vendor_invoices.setdefault(inv.vendor_name, []).append(inv)

        for vendor, vendor_invs in vendor_invoices.items():
            if len(vendor_invs) < 2:
                continue

            # Find invoices due within same week
            today = date.today()
            week_end = today + timedelta(days=7)

            same_week = [
                inv for inv in vendor_invs
                if today <= inv.due_date <= week_end
            ]

            if len(same_week) >= 2:
                total_amount = sum(inv.amount for inv in same_week)
                earliest_due = min(inv.due_date for inv in same_week)

                rec = PaymentRecommendation(
                    tenant_id=tenant_id,
                    recommendation_type='batch_payment',
                    invoice_ids=[inv.id for inv in same_week],
                    title=f'Batch payment opportunity: {vendor}',
                    description=f'Combine {len(same_week)} invoices (${total_amount:,.2f}) for single payment',
                    cash_flow_impact=-total_amount,
                    suggested_payment_date=earliest_due,
                    priority='low',
                    confidence_score=0.85,
                    reasoning={
                        'invoice_count': len(same_week),
                        'total_amount': total_amount,
                        'vendor': vendor,
                    },
                )
                recommendations.append(rec)

        return recommendations

    def _find_delay_opportunities(
        self,
        tenant_id: str,
        invoices: List[Invoice],
        current_balance: float,
        expected_inflows: List[Dict[str, Any]],
    ) -> List[PaymentRecommendation]:
        """Find opportunities to safely delay payments"""
        recommendations = []
        today = date.today()

        # Calculate upcoming inflows
        inflow_by_date = {}
        for inflow in expected_inflows:
            inflow_date = inflow.get('expected_date')
            if isinstance(inflow_date, str):
                inflow_date = datetime.fromisoformat(inflow_date).date()
            if inflow_date:
                inflow_by_date[inflow_date] = inflow_by_date.get(inflow_date, 0) + inflow.get('amount', 0)

        for inv in invoices:
            if inv.relationship_priority == 'critical':
                continue  # Don't delay critical vendors

            days_until_due = (inv.due_date - today).days
            if days_until_due < 3:
                continue  # Too close to due date

            # Check if delaying would help with cash flow
            if current_balance < inv.amount * 2:  # Tight cash situation
                # Look for inflows before due date
                expected_before_due = sum(
                    amount for d, amount in inflow_by_date.items()
                    if today < d <= inv.due_date
                )

                if expected_before_due > 0:
                    # Suggest paying closer to due date
                    suggested_date = inv.due_date - timedelta(days=1)

                    rec = PaymentRecommendation(
                        tenant_id=tenant_id,
                        recommendation_type='delay_payment',
                        invoice_ids=[inv.id],
                        title=f'Timing optimization: {inv.vendor_name}',
                        description=f'Schedule payment for {suggested_date} to align with expected inflow of ${expected_before_due:,.2f}',
                        cash_flow_impact=-inv.amount,
                        suggested_payment_date=suggested_date,
                        original_due_date=inv.due_date,
                        priority='medium',
                        confidence_score=0.75,
                        reasoning={
                            'current_balance': current_balance,
                            'expected_inflow': expected_before_due,
                            'days_until_due': days_until_due,
                        },
                    )
                    recommendations.append(rec)

        return recommendations

    def _identify_priority_payments(
        self,
        tenant_id: str,
        invoices: List[Invoice],
    ) -> List[PaymentRecommendation]:
        """Identify high-priority payments"""
        recommendations = []
        today = date.today()

        for inv in invoices:
            if inv.relationship_priority != 'critical':
                continue

            days_until_due = (inv.due_date - today).days
            if days_until_due > 7:
                continue  # Not urgent yet

            rec = PaymentRecommendation(
                tenant_id=tenant_id,
                recommendation_type='prioritize',
                invoice_ids=[inv.id],
                title=f'Priority payment: {inv.vendor_name}',
                description=f'Critical vendor payment due in {days_until_due} days',
                cash_flow_impact=-inv.amount,
                suggested_payment_date=today if days_until_due <= 2 else inv.due_date - timedelta(days=2),
                original_due_date=inv.due_date,
                priority='high',
                confidence_score=0.90,
                reasoning={
                    'relationship_priority': inv.relationship_priority,
                    'days_until_due': days_until_due,
                },
            )
            recommendations.append(rec)

        return recommendations
