"""
Data Pipeline Service
Aggregates and prepares historical data for ML models
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import json


class DataPipeline:
    """
    Data Pipeline for ML Models

    Responsibilities:
    - Aggregate historical transactions
    - Format time series data
    - Handle missing data
    - Prepare training datasets
    """

    def __init__(self, db):
        self.db = db

    def get_transaction_time_series(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[str] = None,
        granularity: str = 'daily'
    ) -> List[Dict[str, Any]]:
        """
        Get transactions as time series data

        Args:
            start_date: Start of date range (default: 12 months ago)
            end_date: End of date range (default: today)
            transaction_type: 'income', 'expense', or None for all
            granularity: 'daily', 'weekly', or 'monthly'

        Returns:
            List of time series data points
        """
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        transactions = self.db.transactions.find_all()

        # Filter by date range and type
        filtered = []
        for tx in transactions:
            tx_date = self._parse_date(tx.get('date') or tx.get('created_at'))
            if tx_date is None:
                continue

            if start_date <= tx_date <= end_date:
                if transaction_type is None or tx.get('type') == transaction_type:
                    filtered.append({
                        'date': tx_date,
                        'amount': tx.get('amount', 0),
                        'type': tx.get('type'),
                        'category': tx.get('category'),
                        'currency': tx.get('currency', 'USD')
                    })

        # Aggregate by granularity
        return self._aggregate_time_series(filtered, granularity, start_date, end_date)

    def get_cash_flow_data(
        self,
        months: int = 12,
        include_pending: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive cash flow data for forecasting

        Returns:
            Dictionary with income, expenses, net cash flow, and pending items
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=months * 30)

        transactions = self.db.transactions.find_all()
        payments = self.db.payments.find_all() if include_pending else []

        # Aggregate daily cash flows
        daily_income = defaultdict(float)
        daily_expense = defaultdict(float)

        for tx in transactions:
            tx_date = self._parse_date(tx.get('date') or tx.get('created_at'))
            if tx_date is None or tx_date < start_date:
                continue

            date_key = tx_date.strftime('%Y-%m-%d')
            amount = tx.get('amount', 0)

            if tx.get('type') == 'income':
                daily_income[date_key] += amount
            else:
                daily_expense[date_key] += amount

        # Fill missing dates
        all_dates = self._generate_date_range(start_date, end_date)

        time_series = []
        for date in all_dates:
            date_key = date.strftime('%Y-%m-%d')
            income = daily_income.get(date_key, 0)
            expense = daily_expense.get(date_key, 0)

            time_series.append({
                'date': date_key,
                'income': round(income, 2),
                'expense': round(expense, 2),
                'net': round(income - expense, 2)
            })

        # Get pending payments
        pending_receivables = []
        pending_payables = []

        for payment in payments:
            if payment.get('status') != 'pending':
                continue

            due_date = payment.get('due_date', '')[:10]
            amount = payment.get('amount', 0)

            if payment.get('type') == 'receivable':
                pending_receivables.append({
                    'date': due_date,
                    'amount': amount,
                    'description': payment.get('description', '')
                })
            else:
                pending_payables.append({
                    'date': due_date,
                    'amount': amount,
                    'description': payment.get('description', '')
                })

        # Calculate current balance
        current_balance = sum(daily_income.values()) - sum(daily_expense.values())

        return {
            'time_series': time_series,
            'current_balance': round(current_balance, 2),
            'pending_receivables': pending_receivables,
            'pending_payables': pending_payables,
            'total_pending_in': round(sum(p['amount'] for p in pending_receivables), 2),
            'total_pending_out': round(sum(p['amount'] for p in pending_payables), 2),
            'data_start': start_date.isoformat(),
            'data_end': end_date.isoformat(),
            'data_points': len(time_series)
        }

    def get_revenue_data(
        self,
        months: int = 12,
        by_category: bool = False,
        by_customer: bool = False
    ) -> Dict[str, Any]:
        """
        Get revenue data for prediction models
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=months * 30)

        transactions = self.db.transactions.find_all()

        # Filter income transactions
        income_txs = [
            tx for tx in transactions
            if tx.get('type') == 'income' and
            self._parse_date(tx.get('date') or tx.get('created_at')) is not None and
            self._parse_date(tx.get('date') or tx.get('created_at')) >= start_date
        ]

        # Monthly revenue
        monthly_revenue = defaultdict(float)
        category_revenue = defaultdict(lambda: defaultdict(float))
        customer_revenue = defaultdict(lambda: defaultdict(float))

        for tx in income_txs:
            tx_date = self._parse_date(tx.get('date') or tx.get('created_at'))
            month_key = tx_date.strftime('%Y-%m')
            amount = tx.get('amount', 0)

            monthly_revenue[month_key] += amount

            if by_category:
                category = tx.get('category', 'Uncategorized')
                category_revenue[month_key][category] += amount

            if by_customer:
                customer = tx.get('client_id') or tx.get('customer_id') or 'Unknown'
                customer_revenue[month_key][customer] += amount

        # Format output
        result = {
            'monthly_totals': [
                {'month': k, 'revenue': round(v, 2)}
                for k, v in sorted(monthly_revenue.items())
            ],
            'total_revenue': round(sum(monthly_revenue.values()), 2),
            'average_monthly': round(sum(monthly_revenue.values()) / max(len(monthly_revenue), 1), 2)
        }

        if by_category:
            result['by_category'] = {
                month: {cat: round(amt, 2) for cat, amt in cats.items()}
                for month, cats in category_revenue.items()
            }

        if by_customer:
            result['by_customer'] = {
                month: {cust: round(amt, 2) for cust, amt in custs.items()}
                for month, custs in customer_revenue.items()
            }

        return result

    def get_inventory_demand_data(
        self,
        material_id: Optional[str] = None,
        months: int = 12
    ) -> Dict[str, Any]:
        """
        Get inventory movement data for demand forecasting
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=months * 30)

        movements = self.db.movements.find_all()
        materials = self.db.materials.find_all()

        # Filter exit movements (demand)
        demand_data = defaultdict(lambda: defaultdict(int))

        for mov in movements:
            if mov.get('type') != 'exit':
                continue

            mov_date = self._parse_date(mov.get('date') or mov.get('created_at'))
            if mov_date is None or mov_date < start_date:
                continue

            mat_id = mov.get('material_id')
            if material_id and mat_id != material_id:
                continue

            date_key = mov_date.strftime('%Y-%m-%d')
            demand_data[mat_id][date_key] += mov.get('quantity', 0)

        # Get material details
        material_map = {m['id']: m for m in materials}

        result = {}
        for mat_id, daily_demand in demand_data.items():
            material = material_map.get(mat_id, {})

            # Fill missing dates with zeros
            all_dates = self._generate_date_range(start_date, end_date)
            time_series = []

            for date in all_dates:
                date_key = date.strftime('%Y-%m-%d')
                time_series.append({
                    'date': date_key,
                    'demand': daily_demand.get(date_key, 0)
                })

            result[mat_id] = {
                'material_name': material.get('name', 'Unknown'),
                'current_stock': material.get('current_stock', 0),
                'min_stock': material.get('min_stock', 0),
                'unit_cost': material.get('unit_cost', 0),
                'lead_time_days': material.get('lead_time_days', 7),
                'time_series': time_series,
                'total_demand': sum(daily_demand.values()),
                'avg_daily_demand': round(sum(daily_demand.values()) / max(len(time_series), 1), 2)
            }

        if material_id:
            return result.get(material_id, {})

        return result

    def _parse_date(self, date_str: Any) -> Optional[datetime]:
        """Parse date string to datetime"""
        if date_str is None:
            return None

        if isinstance(date_str, datetime):
            return date_str

        try:
            # Handle ISO format
            date_str = str(date_str)[:10]
            return datetime.fromisoformat(date_str)
        except (ValueError, AttributeError):
            return None

    def _generate_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[datetime]:
        """Generate list of dates in range"""
        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current)
            current += timedelta(days=1)
        return dates

    def _aggregate_time_series(
        self,
        data: List[Dict],
        granularity: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Aggregate time series by granularity"""
        if granularity == 'daily':
            aggregated = defaultdict(float)
            for item in data:
                key = item['date'].strftime('%Y-%m-%d')
                aggregated[key] += item['amount']

            # Fill missing dates
            all_dates = self._generate_date_range(start_date, end_date)
            return [
                {'date': d.strftime('%Y-%m-%d'), 'value': aggregated.get(d.strftime('%Y-%m-%d'), 0)}
                for d in all_dates
            ]

        elif granularity == 'weekly':
            aggregated = defaultdict(float)
            for item in data:
                key = item['date'].strftime('%Y-W%W')
                aggregated[key] += item['amount']

            return [
                {'period': k, 'value': round(v, 2)}
                for k, v in sorted(aggregated.items())
            ]

        elif granularity == 'monthly':
            aggregated = defaultdict(float)
            for item in data:
                key = item['date'].strftime('%Y-%m')
                aggregated[key] += item['amount']

            return [
                {'month': k, 'value': round(v, 2)}
                for k, v in sorted(aggregated.items())
            ]

        return []
