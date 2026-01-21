# LogiAccounting Pro - Phase 10 Tasks Part 1
## Backend ML Services - Data Pipeline & Forecasting

---

## TASK 1: ML MODULE INITIALIZATION

### File: `backend/app/services/ml/__init__.py`

```python
"""
Machine Learning Module for LogiAccounting Pro
Provides predictive analytics and forecasting capabilities
"""

from .data_pipeline import DataPipeline
from .preprocessor import DataPreprocessor
from .feature_engineering import FeatureEngineer
from .cash_flow_forecaster import CashFlowForecaster
from .revenue_predictor import RevenuePredictor
from .demand_forecaster import DemandForecaster
from .anomaly_detector import AnomalyDetector
from .model_manager import ModelManager

__all__ = [
    'DataPipeline',
    'DataPreprocessor',
    'FeatureEngineer',
    'CashFlowForecaster',
    'RevenuePredictor',
    'DemandForecaster',
    'AnomalyDetector',
    'ModelManager'
]
```

---

## TASK 2: DATA PIPELINE

### File: `backend/app/services/ml/data_pipeline.py`

```python
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
```

---

## TASK 3: DATA PREPROCESSOR

### File: `backend/app/services/ml/preprocessor.py`

```python
"""
Data Preprocessor
Handles data cleaning, normalization, and transformation
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import math


class DataPreprocessor:
    """
    Data Preprocessing for ML Models
    
    Responsibilities:
    - Handle missing values
    - Detect and handle outliers
    - Normalize/scale data
    - Encode categorical variables
    """
    
    def __init__(self):
        self.scalers = {}
        self.encoders = {}
    
    def fill_missing_values(
        self,
        time_series: List[Dict],
        method: str = 'interpolate',
        value_key: str = 'value'
    ) -> List[Dict]:
        """
        Fill missing values in time series
        
        Methods:
        - 'zero': Fill with 0
        - 'mean': Fill with series mean
        - 'forward': Forward fill (last known value)
        - 'interpolate': Linear interpolation
        """
        if not time_series:
            return []
        
        values = [d.get(value_key, 0) for d in time_series]
        non_zero_values = [v for v in values if v != 0]
        
        if method == 'zero':
            return time_series
        
        elif method == 'mean':
            mean_val = sum(non_zero_values) / len(non_zero_values) if non_zero_values else 0
            return [
                {**d, value_key: d.get(value_key) or mean_val}
                for d in time_series
            ]
        
        elif method == 'forward':
            result = []
            last_value = 0
            for d in time_series:
                val = d.get(value_key, 0)
                if val == 0:
                    val = last_value
                else:
                    last_value = val
                result.append({**d, value_key: val})
            return result
        
        elif method == 'interpolate':
            result = list(time_series)
            
            # Find gaps and interpolate
            for i in range(len(result)):
                if result[i].get(value_key, 0) == 0:
                    # Find previous non-zero
                    prev_idx = i - 1
                    prev_val = 0
                    while prev_idx >= 0:
                        if result[prev_idx].get(value_key, 0) != 0:
                            prev_val = result[prev_idx][value_key]
                            break
                        prev_idx -= 1
                    
                    # Find next non-zero
                    next_idx = i + 1
                    next_val = 0
                    while next_idx < len(result):
                        if result[next_idx].get(value_key, 0) != 0:
                            next_val = result[next_idx][value_key]
                            break
                        next_idx += 1
                    
                    # Interpolate
                    if prev_val != 0 and next_val != 0:
                        steps = next_idx - prev_idx
                        step_val = (next_val - prev_val) / steps
                        result[i] = {**result[i], value_key: round(prev_val + step_val * (i - prev_idx), 2)}
                    elif prev_val != 0:
                        result[i] = {**result[i], value_key: prev_val}
                    elif next_val != 0:
                        result[i] = {**result[i], value_key: next_val}
            
            return result
        
        return time_series
    
    def detect_outliers(
        self,
        values: List[float],
        method: str = 'zscore',
        threshold: float = 3.0
    ) -> List[int]:
        """
        Detect outlier indices
        
        Methods:
        - 'zscore': Z-score method (default threshold: 3.0)
        - 'iqr': Interquartile range method (default threshold: 1.5)
        - 'mad': Median absolute deviation
        """
        if len(values) < 3:
            return []
        
        outlier_indices = []
        
        if method == 'zscore':
            mean = sum(values) / len(values)
            std = math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))
            
            if std == 0:
                return []
            
            for i, v in enumerate(values):
                z_score = abs((v - mean) / std)
                if z_score > threshold:
                    outlier_indices.append(i)
        
        elif method == 'iqr':
            sorted_vals = sorted(values)
            n = len(sorted_vals)
            q1 = sorted_vals[n // 4]
            q3 = sorted_vals[3 * n // 4]
            iqr = q3 - q1
            
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr
            
            for i, v in enumerate(values):
                if v < lower_bound or v > upper_bound:
                    outlier_indices.append(i)
        
        elif method == 'mad':
            median = sorted(values)[len(values) // 2]
            deviations = [abs(v - median) for v in values]
            mad = sorted(deviations)[len(deviations) // 2]
            
            if mad == 0:
                return []
            
            for i, v in enumerate(values):
                modified_z = 0.6745 * (v - median) / mad
                if abs(modified_z) > threshold:
                    outlier_indices.append(i)
        
        return outlier_indices
    
    def handle_outliers(
        self,
        time_series: List[Dict],
        value_key: str = 'value',
        method: str = 'cap',
        detection_method: str = 'zscore'
    ) -> List[Dict]:
        """
        Handle outliers in time series
        
        Methods:
        - 'cap': Cap values at threshold
        - 'remove': Remove outlier points
        - 'interpolate': Replace with interpolated values
        """
        values = [d.get(value_key, 0) for d in time_series]
        outlier_indices = self.detect_outliers(values, method=detection_method)
        
        if not outlier_indices:
            return time_series
        
        result = list(time_series)
        
        if method == 'cap':
            # Calculate cap values
            non_outliers = [v for i, v in enumerate(values) if i not in outlier_indices]
            if non_outliers:
                upper_cap = max(non_outliers)
                lower_cap = min(non_outliers)
                
                for i in outlier_indices:
                    val = result[i].get(value_key, 0)
                    if val > upper_cap:
                        result[i] = {**result[i], value_key: upper_cap}
                    elif val < lower_cap:
                        result[i] = {**result[i], value_key: lower_cap}
        
        elif method == 'remove':
            result = [d for i, d in enumerate(result) if i not in outlier_indices]
        
        elif method == 'interpolate':
            for i in outlier_indices:
                # Get surrounding values
                prev_val = values[i - 1] if i > 0 else 0
                next_val = values[i + 1] if i < len(values) - 1 else 0
                
                if prev_val and next_val:
                    result[i] = {**result[i], value_key: round((prev_val + next_val) / 2, 2)}
                elif prev_val:
                    result[i] = {**result[i], value_key: prev_val}
                elif next_val:
                    result[i] = {**result[i], value_key: next_val}
        
        return result
    
    def normalize(
        self,
        values: List[float],
        method: str = 'minmax'
    ) -> Tuple[List[float], Dict]:
        """
        Normalize values
        
        Methods:
        - 'minmax': Scale to [0, 1]
        - 'zscore': Standardize to mean=0, std=1
        """
        if not values:
            return [], {}
        
        if method == 'minmax':
            min_val = min(values)
            max_val = max(values)
            range_val = max_val - min_val
            
            if range_val == 0:
                return [0.5] * len(values), {'method': 'minmax', 'min': min_val, 'max': max_val}
            
            normalized = [(v - min_val) / range_val for v in values]
            params = {'method': 'minmax', 'min': min_val, 'max': max_val}
            
        elif method == 'zscore':
            mean = sum(values) / len(values)
            std = math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))
            
            if std == 0:
                return [0] * len(values), {'method': 'zscore', 'mean': mean, 'std': std}
            
            normalized = [(v - mean) / std for v in values]
            params = {'method': 'zscore', 'mean': mean, 'std': std}
        
        else:
            return values, {}
        
        return [round(v, 6) for v in normalized], params
    
    def denormalize(
        self,
        values: List[float],
        params: Dict
    ) -> List[float]:
        """
        Reverse normalization
        """
        method = params.get('method')
        
        if method == 'minmax':
            min_val = params.get('min', 0)
            max_val = params.get('max', 1)
            range_val = max_val - min_val
            return [round(v * range_val + min_val, 2) for v in values]
        
        elif method == 'zscore':
            mean = params.get('mean', 0)
            std = params.get('std', 1)
            return [round(v * std + mean, 2) for v in values]
        
        return values
    
    def add_time_features(
        self,
        time_series: List[Dict],
        date_key: str = 'date'
    ) -> List[Dict]:
        """
        Add time-based features for ML models
        """
        result = []
        
        for item in time_series:
            date_str = item.get(date_key)
            try:
                date = datetime.fromisoformat(str(date_str)[:10])
            except (ValueError, AttributeError):
                result.append(item)
                continue
            
            enhanced = {
                **item,
                'day_of_week': date.weekday(),
                'day_of_month': date.day,
                'month': date.month,
                'quarter': (date.month - 1) // 3 + 1,
                'year': date.year,
                'is_weekend': 1 if date.weekday() >= 5 else 0,
                'is_month_start': 1 if date.day <= 5 else 0,
                'is_month_end': 1 if date.day >= 25 else 0,
                'is_quarter_end': 1 if date.month in [3, 6, 9, 12] and date.day >= 25 else 0
            }
            result.append(enhanced)
        
        return result
```

---

## TASK 4: FEATURE ENGINEERING

### File: `backend/app/services/ml/feature_engineering.py`

```python
"""
Feature Engineering Service
Creates features for ML models
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import math


class FeatureEngineer:
    """
    Feature Engineering for ML Models
    
    Creates:
    - Lag features
    - Rolling statistics
    - Trend features
    - Seasonal indicators
    """
    
    def __init__(self):
        self.feature_stats = {}
    
    def add_lag_features(
        self,
        time_series: List[Dict],
        value_key: str = 'value',
        lags: List[int] = [1, 7, 14, 30]
    ) -> List[Dict]:
        """
        Add lagged values as features
        
        Args:
            lags: List of lag periods (e.g., [1, 7, 30] for 1 day, 1 week, 1 month)
        """
        result = []
        values = [d.get(value_key, 0) for d in time_series]
        
        for i, item in enumerate(time_series):
            enhanced = dict(item)
            
            for lag in lags:
                if i >= lag:
                    enhanced[f'lag_{lag}'] = values[i - lag]
                else:
                    enhanced[f'lag_{lag}'] = 0
            
            result.append(enhanced)
        
        return result
    
    def add_rolling_features(
        self,
        time_series: List[Dict],
        value_key: str = 'value',
        windows: List[int] = [7, 14, 30]
    ) -> List[Dict]:
        """
        Add rolling statistics as features
        
        For each window size, adds:
        - Rolling mean
        - Rolling std
        - Rolling min
        - Rolling max
        """
        result = []
        values = [d.get(value_key, 0) for d in time_series]
        
        for i, item in enumerate(time_series):
            enhanced = dict(item)
            
            for window in windows:
                if i >= window - 1:
                    window_values = values[i - window + 1:i + 1]
                    
                    mean_val = sum(window_values) / window
                    enhanced[f'rolling_mean_{window}'] = round(mean_val, 2)
                    
                    std_val = math.sqrt(sum((v - mean_val) ** 2 for v in window_values) / window)
                    enhanced[f'rolling_std_{window}'] = round(std_val, 2)
                    
                    enhanced[f'rolling_min_{window}'] = min(window_values)
                    enhanced[f'rolling_max_{window}'] = max(window_values)
                else:
                    enhanced[f'rolling_mean_{window}'] = 0
                    enhanced[f'rolling_std_{window}'] = 0
                    enhanced[f'rolling_min_{window}'] = 0
                    enhanced[f'rolling_max_{window}'] = 0
            
            result.append(enhanced)
        
        return result
    
    def add_trend_features(
        self,
        time_series: List[Dict],
        value_key: str = 'value',
        periods: List[int] = [7, 30]
    ) -> List[Dict]:
        """
        Add trend-based features
        
        For each period, adds:
        - Percent change from period ago
        - Trend direction (-1, 0, 1)
        - Trend strength
        """
        result = []
        values = [d.get(value_key, 0) for d in time_series]
        
        for i, item in enumerate(time_series):
            enhanced = dict(item)
            
            for period in periods:
                if i >= period:
                    prev_val = values[i - period]
                    curr_val = values[i]
                    
                    # Percent change
                    if prev_val != 0:
                        pct_change = ((curr_val - prev_val) / prev_val) * 100
                    else:
                        pct_change = 0
                    enhanced[f'pct_change_{period}'] = round(pct_change, 2)
                    
                    # Trend direction
                    if pct_change > 5:
                        direction = 1
                    elif pct_change < -5:
                        direction = -1
                    else:
                        direction = 0
                    enhanced[f'trend_dir_{period}'] = direction
                    
                    # Trend strength (absolute pct change capped at 100)
                    enhanced[f'trend_strength_{period}'] = min(abs(pct_change), 100)
                else:
                    enhanced[f'pct_change_{period}'] = 0
                    enhanced[f'trend_dir_{period}'] = 0
                    enhanced[f'trend_strength_{period}'] = 0
            
            result.append(enhanced)
        
        return result
    
    def add_seasonal_features(
        self,
        time_series: List[Dict],
        date_key: str = 'date',
        region: str = 'US'
    ) -> List[Dict]:
        """
        Add seasonal indicator features
        """
        # Holiday calendars
        us_holidays = [
            (1, 1), (1, 15), (2, 19), (5, 27), (7, 4),
            (9, 2), (11, 28), (12, 25)
        ]
        
        eu_holidays = [
            (1, 1), (5, 1), (12, 25), (12, 26)
        ]
        
        holidays = us_holidays if region == 'US' else eu_holidays
        
        # Seasonal patterns
        retail_peak_months = [11, 12] if region == 'US' else [7, 11, 12]
        
        result = []
        
        for item in time_series:
            enhanced = dict(item)
            
            date_str = item.get(date_key)
            try:
                date = datetime.fromisoformat(str(date_str)[:10])
            except (ValueError, AttributeError):
                result.append(enhanced)
                continue
            
            # Holiday proximity
            is_holiday = any(
                date.month == m and abs(date.day - d) <= 1
                for m, d in holidays
            )
            enhanced['is_holiday'] = 1 if is_holiday else 0
            
            # Holiday week
            is_holiday_week = any(
                date.month == m and abs(date.day - d) <= 7
                for m, d in holidays
            )
            enhanced['is_holiday_week'] = 1 if is_holiday_week else 0
            
            # Retail season
            enhanced['is_retail_peak'] = 1 if date.month in retail_peak_months else 0
            
            # Tax season (US: Jan-Apr, EU: varies)
            if region == 'US':
                enhanced['is_tax_season'] = 1 if date.month in [1, 2, 3, 4] else 0
            else:
                enhanced['is_tax_season'] = 0
            
            # Seasonal index (cyclical encoding)
            day_of_year = date.timetuple().tm_yday
            enhanced['season_sin'] = round(math.sin(2 * math.pi * day_of_year / 365), 4)
            enhanced['season_cos'] = round(math.cos(2 * math.pi * day_of_year / 365), 4)
            
            result.append(enhanced)
        
        return result
    
    def create_forecast_features(
        self,
        historical_data: List[Dict],
        forecast_dates: List[str],
        value_key: str = 'value'
    ) -> List[Dict]:
        """
        Create feature set for forecast dates based on historical patterns
        """
        # Calculate historical statistics
        values = [d.get(value_key, 0) for d in historical_data if d.get(value_key)]
        
        if not values:
            return [{
                'date': d,
                'predicted_base': 0
            } for d in forecast_dates]
        
        mean_val = sum(values) / len(values)
        
        # Calculate day-of-week patterns
        dow_means = {}
        for item in historical_data:
            try:
                date = datetime.fromisoformat(str(item.get('date'))[:10])
                dow = date.weekday()
                if dow not in dow_means:
                    dow_means[dow] = []
                dow_means[dow].append(item.get(value_key, 0))
            except:
                continue
        
        dow_factors = {
            dow: sum(vals) / len(vals) / mean_val if vals and mean_val else 1.0
            for dow, vals in dow_means.items()
        }
        
        # Generate features for forecast dates
        result = []
        last_values = values[-30:] if len(values) >= 30 else values
        
        for i, date_str in enumerate(forecast_dates):
            try:
                date = datetime.fromisoformat(date_str)
            except:
                continue
            
            dow = date.weekday()
            dow_factor = dow_factors.get(dow, 1.0)
            
            # Base prediction
            predicted_base = mean_val * dow_factor
            
            # Add trend adjustment
            if len(last_values) >= 7:
                recent_mean = sum(last_values[-7:]) / 7
                trend_factor = recent_mean / mean_val if mean_val else 1.0
                predicted_base *= trend_factor
            
            feature_set = {
                'date': date_str,
                'day_of_week': dow,
                'dow_factor': round(dow_factor, 3),
                'month': date.month,
                'is_weekend': 1 if dow >= 5 else 0,
                'predicted_base': round(predicted_base, 2),
                'historical_mean': round(mean_val, 2)
            }
            
            result.append(feature_set)
        
        return result
```

---

## TASK 5: CASH FLOW FORECASTER

### File: `backend/app/services/ml/cash_flow_forecaster.py`

```python
"""
Cash Flow Forecaster
Predicts future cash flow using time series analysis
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import math

# Try importing ML libraries (optional dependencies)
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False


@dataclass
class ForecastPoint:
    """Single forecast data point"""
    date: str
    predicted: float
    lower_bound: float
    upper_bound: float
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CashFlowForecast:
    """Complete cash flow forecast result"""
    generated_at: str
    current_balance: float
    forecast_days: int
    model_type: str
    confidence_level: float
    predictions: List[Dict]
    scenarios: Dict[str, List[Dict]]
    summary: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return asdict(self)


class CashFlowForecaster:
    """
    Cash Flow Forecasting Engine
    
    Uses:
    - Prophet for time series forecasting (if available)
    - Statistical methods as fallback
    - Scenario generation for best/worst/base cases
    """
    
    def __init__(self, db):
        self.db = db
        self.model = None
        self.model_type = 'statistical'
    
    def forecast(
        self,
        days: int = 90,
        include_pending: bool = True,
        scenarios: bool = True,
        confidence_level: float = 0.95
    ) -> CashFlowForecast:
        """
        Generate cash flow forecast
        
        Args:
            days: Number of days to forecast (30, 60, or 90 recommended)
            include_pending: Include known pending payments
            scenarios: Generate optimistic/pessimistic scenarios
            confidence_level: Confidence interval (0.80, 0.90, or 0.95)
        
        Returns:
            CashFlowForecast with predictions and scenarios
        """
        # Get historical data
        transactions = self.db.transactions.find_all()
        payments = self.db.payments.find_all() if include_pending else []
        
        # Prepare time series
        cash_flow_data = self._prepare_cash_flow_series(transactions)
        
        if not cash_flow_data:
            return self._empty_forecast(days)
        
        # Generate forecast
        if PROPHET_AVAILABLE and len(cash_flow_data) >= 30:
            predictions = self._prophet_forecast(cash_flow_data, days, confidence_level)
            self.model_type = 'prophet'
        else:
            predictions = self._statistical_forecast(cash_flow_data, days, confidence_level)
            self.model_type = 'statistical'
        
        # Adjust for pending payments
        if include_pending:
            predictions = self._adjust_for_pending(predictions, payments)
        
        # Calculate current balance
        current_balance = self._calculate_current_balance(transactions, payments)
        
        # Generate scenarios
        scenario_data = {}
        if scenarios:
            scenario_data = self._generate_scenarios(predictions)
        
        # Calculate summary
        summary = self._calculate_summary(predictions, current_balance)
        
        return CashFlowForecast(
            generated_at=datetime.utcnow().isoformat(),
            current_balance=current_balance,
            forecast_days=days,
            model_type=self.model_type,
            confidence_level=confidence_level,
            predictions=[p.to_dict() for p in predictions],
            scenarios=scenario_data,
            summary=summary
        )
    
    def _prepare_cash_flow_series(
        self,
        transactions: List[Dict]
    ) -> List[Dict]:
        """Prepare daily cash flow time series"""
        daily_cf = {}
        
        for tx in transactions:
            date_str = (tx.get('date') or tx.get('created_at', ''))[:10]
            if not date_str:
                continue
            
            try:
                datetime.fromisoformat(date_str)
            except ValueError:
                continue
            
            amount = tx.get('amount', 0)
            
            if tx.get('type') == 'income':
                daily_cf[date_str] = daily_cf.get(date_str, 0) + amount
            else:
                daily_cf[date_str] = daily_cf.get(date_str, 0) - amount
        
        # Sort and return
        return [
            {'date': k, 'value': v}
            for k, v in sorted(daily_cf.items())
        ]
    
    def _statistical_forecast(
        self,
        data: List[Dict],
        days: int,
        confidence: float
    ) -> List[ForecastPoint]:
        """
        Statistical forecasting (fallback method)
        Uses weighted moving average with trend adjustment
        """
        values = [d['value'] for d in data]
        
        if not values:
            return []
        
        # Calculate statistics
        mean_val = sum(values) / len(values)
        std_val = math.sqrt(sum((v - mean_val) ** 2 for v in values) / len(values)) if len(values) > 1 else mean_val * 0.2
        
        # Calculate trend
        if len(values) >= 7:
            recent_mean = sum(values[-7:]) / 7
            trend = (recent_mean - mean_val) / max(abs(mean_val), 1) * 0.1
        else:
            trend = 0
        
        # Day-of-week patterns
        dow_factors = self._calculate_dow_factors(data)
        
        # Confidence multiplier
        conf_mult = {0.80: 1.28, 0.90: 1.645, 0.95: 1.96}.get(confidence, 1.96)
        
        # Generate predictions
        predictions = []
        last_date = datetime.fromisoformat(data[-1]['date'])
        
        for i in range(days):
            pred_date = last_date + timedelta(days=i + 1)
            dow = pred_date.weekday()
            
            # Base prediction with trend
            base_pred = mean_val * (1 + trend * (i / days))
            
            # Apply day-of-week factor
            dow_factor = dow_factors.get(dow, 1.0)
            predicted = base_pred * dow_factor
            
            # Confidence intervals widen over time
            time_factor = 1 + (i / days) * 0.5
            margin = conf_mult * std_val * time_factor
            
            predictions.append(ForecastPoint(
                date=pred_date.strftime('%Y-%m-%d'),
                predicted=round(predicted, 2),
                lower_bound=round(predicted - margin, 2),
                upper_bound=round(predicted + margin, 2)
            ))
        
        return predictions
    
    def _prophet_forecast(
        self,
        data: List[Dict],
        days: int,
        confidence: float
    ) -> List[ForecastPoint]:
        """
        Prophet-based forecasting
        """
        try:
            import pandas as pd
            
            # Prepare dataframe
            df = pd.DataFrame(data)
            df.columns = ['ds', 'y']
            df['ds'] = pd.to_datetime(df['ds'])
            
            # Configure Prophet
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                interval_width=confidence,
                changepoint_prior_scale=0.05
            )
            
            # Add US holidays
            model.add_country_holidays(country_name='US')
            
            # Fit model
            model.fit(df)
            
            # Generate future dates
            future = model.make_future_dataframe(periods=days)
            
            # Predict
            forecast = model.predict(future)
            
            # Extract predictions for future dates
            predictions = []
            last_historical = df['ds'].max()
            
            for _, row in forecast.iterrows():
                if row['ds'] > last_historical:
                    predictions.append(ForecastPoint(
                        date=row['ds'].strftime('%Y-%m-%d'),
                        predicted=round(row['yhat'], 2),
                        lower_bound=round(row['yhat_lower'], 2),
                        upper_bound=round(row['yhat_upper'], 2)
                    ))
            
            return predictions[:days]
            
        except Exception as e:
            # Fallback to statistical method
            return self._statistical_forecast(data, days, confidence)
    
    def _calculate_dow_factors(self, data: List[Dict]) -> Dict[int, float]:
        """Calculate day-of-week seasonal factors"""
        dow_values = {}
        
        for item in data:
            try:
                date = datetime.fromisoformat(item['date'])
                dow = date.weekday()
                if dow not in dow_values:
                    dow_values[dow] = []
                dow_values[dow].append(item['value'])
            except:
                continue
        
        if not dow_values:
            return {i: 1.0 for i in range(7)}
        
        overall_mean = sum(sum(v) for v in dow_values.values()) / sum(len(v) for v in dow_values.values())
        
        if overall_mean == 0:
            return {i: 1.0 for i in range(7)}
        
        return {
            dow: (sum(vals) / len(vals)) / overall_mean if vals else 1.0
            for dow, vals in dow_values.items()
        }
    
    def _adjust_for_pending(
        self,
        predictions: List[ForecastPoint],
        payments: List[Dict]
    ) -> List[ForecastPoint]:
        """Adjust forecast for known pending payments"""
        pending_by_date = {}
        
        for payment in payments:
            if payment.get('status') != 'pending':
                continue
            
            due_date = (payment.get('due_date') or '')[:10]
            if not due_date:
                continue
            
            amount = payment.get('amount', 0)
            
            if payment.get('type') == 'receivable':
                pending_by_date[due_date] = pending_by_date.get(due_date, 0) + amount
            else:
                pending_by_date[due_date] = pending_by_date.get(due_date, 0) - amount
        
        # Apply adjustments
        adjusted = []
        for pred in predictions:
            adjustment = pending_by_date.get(pred.date, 0)
            adjusted.append(ForecastPoint(
                date=pred.date,
                predicted=round(pred.predicted + adjustment, 2),
                lower_bound=round(pred.lower_bound + adjustment, 2),
                upper_bound=round(pred.upper_bound + adjustment, 2)
            ))
        
        return adjusted
    
    def _calculate_current_balance(
        self,
        transactions: List[Dict],
        payments: List[Dict]
    ) -> float:
        """Calculate current cash balance"""
        balance = 0
        
        for tx in transactions:
            amount = tx.get('amount', 0)
            if tx.get('type') == 'income':
                balance += amount
            else:
                balance -= amount
        
        return round(balance, 2)
    
    def _generate_scenarios(
        self,
        base_predictions: List[ForecastPoint]
    ) -> Dict[str, List[Dict]]:
        """
        Generate optimistic, pessimistic, and base scenarios
        """
        scenarios = {
            'optimistic': [],
            'base': [],
            'pessimistic': []
        }
        
        for pred in base_predictions:
            # Base scenario
            scenarios['base'].append({
                'date': pred.date,
                'value': pred.predicted
            })
            
            # Optimistic: upper confidence + 10%
            opt_val = pred.upper_bound * 1.1
            scenarios['optimistic'].append({
                'date': pred.date,
                'value': round(opt_val, 2)
            })
            
            # Pessimistic: lower confidence - 10%
            pess_val = pred.lower_bound * 0.9
            scenarios['pessimistic'].append({
                'date': pred.date,
                'value': round(pess_val, 2)
            })
        
        return scenarios
    
    def _calculate_summary(
        self,
        predictions: List[ForecastPoint],
        current_balance: float
    ) -> Dict[str, Any]:
        """Calculate forecast summary statistics"""
        if not predictions:
            return {}
        
        predicted_values = [p.predicted for p in predictions]
        
        # Running balance
        cumulative = current_balance
        min_balance = current_balance
        
        for val in predicted_values:
            cumulative += val
            min_balance = min(min_balance, cumulative)
        
        # Summary stats
        total_net = sum(predicted_values)
        avg_daily = total_net / len(predicted_values)
        
        # 30/60/90 day projections
        day_30 = sum(predicted_values[:30]) if len(predicted_values) >= 30 else sum(predicted_values)
        day_60 = sum(predicted_values[:60]) if len(predicted_values) >= 60 else sum(predicted_values)
        day_90 = sum(predicted_values[:90]) if len(predicted_values) >= 90 else sum(predicted_values)
        
        return {
            'total_net_flow': round(total_net, 2),
            'average_daily_flow': round(avg_daily, 2),
            'projected_balance_30d': round(current_balance + day_30, 2),
            'projected_balance_60d': round(current_balance + day_60, 2),
            'projected_balance_90d': round(current_balance + day_90, 2),
            'minimum_projected_balance': round(min_balance, 2),
            'positive_days': len([v for v in predicted_values if v > 0]),
            'negative_days': len([v for v in predicted_values if v < 0])
        }
    
    def _empty_forecast(self, days: int) -> CashFlowForecast:
        """Return empty forecast when no data available"""
        return CashFlowForecast(
            generated_at=datetime.utcnow().isoformat(),
            current_balance=0,
            forecast_days=days,
            model_type='none',
            confidence_level=0.95,
            predictions=[],
            scenarios={},
            summary={'message': 'Insufficient historical data for forecasting'}
        )
```

---

## Continue to Part 2 for Revenue Predictor, Demand Forecaster, and Anomaly Detector...

---

*Phase 10 Tasks Part 1 - LogiAccounting Pro*
*Backend ML Services - Data Pipeline & Forecasting*
