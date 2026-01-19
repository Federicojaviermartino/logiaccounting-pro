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
