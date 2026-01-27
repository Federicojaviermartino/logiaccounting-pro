"""
Trend Analyzer Service
Automated trend detection and analysis
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict
import math


class TrendAnalyzer:
    """
    Trend Analysis Engine

    Provides:
    - Automated trend detection
    - Seasonality analysis
    - Year-over-year comparisons
    - Moving averages
    """

    def __init__(self, db):
        self.db = db

    def get_trends_overview(self) -> Dict[str, Any]:
        """Get comprehensive trend analysis"""
        transactions = self.db.transactions.find_all()

        return {
            'generated_at': datetime.utcnow().isoformat(),
            'revenue_trend': self._analyze_trend(transactions, 'income'),
            'expense_trend': self._analyze_trend(transactions, 'expense'),
            'profit_trend': self._analyze_profit_trend(transactions),
            'seasonality': self._detect_seasonality(transactions),
            'yoy_comparison': self._yoy_comparison(transactions),
            'mom_comparison': self._mom_comparison(transactions)
        }

    def get_metric_trend(self, metric: str, period: str = 'monthly', months: int = 12) -> Dict[str, Any]:
        """Get trend for specific metric"""
        transactions = self.db.transactions.find_all()

        if metric == 'revenue':
            data = self._get_metric_data(transactions, 'income', period, months)
        elif metric == 'expenses':
            data = self._get_metric_data(transactions, 'expense', period, months)
        elif metric == 'profit':
            data = self._get_profit_data(transactions, period, months)
        else:
            return {'error': f'Unknown metric: {metric}'}

        values = [d['value'] for d in data]

        if len(values) < 2:
            return {'metric': metric, 'period': period, 'data': data, 'trend': 'insufficient_data'}

        trend = self._calculate_trend(values)
        moving_avg = self._calculate_moving_average(values, min(3, len(values)))

        return {
            'metric': metric,
            'period': period,
            'data': data,
            'trend_direction': trend['direction'],
            'trend_strength': trend['strength'],
            'growth_rate': trend['growth_rate'],
            'moving_average': moving_avg,
            'statistics': {
                'mean': round(sum(values) / len(values), 2),
                'min': round(min(values), 2),
                'max': round(max(values), 2),
                'std_dev': round(self._std_dev(values), 2)
            }
        }

    def get_yoy_analysis(self) -> Dict[str, Any]:
        """Get year-over-year analysis"""
        transactions = self.db.transactions.find_all()
        return self._yoy_comparison(transactions)

    def get_seasonality_analysis(self) -> Dict[str, Any]:
        """Get detailed seasonality analysis"""
        transactions = self.db.transactions.find_all()

        return {
            'generated_at': datetime.utcnow().isoformat(),
            'monthly_patterns': self._monthly_seasonality(transactions),
            'weekly_patterns': self._weekly_seasonality(transactions),
            'quarterly_patterns': self._quarterly_seasonality(transactions)
        }

    def _analyze_trend(self, transactions: List[Dict], tx_type: str) -> Dict[str, Any]:
        """Analyze trend for transaction type"""
        monthly = self._aggregate_monthly(transactions, tx_type)

        if len(monthly) < 2:
            return {'direction': 'stable', 'strength': 0, 'data': []}

        values = [m['value'] for m in monthly]
        trend = self._calculate_trend(values)

        return {
            'direction': trend['direction'],
            'strength': trend['strength'],
            'growth_rate': trend['growth_rate'],
            'current_period': monthly[-1]['value'] if monthly else 0,
            'previous_period': monthly[-2]['value'] if len(monthly) > 1 else 0,
            'data': monthly[-12:]
        }

    def _analyze_profit_trend(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Analyze profit trend"""
        monthly_income = self._aggregate_monthly(transactions, 'income')
        monthly_expense = self._aggregate_monthly(transactions, 'expense')

        income_map = {m['month']: m['value'] for m in monthly_income}
        expense_map = {m['month']: m['value'] for m in monthly_expense}

        all_months = sorted(set(income_map.keys()) | set(expense_map.keys()))

        monthly_profit = [
            {'month': m, 'value': income_map.get(m, 0) - expense_map.get(m, 0)}
            for m in all_months
        ]

        if len(monthly_profit) < 2:
            return {'direction': 'stable', 'strength': 0}

        values = [p['value'] for p in monthly_profit]
        trend = self._calculate_trend(values)

        return {
            'direction': trend['direction'],
            'strength': trend['strength'],
            'growth_rate': trend['growth_rate'],
            'current_period': monthly_profit[-1]['value'] if monthly_profit else 0,
            'data': monthly_profit[-12:]
        }

    def _detect_seasonality(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Detect seasonal patterns"""
        monthly_avg = defaultdict(list)

        for tx in transactions:
            if tx.get('type') != 'income':
                continue

            date_str = tx.get('date') or tx.get('created_at', '')[:10]
            try:
                tx_date = datetime.fromisoformat(date_str.replace('Z', ''))
            except (ValueError, AttributeError):
                continue

            month = tx_date.month
            monthly_avg[month].append(tx.get('amount', 0))

        overall_avg = sum(sum(v) for v in monthly_avg.values()) / sum(len(v) for v in monthly_avg.values()) if monthly_avg else 0

        seasonal_indices = {}
        for month, values in monthly_avg.items():
            month_avg = sum(values) / len(values) if values else 0
            seasonal_indices[month] = round(month_avg / overall_avg, 2) if overall_avg > 0 else 1.0

        if seasonal_indices:
            peak_month = max(seasonal_indices, key=seasonal_indices.get)
            low_month = min(seasonal_indices, key=seasonal_indices.get)
        else:
            peak_month = None
            low_month = None

        month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December']

        return {
            'seasonal_indices': seasonal_indices,
            'peak_month': month_names[peak_month] if peak_month else None,
            'low_month': month_names[low_month] if low_month else None,
            'seasonality_strength': self._seasonality_strength(seasonal_indices)
        }

    def _yoy_comparison(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Year-over-year comparison"""
        today = datetime.utcnow()
        current_year = today.year
        previous_year = current_year - 1

        current_income = current_expense = previous_income = previous_expense = 0

        for tx in transactions:
            date_str = tx.get('date') or tx.get('created_at', '')[:10]
            try:
                tx_date = datetime.fromisoformat(date_str.replace('Z', ''))
            except (ValueError, AttributeError):
                continue

            amount = tx.get('amount', 0)

            if tx_date.year == current_year:
                if tx.get('type') == 'income':
                    current_income += amount
                else:
                    current_expense += amount
            elif tx_date.year == previous_year:
                if tx.get('type') == 'income':
                    previous_income += amount
                else:
                    previous_expense += amount

        def calc_change(current, previous):
            if previous > 0:
                return round((current - previous) / previous * 100, 1)
            return 100 if current > 0 else 0

        return {
            'current_year': current_year,
            'previous_year': previous_year,
            'revenue': {
                'current': round(current_income, 2),
                'previous': round(previous_income, 2),
                'change_percent': calc_change(current_income, previous_income)
            },
            'expenses': {
                'current': round(current_expense, 2),
                'previous': round(previous_expense, 2),
                'change_percent': calc_change(current_expense, previous_expense)
            },
            'profit': {
                'current': round(current_income - current_expense, 2),
                'previous': round(previous_income - previous_expense, 2),
                'change_percent': calc_change(current_income - current_expense, previous_income - previous_expense)
            }
        }

    def _mom_comparison(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Month-over-month comparison"""
        today = datetime.utcnow()
        current_month_start = today.replace(day=1)
        previous_month_end = current_month_start - timedelta(days=1)
        previous_month_start = previous_month_end.replace(day=1)

        current = {'income': 0, 'expense': 0}
        previous = {'income': 0, 'expense': 0}

        for tx in transactions:
            date_str = tx.get('date') or tx.get('created_at', '')[:10]
            try:
                tx_date = datetime.fromisoformat(date_str.replace('Z', ''))
            except (ValueError, AttributeError):
                continue

            tx_type = tx.get('type', 'expense')
            amount = tx.get('amount', 0)

            if tx_date >= current_month_start:
                current[tx_type] += amount
            elif tx_date >= previous_month_start:
                previous[tx_type] += amount

        def calc_change(c, p):
            if p > 0:
                return round((c - p) / p * 100, 1)
            return 100 if c > 0 else 0

        return {
            'current_month': today.strftime('%B %Y'),
            'previous_month': previous_month_start.strftime('%B %Y'),
            'revenue_change': calc_change(current['income'], previous['income']),
            'expense_change': calc_change(current['expense'], previous['expense']),
            'profit_change': calc_change(
                current['income'] - current['expense'],
                previous['income'] - previous['expense']
            )
        }

    def _aggregate_monthly(self, transactions: List[Dict], tx_type: str) -> List[Dict]:
        """Aggregate transactions by month"""
        monthly = defaultdict(float)

        for tx in transactions:
            if tx.get('type') != tx_type:
                continue

            date_str = tx.get('date') or tx.get('created_at', '')[:10]
            try:
                tx_date = datetime.fromisoformat(date_str.replace('Z', ''))
            except (ValueError, AttributeError):
                continue

            month_key = tx_date.strftime('%Y-%m')
            monthly[month_key] += tx.get('amount', 0)

        return [{'month': k, 'value': round(v, 2)} for k, v in sorted(monthly.items())]

    def _get_metric_data(self, transactions: List[Dict], tx_type: str, period: str, months: int) -> List[Dict]:
        """Get metric data for specified period"""
        if period == 'monthly':
            data = self._aggregate_monthly(transactions, tx_type)
        else:
            data = self._aggregate_monthly(transactions, tx_type)

        return data[-months:]

    def _get_profit_data(self, transactions: List[Dict], period: str, months: int) -> List[Dict]:
        """Get profit data for specified period"""
        income_data = self._get_metric_data(transactions, 'income', period, months)
        expense_data = self._get_metric_data(transactions, 'expense', period, months)

        income_map = {d.get('month'): d['value'] for d in income_data}
        expense_map = {d.get('month'): d['value'] for d in expense_data}

        all_periods = sorted(set(income_map.keys()) | set(expense_map.keys()))

        return [{'month': p, 'value': income_map.get(p, 0) - expense_map.get(p, 0)} for p in all_periods]

    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """Calculate trend direction and strength"""
        if len(values) < 2:
            return {'direction': 'stable', 'strength': 0, 'growth_rate': 0}

        n = len(values)
        x = list(range(n))

        x_mean = sum(x) / n
        y_mean = sum(values) / n

        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        slope = numerator / denominator if denominator != 0 else 0

        if slope > y_mean * 0.02:
            direction = 'up'
        elif slope < -y_mean * 0.02:
            direction = 'down'
        else:
            direction = 'stable'

        y_pred = [y_mean + slope * (x[i] - x_mean) for i in range(n)]
        ss_res = sum((values[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((values[i] - y_mean) ** 2 for i in range(n))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        if values[0] > 0:
            growth_rate = ((values[-1] - values[0]) / values[0]) * 100
        else:
            growth_rate = 100 if values[-1] > 0 else 0

        return {
            'direction': direction,
            'strength': round(max(0, r_squared), 2),
            'growth_rate': round(growth_rate, 1)
        }

    def _calculate_moving_average(self, values: List[float], window: int) -> List[float]:
        """Calculate moving average"""
        if len(values) < window:
            return values

        result = []
        for i in range(len(values) - window + 1):
            avg = sum(values[i:i + window]) / window
            result.append(round(avg, 2))

        return result

    def _std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0

        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return math.sqrt(variance)

    def _seasonality_strength(self, indices: Dict[int, float]) -> str:
        """Determine seasonality strength"""
        if not indices:
            return 'none'

        values = list(indices.values())
        variation = max(values) - min(values)

        if variation > 0.5:
            return 'strong'
        elif variation > 0.2:
            return 'moderate'
        elif variation > 0.1:
            return 'weak'
        else:
            return 'none'

    def _monthly_seasonality(self, transactions: List[Dict]) -> List[Dict]:
        """Get monthly seasonality patterns"""
        monthly = defaultdict(list)

        for tx in transactions:
            if tx.get('type') != 'income':
                continue

            date_str = tx.get('date') or tx.get('created_at', '')[:10]
            try:
                tx_date = datetime.fromisoformat(date_str.replace('Z', ''))
            except (ValueError, AttributeError):
                continue

            monthly[tx_date.month].append(tx.get('amount', 0))

        month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        return [
            {
                'month': month_names[m],
                'average': round(sum(values) / len(values), 2) if values else 0,
                'count': len(values)
            }
            for m, values in sorted(monthly.items())
        ]

    def _weekly_seasonality(self, transactions: List[Dict]) -> List[Dict]:
        """Get weekly seasonality patterns"""
        daily = defaultdict(list)

        for tx in transactions:
            if tx.get('type') != 'income':
                continue

            date_str = tx.get('date') or tx.get('created_at', '')[:10]
            try:
                tx_date = datetime.fromisoformat(date_str.replace('Z', ''))
            except (ValueError, AttributeError):
                continue

            daily[tx_date.weekday()].append(tx.get('amount', 0))

        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

        return [
            {
                'day': day_names[d],
                'average': round(sum(values) / len(values), 2) if values else 0,
                'count': len(values)
            }
            for d, values in sorted(daily.items())
        ]

    def _quarterly_seasonality(self, transactions: List[Dict]) -> List[Dict]:
        """Get quarterly seasonality patterns"""
        quarterly = defaultdict(list)

        for tx in transactions:
            if tx.get('type') != 'income':
                continue

            date_str = tx.get('date') or tx.get('created_at', '')[:10]
            try:
                tx_date = datetime.fromisoformat(date_str.replace('Z', ''))
            except (ValueError, AttributeError):
                continue

            quarter = (tx_date.month - 1) // 3 + 1
            quarterly[quarter].append(tx.get('amount', 0))

        return [
            {
                'quarter': f'Q{q}',
                'average': round(sum(values) / len(values), 2) if values else 0,
                'total': round(sum(values), 2),
                'count': len(values)
            }
            for q, values in sorted(quarterly.items())
        ]
