"""
Cash Flow Predictor
Time series forecasting using Prophet
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import statistics

from ...config import get_ai_config
from ...models.prediction import CashFlowForecast

logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """Single day prediction"""
    date: date
    predicted_balance: float
    lower_bound: float
    upper_bound: float
    expected_inflows: float
    expected_outflows: float
    confidence: float


class CashFlowPredictor:
    """Cash flow prediction using time series analysis"""

    def __init__(self):
        self.config = get_ai_config()
        self._prophet_model = None

    def _prepare_data(self, transactions: List[Dict]) -> List[Dict]:
        """Prepare transaction data for Prophet"""
        daily_data = {}

        for txn in transactions:
            txn_date = txn.get('date')
            if isinstance(txn_date, str):
                txn_date = datetime.fromisoformat(txn_date).date()
            elif isinstance(txn_date, datetime):
                txn_date = txn_date.date()

            if txn_date not in daily_data:
                daily_data[txn_date] = {'inflows': 0, 'outflows': 0}

            amount = float(txn.get('amount', 0))
            if amount > 0:
                daily_data[txn_date]['inflows'] += amount
            else:
                daily_data[txn_date]['outflows'] += abs(amount)

        # Convert to list sorted by date
        result = []
        for d in sorted(daily_data.keys()):
            result.append({
                'ds': d,
                'inflows': daily_data[d]['inflows'],
                'outflows': daily_data[d]['outflows'],
                'y': daily_data[d]['inflows'] - daily_data[d]['outflows'],
            })

        return result

    def _simple_forecast(
        self,
        historical_data: List[Dict],
        horizon_days: int,
        current_balance: float,
    ) -> List[PredictionResult]:
        """Simple statistical forecast when Prophet is not available"""
        if not historical_data:
            return []

        # Calculate average daily flows
        inflows = [d['inflows'] for d in historical_data if d['inflows'] > 0]
        outflows = [d['outflows'] for d in historical_data if d['outflows'] > 0]

        avg_inflow = statistics.mean(inflows) if inflows else 0
        avg_outflow = statistics.mean(outflows) if outflows else 0
        std_inflow = statistics.stdev(inflows) if len(inflows) > 1 else avg_inflow * 0.2
        std_outflow = statistics.stdev(outflows) if len(outflows) > 1 else avg_outflow * 0.2

        # Weekly patterns (simple day-of-week adjustment)
        weekday_factors = {
            0: 1.1,  # Monday - higher activity
            1: 1.0,
            2: 1.0,
            3: 1.0,
            4: 1.2,  # Friday - higher activity
            5: 0.3,  # Saturday - lower
            6: 0.2,  # Sunday - lowest
        }

        predictions = []
        running_balance = current_balance
        start_date = date.today()

        for i in range(horizon_days):
            pred_date = start_date + timedelta(days=i + 1)
            factor = weekday_factors.get(pred_date.weekday(), 1.0)

            expected_inflow = avg_inflow * factor
            expected_outflow = avg_outflow * factor
            net_flow = expected_inflow - expected_outflow

            running_balance += net_flow

            predictions.append(PredictionResult(
                date=pred_date,
                predicted_balance=running_balance,
                lower_bound=running_balance - (std_inflow + std_outflow) * 1.5,
                upper_bound=running_balance + (std_inflow + std_outflow) * 1.5,
                expected_inflows=expected_inflow,
                expected_outflows=expected_outflow,
                confidence=0.7,
            ))

        return predictions

    def _prophet_forecast(
        self,
        historical_data: List[Dict],
        horizon_days: int,
        current_balance: float,
    ) -> List[PredictionResult]:
        """Forecast using Prophet model"""
        try:
            from prophet import Prophet
            import pandas as pd
        except ImportError:
            logger.warning("Prophet not available, using simple forecast")
            return self._simple_forecast(historical_data, horizon_days, current_balance)

        # Prepare dataframe
        df = pd.DataFrame(historical_data)
        df['ds'] = pd.to_datetime(df['ds'])

        # Train model
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            changepoint_prior_scale=0.05,
        )
        model.fit(df[['ds', 'y']])

        # Make future dataframe
        future = model.make_future_dataframe(periods=horizon_days)
        forecast = model.predict(future)

        # Extract predictions for future dates
        predictions = []
        running_balance = current_balance
        future_forecast = forecast.tail(horizon_days)

        for _, row in future_forecast.iterrows():
            pred_date = row['ds'].date()
            net_flow = row['yhat']
            running_balance += net_flow

            predictions.append(PredictionResult(
                date=pred_date,
                predicted_balance=running_balance,
                lower_bound=running_balance + row['yhat_lower'] - row['yhat'],
                upper_bound=running_balance + row['yhat_upper'] - row['yhat'],
                expected_inflows=max(0, net_flow),
                expected_outflows=max(0, -net_flow),
                confidence=0.85,
            ))

        return predictions

    def predict(
        self,
        tenant_id: str,
        transactions: List[Dict],
        current_balance: float,
        horizon_days: int = 30,
        use_prophet: bool = True,
    ) -> CashFlowForecast:
        """
        Generate cash flow forecast

        Args:
            tenant_id: Tenant ID
            transactions: Historical transaction data
            current_balance: Current account balance
            horizon_days: Number of days to forecast
            use_prophet: Whether to use Prophet (if available)

        Returns:
            CashFlowForecast with predictions
        """
        historical_data = self._prepare_data(transactions)

        if use_prophet:
            predictions = self._prophet_forecast(
                historical_data, horizon_days, current_balance
            )
        else:
            predictions = self._simple_forecast(
                historical_data, horizon_days, current_balance
            )

        # Calculate summary statistics
        balances = [p.predicted_balance for p in predictions]
        min_balance = min(balances) if balances else current_balance
        max_balance = max(balances) if balances else current_balance
        end_balance = balances[-1] if balances else current_balance

        # Identify risk factors
        risk_factors = []
        risk_score = 0.0

        if min_balance < 0:
            risk_factors.append({
                'type': 'negative_balance',
                'severity': 'high',
                'description': f'Balance may go negative (min: ${min_balance:,.2f})',
                'date': next((p.date.isoformat() for p in predictions if p.predicted_balance < 0), None),
            })
            risk_score += 0.4

        if min_balance < current_balance * 0.2:
            risk_factors.append({
                'type': 'low_balance',
                'severity': 'medium',
                'description': f'Balance may drop below 20% of current (${min_balance:,.2f})',
            })
            risk_score += 0.2

        if end_balance < current_balance * 0.5:
            risk_factors.append({
                'type': 'declining_trend',
                'severity': 'medium',
                'description': 'Cash flow showing significant decline trend',
            })
            risk_score += 0.2

        # Generate insights
        insights = []
        if end_balance > current_balance:
            insights.append(f"Cash position expected to improve by ${end_balance - current_balance:,.2f}")
        else:
            insights.append(f"Cash position expected to decrease by ${current_balance - end_balance:,.2f}")

        avg_confidence = statistics.mean([p.confidence for p in predictions]) if predictions else 0
        insights.append(f"Forecast confidence: {avg_confidence * 100:.0f}%")

        # Generate recommendations
        recommendations = []
        if min_balance < current_balance * 0.3:
            recommendations.append({
                'type': 'accelerate_collections',
                'priority': 'high',
                'description': 'Consider accelerating accounts receivable collections',
            })

        if risk_score > 0.3:
            recommendations.append({
                'type': 'defer_payments',
                'priority': 'medium',
                'description': 'Consider deferring non-critical payments where possible',
            })

        # Create forecast record
        forecast = CashFlowForecast(
            tenant_id=tenant_id,
            forecast_date=date.today(),
            horizon_days=horizon_days,
            current_balance=current_balance,
            daily_predictions=[
                {
                    'date': p.date.isoformat(),
                    'predicted_balance': p.predicted_balance,
                    'lower_bound': p.lower_bound,
                    'upper_bound': p.upper_bound,
                    'expected_inflows': p.expected_inflows,
                    'expected_outflows': p.expected_outflows,
                    'confidence': p.confidence,
                }
                for p in predictions
            ],
            predicted_min_balance=min_balance,
            predicted_max_balance=max_balance,
            predicted_end_balance=end_balance,
            risk_score=min(1.0, risk_score),
            risk_factors=risk_factors,
            insights=insights,
            recommendations=recommendations,
            model_name='prophet' if use_prophet else 'simple_statistical',
        )

        forecast.save()
        return forecast
