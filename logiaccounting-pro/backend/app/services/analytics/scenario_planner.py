"""
Scenario Planner Service
What-if analysis and business scenario modeling
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

from app.utils.datetime_utils import utc_now


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
            'generated_at': utc_now().isoformat(),
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
            'generated_at': utc_now().isoformat(),
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

    def get_scenario_comparison(self, scenarios: List[Dict]) -> Dict[str, Any]:
        """Compare multiple scenarios"""
        transactions = self.db.transactions.find_all()
        baseline = self._calculate_baseline(transactions)

        results = []
        for scenario in scenarios:
            scenario_type = scenario.get('type', 'growth')
            parameters = scenario.get('parameters', {})

            if scenario_type == 'revenue_change':
                result = self._revenue_change_scenario(baseline, parameters)
            elif scenario_type == 'expense_change':
                result = self._expense_change_scenario(baseline, parameters)
            elif scenario_type == 'growth':
                result = self._growth_scenario(baseline, parameters)
            else:
                continue

            results.append({
                'name': scenario.get('name', result.name),
                'result': asdict(result)
            })

        return {
            'generated_at': utc_now().isoformat(),
            'baseline': baseline,
            'scenarios': results
        }

    def _calculate_baseline(self, transactions: List[Dict]) -> Dict[str, float]:
        """Calculate baseline metrics from last 12 months"""
        year_ago = utc_now() - timedelta(days=365)

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
