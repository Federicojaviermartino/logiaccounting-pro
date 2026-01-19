# LogiAccounting Pro - Phase 10 Tasks Part 2

## MORE BACKEND SERVICES

---

## TASK 6: INVENTORY ANALYTICS SERVICE

### 6.1 Create Inventory Analytics

**File:** `backend/app/services/analytics/inventory_analytics.py`

```python
"""
Inventory Analytics Service
Demand forecasting, optimization, and inventory intelligence
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
import math


class InventoryAnalytics:
    """
    Inventory Analytics Engine
    
    Provides:
    - Demand forecasting per SKU
    - Reorder point optimization
    - Safety stock calculation
    - Inventory turnover analysis
    - ABC classification
    - Stockout risk assessment
    """

    def __init__(self, db):
        self.db = db

    def get_inventory_overview(self) -> Dict[str, Any]:
        """Get comprehensive inventory analytics overview"""
        materials = self.db.materials.find_all()
        movements = self.db.movements.find_all()
        
        total_value = sum(
            m.get('current_stock', 0) * m.get('unit_cost', 0)
            for m in materials
        )
        
        total_items = len(materials)
        low_stock_count = len([
            m for m in materials
            if m.get('current_stock', 0) <= m.get('min_stock', 10)
        ])
        
        return {
            'generated_at': datetime.utcnow().isoformat(),
            'total_items': total_items,
            'total_value': round(total_value, 2),
            'low_stock_items': low_stock_count,
            'out_of_stock_items': len([m for m in materials if m.get('current_stock', 0) == 0]),
            'abc_classification': self._abc_classification(materials),
            'turnover_metrics': self._calculate_turnover_metrics(materials, movements),
            'stockout_risk': self._assess_stockout_risk(materials, movements),
            'top_movers': self._get_top_movers(movements, materials)
        }

    def get_demand_forecast(self, sku: str, days: int = 90) -> Dict[str, Any]:
        """Get demand forecast for specific SKU"""
        movements = self.db.movements.find_all()
        material = self.db.materials.find_by_id(sku)
        
        if not material:
            return {'error': 'SKU not found'}
        
        demand_history = self._get_demand_history(movements, sku)
        
        if not demand_history:
            return {
                'sku': sku,
                'name': material.get('name'),
                'message': 'Insufficient demand history',
                'forecast': [],
                'recommendations': self._get_basic_recommendations(material)
            }
        
        forecast = self._forecast_demand(demand_history, days)
        optimization = self._calculate_optimization_metrics(
            demand_history, forecast, material
        )
        
        return {
            'sku': sku,
            'name': material.get('name'),
            'current_stock': material.get('current_stock', 0),
            'unit_cost': material.get('unit_cost', 0),
            'forecast': forecast,
            'optimization': optimization,
            'recommendations': self._get_inventory_recommendations(
                material, forecast, optimization
            )
        }

    def get_reorder_recommendations(self) -> Dict[str, Any]:
        """Get reorder recommendations for all items"""
        materials = self.db.materials.find_all()
        movements = self.db.movements.find_all()
        
        recommendations = []
        
        for material in materials:
            sku = material.get('id')
            demand_history = self._get_demand_history(movements, sku)
            
            if not demand_history:
                avg_daily_demand = 1
            else:
                avg_daily_demand = sum(d['quantity'] for d in demand_history) / max(len(demand_history), 1)
            
            current_stock = material.get('current_stock', 0)
            lead_time = material.get('lead_time_days', 7)
            
            safety_stock = avg_daily_demand * 3
            reorder_point = (avg_daily_demand * lead_time) + safety_stock
            
            eoq = self._calculate_eoq(
                avg_daily_demand * 365,
                50,
                material.get('unit_cost', 10) * 0.2
            )
            
            days_until_stockout = current_stock / avg_daily_demand if avg_daily_demand > 0 else 999
            should_reorder = current_stock <= reorder_point
            
            if should_reorder or days_until_stockout <= 14:
                recommendations.append({
                    'sku': sku,
                    'name': material.get('name'),
                    'current_stock': current_stock,
                    'reorder_point': round(reorder_point),
                    'recommended_quantity': round(eoq),
                    'days_until_stockout': round(days_until_stockout, 1),
                    'urgency': 'critical' if days_until_stockout <= 3 else (
                        'high' if days_until_stockout <= 7 else 'medium'
                    ),
                    'estimated_cost': round(eoq * material.get('unit_cost', 0), 2)
                })
        
        urgency_order = {'critical': 0, 'high': 1, 'medium': 2}
        recommendations.sort(key=lambda x: (urgency_order.get(x['urgency'], 3), x['days_until_stockout']))
        
        return {
            'generated_at': datetime.utcnow().isoformat(),
            'total_recommendations': len(recommendations),
            'critical_count': len([r for r in recommendations if r['urgency'] == 'critical']),
            'total_estimated_cost': round(sum(r['estimated_cost'] for r in recommendations), 2),
            'recommendations': recommendations
        }

    def get_abc_analysis(self) -> Dict[str, Any]:
        """Perform ABC inventory classification"""
        materials = self.db.materials.find_all()
        movements = self.db.movements.find_all()
        
        item_values = []
        
        for material in materials:
            sku = material.get('id')
            annual_consumption = self._get_annual_consumption(movements, sku)
            unit_cost = material.get('unit_cost', 0)
            annual_value = annual_consumption * unit_cost
            
            item_values.append({
                'sku': sku,
                'name': material.get('name'),
                'annual_consumption': annual_consumption,
                'unit_cost': unit_cost,
                'annual_value': round(annual_value, 2),
                'current_stock': material.get('current_stock', 0)
            })
        
        item_values.sort(key=lambda x: x['annual_value'], reverse=True)
        total_value = sum(i['annual_value'] for i in item_values)
        
        cumulative = 0
        for item in item_values:
            cumulative += item['annual_value']
            item['cumulative_percent'] = round(cumulative / total_value * 100, 1) if total_value > 0 else 0
            
            if item['cumulative_percent'] <= 70:
                item['class'] = 'A'
            elif item['cumulative_percent'] <= 90:
                item['class'] = 'B'
            else:
                item['class'] = 'C'
        
        class_summary = {'A': {'count': 0, 'value': 0}, 'B': {'count': 0, 'value': 0}, 'C': {'count': 0, 'value': 0}}
        
        for item in item_values:
            cls = item['class']
            class_summary[cls]['count'] += 1
            class_summary[cls]['value'] += item['annual_value']
        
        for cls in class_summary:
            class_summary[cls]['value'] = round(class_summary[cls]['value'], 2)
            class_summary[cls]['percent_items'] = round(
                class_summary[cls]['count'] / len(item_values) * 100, 1
            ) if item_values else 0
            class_summary[cls]['percent_value'] = round(
                class_summary[cls]['value'] / total_value * 100, 1
            ) if total_value > 0 else 0
        
        return {
            'generated_at': datetime.utcnow().isoformat(),
            'total_items': len(item_values),
            'total_annual_value': round(total_value, 2),
            'class_summary': class_summary,
            'items': item_values,
            'recommendations': {
                'A': 'Tight control, accurate records, frequent review, reliable suppliers',
                'B': 'Moderate control, good records, regular review',
                'C': 'Simple controls, minimal records, order large quantities'
            }
        }

    def _get_demand_history(self, movements: List[Dict], sku: str) -> List[Dict]:
        """Get historical demand for SKU"""
        demand = []
        
        for mov in movements:
            if mov.get('material_id') != sku or mov.get('type') != 'exit':
                continue
            
            date_str = mov.get('date') or mov.get('created_at', '')[:10]
            try:
                mov_date = datetime.fromisoformat(date_str.replace('Z', '')).date()
            except (ValueError, AttributeError):
                continue
            
            demand.append({
                'date': mov_date.isoformat(),
                'quantity': mov.get('quantity', 0)
            })
        
        return sorted(demand, key=lambda x: x['date'])

    def _forecast_demand(self, history: List[Dict], days: int) -> List[Dict]:
        """Generate demand forecast using simple moving average"""
        if not history:
            return []
        
        daily = defaultdict(int)
        for h in history:
            daily[h['date']] += h['quantity']
        
        values = list(daily.values())
        
        if not values:
            return []
        
        window = min(7, len(values))
        avg = sum(values[-window:]) / window
        std = math.sqrt(sum((v - avg) ** 2 for v in values[-window:]) / window) if window > 1 else avg * 0.2
        
        forecast = []
        last_date = datetime.fromisoformat(max(daily.keys()))
        
        weekly_factors = {0: 1.1, 1: 1.0, 2: 1.0, 3: 1.0, 4: 0.95, 5: 0.5, 6: 0.4}
        
        for i in range(days):
            pred_date = last_date + timedelta(days=i + 1)
            weekday = pred_date.weekday()
            
            predicted = max(0, avg * weekly_factors.get(weekday, 1.0))
            
            forecast.append({
                'date': pred_date.strftime('%Y-%m-%d'),
                'predicted': round(predicted, 1),
                'lower': round(max(0, predicted - 1.5 * std), 1),
                'upper': round(predicted + 1.5 * std, 1)
            })
        
        return forecast

    def _calculate_optimization_metrics(self, history: List[Dict], forecast: List[Dict], material: Dict) -> Dict[str, Any]:
        """Calculate inventory optimization metrics"""
        if history:
            total_demand = sum(h['quantity'] for h in history)
            days_span = (
                datetime.fromisoformat(history[-1]['date']) - 
                datetime.fromisoformat(history[0]['date'])
            ).days or 1
            avg_daily_demand = total_demand / days_span
        else:
            avg_daily_demand = 1
        
        lead_time = material.get('lead_time_days', 7)
        unit_cost = material.get('unit_cost', 10)
        
        safety_stock = avg_daily_demand * 3
        reorder_point = (avg_daily_demand * lead_time) + safety_stock
        
        annual_demand = avg_daily_demand * 365
        order_cost = 50
        holding_cost = unit_cost * 0.2
        eoq = self._calculate_eoq(annual_demand, order_cost, holding_cost)
        
        current_stock = material.get('current_stock', 0)
        days_of_stock = current_stock / avg_daily_demand if avg_daily_demand > 0 else 999
        
        return {
            'avg_daily_demand': round(avg_daily_demand, 2),
            'safety_stock': round(safety_stock),
            'reorder_point': round(reorder_point),
            'economic_order_quantity': round(eoq),
            'days_of_stock': round(days_of_stock, 1),
            'annual_demand': round(annual_demand),
            'holding_cost_percent': 20,
            'order_cost': order_cost
        }

    def _calculate_eoq(self, annual_demand: float, order_cost: float, holding_cost: float) -> float:
        """Calculate Economic Order Quantity"""
        if holding_cost <= 0 or annual_demand <= 0:
            return 0
        return math.sqrt((2 * annual_demand * order_cost) / holding_cost)

    def _get_inventory_recommendations(self, material: Dict, forecast: List[Dict], optimization: Dict) -> List[str]:
        """Generate inventory recommendations"""
        recommendations = []
        
        current_stock = material.get('current_stock', 0)
        reorder_point = optimization.get('reorder_point', 10)
        days_of_stock = optimization.get('days_of_stock', 0)
        eoq = optimization.get('economic_order_quantity', 0)
        
        if current_stock <= reorder_point:
            if days_of_stock <= 3:
                recommendations.append(f'URGENT: Reorder {eoq} units immediately - only {days_of_stock:.1f} days of stock')
            else:
                recommendations.append(f'Reorder {eoq} units to maintain optimal stock levels')
        
        if days_of_stock > 60:
            recommendations.append('Consider reducing stock levels - excess inventory detected')
        
        if optimization['avg_daily_demand'] < 0.5:
            recommendations.append('Low demand item - consider minimum order quantities')
        
        return recommendations

    def _get_basic_recommendations(self, material: Dict) -> List[str]:
        """Get basic recommendations when no history available"""
        return [
            'No demand history available - using default parameters',
            f'Current stock: {material.get("current_stock", 0)} units',
            f'Minimum stock threshold: {material.get("min_stock", 10)} units'
        ]

    def _abc_classification(self, materials: List[Dict]) -> Dict[str, int]:
        """Quick ABC classification counts"""
        movements = self.db.movements.find_all()
        
        item_values = []
        for m in materials:
            annual = self._get_annual_consumption(movements, m.get('id'))
            value = annual * m.get('unit_cost', 0)
            item_values.append(value)
        
        if not item_values:
            return {'A': 0, 'B': 0, 'C': 0}
        
        item_values.sort(reverse=True)
        total = sum(item_values)
        
        counts = {'A': 0, 'B': 0, 'C': 0}
        cumulative = 0
        
        for value in item_values:
            cumulative += value
            percent = cumulative / total * 100 if total > 0 else 0
            
            if percent <= 70:
                counts['A'] += 1
            elif percent <= 90:
                counts['B'] += 1
            else:
                counts['C'] += 1
        
        return counts

    def _calculate_turnover_metrics(self, materials: List[Dict], movements: List[Dict]) -> Dict[str, Any]:
        """Calculate inventory turnover metrics"""
        total_inventory = sum(
            m.get('current_stock', 0) * m.get('unit_cost', 0)
            for m in materials
        )
        
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
        
        turnover = annual_cogs / total_inventory if total_inventory > 0 else 0
        days_inventory = 365 / turnover if turnover > 0 else 999
        
        return {
            'turnover_ratio': round(turnover, 2),
            'days_of_inventory': round(days_inventory, 1),
            'total_inventory_value': round(total_inventory, 2),
            'annual_cogs': round(annual_cogs, 2),
            'status': 'good' if turnover >= 4 else ('fair' if turnover >= 2 else 'poor')
        }

    def _assess_stockout_risk(self, materials: List[Dict], movements: List[Dict]) -> Dict[str, Any]:
        """Assess stockout risk across inventory"""
        at_risk = []
        
        for material in materials:
            sku = material.get('id')
            demand_history = self._get_demand_history(movements, sku)
            
            if demand_history:
                avg_demand = sum(h['quantity'] for h in demand_history[-30:]) / 30
            else:
                avg_demand = 0.5
            
            current_stock = material.get('current_stock', 0)
            lead_time = material.get('lead_time_days', 7)
            
            days_of_stock = current_stock / avg_demand if avg_demand > 0 else 999
            
            if days_of_stock <= lead_time + 3:
                at_risk.append({
                    'sku': sku,
                    'name': material.get('name'),
                    'days_until_stockout': round(days_of_stock, 1),
                    'risk_level': 'critical' if days_of_stock <= 3 else 'high'
                })
        
        return {
            'at_risk_count': len(at_risk),
            'critical_count': len([r for r in at_risk if r['risk_level'] == 'critical']),
            'items': sorted(at_risk, key=lambda x: x['days_until_stockout'])[:10]
        }

    def _get_top_movers(self, movements: List[Dict], materials: List[Dict]) -> List[Dict]:
        """Get top moving items"""
        movement_counts = defaultdict(int)
        
        cutoff = datetime.utcnow() - timedelta(days=30)
        
        for mov in movements:
            if mov.get('type') != 'exit':
                continue
            
            date_str = mov.get('date') or mov.get('created_at', '')[:10]
            try:
                mov_date = datetime.fromisoformat(date_str.replace('Z', ''))
            except (ValueError, AttributeError):
                continue
            
            if mov_date >= cutoff:
                movement_counts[mov.get('material_id')] += mov.get('quantity', 0)
        
        top = sorted(movement_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        result = []
        for sku, quantity in top:
            material = next((m for m in materials if m.get('id') == sku), None)
            if material:
                result.append({
                    'sku': sku,
                    'name': material.get('name'),
                    'units_moved': quantity
                })
        
        return result

    def _get_annual_consumption(self, movements: List[Dict], sku: str) -> int:
        """Get annual consumption for SKU"""
        year_ago = datetime.utcnow() - timedelta(days=365)
        total = 0
        
        for mov in movements:
            if mov.get('material_id') != sku or mov.get('type') != 'exit':
                continue
            
            date_str = mov.get('date') or mov.get('created_at', '')[:10]
            try:
                mov_date = datetime.fromisoformat(date_str.replace('Z', ''))
            except (ValueError, AttributeError):
                continue
            
            if mov_date >= year_ago:
                total += mov.get('quantity', 0)
        
        return total
```

---

## TASK 7: TREND ANALYZER SERVICE

### 7.1 Create Trend Analyzer

**File:** `backend/app/services/analytics/trend_analyzer.py`

```python
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
```

---

## TASK 8: SCENARIO PLANNER SERVICE

### 8.1 Create Scenario Planner

**File:** `backend/app/services/analytics/scenario_planner.py`

```python
"""
Scenario Planner Service
What-if analysis and business scenario modeling
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass, asdict


@dataclass
class ScenarioResult:
    """Scenario simulation result"""
    name: str
    parameters: Dict[str, Any]
    projections: Dict[str, Any]
    impact_summary: Dict[str, Any]
    risk_assessment: str
    recommendations: List[str]


class ScenarioPlanner:
    """
    Scenario Planning Engine
    
    Provides:
    - What-if scenario modeling
    - Best/Worst/Expected case analysis
    - Break-even analysis
    - Growth projections
    """

    def __init__(self, db):
        self.db = db

    def run_scenario(self, scenario_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run specific scenario analysis"""
        transactions = self.db.transactions.find_all()
        baseline = self._calculate_baseline(transactions)
        
        if scenario_type == 'revenue_change':
            result = self._revenue_change_scenario(baseline, parameters)
        elif scenario_type == 'expense_change':
            result = self._expense_change_scenario(baseline, parameters)
        elif scenario_type == 'growth':
            result = self._growth_scenario(baseline, parameters)
        elif scenario_type == 'breakeven':
            result = self._breakeven_analysis(baseline, parameters)
        else:
            return {'error': f'Unknown scenario type: {scenario_type}'}
        
        return {
            'generated_at': datetime.utcnow().isoformat(),
            'scenario_type': scenario_type,
            'baseline': baseline,
            'result': asdict(result) if hasattr(result, '__dataclass_fields__') else result
        }

    def get_best_worst_expected(self) -> Dict[str, Any]:
        """Get best, worst, and expected case scenarios"""
        transactions = self.db.transactions.find_all()
        baseline = self._calculate_baseline(transactions)
        
        best_case = self._growth_scenario(baseline, {
            'revenue_growth': 20, 'expense_growth': -10, 'months': 12
        })
        
        worst_case = self._growth_scenario(baseline, {
            'revenue_growth': -15, 'expense_growth': 20, 'months': 12
        })
        
        expected_case = self._growth_scenario(baseline, {
            'revenue_growth': 8, 'expense_growth': 5, 'months': 12
        })
        
        return {
            'generated_at': datetime.utcnow().isoformat(),
            'baseline': baseline,
            'best_case': asdict(best_case),
            'worst_case': asdict(worst_case),
            'expected_case': asdict(expected_case),
            'summary': {
                'best_profit': best_case.projections['projected_profit'],
                'worst_profit': worst_case.projections['projected_profit'],
                'expected_profit': expected_case.projections['projected_profit'],
                'profit_range': round(
                    best_case.projections['projected_profit'] - 
                    worst_case.projections['projected_profit'], 2
                )
            }
        }

    def _calculate_baseline(self, transactions: List[Dict]) -> Dict[str, float]:
        """Calculate baseline metrics from last 12 months"""
        year_ago = datetime.utcnow() - timedelta(days=365)
        
        total_income = total_expense = 0
        
        for tx in transactions:
            date_str = tx.get('date') or tx.get('created_at', '')[:10]
            try:
                tx_date = datetime.fromisoformat(date_str.replace('Z', ''))
            except (ValueError, AttributeError):
                continue
            
            if tx_date >= year_ago:
                if tx.get('type') == 'income':
                    total_income += tx.get('amount', 0)
                else:
                    total_expense += tx.get('amount', 0)
        
        monthly_income = total_income / 12
        monthly_expense = total_expense / 12
        monthly_profit = monthly_income - monthly_expense
        
        margin = (monthly_profit / monthly_income * 100) if monthly_income > 0 else 0
        
        return {
            'annual_revenue': round(total_income, 2),
            'annual_expenses': round(total_expense, 2),
            'annual_profit': round(total_income - total_expense, 2),
            'monthly_revenue': round(monthly_income, 2),
            'monthly_expenses': round(monthly_expense, 2),
            'monthly_profit': round(monthly_profit, 2),
            'profit_margin': round(margin, 1)
        }

    def _revenue_change_scenario(self, baseline: Dict, parameters: Dict) -> ScenarioResult:
        """Model revenue change impact"""
        change_percent = parameters.get('change_percent', 10)
        months = parameters.get('months', 12)
        
        new_monthly_revenue = baseline['monthly_revenue'] * (1 + change_percent / 100)
        new_monthly_profit = new_monthly_revenue - baseline['monthly_expenses']
        
        projected_annual_revenue = new_monthly_revenue * months
        projected_annual_profit = new_monthly_profit * months
        
        risk = 'high' if abs(change_percent) >= 15 else ('medium' if abs(change_percent) >= 5 else 'low')
        
        recommendations = []
        if change_percent > 0:
            recommendations.append(f'Target {change_percent}% revenue growth through:')
            recommendations.append('- Expand customer base or upsell existing customers')
            recommendations.append('- Review pricing strategy')
        else:
            recommendations.append('Prepare for revenue decline by:')
            recommendations.append('- Identifying cost reduction opportunities')
            recommendations.append('- Diversifying revenue streams')
        
        return ScenarioResult(
            name=f'Revenue {"Increase" if change_percent > 0 else "Decrease"} {abs(change_percent)}%',
            parameters=parameters,
            projections={
                'projected_monthly_revenue': round(new_monthly_revenue, 2),
                'projected_monthly_profit': round(new_monthly_profit, 2),
                'projected_annual_revenue': round(projected_annual_revenue, 2),
                'projected_annual_profit': round(projected_annual_profit, 2)
            },
            impact_summary={
                'revenue_impact': round(projected_annual_revenue - baseline['annual_revenue'], 2),
                'profit_impact': round(projected_annual_profit - baseline['annual_profit'], 2)
            },
            risk_assessment=risk,
            recommendations=recommendations
        )

    def _expense_change_scenario(self, baseline: Dict, parameters: Dict) -> ScenarioResult:
        """Model expense change impact"""
        change_percent = parameters.get('change_percent', 10)
        months = parameters.get('months', 12)
        
        new_monthly_expenses = baseline['monthly_expenses'] * (1 + change_percent / 100)
        new_monthly_profit = baseline['monthly_revenue'] - new_monthly_expenses
        
        projected_annual_expenses = new_monthly_expenses * months
        projected_annual_profit = (baseline['monthly_revenue'] * months) - projected_annual_expenses
        
        recommendations = []
        if change_percent > 0:
            recommendations.append('Expense increase projected. Consider:')
            recommendations.append('- Review and optimize operational costs')
            recommendations.append('- Negotiate better supplier terms')
        else:
            recommendations.append('Expense reduction achievable through:')
            recommendations.append('- Process optimization')
            recommendations.append('- Supplier negotiations')
        
        return ScenarioResult(
            name=f'Expense {"Increase" if change_percent > 0 else "Decrease"} {abs(change_percent)}%',
            parameters=parameters,
            projections={
                'projected_monthly_expenses': round(new_monthly_expenses, 2),
                'projected_monthly_profit': round(new_monthly_profit, 2),
                'projected_annual_expenses': round(projected_annual_expenses, 2),
                'projected_annual_profit': round(projected_annual_profit, 2)
            },
            impact_summary={
                'expense_impact': round(projected_annual_expenses - baseline['annual_expenses'], 2),
                'profit_impact': round(projected_annual_profit - baseline['annual_profit'], 2)
            },
            risk_assessment='medium' if abs(change_percent) < 15 else 'high',
            recommendations=recommendations
        )

    def _growth_scenario(self, baseline: Dict, parameters: Dict) -> ScenarioResult:
        """Model combined growth scenario"""
        revenue_growth = parameters.get('revenue_growth', 10)
        expense_growth = parameters.get('expense_growth', 5)
        months = parameters.get('months', 12)
        
        monthly_projections = []
        current_revenue = baseline['monthly_revenue']
        current_expense = baseline['monthly_expenses']
        
        monthly_rev_factor = (1 + revenue_growth / 100) ** (1/12)
        monthly_exp_factor = (1 + expense_growth / 100) ** (1/12)
        
        for i in range(months):
            current_revenue *= monthly_rev_factor
            current_expense *= monthly_exp_factor
            profit = current_revenue - current_expense
            
            monthly_projections.append({
                'month': i + 1,
                'revenue': round(current_revenue, 2),
                'expenses': round(current_expense, 2),
                'profit': round(profit, 2)
            })
        
        final_revenue = current_revenue * 12
        final_expense = current_expense * 12
        final_profit = final_revenue - final_expense
        
        risk = 'low' if revenue_growth > expense_growth else ('medium' if revenue_growth == expense_growth else 'high')
        
        recommendations = []
        if revenue_growth > expense_growth:
            recommendations.append('Positive growth trajectory - margins improving')
            recommendations.append('Consider reinvesting profits for further growth')
        else:
            recommendations.append('Warning: Expenses growing faster than revenue')
            recommendations.append('Review cost structure immediately')
        
        return ScenarioResult(
            name=f'Growth Scenario (Rev: {revenue_growth}%, Exp: {expense_growth}%)',
            parameters=parameters,
            projections={
                'projected_annual_revenue': round(final_revenue, 2),
                'projected_annual_expenses': round(final_expense, 2),
                'projected_profit': round(final_profit, 2),
                'monthly_projections': monthly_projections
            },
            impact_summary={
                'revenue_change': round(final_revenue - baseline['annual_revenue'], 2),
                'expense_change': round(final_expense - baseline['annual_expenses'], 2),
                'profit_change': round(final_profit - baseline['annual_profit'], 2)
            },
            risk_assessment=risk,
            recommendations=recommendations
        )

    def _breakeven_analysis(self, baseline: Dict, parameters: Dict) -> Dict[str, Any]:
        """Calculate break-even point"""
        fixed_costs = parameters.get('fixed_costs', baseline['annual_expenses'] * 0.6)
        variable_cost_ratio = parameters.get('variable_cost_ratio', 0.4)
        
        contribution_margin = 1 - variable_cost_ratio
        
        if contribution_margin > 0:
            breakeven_revenue = fixed_costs / contribution_margin
            breakeven_monthly = breakeven_revenue / 12
        else:
            breakeven_revenue = float('inf')
            breakeven_monthly = float('inf')
        
        current_status = 'above' if baseline['annual_revenue'] > breakeven_revenue else 'below'
        margin_of_safety = (baseline['annual_revenue'] - breakeven_revenue) / baseline['annual_revenue'] * 100 if baseline['annual_revenue'] > 0 else 0
        
        return {
            'breakeven_annual_revenue': round(breakeven_revenue, 2),
            'breakeven_monthly_revenue': round(breakeven_monthly, 2),
            'current_revenue': baseline['annual_revenue'],
            'status': current_status,
            'margin_of_safety_percent': round(margin_of_safety, 1),
            'fixed_costs': round(fixed_costs, 2),
            'variable_cost_ratio': variable_cost_ratio,
            'contribution_margin': round(contribution_margin, 2)
        }
```

---

## TASK 9: INSIGHTS GENERATOR SERVICE

### 9.1 Create Insights Generator

**File:** `backend/app/services/analytics/insights_generator.py`

```python
"""
Insights Generator Service
AI-powered business insights and recommendations
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict


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
            'generated_at': datetime.utcnow().isoformat(),
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
        
        week_ago = datetime.utcnow() - timedelta(days=7)
        two_weeks_ago = datetime.utcnow() - timedelta(days=14)
        
        this_week = self._get_period_metrics(transactions, week_ago, datetime.utcnow())
        last_week = self._get_period_metrics(transactions, two_weeks_ago, week_ago)
        
        revenue_change = self._calc_change(this_week['revenue'], last_week['revenue'])
        expense_change = self._calc_change(this_week['expenses'], last_week['expenses'])
        
        upcoming = [
            p for p in payments
            if p.get('status') == 'pending' and self._is_due_within_days(p.get('due_date'), 7)
        ]
        
        return {
            'period': 'Last 7 Days',
            'generated_at': datetime.utcnow().isoformat(),
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
        now = datetime.utcnow()
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
        
        current = self._get_period_metrics(transactions, datetime.utcnow() - timedelta(days=30), datetime.utcnow())
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
        
        current = self._get_period_metrics(transactions, datetime.utcnow() - timedelta(days=30), datetime.utcnow())
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
        cutoff = datetime.utcnow() - timedelta(days=months * 31)
        
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
            return datetime.utcnow() <= due <= datetime.utcnow() + timedelta(days=days)
        except (ValueError, AttributeError):
            return False

    def _is_overdue(self, due_date: str) -> bool:
        """Check if payment is overdue"""
        if not due_date:
            return False
        
        try:
            due = datetime.fromisoformat(due_date[:10])
            return datetime.utcnow() > due
        except (ValueError, AttributeError):
            return False

    def _generate_highlights(self, current: Dict, previous: Dict, rev_change: Dict, exp_change: Dict) -> List[str]:
        """Generate weekly highlights"""
        highlights = []
        
        if rev_change['percent'] > 10:
            highlights.append(f"🎉 Revenue up {rev_change['percent']:.1f}% from last week!")
        elif rev_change['percent'] < -10:
            highlights.append(f"⚠️ Revenue down {abs(rev_change['percent']):.1f}% from last week")
        
        if exp_change['percent'] < -5:
            highlights.append(f"💰 Expenses reduced by {abs(exp_change['percent']):.1f}%")
        elif exp_change['percent'] > 15:
            highlights.append(f"📊 Expenses increased {exp_change['percent']:.1f}% - review spending")
        
        if current['profit'] > 0 and previous['profit'] <= 0:
            highlights.append("✅ Returned to profitability this week!")
        
        return highlights[:3]
```

---

## Continue to Part 3 for API Routes and Frontend Components

---

*Phase 10 Tasks Part 2 - LogiAccounting Pro*
*Backend Analytics Services*
