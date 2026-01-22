"""
Payment Scheduler
Schedule and manage payment execution
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List

from ...models.payment_recommendation import PaymentRecommendation

logger = logging.getLogger(__name__)


class PaymentScheduler:
    """Schedule and manage payments"""

    async def get_recommendations(
        self,
        tenant_id: str,
        status: str = 'pending',
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get payment recommendations

        Args:
            tenant_id: Tenant ID
            status: Filter by status
            limit: Maximum results

        Returns:
            List of recommendations
        """
        recs = PaymentRecommendation.get_by_tenant(tenant_id, status, limit)
        return [rec.to_dict() for rec in recs]

    async def get_recommendation(
        self,
        tenant_id: str,
        recommendation_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get specific recommendation"""
        rec = PaymentRecommendation.get_by_id(recommendation_id, tenant_id)
        return rec.to_dict() if rec else None

    async def accept_recommendation(
        self,
        tenant_id: str,
        recommendation_id: str,
        user_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Accept a payment recommendation

        Args:
            tenant_id: Tenant ID
            recommendation_id: Recommendation ID
            user_id: User accepting

        Returns:
            Updated recommendation or None
        """
        rec = PaymentRecommendation.get_by_id(recommendation_id, tenant_id)
        if not rec:
            return None

        rec.status = 'accepted'
        rec.actioned_at = datetime.utcnow()
        rec.actioned_by = user_id
        rec.action_result = {'action': 'accepted', 'timestamp': datetime.utcnow().isoformat()}
        rec.save()

        return rec.to_dict()

    async def reject_recommendation(
        self,
        tenant_id: str,
        recommendation_id: str,
        user_id: str,
        reason: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Reject a payment recommendation

        Args:
            tenant_id: Tenant ID
            recommendation_id: Recommendation ID
            user_id: User rejecting
            reason: Rejection reason

        Returns:
            Updated recommendation or None
        """
        rec = PaymentRecommendation.get_by_id(recommendation_id, tenant_id)
        if not rec:
            return None

        rec.status = 'rejected'
        rec.actioned_at = datetime.utcnow()
        rec.actioned_by = user_id
        rec.action_result = {
            'action': 'rejected',
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat(),
        }
        rec.save()

        return rec.to_dict()

    async def get_payment_calendar(
        self,
        tenant_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Get payment calendar with scheduled payments

        Args:
            tenant_id: Tenant ID
            start_date: Calendar start date
            end_date: Calendar end date

        Returns:
            Calendar data with payments by date
        """
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = start_date + timedelta(days=30)

        # Get accepted recommendations
        recs = PaymentRecommendation.get_by_tenant(tenant_id, status='accepted', limit=100)

        # Build calendar
        calendar = {}
        current = start_date
        while current <= end_date:
            calendar[current.isoformat()] = {
                'date': current.isoformat(),
                'payments': [],
                'total_amount': 0,
            }
            current += timedelta(days=1)

        # Add payments to calendar
        for rec in recs:
            payment_date = rec.suggested_payment_date
            if payment_date and start_date <= payment_date <= end_date:
                date_key = payment_date.isoformat()
                if date_key in calendar:
                    payment_info = {
                        'recommendation_id': rec.id,
                        'title': rec.title,
                        'amount': abs(rec.cash_flow_impact) if rec.cash_flow_impact else 0,
                        'type': rec.recommendation_type,
                        'invoice_ids': rec.invoice_ids,
                    }
                    calendar[date_key]['payments'].append(payment_info)
                    calendar[date_key]['total_amount'] += payment_info['amount']

        return {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days': list(calendar.values()),
            'total_scheduled': sum(d['total_amount'] for d in calendar.values()),
        }

    async def get_savings_summary(
        self,
        tenant_id: str,
    ) -> Dict[str, Any]:
        """
        Get summary of potential and realized savings

        Args:
            tenant_id: Tenant ID

        Returns:
            Savings summary
        """
        all_recs = PaymentRecommendation.get_by_tenant(tenant_id, status='all', limit=1000)

        pending_savings = 0
        realized_savings = 0
        pending_count = 0
        accepted_count = 0

        for rec in all_recs:
            savings = rec.potential_savings or 0
            if rec.status == 'pending':
                pending_savings += savings
                pending_count += 1
            elif rec.status == 'accepted':
                realized_savings += savings
                accepted_count += 1

        return {
            'pending_savings': pending_savings,
            'realized_savings': realized_savings,
            'pending_recommendations': pending_count,
            'accepted_recommendations': accepted_count,
            'total_recommendations': len(all_recs),
        }
