"""
Cash Flow Forecaster
Predicts future cash flow using time series analysis
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import math

from app.utils.datetime_utils import utc_now


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
    - Statistical methods for time series forecasting
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

        # Generate forecast using statistical method
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
            generated_at=utc_now().isoformat(),
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
            'negative_days': len([v for v in predicted_values if v < 0]),
            'current_balance': current_balance,
            'projected_balance': round(cumulative, 2)
        }

    def _empty_forecast(self, days: int) -> CashFlowForecast:
        """Return empty forecast when no data available"""
        return CashFlowForecast(
            generated_at=utc_now().isoformat(),
            current_balance=0,
            forecast_days=days,
            model_type='none',
            confidence_level=0.95,
            predictions=[],
            scenarios={},
            summary={'message': 'Insufficient historical data for forecasting'}
        )
