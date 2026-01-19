"""
KPI Calculator Service
Financial health scoring and key performance indicators
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class HealthScore:
    """Financial health score result"""
    score: int
    grade: str
    category: str
    components: Dict[str, Any]
    recommendations: List[str]


class KPICalculator:
    """
    KPI Calculator Engine

    Provides:
    - Financial health scoring (0-100)
    - Key performance indicators
    - KPI trend analysis
    - Dashboard metrics
    """

    def __init__(self, db):
        self.db = db

    def get_dashboard_kpis(self) -> Dict[str, Any]:
        """Get all KPIs for main dashboard"""
        transactions = self.db.transactions.find_all()
        payments = self.db.payments.find_all()
        materials = self.db.materials.find_all()
        projects = self.db.projects.find_all()

        health = self.get_health_score()

        return {
            'generated_at': datetime.utcnow().isoformat(),
            'health_score': {
                'score': health.score,
                'grade': health.grade,
                'category': health.category,
                'recommendations': health.recommendations
            },
            'kpis': {
                'revenue': self._calculate_revenue_kpi(transactions),
                'expenses': self._calculate_expense_kpi(transactions),
                'profit': self._calculate_profit_kpi(transactions),
                'net_margin': self._calculate_margin_kpi(transactions),
                'cash_runway': self._calculate_cash_runway(transactions, payments),
                'inventory_turnover': self._calculate_inventory_turnover(materials),
                'receivables_aging': self._calculate_receivables_aging(payments),
                'project_profitability': self._calculate_project_profitability(projects)
            }
        }

    def get_health_score(self) -> HealthScore:
        """
        Calculate financial health score (0-100)

        Components:
        - Profitability (25%)
        - Cash flow (25%)
        - Receivables (20%)
        - Growth (15%)
        - Expense control (15%)
        """
        transactions = self.db.transactions.find_all()
        payments = self.db.payments.find_all()

        # Calculate component scores
        profitability_score = self._score_profitability(transactions)
        cashflow_score = self._score_cashflow(transactions)
        receivables_score = self._score_receivables(payments)
        growth_score = self._score_growth(transactions)
        expense_score = self._score_expense_control(transactions)

        # Weighted total
        total_score = (
            profitability_score * 0.25 +
            cashflow_score * 0.25 +
            receivables_score * 0.20 +
            growth_score * 0.15 +
            expense_score * 0.15
        )

        score = round(total_score)
        grade = self._score_to_grade(score)
        category = self._score_to_category(score)

        recommendations = self._generate_health_recommendations(
            profitability_score, cashflow_score, receivables_score,
            growth_score, expense_score
        )

        return HealthScore(
            score=score,
            grade=grade,
            category=category,
            components={
                'profitability': {'score': round(profitability_score), 'weight': 25},
                'cashflow': {'score': round(cashflow_score), 'weight': 25},
                'receivables': {'score': round(receivables_score), 'weight': 20},
                'growth': {'score': round(growth_score), 'weight': 15},
                'expense_control': {'score': round(expense_score), 'weight': 15}
            },
            recommendations=recommendations
        )

    def get_kpi_trends(self, metric: str, periods: int = 6) -> Dict[str, Any]:
        """Get KPI trend over time"""
        transactions = self.db.transactions.find_all()

        trends = []
        now = datetime.utcnow()

        for i in range(periods):
            period_end = now - timedelta(days=30 * i)
            period_start = period_end - timedelta(days=30)

            period_data = self._get_period_data(transactions, period_start, period_end)

            if metric == 'revenue':
                value = period_data['income']
            elif metric == 'expenses':
                value = period_data['expense']
            elif metric == 'profit':
                value = period_data['income'] - period_data['expense']
            elif metric == 'margin':
                value = ((period_data['income'] - period_data['expense']) / period_data['income'] * 100) if period_data['income'] > 0 else 0
            else:
                value = 0

            trends.insert(0, {
                'period': period_start.strftime('%Y-%m'),
                'value': round(value, 2)
            })

        return {
            'metric': metric,
            'periods': periods,
            'data': trends
        }

    def _calculate_revenue_kpi(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Calculate revenue KPI"""
        now = datetime.utcnow()
        current_period = self._get_period_data(transactions, now - timedelta(days=30), now)
        previous_period = self._get_period_data(transactions, now - timedelta(days=60), now - timedelta(days=30))

        current = current_period['income']
        previous = previous_period['income']

        change = ((current - previous) / previous * 100) if previous > 0 else 0
        trend = 'up' if change > 0 else ('down' if change < 0 else 'stable')

        return {
            'value': round(current, 2),
            'previous': round(previous, 2),
            'change_percent': round(change, 1),
            'trend': trend
        }

    def _calculate_expense_kpi(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Calculate expense KPI"""
        now = datetime.utcnow()
        current_period = self._get_period_data(transactions, now - timedelta(days=30), now)
        previous_period = self._get_period_data(transactions, now - timedelta(days=60), now - timedelta(days=30))

        current = current_period['expense']
        previous = previous_period['expense']

        change = ((current - previous) / previous * 100) if previous > 0 else 0
        trend = 'up' if change > 0 else ('down' if change < 0 else 'stable')

        return {
            'value': round(current, 2),
            'previous': round(previous, 2),
            'change_percent': round(change, 1),
            'trend': trend
        }

    def _calculate_profit_kpi(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Calculate profit KPI"""
        now = datetime.utcnow()
        current_period = self._get_period_data(transactions, now - timedelta(days=30), now)
        previous_period = self._get_period_data(transactions, now - timedelta(days=60), now - timedelta(days=30))

        current = current_period['income'] - current_period['expense']
        previous = previous_period['income'] - previous_period['expense']

        change = ((current - previous) / abs(previous) * 100) if previous != 0 else 0
        trend = 'up' if change > 0 else ('down' if change < 0 else 'stable')

        return {
            'value': round(current, 2),
            'previous': round(previous, 2),
            'change_percent': round(change, 1),
            'trend': trend
        }

    def _calculate_margin_kpi(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Calculate net margin KPI"""
        now = datetime.utcnow()
        current_period = self._get_period_data(transactions, now - timedelta(days=30), now)

        income = current_period['income']
        expense = current_period['expense']

        margin = ((income - expense) / income * 100) if income > 0 else 0

        if margin >= 15:
            status = 'excellent'
        elif margin >= 10:
            status = 'good'
        elif margin >= 5:
            status = 'fair'
        else:
            status = 'poor'

        return {
            'value': round(margin, 1),
            'target': 15,
            'status': status
        }

    def _calculate_cash_runway(self, transactions: List[Dict], payments: List[Dict]) -> Dict[str, Any]:
        """Calculate cash runway in months"""
        now = datetime.utcnow()
        period_data = self._get_period_data(transactions, now - timedelta(days=90), now)

        monthly_burn = (period_data['expense'] - period_data['income']) / 3

        current_balance = sum(
            tx.get('amount', 0) if tx.get('type') == 'income' else -tx.get('amount', 0)
            for tx in transactions
        )

        if monthly_burn > 0:
            runway_months = current_balance / monthly_burn
        else:
            runway_months = 999

        if runway_months >= 12:
            status = 'excellent'
        elif runway_months >= 6:
            status = 'good'
        elif runway_months >= 3:
            status = 'warning'
        else:
            status = 'critical'

        return {
            'current_balance': round(current_balance, 2),
            'monthly_burn': round(monthly_burn, 2),
            'runway_months': round(min(runway_months, 999), 1),
            'status': status
        }

    def _calculate_inventory_turnover(self, materials: List[Dict]) -> Dict[str, Any]:
        """Calculate inventory turnover"""
        total_value = sum(
            m.get('current_stock', 0) * m.get('unit_cost', 0)
            for m in materials
        )

        movements = self.db.movements.find_all()
        year_ago = datetime.utcnow() - timedelta(days=365)

        annual_cogs = 0
        for mov in movements:
            if mov.get('type') != 'exit':
                continue

            date_str = mov.get('date') or mov.get('created_at', '')[:10]
            try:
                mov_date = datetime.fromisoformat(date_str.replace('Z', ''))
            except (ValueError, AttributeError):
                continue

            if mov_date >= year_ago:
                material = next(
                    (m for m in materials if m.get('id') == mov.get('material_id')),
                    None
                )
                if material:
                    annual_cogs += mov.get('quantity', 0) * material.get('unit_cost', 0)

        turnover = annual_cogs / total_value if total_value > 0 else 0

        if turnover >= 6:
            status = 'excellent'
        elif turnover >= 4:
            status = 'good'
        elif turnover >= 2:
            status = 'fair'
        else:
            status = 'poor'

        return {
            'turnover_ratio': round(turnover, 2),
            'total_value': round(total_value, 2),
            'annual_cogs': round(annual_cogs, 2),
            'status': status
        }

    def _calculate_receivables_aging(self, payments: List[Dict]) -> Dict[str, Any]:
        """Calculate receivables aging"""
        now = datetime.utcnow()

        receivables = [
            p for p in payments
            if p.get('type') == 'receivable' and p.get('status') == 'pending'
        ]

        total = sum(p.get('amount', 0) for p in receivables)

        aging = {
            'current': 0,
            '30_days': 0,
            '60_days': 0,
            '90_plus': 0
        }

        for p in receivables:
            due_date_str = p.get('due_date', '')[:10]
            try:
                due_date = datetime.fromisoformat(due_date_str)
            except (ValueError, AttributeError):
                continue

            days_overdue = (now - due_date).days
            amount = p.get('amount', 0)

            if days_overdue <= 0:
                aging['current'] += amount
            elif days_overdue <= 30:
                aging['30_days'] += amount
            elif days_overdue <= 60:
                aging['60_days'] += amount
            else:
                aging['90_plus'] += amount

        overdue_percent = ((aging['30_days'] + aging['60_days'] + aging['90_plus']) / total * 100) if total > 0 else 0

        if overdue_percent <= 5:
            status = 'excellent'
        elif overdue_percent <= 15:
            status = 'good'
        elif overdue_percent <= 30:
            status = 'warning'
        else:
            status = 'critical'

        return {
            'total': round(total, 2),
            'aging': {k: round(v, 2) for k, v in aging.items()},
            'overdue_percent': round(overdue_percent, 1),
            'status': status
        }

    def _calculate_project_profitability(self, projects: List[Dict]) -> Dict[str, Any]:
        """Calculate project profitability"""
        completed = [p for p in projects if p.get('status') == 'completed']

        if not completed:
            return {
                'profitability_rate': 0,
                'profitable_count': 0,
                'total_count': 0,
                'status': 'no_data'
            }

        profitable = 0
        for p in completed:
            budget = p.get('budget', 0)
            actual = p.get('actual_cost', 0)
            if actual < budget:
                profitable += 1

        rate = (profitable / len(completed) * 100)

        if rate >= 80:
            status = 'excellent'
        elif rate >= 60:
            status = 'good'
        elif rate >= 40:
            status = 'fair'
        else:
            status = 'poor'

        return {
            'profitability_rate': round(rate, 1),
            'profitable_count': profitable,
            'total_count': len(completed),
            'status': status
        }

    def _get_period_data(self, transactions: List[Dict], start: datetime, end: datetime) -> Dict[str, float]:
        """Get transaction data for a period"""
        income = expense = 0

        for tx in transactions:
            date_str = tx.get('date') or tx.get('created_at', '')[:10]
            try:
                tx_date = datetime.fromisoformat(date_str.replace('Z', ''))
            except (ValueError, AttributeError):
                continue

            if start <= tx_date <= end:
                if tx.get('type') == 'income':
                    income += tx.get('amount', 0)
                else:
                    expense += tx.get('amount', 0)

        return {'income': income, 'expense': expense}

    def _score_profitability(self, transactions: List[Dict]) -> float:
        """Score profitability (0-100)"""
        now = datetime.utcnow()
        data = self._get_period_data(transactions, now - timedelta(days=90), now)

        if data['income'] == 0:
            return 0

        margin = (data['income'] - data['expense']) / data['income'] * 100

        if margin >= 20:
            return 100
        elif margin >= 15:
            return 85
        elif margin >= 10:
            return 70
        elif margin >= 5:
            return 55
        elif margin >= 0:
            return 40
        else:
            return max(0, 40 + margin * 2)

    def _score_cashflow(self, transactions: List[Dict]) -> float:
        """Score cash flow (0-100)"""
        now = datetime.utcnow()
        data = self._get_period_data(transactions, now - timedelta(days=30), now)

        net_flow = data['income'] - data['expense']

        if data['expense'] == 0:
            return 100 if net_flow >= 0 else 50

        ratio = data['income'] / data['expense']

        if ratio >= 1.5:
            return 100
        elif ratio >= 1.2:
            return 85
        elif ratio >= 1.0:
            return 70
        elif ratio >= 0.8:
            return 50
        else:
            return max(0, ratio * 50)

    def _score_receivables(self, payments: List[Dict]) -> float:
        """Score receivables health (0-100)"""
        receivables = [
            p for p in payments
            if p.get('type') == 'receivable' and p.get('status') == 'pending'
        ]

        if not receivables:
            return 100

        now = datetime.utcnow()
        total = sum(p.get('amount', 0) for p in receivables)
        overdue_amount = 0

        for p in receivables:
            due_date_str = p.get('due_date', '')[:10]
            try:
                due_date = datetime.fromisoformat(due_date_str)
                if now > due_date:
                    overdue_amount += p.get('amount', 0)
            except (ValueError, AttributeError):
                continue

        overdue_percent = (overdue_amount / total * 100) if total > 0 else 0

        return max(0, 100 - overdue_percent * 2)

    def _score_growth(self, transactions: List[Dict]) -> float:
        """Score revenue growth (0-100)"""
        now = datetime.utcnow()

        current = self._get_period_data(transactions, now - timedelta(days=90), now)
        previous = self._get_period_data(transactions, now - timedelta(days=180), now - timedelta(days=90))

        if previous['income'] == 0:
            return 50

        growth = ((current['income'] - previous['income']) / previous['income']) * 100

        if growth >= 20:
            return 100
        elif growth >= 10:
            return 85
        elif growth >= 5:
            return 70
        elif growth >= 0:
            return 55
        elif growth >= -10:
            return 40
        else:
            return max(0, 40 + growth)

    def _score_expense_control(self, transactions: List[Dict]) -> float:
        """Score expense control (0-100)"""
        now = datetime.utcnow()

        current = self._get_period_data(transactions, now - timedelta(days=90), now)
        previous = self._get_period_data(transactions, now - timedelta(days=180), now - timedelta(days=90))

        if previous['expense'] == 0:
            return 50

        expense_growth = ((current['expense'] - previous['expense']) / previous['expense']) * 100
        revenue_growth = ((current['income'] - previous['income']) / previous['income'] * 100) if previous['income'] > 0 else 0

        if expense_growth < revenue_growth:
            return min(100, 80 + (revenue_growth - expense_growth))
        elif expense_growth <= 0:
            return 85
        elif expense_growth <= 5:
            return 70
        elif expense_growth <= 10:
            return 55
        else:
            return max(0, 55 - expense_growth)

    def _score_to_grade(self, score: int) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

    def _score_to_category(self, score: int) -> str:
        """Convert score to category"""
        if score >= 80:
            return 'Excellent'
        elif score >= 60:
            return 'Good'
        elif score >= 40:
            return 'Fair'
        elif score >= 20:
            return 'Poor'
        else:
            return 'Critical'

    def _generate_health_recommendations(
        self, profitability: float, cashflow: float,
        receivables: float, growth: float, expense: float
    ) -> List[str]:
        """Generate health improvement recommendations"""
        recommendations = []

        if profitability < 60:
            recommendations.append('Focus on improving profit margins through pricing optimization or cost reduction')

        if cashflow < 60:
            recommendations.append('Improve cash flow by accelerating collections or negotiating better payment terms')

        if receivables < 60:
            recommendations.append('Address overdue receivables with collection efforts and payment reminders')

        if growth < 60:
            recommendations.append('Implement growth strategies to increase revenue')

        if expense < 60:
            recommendations.append('Review expense structure and identify opportunities for cost optimization')

        if not recommendations:
            recommendations.append('Continue monitoring key metrics to maintain financial health')

        return recommendations[:3]
