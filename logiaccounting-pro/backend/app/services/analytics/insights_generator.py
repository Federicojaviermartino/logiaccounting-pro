"""
Insights Generator Service
AI-powered business insights and recommendations
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict

from app.utils.datetime_utils import utc_now


class InsightsGenerator:
    """
    AI Insights Engine

    Generates:
    - Weekly business summaries
    - Trend insights
    - Risk alerts
    - Opportunity identification
    - Action recommendations
    """

    def __init__(self, db):
        self.db = db

    def get_insights(self) -> Dict[str, Any]:
        """Generate comprehensive business insights"""
        transactions = self.db.transactions.find_all()
        payments = self.db.payments.find_all()
        materials = self.db.materials.find_all()
        projects = self.db.projects.find_all()

        return {
            'generated_at': utc_now().isoformat(),
            'summary': self._generate_summary(transactions),
            'key_insights': self._generate_key_insights(transactions, payments, materials, projects),
            'opportunities': self._identify_opportunities(transactions, payments),
            'risks': self._identify_risks(transactions, payments, materials),
            'recommendations': self._generate_recommendations(transactions, payments, materials)
        }

    def get_weekly_summary(self) -> Dict[str, Any]:
        """Generate weekly business summary"""
        transactions = self.db.transactions.find_all()
        payments = self.db.payments.find_all()

        week_ago = utc_now() - timedelta(days=7)
        two_weeks_ago = utc_now() - timedelta(days=14)

        this_week = self._get_period_metrics(transactions, week_ago, utc_now())
        last_week = self._get_period_metrics(transactions, two_weeks_ago, week_ago)

        revenue_change = self._calc_change(this_week['revenue'], last_week['revenue'])
        expense_change = self._calc_change(this_week['expenses'], last_week['expenses'])

        upcoming = [
            p for p in payments
            if p.get('status') == 'pending' and self._is_due_within_days(p.get('due_date'), 7)
        ]

        return {
            'period': 'Last 7 Days',
            'generated_at': utc_now().isoformat(),
            'metrics': {
                'revenue': round(this_week['revenue'], 2),
                'expenses': round(this_week['expenses'], 2),
                'profit': round(this_week['profit'], 2),
                'transactions': this_week['count']
            },
            'changes': {
                'revenue': revenue_change,
                'expenses': expense_change
            },
            'upcoming_payments': {
                'count': len(upcoming),
                'total': round(sum(p.get('amount', 0) for p in upcoming), 2)
            },
            'highlights': self._generate_highlights(this_week, last_week, revenue_change, expense_change)
        }

    def _generate_summary(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Generate overall business summary"""
        now = utc_now()
        thirty_days = timedelta(days=30)

        current = self._get_period_metrics(transactions, now - thirty_days, now)
        previous = self._get_period_metrics(transactions, now - thirty_days * 2, now - thirty_days)

        profit_trend = 'up' if current['profit'] > previous['profit'] else 'down'
        margin_current = (current['profit'] / current['revenue'] * 100) if current['revenue'] > 0 else 0

        if margin_current >= 15 and profit_trend == 'up':
            status = 'excellent'
            message = 'Business is performing exceptionally well with growing profits.'
        elif margin_current >= 10:
            status = 'good'
            message = 'Healthy profit margins. Continue current strategies.'
        elif margin_current >= 5:
            status = 'fair'
            message = 'Moderate performance. Consider cost optimization.'
        elif margin_current >= 0:
            status = 'concerning'
            message = 'Low margins. Review pricing and expenses.'
        else:
            status = 'critical'
            message = 'Operating at a loss. Immediate action required.'

        return {
            'status': status,
            'message': message,
            'period_profit': round(current['profit'], 2),
            'profit_margin': round(margin_current, 1),
            'profit_trend': profit_trend
        }

    def _generate_key_insights(self, transactions: List[Dict], payments: List[Dict], materials: List[Dict], projects: List[Dict]) -> List[Dict]:
        """Generate key business insights"""
        insights = []

        monthly = self._get_monthly_totals(transactions, 'income', 3)
        if len(monthly) >= 2:
            trend = 'increasing' if monthly[-1] > monthly[-2] else 'decreasing'
            change = abs((monthly[-1] - monthly[-2]) / monthly[-2] * 100) if monthly[-2] > 0 else 0
            insights.append({
                'type': 'revenue',
                'icon': '📈' if trend == 'increasing' else '📉',
                'title': f'Revenue is {trend}',
                'detail': f'{change:.1f}% change from previous month'
            })

        pending_receivables = sum(
            p.get('amount', 0) for p in payments
            if p.get('type') == 'receivable' and p.get('status') == 'pending'
        )
        if pending_receivables > 0:
            insights.append({
                'type': 'receivables',
                'icon': '💰',
                'title': 'Pending Receivables',
                'detail': f'${pending_receivables:,.2f} awaiting collection'
            })

        low_stock = [m for m in materials if m.get('current_stock', 0) <= m.get('min_stock', 10)]
        if low_stock:
            insights.append({
                'type': 'inventory',
                'icon': '📦',
                'title': f'{len(low_stock)} items low on stock',
                'detail': 'Review reorder points and place orders'
            })

        active_projects = [p for p in projects if p.get('status') == 'active']
        if active_projects:
            insights.append({
                'type': 'projects',
                'icon': '🎯',
                'title': f'{len(active_projects)} active projects',
                'detail': 'Monitor progress and budget utilization'
            })

        return insights[:5]

    def _identify_opportunities(self, transactions: List[Dict], payments: List[Dict]) -> List[Dict]:
        """Identify business opportunities"""
        opportunities = []

        customer_revenue = defaultdict(float)
        for tx in transactions:
            if tx.get('type') == 'income':
                customer_id = tx.get('client_id') or tx.get('customer_id')
                if customer_id:
                    customer_revenue[customer_id] += tx.get('amount', 0)

        if customer_revenue:
            top_customers = sorted(customer_revenue.items(), key=lambda x: x[1], reverse=True)[:3]
            opportunities.append({
                'type': 'upsell',
                'icon': '🚀',
                'title': 'Top Customer Opportunity',
                'detail': f'Your top {len(top_customers)} customers account for significant revenue. Consider upselling.',
                'potential_impact': 'High'
            })

        pending_payables = sum(
            p.get('amount', 0) for p in payments
            if p.get('type') == 'payable' and p.get('status') == 'pending'
        )
        if pending_payables > 5000:
            opportunities.append({
                'type': 'discount',
                'icon': '💵',
                'title': 'Early Payment Discounts',
                'detail': f'${pending_payables:,.2f} in pending payables. Negotiate 2% early payment discounts.',
                'potential_impact': f'Save ${pending_payables * 0.02:,.2f}'
            })

        return opportunities

    def _identify_risks(self, transactions: List[Dict], payments: List[Dict], materials: List[Dict]) -> List[Dict]:
        """Identify business risks"""
        risks = []

        overdue = [
            p for p in payments
            if p.get('type') == 'receivable' and p.get('status') == 'pending' and self._is_overdue(p.get('due_date'))
        ]
        if overdue:
            overdue_amount = sum(p.get('amount', 0) for p in overdue)
            risks.append({
                'type': 'receivables',
                'severity': 'high' if overdue_amount > 10000 else 'medium',
                'icon': '⚠️',
                'title': f'{len(overdue)} Overdue Invoices',
                'detail': f'${overdue_amount:,.2f} overdue. Risk of bad debt.',
                'action': 'Follow up immediately with collection efforts'
            })

        critical_stock = [
            m for m in materials
            if m.get('current_stock', 0) <= m.get('min_stock', 10) * 0.5
        ]
        if critical_stock:
            risks.append({
                'type': 'inventory',
                'severity': 'high',
                'icon': '🔴',
                'title': f'{len(critical_stock)} Items Critical Stock',
                'detail': 'Items below 50% of minimum stock level',
                'action': 'Place emergency orders'
            })

        current = self._get_period_metrics(transactions, utc_now() - timedelta(days=30), utc_now())
        if current['profit'] < 0:
            risks.append({
                'type': 'cashflow',
                'severity': 'critical',
                'icon': '💸',
                'title': 'Negative Cash Flow',
                'detail': f'${abs(current["profit"]):,.2f} loss this month',
                'action': 'Review expenses and increase revenue immediately'
            })

        return risks

    def _generate_recommendations(self, transactions: List[Dict], payments: List[Dict], materials: List[Dict]) -> List[Dict]:
        """Generate actionable recommendations"""
        recommendations = []

        current = self._get_period_metrics(transactions, utc_now() - timedelta(days=30), utc_now())
        margin = (current['profit'] / current['revenue'] * 100) if current['revenue'] > 0 else 0

        if margin < 10:
            recommendations.append({
                'priority': 'high',
                'category': 'profitability',
                'title': 'Improve Profit Margins',
                'actions': [
                    'Review pricing strategy',
                    'Identify and cut unnecessary expenses',
                    'Negotiate better supplier terms'
                ]
            })

        pending_receivables = sum(
            p.get('amount', 0) for p in payments
            if p.get('type') == 'receivable' and p.get('status') == 'pending'
        )
        if pending_receivables > current['revenue'] * 0.3:
            recommendations.append({
                'priority': 'high',
                'category': 'collections',
                'title': 'Accelerate Collections',
                'actions': [
                    'Send payment reminders',
                    'Offer early payment discounts',
                    'Review credit terms'
                ]
            })

        low_stock = [m for m in materials if m.get('current_stock', 0) <= m.get('min_stock', 10)]
        if low_stock:
            recommendations.append({
                'priority': 'medium',
                'category': 'inventory',
                'title': 'Optimize Inventory',
                'actions': [
                    f'Reorder {len(low_stock)} low stock items',
                    'Review reorder points',
                    'Consider safety stock adjustments'
                ]
            })

        return recommendations[:5]

    def _get_period_metrics(self, transactions: List[Dict], start: datetime, end: datetime) -> Dict[str, float]:
        """Get metrics for a specific period"""
        revenue = expenses = count = 0

        for tx in transactions:
            date_str = tx.get('date') or tx.get('created_at', '')[:10]
            try:
                tx_date = datetime.fromisoformat(date_str.replace('Z', ''))
            except (ValueError, AttributeError):
                continue

            if start <= tx_date <= end:
                count += 1
                if tx.get('type') == 'income':
                    revenue += tx.get('amount', 0)
                else:
                    expenses += tx.get('amount', 0)

        return {'revenue': revenue, 'expenses': expenses, 'profit': revenue - expenses, 'count': count}

    def _get_monthly_totals(self, transactions: List[Dict], tx_type: str, months: int) -> List[float]:
        """Get monthly totals for last N months"""
        monthly = defaultdict(float)
        cutoff = utc_now() - timedelta(days=months * 31)

        for tx in transactions:
            if tx.get('type') != tx_type:
                continue

            date_str = tx.get('date') or tx.get('created_at', '')[:10]
            try:
                tx_date = datetime.fromisoformat(date_str.replace('Z', ''))
            except (ValueError, AttributeError):
                continue

            if tx_date >= cutoff:
                month_key = tx_date.strftime('%Y-%m')
                monthly[month_key] += tx.get('amount', 0)

        return [monthly[k] for k in sorted(monthly.keys())]

    def _calc_change(self, current: float, previous: float) -> Dict[str, Any]:
        """Calculate percentage change"""
        if previous > 0:
            percent = ((current - previous) / previous) * 100
        else:
            percent = 100 if current > 0 else 0

        return {
            'amount': round(current - previous, 2),
            'percent': round(percent, 1),
            'direction': 'up' if percent > 0 else ('down' if percent < 0 else 'stable')
        }

    def _is_due_within_days(self, due_date: str, days: int) -> bool:
        """Check if payment is due within N days"""
        if not due_date:
            return False

        try:
            due = datetime.fromisoformat(due_date[:10])
            return utc_now() <= due <= utc_now() + timedelta(days=days)
        except (ValueError, AttributeError):
            return False

    def _is_overdue(self, due_date: str) -> bool:
        """Check if payment is overdue"""
        if not due_date:
            return False

        try:
            due = datetime.fromisoformat(due_date[:10])
            return utc_now() > due
        except (ValueError, AttributeError):
            return False

    def _generate_highlights(self, current: Dict, previous: Dict, rev_change: Dict, exp_change: Dict) -> List[str]:
        """Generate weekly highlights"""
        highlights = []

        if rev_change['percent'] > 10:
            highlights.append(f"Revenue up {rev_change['percent']:.1f}% from last week!")
        elif rev_change['percent'] < -10:
            highlights.append(f"Revenue down {abs(rev_change['percent']):.1f}% from last week")

        if exp_change['percent'] < -5:
            highlights.append(f"Expenses reduced by {abs(exp_change['percent']):.1f}%")
        elif exp_change['percent'] > 15:
            highlights.append(f"Expenses increased {exp_change['percent']:.1f}% - review spending")

        if current['profit'] > 0 and previous['profit'] <= 0:
            highlights.append("Returned to profitability this week!")

        return highlights[:3]
