"""
Cash Flow Predictor
Main predictor class for cash flow forecasting
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import logging

from app.utils.datetime_utils import utc_now
from app.ai.base import AIResult, Prediction, PredictionConfidence, BasePredictor

logger = logging.getLogger(__name__)


@dataclass
class CashFlowForecast:
    """Single day forecast."""
    date: str
    predicted_balance: float
    predicted_inflows: float
    predicted_outflows: float
    confidence_low: float
    confidence_high: float
    confidence_level: str = "medium"
    contributing_factors: List[str] = field(default_factory=list)


@dataclass
class CashFlowSummary:
    """Summary of cash flow forecast."""
    starting_balance: float
    ending_balance: float
    total_inflows: float
    total_outflows: float
    net_change: float
    trend: str  # "increasing", "decreasing", "stable"
    lowest_point: Dict = field(default_factory=dict)
    highest_point: Dict = field(default_factory=dict)
    avg_daily_change: float = 0.0


@dataclass
class CashFlowAlert:
    """Cash flow alert."""
    type: str  # "low_balance", "negative_balance", "large_outflow", "unusual_pattern"
    severity: str
    date: str
    message: str
    details: Dict = field(default_factory=dict)


class CashFlowPredictor(BasePredictor):
    """Predicts future cash flow based on historical data."""

    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._trained: Dict[str, bool] = {}
        self._last_training: Dict[str, datetime] = {}
        self._feature_engine = None

    async def train(
        self,
        customer_id: str,
        historical_data: List[Dict],
        current_balance: float,
        **kwargs,
    ) -> AIResult:
        """Train cash flow prediction model."""
        try:
            if len(historical_data) < 30:
                return AIResult.fail("Insufficient historical data (minimum 30 days required)")

            # Convert to DataFrame
            df = pd.DataFrame(historical_data)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")

            # Calculate daily net flow
            if "net_flow" not in df.columns:
                df["net_flow"] = df.get("inflows", 0) - df.get("outflows", 0)

            # Store training data
            self._models[customer_id] = {
                "historical_data": df,
                "current_balance": current_balance,
                "mean_inflows": df["inflows"].mean() if "inflows" in df.columns else 0,
                "mean_outflows": df["outflows"].mean() if "outflows" in df.columns else 0,
                "std_inflows": df["inflows"].std() if "inflows" in df.columns else 0,
                "std_outflows": df["outflows"].std() if "outflows" in df.columns else 0,
                "day_of_week_pattern": self._calculate_dow_pattern(df),
                "day_of_month_pattern": self._calculate_dom_pattern(df),
            }

            self._trained[customer_id] = True
            self._last_training[customer_id] = utc_now()

            return AIResult.ok({
                "status": "trained",
                "data_points": len(df),
                "date_range": {
                    "start": df["date"].min().isoformat(),
                    "end": df["date"].max().isoformat(),
                },
            })

        except Exception as e:
            logger.error(f"Training failed: {e}")
            return AIResult.fail(str(e))

    def _calculate_dow_pattern(self, df: pd.DataFrame) -> Dict:
        """Calculate day of week patterns."""
        df = df.copy()
        df["dow"] = df["date"].dt.dayofweek

        patterns = {}
        for dow in range(7):
            dow_data = df[df["dow"] == dow]
            if len(dow_data) > 0:
                patterns[dow] = {
                    "inflows_factor": dow_data["inflows"].mean() / df["inflows"].mean() if df["inflows"].mean() > 0 else 1,
                    "outflows_factor": dow_data["outflows"].mean() / df["outflows"].mean() if df["outflows"].mean() > 0 else 1,
                }
            else:
                patterns[dow] = {"inflows_factor": 1, "outflows_factor": 1}

        return patterns

    def _calculate_dom_pattern(self, df: pd.DataFrame) -> Dict:
        """Calculate day of month patterns."""
        df = df.copy()
        df["dom"] = df["date"].dt.day

        patterns = {}
        for dom in range(1, 32):
            dom_data = df[df["dom"] == dom]
            if len(dom_data) > 0:
                patterns[dom] = {
                    "inflows_factor": dom_data["inflows"].mean() / df["inflows"].mean() if df["inflows"].mean() > 0 else 1,
                    "outflows_factor": dom_data["outflows"].mean() / df["outflows"].mean() if df["outflows"].mean() > 0 else 1,
                }
            else:
                patterns[dom] = {"inflows_factor": 1, "outflows_factor": 1}

        return patterns

    async def predict(
        self,
        customer_id: str,
        horizon_days: int = 30,
        scenario: str = "expected",
        include_pending: bool = True,
        pending_transactions: List[Dict] = None,
        recurring_transactions: List[Dict] = None,
        **kwargs,
    ) -> AIResult:
        """Generate cash flow forecast."""
        try:
            if customer_id not in self._trained or not self._trained[customer_id]:
                return AIResult.fail("Model not trained for this customer")

            model_data = self._models[customer_id]
            current_balance = model_data["current_balance"]

            # Generate predictions
            forecasts = []
            running_balance = current_balance
            start_date = utc_now().date()

            # Scenario adjustments
            scenario_factors = {
                "expected": (1.0, 1.0),
                "optimistic": (1.15, 0.9),
                "pessimistic": (0.85, 1.15),
            }
            inflow_factor, outflow_factor = scenario_factors.get(scenario, (1.0, 1.0))

            for day_offset in range(horizon_days):
                forecast_date = start_date + timedelta(days=day_offset)
                dow = forecast_date.weekday()
                dom = forecast_date.day

                # Base predictions
                dow_pattern = model_data["day_of_week_pattern"].get(dow, {"inflows_factor": 1, "outflows_factor": 1})
                dom_pattern = model_data["day_of_month_pattern"].get(dom, {"inflows_factor": 1, "outflows_factor": 1})

                predicted_inflows = (
                    model_data["mean_inflows"]
                    * dow_pattern["inflows_factor"]
                    * dom_pattern["inflows_factor"]
                    * inflow_factor
                )

                predicted_outflows = (
                    model_data["mean_outflows"]
                    * dow_pattern["outflows_factor"]
                    * dom_pattern["outflows_factor"]
                    * outflow_factor
                )

                # Add pending transactions
                if include_pending and pending_transactions:
                    for tx in pending_transactions:
                        tx_date = datetime.fromisoformat(tx["date"]).date() if isinstance(tx["date"], str) else tx["date"]
                        if tx_date == forecast_date:
                            if tx.get("type") == "inflow":
                                predicted_inflows += tx.get("amount", 0)
                            else:
                                predicted_outflows += tx.get("amount", 0)

                # Add recurring transactions
                if recurring_transactions:
                    for tx in recurring_transactions:
                        if self._matches_recurring(tx, forecast_date):
                            if tx.get("type") == "inflow":
                                predicted_inflows += tx.get("amount", 0)
                            else:
                                predicted_outflows += tx.get("amount", 0)

                # Update running balance
                net_change = predicted_inflows - predicted_outflows
                running_balance += net_change

                # Confidence intervals
                std_factor = 1 + (day_offset / horizon_days)  # Uncertainty grows over time
                confidence_range = (model_data["std_inflows"] + model_data["std_outflows"]) * std_factor

                confidence_level = "high" if day_offset < 7 else "medium" if day_offset < 21 else "low"

                forecasts.append(CashFlowForecast(
                    date=forecast_date.isoformat(),
                    predicted_balance=round(running_balance, 2),
                    predicted_inflows=round(predicted_inflows, 2),
                    predicted_outflows=round(predicted_outflows, 2),
                    confidence_low=round(running_balance - confidence_range, 2),
                    confidence_high=round(running_balance + confidence_range, 2),
                    confidence_level=confidence_level,
                ))

            # Generate summary
            summary = self._generate_summary(forecasts, current_balance)

            # Generate alerts
            alerts = self._generate_alerts(forecasts, current_balance)

            return AIResult.ok({
                "forecast": [f.__dict__ for f in forecasts],
                "summary": summary.__dict__,
                "alerts": [a.__dict__ for a in alerts],
            })

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return AIResult.fail(str(e))

    def _matches_recurring(self, tx: Dict, date: datetime.date) -> bool:
        """Check if a recurring transaction matches the date."""
        frequency = tx.get("frequency", "monthly")
        tx_day = tx.get("day", 1)

        if frequency == "daily":
            return True
        elif frequency == "weekly":
            return date.weekday() == tx_day
        elif frequency == "monthly":
            return date.day == tx_day
        elif frequency == "yearly":
            return date.day == tx_day and date.month == tx.get("month", 1)

        return False

    def _generate_summary(self, forecasts: List[CashFlowForecast], starting_balance: float) -> CashFlowSummary:
        """Generate forecast summary."""
        if not forecasts:
            return CashFlowSummary(
                starting_balance=starting_balance,
                ending_balance=starting_balance,
                total_inflows=0,
                total_outflows=0,
                net_change=0,
                trend="stable",
            )

        total_inflows = sum(f.predicted_inflows for f in forecasts)
        total_outflows = sum(f.predicted_outflows for f in forecasts)
        ending_balance = forecasts[-1].predicted_balance

        # Find lowest and highest points
        min_forecast = min(forecasts, key=lambda f: f.predicted_balance)
        max_forecast = max(forecasts, key=lambda f: f.predicted_balance)

        # Determine trend
        if ending_balance > starting_balance * 1.05:
            trend = "increasing"
        elif ending_balance < starting_balance * 0.95:
            trend = "decreasing"
        else:
            trend = "stable"

        return CashFlowSummary(
            starting_balance=starting_balance,
            ending_balance=ending_balance,
            total_inflows=round(total_inflows, 2),
            total_outflows=round(total_outflows, 2),
            net_change=round(ending_balance - starting_balance, 2),
            trend=trend,
            lowest_point={"date": min_forecast.date, "balance": min_forecast.predicted_balance},
            highest_point={"date": max_forecast.date, "balance": max_forecast.predicted_balance},
            avg_daily_change=round((ending_balance - starting_balance) / len(forecasts), 2),
        )

    def _generate_alerts(self, forecasts: List[CashFlowForecast], current_balance: float) -> List[CashFlowAlert]:
        """Generate alerts for potential issues."""
        alerts = []
        low_balance_threshold = current_balance * 0.2

        for forecast in forecasts:
            # Negative balance
            if forecast.predicted_balance < 0:
                alerts.append(CashFlowAlert(
                    type="negative_balance",
                    severity="critical",
                    date=forecast.date,
                    message=f"Predicted negative balance of ${forecast.predicted_balance:,.2f}",
                    details={"predicted_balance": forecast.predicted_balance},
                ))
            # Low balance
            elif forecast.predicted_balance < low_balance_threshold:
                alerts.append(CashFlowAlert(
                    type="low_balance",
                    severity="warning",
                    date=forecast.date,
                    message=f"Cash balance may drop to ${forecast.predicted_balance:,.2f}",
                    details={"predicted_balance": forecast.predicted_balance, "threshold": low_balance_threshold},
                ))

        return alerts[:10]  # Limit alerts

    def get_model_info(self, customer_id: str = None) -> Dict:
        """Get model information."""
        if customer_id:
            return {
                "trained": self._trained.get(customer_id, False),
                "last_training": self._last_training.get(customer_id, None),
            }
        return {
            "total_models": len(self._trained),
            "trained_customers": list(self._trained.keys()),
        }


# Global predictor instance
cashflow_predictor = CashFlowPredictor()
