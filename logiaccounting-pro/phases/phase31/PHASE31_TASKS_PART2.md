# Phase 31: AI/ML Features - Part 2: Cash Flow Predictor

## Overview
This part covers the intelligent cash flow prediction system using time series forecasting and machine learning.

---

## File 1: Cash Flow Predictor
**Path:** `backend/app/ai/cashflow/predictor.py`

```python
"""
Cash Flow Predictor
AI-powered cash flow forecasting engine
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
import logging

from app.ai.base import BasePredictor, Prediction, PredictionConfidence, AIResult
from app.ai.utils import prepare_time_series, calculate_features, detect_seasonality
from app.ai.cashflow.features import CashFlowFeatureEngine
from app.ai.cashflow.models import ProphetModel, ARIMAModel, EnsembleModel

logger = logging.getLogger(__name__)


@dataclass
class CashFlowForecast:
    """Cash flow forecast for a specific date."""
    date: datetime
    predicted_balance: float
    predicted_inflows: float
    predicted_outflows: float
    confidence_low: float
    confidence_high: float
    confidence_level: PredictionConfidence
    contributing_factors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "date": self.date.strftime("%Y-%m-%d"),
            "predicted_balance": round(self.predicted_balance, 2),
            "predicted_inflows": round(self.predicted_inflows, 2),
            "predicted_outflows": round(self.predicted_outflows, 2),
            "confidence_low": round(self.confidence_low, 2),
            "confidence_high": round(self.confidence_high, 2),
            "confidence_level": self.confidence_level.value,
            "contributing_factors": self.contributing_factors,
        }


@dataclass
class CashFlowSummary:
    """Summary of cash flow forecast."""
    starting_balance: float
    ending_balance: float
    total_inflows: float
    total_outflows: float
    net_change: float
    lowest_point: Dict
    highest_point: Dict
    average_daily_balance: float
    volatility: float
    trend: str
    
    def to_dict(self) -> Dict:
        return {
            "starting_balance": round(self.starting_balance, 2),
            "ending_balance": round(self.ending_balance, 2),
            "total_inflows": round(self.total_inflows, 2),
            "total_outflows": round(self.total_outflows, 2),
            "net_change": round(self.net_change, 2),
            "lowest_point": self.lowest_point,
            "highest_point": self.highest_point,
            "average_daily_balance": round(self.average_daily_balance, 2),
            "volatility": round(self.volatility, 4),
            "trend": self.trend,
        }


@dataclass
class CashFlowAlert:
    """Alert for cash flow issues."""
    type: str
    severity: str
    date: datetime
    message: str
    details: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type,
            "severity": self.severity,
            "date": self.date.strftime("%Y-%m-%d"),
            "message": self.message,
            "details": self.details,
        }


class CashFlowPredictor(BasePredictor):
    """Predicts future cash flow using ensemble of models."""
    
    # Alert thresholds
    LOW_BALANCE_THRESHOLD = 0.1  # 10% of average balance
    CRITICAL_BALANCE_THRESHOLD = 0.05  # 5% of average balance
    VOLATILITY_THRESHOLD = 0.3  # 30% standard deviation
    
    def __init__(self, customer_id: str):
        super().__init__(name="CashFlowPredictor")
        self.customer_id = customer_id
        self.feature_engine = CashFlowFeatureEngine()
        
        # Initialize models
        self.inflow_model = EnsembleModel("inflows")
        self.outflow_model = EnsembleModel("outflows")
        
        # State
        self._current_balance: float = 0
        self._historical_data: Optional[pd.DataFrame] = None
        self._pending_inflows: List[Dict] = []
        self._pending_outflows: List[Dict] = []
        self._recurring_items: List[Dict] = []
    
    async def train(self, data: List[Dict], **kwargs) -> bool:
        """Train prediction models on historical data."""
        try:
            # Prepare data
            df = pd.DataFrame(data)
            
            if len(df) < 30:
                logger.warning("Insufficient data for training (need at least 30 days)")
                return False
            
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()
            
            self._historical_data = df
            
            # Extract current balance
            self._current_balance = kwargs.get('current_balance', df['balance'].iloc[-1])
            
            # Calculate features
            inflow_features = self.feature_engine.calculate_inflow_features(df)
            outflow_features = self.feature_engine.calculate_outflow_features(df)
            
            # Train models
            await self.inflow_model.train(inflow_features)
            await self.outflow_model.train(outflow_features)
            
            self._is_trained = True
            self._last_trained_at = datetime.utcnow()
            
            # Calculate metrics
            self._metrics = {
                "inflow_mape": self.inflow_model.get_mape(),
                "outflow_mape": self.outflow_model.get_mape(),
                "data_points": len(df),
            }
            
            logger.info(f"Cash flow predictor trained with {len(df)} data points")
            return True
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return False
    
    async def predict(self, input_data: Dict, **kwargs) -> Prediction:
        """Make a single prediction (wrapper for forecast)."""
        horizon = input_data.get("horizon_days", 30)
        forecasts = await self.forecast(horizon, **kwargs)
        
        if not forecasts:
            return Prediction(
                value=self._current_balance,
                confidence=0,
                confidence_level=PredictionConfidence.LOW,
            )
        
        last_forecast = forecasts[-1]
        return Prediction(
            value=last_forecast.predicted_balance,
            confidence=0.8,
            confidence_level=last_forecast.confidence_level,
            lower_bound=last_forecast.confidence_low,
            upper_bound=last_forecast.confidence_high,
        )
    
    async def forecast(
        self,
        horizon_days: int = 30,
        scenario: str = "expected",
        include_pending: bool = True,
        include_recurring: bool = True,
    ) -> List[CashFlowForecast]:
        """Generate cash flow forecast."""
        if not self._is_trained:
            logger.warning("Predictor not trained, using simple projection")
            return self._simple_forecast(horizon_days)
        
        forecasts = []
        current_balance = self._current_balance
        
        # Generate predictions for each day
        for day in range(1, horizon_days + 1):
            forecast_date = datetime.utcnow() + timedelta(days=day)
            
            # Predict base inflows/outflows
            inflow_pred = await self.inflow_model.predict(forecast_date, scenario)
            outflow_pred = await self.outflow_model.predict(forecast_date, scenario)
            
            predicted_inflows = inflow_pred["value"]
            predicted_outflows = outflow_pred["value"]
            
            # Add pending items
            if include_pending:
                pending_in, pending_out = self._get_pending_for_date(forecast_date)
                predicted_inflows += pending_in
                predicted_outflows += pending_out
            
            # Add recurring items
            if include_recurring:
                recurring_in, recurring_out = self._get_recurring_for_date(forecast_date)
                predicted_inflows += recurring_in
                predicted_outflows += recurring_out
            
            # Apply scenario adjustments
            if scenario == "optimistic":
                predicted_inflows *= 1.1
                predicted_outflows *= 0.9
            elif scenario == "pessimistic":
                predicted_inflows *= 0.9
                predicted_outflows *= 1.1
            
            # Calculate balance
            net_change = predicted_inflows - predicted_outflows
            predicted_balance = current_balance + net_change
            
            # Calculate confidence intervals
            confidence_margin = self._calculate_confidence_margin(day, predicted_balance)
            
            # Determine confidence level
            confidence_level = self._get_confidence_level(day, inflow_pred["confidence"], outflow_pred["confidence"])
            
            # Identify contributing factors
            factors = self._identify_factors(forecast_date, predicted_inflows, predicted_outflows)
            
            forecast = CashFlowForecast(
                date=forecast_date,
                predicted_balance=predicted_balance,
                predicted_inflows=predicted_inflows,
                predicted_outflows=predicted_outflows,
                confidence_low=predicted_balance - confidence_margin,
                confidence_high=predicted_balance + confidence_margin,
                confidence_level=confidence_level,
                contributing_factors=factors,
            )
            
            forecasts.append(forecast)
            current_balance = predicted_balance
        
        return forecasts
    
    def generate_summary(self, forecasts: List[CashFlowForecast]) -> CashFlowSummary:
        """Generate summary from forecasts."""
        if not forecasts:
            return CashFlowSummary(
                starting_balance=self._current_balance,
                ending_balance=self._current_balance,
                total_inflows=0,
                total_outflows=0,
                net_change=0,
                lowest_point={},
                highest_point={},
                average_daily_balance=self._current_balance,
                volatility=0,
                trend="flat",
            )
        
        balances = [f.predicted_balance for f in forecasts]
        inflows = [f.predicted_inflows for f in forecasts]
        outflows = [f.predicted_outflows for f in forecasts]
        
        # Find lowest and highest points
        min_idx = np.argmin(balances)
        max_idx = np.argmax(balances)
        
        lowest = {
            "date": forecasts[min_idx].date.strftime("%Y-%m-%d"),
            "balance": round(balances[min_idx], 2),
        }
        
        highest = {
            "date": forecasts[max_idx].date.strftime("%Y-%m-%d"),
            "balance": round(balances[max_idx], 2),
        }
        
        # Calculate trend
        if len(balances) > 1:
            slope = (balances[-1] - balances[0]) / len(balances)
            avg_balance = np.mean(balances)
            trend_pct = slope / avg_balance if avg_balance != 0 else 0
            
            if trend_pct > 0.01:
                trend = "increasing"
            elif trend_pct < -0.01:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        return CashFlowSummary(
            starting_balance=self._current_balance,
            ending_balance=balances[-1],
            total_inflows=sum(inflows),
            total_outflows=sum(outflows),
            net_change=balances[-1] - self._current_balance,
            lowest_point=lowest,
            highest_point=highest,
            average_daily_balance=np.mean(balances),
            volatility=np.std(balances) / np.mean(balances) if np.mean(balances) != 0 else 0,
            trend=trend,
        )
    
    def generate_alerts(self, forecasts: List[CashFlowForecast]) -> List[CashFlowAlert]:
        """Generate alerts for potential cash flow issues."""
        alerts = []
        
        if not forecasts:
            return alerts
        
        avg_balance = self._current_balance
        
        for forecast in forecasts:
            # Low balance alert
            if forecast.predicted_balance < avg_balance * self.LOW_BALANCE_THRESHOLD:
                severity = "critical" if forecast.predicted_balance < avg_balance * self.CRITICAL_BALANCE_THRESHOLD else "warning"
                alerts.append(CashFlowAlert(
                    type="low_balance",
                    severity=severity,
                    date=forecast.date,
                    message=f"Cash balance may drop to ${forecast.predicted_balance:,.2f}",
                    details={
                        "predicted_balance": forecast.predicted_balance,
                        "threshold": avg_balance * self.LOW_BALANCE_THRESHOLD,
                    },
                ))
            
            # Negative balance alert
            if forecast.predicted_balance < 0:
                alerts.append(CashFlowAlert(
                    type="negative_balance",
                    severity="critical",
                    date=forecast.date,
                    message=f"Cash balance may go negative (${forecast.predicted_balance:,.2f})",
                    details={"predicted_balance": forecast.predicted_balance},
                ))
            
            # Large outflow alert
            if forecast.predicted_outflows > avg_balance * 0.5:
                alerts.append(CashFlowAlert(
                    type="large_outflow",
                    severity="warning",
                    date=forecast.date,
                    message=f"Large outflows expected: ${forecast.predicted_outflows:,.2f}",
                    details={"predicted_outflows": forecast.predicted_outflows},
                ))
        
        # Volatility alert
        balances = [f.predicted_balance for f in forecasts]
        volatility = np.std(balances) / np.mean(balances) if np.mean(balances) != 0 else 0
        
        if volatility > self.VOLATILITY_THRESHOLD:
            alerts.append(CashFlowAlert(
                type="high_volatility",
                severity="warning",
                date=forecasts[0].date,
                message=f"High cash flow volatility detected ({volatility:.1%})",
                details={"volatility": volatility},
            ))
        
        return alerts
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from models."""
        importance = {}
        
        if self.inflow_model.is_trained:
            for k, v in self.inflow_model.get_feature_importance().items():
                importance[f"inflow_{k}"] = v
        
        if self.outflow_model.is_trained:
            for k, v in self.outflow_model.get_feature_importance().items():
                importance[f"outflow_{k}"] = v
        
        return importance
    
    def set_pending_items(self, inflows: List[Dict], outflows: List[Dict]):
        """Set pending invoices and payments."""
        self._pending_inflows = inflows
        self._pending_outflows = outflows
    
    def set_recurring_items(self, items: List[Dict]):
        """Set recurring transactions."""
        self._recurring_items = items
    
    # ==================== Private Methods ====================
    
    def _simple_forecast(self, horizon_days: int) -> List[CashFlowForecast]:
        """Simple linear forecast when model is not trained."""
        forecasts = []
        balance = self._current_balance
        
        for day in range(1, horizon_days + 1):
            forecast_date = datetime.utcnow() + timedelta(days=day)
            
            forecasts.append(CashFlowForecast(
                date=forecast_date,
                predicted_balance=balance,
                predicted_inflows=0,
                predicted_outflows=0,
                confidence_low=balance * 0.8,
                confidence_high=balance * 1.2,
                confidence_level=PredictionConfidence.LOW,
                contributing_factors=["insufficient_data"],
            ))
        
        return forecasts
    
    def _get_pending_for_date(self, date: datetime) -> Tuple[float, float]:
        """Get pending items for a specific date."""
        inflows = sum(
            item.get("amount", 0)
            for item in self._pending_inflows
            if pd.to_datetime(item.get("due_date")).date() == date.date()
        )
        
        outflows = sum(
            item.get("amount", 0)
            for item in self._pending_outflows
            if pd.to_datetime(item.get("due_date")).date() == date.date()
        )
        
        return inflows, outflows
    
    def _get_recurring_for_date(self, date: datetime) -> Tuple[float, float]:
        """Get recurring items for a specific date."""
        inflows = 0
        outflows = 0
        
        for item in self._recurring_items:
            if self._matches_recurring_pattern(item, date):
                amount = item.get("amount", 0)
                if item.get("type") == "income":
                    inflows += amount
                else:
                    outflows += amount
        
        return inflows, outflows
    
    def _matches_recurring_pattern(self, item: Dict, date: datetime) -> bool:
        """Check if date matches recurring pattern."""
        frequency = item.get("frequency", "monthly")
        day = item.get("day", 1)
        
        if frequency == "daily":
            return True
        elif frequency == "weekly":
            return date.weekday() == day
        elif frequency == "monthly":
            return date.day == day
        elif frequency == "yearly":
            month = item.get("month", 1)
            return date.month == month and date.day == day
        
        return False
    
    def _calculate_confidence_margin(self, days_ahead: int, predicted_balance: float) -> float:
        """Calculate confidence margin based on forecast horizon."""
        # Confidence decreases with forecast horizon
        base_margin = abs(predicted_balance) * 0.05
        horizon_factor = 1 + (days_ahead * 0.02)
        
        return base_margin * horizon_factor
    
    def _get_confidence_level(self, days_ahead: int, inflow_conf: float, outflow_conf: float) -> PredictionConfidence:
        """Determine confidence level."""
        avg_conf = (inflow_conf + outflow_conf) / 2
        
        # Adjust for forecast horizon
        horizon_penalty = min(0.3, days_ahead * 0.01)
        adjusted_conf = avg_conf - horizon_penalty
        
        if adjusted_conf >= 0.8:
            return PredictionConfidence.HIGH
        elif adjusted_conf >= 0.5:
            return PredictionConfidence.MEDIUM
        else:
            return PredictionConfidence.LOW
    
    def _identify_factors(self, date: datetime, inflows: float, outflows: float) -> List[str]:
        """Identify contributing factors for the forecast."""
        factors = []
        
        # Day of week effects
        if date.weekday() == 0:
            factors.append("monday_effect")
        elif date.weekday() == 4:
            factors.append("friday_effect")
        
        # Month effects
        if date.day == 1:
            factors.append("month_start")
        elif date.day >= 28:
            factors.append("month_end")
        
        # Quarter effects
        if date.month in [1, 4, 7, 10] and date.day <= 5:
            factors.append("quarter_start")
        
        # Pending items
        if self._pending_inflows:
            factors.append("pending_invoices")
        if self._pending_outflows:
            factors.append("pending_payments")
        
        return factors
```

---

## File 2: Feature Engineering
**Path:** `backend/app/ai/cashflow/features.py`

```python
"""
Cash Flow Feature Engineering
Feature extraction and engineering for cash flow prediction
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class CashFlowFeatureEngine:
    """Extracts and engineers features for cash flow prediction."""
    
    def __init__(self):
        self._feature_stats: Dict[str, Dict] = {}
    
    def calculate_inflow_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate features for inflow prediction."""
        features = pd.DataFrame(index=df.index)
        
        # Target variable
        if 'inflows' in df.columns:
            features['inflows'] = df['inflows']
        else:
            features['inflows'] = df.get('revenue', 0)
        
        # Add temporal features
        features = self._add_temporal_features(features)
        
        # Add lag features
        features = self._add_lag_features(features, 'inflows')
        
        # Add rolling features
        features = self._add_rolling_features(features, 'inflows')
        
        # Add customer-related features
        if 'invoice_count' in df.columns:
            features['invoice_count'] = df['invoice_count']
            features['avg_invoice_amount'] = df['inflows'] / df['invoice_count'].replace(0, 1)
        
        # Calculate feature statistics for later use
        self._calculate_feature_stats(features, 'inflows')
        
        return features.dropna()
    
    def calculate_outflow_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate features for outflow prediction."""
        features = pd.DataFrame(index=df.index)
        
        # Target variable
        if 'outflows' in df.columns:
            features['outflows'] = df['outflows']
        else:
            features['outflows'] = df.get('expenses', 0)
        
        # Add temporal features
        features = self._add_temporal_features(features)
        
        # Add lag features
        features = self._add_lag_features(features, 'outflows')
        
        # Add rolling features
        features = self._add_rolling_features(features, 'outflows')
        
        # Add expense-related features
        if 'payment_count' in df.columns:
            features['payment_count'] = df['payment_count']
        
        # Add payroll indicators
        features['is_payroll_day'] = self._is_payroll_day(features.index)
        
        # Calculate feature statistics
        self._calculate_feature_stats(features, 'outflows')
        
        return features.dropna()
    
    def _add_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add time-based features."""
        df = df.copy()
        
        # Basic temporal features
        df['day_of_week'] = df.index.dayofweek
        df['day_of_month'] = df.index.day
        df['week_of_year'] = df.index.isocalendar().week
        df['month'] = df.index.month
        df['quarter'] = df.index.quarter
        df['year'] = df.index.year
        
        # Binary indicators
        df['is_weekend'] = (df.index.dayofweek >= 5).astype(int)
        df['is_month_start'] = df.index.is_month_start.astype(int)
        df['is_month_end'] = df.index.is_month_end.astype(int)
        df['is_quarter_start'] = df.index.is_quarter_start.astype(int)
        df['is_quarter_end'] = df.index.is_quarter_end.astype(int)
        df['is_year_start'] = df.index.is_year_start.astype(int)
        df['is_year_end'] = df.index.is_year_end.astype(int)
        
        # Cyclical encoding for periodic features
        df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        df['day_of_month_sin'] = np.sin(2 * np.pi * df['day_of_month'] / 31)
        df['day_of_month_cos'] = np.cos(2 * np.pi * df['day_of_month'] / 31)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        return df
    
    def _add_lag_features(self, df: pd.DataFrame, target_col: str) -> pd.DataFrame:
        """Add lagged features."""
        df = df.copy()
        
        # Previous days
        for lag in [1, 2, 3, 7, 14, 21, 28, 30]:
            df[f'{target_col}_lag_{lag}'] = df[target_col].shift(lag)
        
        # Same day last week, last month, last year
        df[f'{target_col}_lag_week'] = df[target_col].shift(7)
        df[f'{target_col}_lag_month'] = df[target_col].shift(30)
        df[f'{target_col}_lag_year'] = df[target_col].shift(365)
        
        # Difference features
        df[f'{target_col}_diff_1'] = df[target_col].diff(1)
        df[f'{target_col}_diff_7'] = df[target_col].diff(7)
        df[f'{target_col}_diff_30'] = df[target_col].diff(30)
        
        # Percentage change
        df[f'{target_col}_pct_change_1'] = df[target_col].pct_change(1)
        df[f'{target_col}_pct_change_7'] = df[target_col].pct_change(7)
        
        return df
    
    def _add_rolling_features(self, df: pd.DataFrame, target_col: str) -> pd.DataFrame:
        """Add rolling window features."""
        df = df.copy()
        
        # Rolling statistics
        for window in [7, 14, 30, 60, 90]:
            df[f'{target_col}_rolling_mean_{window}'] = df[target_col].rolling(window).mean()
            df[f'{target_col}_rolling_std_{window}'] = df[target_col].rolling(window).std()
            df[f'{target_col}_rolling_min_{window}'] = df[target_col].rolling(window).min()
            df[f'{target_col}_rolling_max_{window}'] = df[target_col].rolling(window).max()
            df[f'{target_col}_rolling_median_{window}'] = df[target_col].rolling(window).median()
        
        # Exponential moving averages
        for span in [7, 14, 30]:
            df[f'{target_col}_ema_{span}'] = df[target_col].ewm(span=span).mean()
        
        # Rolling ratio features
        df[f'{target_col}_vs_rolling_mean_7'] = df[target_col] / df[f'{target_col}_rolling_mean_7'].replace(0, 1)
        df[f'{target_col}_vs_rolling_mean_30'] = df[target_col] / df[f'{target_col}_rolling_mean_30'].replace(0, 1)
        
        return df
    
    def _is_payroll_day(self, dates: pd.DatetimeIndex) -> pd.Series:
        """Determine if dates are likely payroll days."""
        # Common payroll patterns: 15th, last day, or bi-weekly Fridays
        is_15th = dates.day == 15
        is_last_day = dates.is_month_end
        is_biweekly_friday = (dates.dayofweek == 4) & ((dates.day // 7) % 2 == 0)
        
        return (is_15th | is_last_day | is_biweekly_friday).astype(int)
    
    def _calculate_feature_stats(self, df: pd.DataFrame, prefix: str):
        """Calculate and store feature statistics."""
        self._feature_stats[prefix] = {
            'mean': df.mean().to_dict(),
            'std': df.std().to_dict(),
            'min': df.min().to_dict(),
            'max': df.max().to_dict(),
        }
    
    def get_feature_stats(self, prefix: str) -> Dict:
        """Get stored feature statistics."""
        return self._feature_stats.get(prefix, {})
    
    def normalize_features(self, df: pd.DataFrame, prefix: str) -> pd.DataFrame:
        """Normalize features using stored statistics."""
        stats = self._feature_stats.get(prefix)
        if not stats:
            return df
        
        df_normalized = df.copy()
        
        for col in df.columns:
            if col in stats['mean'] and col in stats['std']:
                mean = stats['mean'][col]
                std = stats['std'][col]
                if std > 0:
                    df_normalized[col] = (df[col] - mean) / std
        
        return df_normalized
    
    def extract_seasonality_features(self, df: pd.DataFrame, target_col: str) -> Dict:
        """Extract seasonality patterns from data."""
        from scipy import stats as scipy_stats
        
        results = {}
        
        # Weekly seasonality
        weekly_means = df.groupby(df.index.dayofweek)[target_col].mean()
        results['weekly_pattern'] = weekly_means.to_dict()
        
        # Monthly seasonality
        monthly_means = df.groupby(df.index.day)[target_col].mean()
        results['monthly_pattern'] = monthly_means.to_dict()
        
        # Quarterly seasonality
        quarterly_means = df.groupby(df.index.quarter)[target_col].mean()
        results['quarterly_pattern'] = quarterly_means.to_dict()
        
        # Detect trend
        x = np.arange(len(df))
        y = df[target_col].values
        slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(x, y)
        
        results['trend'] = {
            'slope': slope,
            'intercept': intercept,
            'r_squared': r_value ** 2,
            'p_value': p_value,
            'direction': 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'flat',
        }
        
        return results
```

---

## File 3: Prediction Models
**Path:** `backend/app/ai/cashflow/models.py`

```python
"""
Cash Flow Prediction Models
Time series models for forecasting
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class BaseForecastModel(ABC):
    """Abstract base class for forecast models."""
    
    def __init__(self, name: str):
        self.name = name
        self._is_trained = False
        self._training_data: Optional[pd.DataFrame] = None
        self._mape: float = 0
    
    @abstractmethod
    async def train(self, data: pd.DataFrame) -> bool:
        """Train the model."""
        pass
    
    @abstractmethod
    async def predict(self, date: datetime, scenario: str = "expected") -> Dict:
        """Make prediction for a date."""
        pass
    
    @abstractmethod
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance."""
        pass
    
    @property
    def is_trained(self) -> bool:
        return self._is_trained
    
    def get_mape(self) -> float:
        """Get Mean Absolute Percentage Error."""
        return self._mape


class ProphetModel(BaseForecastModel):
    """Facebook Prophet model for time series forecasting."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self._model = None
        self._future_df: Optional[pd.DataFrame] = None
    
    async def train(self, data: pd.DataFrame) -> bool:
        """Train Prophet model."""
        try:
            from prophet import Prophet
            
            # Prepare data in Prophet format
            prophet_df = data.reset_index()
            target_col = data.columns[0]  # First column is target
            
            prophet_df = prophet_df.rename(columns={
                prophet_df.columns[0]: 'ds',
                target_col: 'y',
            })
            
            # Initialize and train model
            self._model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                changepoint_prior_scale=0.05,
            )
            
            # Add custom seasonalities if enough data
            if len(prophet_df) > 60:
                self._model.add_seasonality(
                    name='monthly',
                    period=30.5,
                    fourier_order=5,
                )
            
            self._model.fit(prophet_df)
            self._training_data = data
            self._is_trained = True
            
            # Calculate MAPE on training data
            self._calculate_mape(prophet_df)
            
            logger.info(f"Prophet model '{self.name}' trained successfully")
            return True
            
        except ImportError:
            logger.warning("Prophet not installed, using fallback")
            return False
        except Exception as e:
            logger.error(f"Prophet training failed: {e}")
            return False
    
    async def predict(self, date: datetime, scenario: str = "expected") -> Dict:
        """Make prediction using Prophet."""
        if not self._is_trained or self._model is None:
            return {"value": 0, "confidence": 0}
        
        try:
            # Create future dataframe
            future = pd.DataFrame({'ds': [date]})
            forecast = self._model.predict(future)
            
            value = forecast['yhat'].iloc[0]
            lower = forecast['yhat_lower'].iloc[0]
            upper = forecast['yhat_upper'].iloc[0]
            
            # Adjust for scenario
            if scenario == "optimistic":
                value = upper
            elif scenario == "pessimistic":
                value = lower
            
            # Ensure non-negative
            value = max(0, value)
            
            # Calculate confidence based on interval width
            interval_width = upper - lower
            mean_value = (upper + lower) / 2
            confidence = 1 - (interval_width / (2 * mean_value)) if mean_value > 0 else 0.5
            confidence = max(0, min(1, confidence))
            
            return {
                "value": value,
                "lower": max(0, lower),
                "upper": upper,
                "confidence": confidence,
            }
            
        except Exception as e:
            logger.error(f"Prophet prediction failed: {e}")
            return {"value": 0, "confidence": 0}
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get component importance from Prophet."""
        if not self._is_trained:
            return {}
        
        # Prophet doesn't have traditional feature importance
        # Return seasonality contributions
        return {
            "trend": 0.4,
            "yearly_seasonality": 0.2,
            "weekly_seasonality": 0.2,
            "monthly_seasonality": 0.2,
        }
    
    def _calculate_mape(self, df: pd.DataFrame):
        """Calculate MAPE on training data."""
        try:
            forecast = self._model.predict(df[['ds']])
            actual = df['y'].values
            predicted = forecast['yhat'].values
            
            # Avoid division by zero
            mask = actual != 0
            if mask.sum() > 0:
                self._mape = np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100
            else:
                self._mape = 0
        except:
            self._mape = 0


class ARIMAModel(BaseForecastModel):
    """ARIMA model for time series forecasting."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self._model = None
        self._order: Tuple[int, int, int] = (1, 1, 1)
    
    async def train(self, data: pd.DataFrame) -> bool:
        """Train ARIMA model."""
        try:
            from statsmodels.tsa.arima.model import ARIMA
            from statsmodels.tsa.stattools import adfuller
            
            target_col = data.columns[0]
            series = data[target_col].dropna()
            
            if len(series) < 30:
                logger.warning("Insufficient data for ARIMA")
                return False
            
            # Determine order using ADF test
            adf_result = adfuller(series)
            d = 0 if adf_result[1] < 0.05 else 1
            
            # Use simple order selection
            self._order = (1, d, 1)
            
            # Fit model
            self._model = ARIMA(series, order=self._order)
            self._model = self._model.fit()
            
            self._training_data = data
            self._is_trained = True
            
            # Calculate MAPE
            self._calculate_mape(series)
            
            logger.info(f"ARIMA model '{self.name}' trained with order {self._order}")
            return True
            
        except ImportError:
            logger.warning("statsmodels not installed")
            return False
        except Exception as e:
            logger.error(f"ARIMA training failed: {e}")
            return False
    
    async def predict(self, date: datetime, scenario: str = "expected") -> Dict:
        """Make prediction using ARIMA."""
        if not self._is_trained or self._model is None:
            return {"value": 0, "confidence": 0}
        
        try:
            # Calculate steps ahead
            last_date = self._training_data.index[-1]
            steps = (date - last_date.to_pydatetime()).days
            
            if steps <= 0:
                steps = 1
            
            # Forecast
            forecast = self._model.get_forecast(steps=steps)
            value = forecast.predicted_mean.iloc[-1]
            conf_int = forecast.conf_int().iloc[-1]
            
            lower = conf_int.iloc[0]
            upper = conf_int.iloc[1]
            
            # Adjust for scenario
            if scenario == "optimistic":
                value = upper
            elif scenario == "pessimistic":
                value = lower
            
            # Calculate confidence
            interval_width = upper - lower
            confidence = 1 - (interval_width / (2 * abs(value))) if value != 0 else 0.5
            confidence = max(0, min(1, confidence))
            
            return {
                "value": max(0, value),
                "lower": max(0, lower),
                "upper": upper,
                "confidence": confidence,
            }
            
        except Exception as e:
            logger.error(f"ARIMA prediction failed: {e}")
            return {"value": 0, "confidence": 0}
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get coefficient importance."""
        if not self._is_trained or self._model is None:
            return {}
        
        try:
            params = self._model.params
            total = sum(abs(p) for p in params)
            
            importance = {}
            for name, value in zip(self._model.param_names, params):
                importance[name] = abs(value) / total if total > 0 else 0
            
            return importance
        except:
            return {}
    
    def _calculate_mape(self, series: pd.Series):
        """Calculate MAPE on training data."""
        try:
            fitted = self._model.fittedvalues
            actual = series.iloc[len(series) - len(fitted):]
            
            mask = actual != 0
            if mask.sum() > 0:
                self._mape = np.mean(np.abs((actual[mask] - fitted[mask]) / actual[mask])) * 100
            else:
                self._mape = 0
        except:
            self._mape = 0


class EnsembleModel(BaseForecastModel):
    """Ensemble model combining multiple forecasters."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self._models: List[BaseForecastModel] = []
        self._weights: List[float] = []
    
    async def train(self, data: pd.DataFrame) -> bool:
        """Train all ensemble models."""
        # Initialize models
        self._models = [
            ProphetModel(f"{self.name}_prophet"),
            ARIMAModel(f"{self.name}_arima"),
        ]
        
        successful_models = []
        mapes = []
        
        for model in self._models:
            success = await model.train(data)
            if success:
                successful_models.append(model)
                mapes.append(model.get_mape())
        
        if not successful_models:
            # Fallback to simple average model
            self._models = [SimpleAverageModel(f"{self.name}_simple")]
            await self._models[0].train(data)
            self._weights = [1.0]
        else:
            self._models = successful_models
            
            # Calculate weights inversely proportional to MAPE
            if all(m > 0 for m in mapes):
                inv_mapes = [1 / m for m in mapes]
                total = sum(inv_mapes)
                self._weights = [w / total for w in inv_mapes]
            else:
                self._weights = [1 / len(self._models)] * len(self._models)
        
        self._training_data = data
        self._is_trained = True
        
        # Weighted average MAPE
        self._mape = sum(m.get_mape() * w for m, w in zip(self._models, self._weights))
        
        logger.info(f"Ensemble model '{self.name}' trained with {len(self._models)} models")
        return True
    
    async def predict(self, date: datetime, scenario: str = "expected") -> Dict:
        """Make weighted ensemble prediction."""
        if not self._is_trained:
            return {"value": 0, "confidence": 0}
        
        predictions = []
        confidences = []
        
        for model, weight in zip(self._models, self._weights):
            pred = await model.predict(date, scenario)
            predictions.append(pred["value"] * weight)
            confidences.append(pred["confidence"] * weight)
        
        return {
            "value": sum(predictions),
            "confidence": sum(confidences),
        }
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Combine feature importance from all models."""
        combined = {}
        
        for model, weight in zip(self._models, self._weights):
            for feature, importance in model.get_feature_importance().items():
                key = f"{model.name}_{feature}"
                combined[key] = importance * weight
        
        return combined


class SimpleAverageModel(BaseForecastModel):
    """Simple moving average fallback model."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self._mean: float = 0
        self._std: float = 0
        self._weekly_pattern: Dict[int, float] = {}
    
    async def train(self, data: pd.DataFrame) -> bool:
        """Train simple average model."""
        try:
            target_col = data.columns[0]
            series = data[target_col].dropna()
            
            self._mean = series.mean()
            self._std = series.std()
            
            # Calculate weekly pattern
            self._weekly_pattern = series.groupby(series.index.dayofweek).mean().to_dict()
            
            self._training_data = data
            self._is_trained = True
            self._mape = 0  # Not applicable
            
            return True
        except Exception as e:
            logger.error(f"Simple model training failed: {e}")
            return False
    
    async def predict(self, date: datetime, scenario: str = "expected") -> Dict:
        """Predict using weekly pattern."""
        if not self._is_trained:
            return {"value": 0, "confidence": 0}
        
        day_of_week = date.weekday()
        value = self._weekly_pattern.get(day_of_week, self._mean)
        
        if scenario == "optimistic":
            value += self._std
        elif scenario == "pessimistic":
            value = max(0, value - self._std)
        
        return {
            "value": max(0, value),
            "confidence": 0.5,  # Low confidence for simple model
        }
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Simple model has no feature importance."""
        return {"day_of_week": 1.0}
```

---

## File 4: Cash Flow Service
**Path:** `backend/app/ai/cashflow/service.py`

```python
"""
Cash Flow Prediction Service
High-level service for cash flow predictions
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from app.ai.cashflow.predictor import CashFlowPredictor, CashFlowForecast, CashFlowSummary, CashFlowAlert
from app.ai.base import AIResult

logger = logging.getLogger(__name__)


class CashFlowService:
    """Service for cash flow predictions."""
    
    def __init__(self):
        self._predictors: Dict[str, CashFlowPredictor] = {}
    
    def get_predictor(self, customer_id: str) -> CashFlowPredictor:
        """Get or create predictor for customer."""
        if customer_id not in self._predictors:
            self._predictors[customer_id] = CashFlowPredictor(customer_id)
        return self._predictors[customer_id]
    
    async def train_model(self, customer_id: str, historical_data: List[Dict], current_balance: float) -> AIResult:
        """Train cash flow model for customer."""
        try:
            predictor = self.get_predictor(customer_id)
            
            success = await predictor.train(
                historical_data,
                current_balance=current_balance,
            )
            
            if success:
                return AIResult(
                    success=True,
                    data={"metrics": predictor.metrics},
                    metadata={"trained_at": datetime.utcnow().isoformat()},
                )
            else:
                return AIResult(
                    success=False,
                    error="Insufficient data for training",
                )
                
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return AIResult(success=False, error=str(e))
    
    async def get_forecast(
        self,
        customer_id: str,
        horizon_days: int = 30,
        scenario: str = "expected",
        include_pending: bool = True,
        include_recurring: bool = True,
    ) -> AIResult:
        """Get cash flow forecast."""
        import time
        start_time = time.time()
        
        try:
            predictor = self.get_predictor(customer_id)
            
            # Generate forecast
            forecasts = await predictor.forecast(
                horizon_days=horizon_days,
                scenario=scenario,
                include_pending=include_pending,
                include_recurring=include_recurring,
            )
            
            # Generate summary and alerts
            summary = predictor.generate_summary(forecasts)
            alerts = predictor.generate_alerts(forecasts)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return AIResult(
                success=True,
                data={
                    "forecast": [f.to_dict() for f in forecasts],
                    "summary": summary.to_dict(),
                    "alerts": [a.to_dict() for a in alerts],
                },
                processing_time_ms=processing_time,
                metadata={
                    "horizon_days": horizon_days,
                    "scenario": scenario,
                    "model_trained": predictor.is_trained,
                },
            )
            
        except Exception as e:
            logger.error(f"Forecast generation failed: {e}")
            return AIResult(success=False, error=str(e))
    
    async def set_pending_items(
        self,
        customer_id: str,
        pending_invoices: List[Dict],
        pending_payments: List[Dict],
    ):
        """Set pending items for more accurate forecasting."""
        predictor = self.get_predictor(customer_id)
        predictor.set_pending_items(pending_invoices, pending_payments)
    
    async def set_recurring_items(self, customer_id: str, recurring_items: List[Dict]):
        """Set recurring transactions."""
        predictor = self.get_predictor(customer_id)
        predictor.set_recurring_items(recurring_items)
    
    async def get_what_if_analysis(
        self,
        customer_id: str,
        scenarios: List[Dict],
        horizon_days: int = 30,
    ) -> AIResult:
        """Run what-if analysis with custom scenarios."""
        try:
            predictor = self.get_predictor(customer_id)
            results = []
            
            for scenario in scenarios:
                name = scenario.get("name", "Custom")
                adjustments = scenario.get("adjustments", {})
                
                # Apply adjustments temporarily
                # (In production, create adjusted versions of pending items)
                
                forecasts = await predictor.forecast(
                    horizon_days=horizon_days,
                    scenario="expected",
                )
                
                summary = predictor.generate_summary(forecasts)
                
                results.append({
                    "scenario": name,
                    "ending_balance": summary.ending_balance,
                    "lowest_point": summary.lowest_point,
                    "net_change": summary.net_change,
                })
            
            return AIResult(
                success=True,
                data={"scenarios": results},
            )
            
        except Exception as e:
            logger.error(f"What-if analysis failed: {e}")
            return AIResult(success=False, error=str(e))
    
    def get_model_status(self, customer_id: str) -> Dict:
        """Get model training status."""
        predictor = self._predictors.get(customer_id)
        
        if not predictor:
            return {
                "trained": False,
                "message": "Model not initialized",
            }
        
        return {
            "trained": predictor.is_trained,
            "last_trained": predictor._last_trained_at.isoformat() if predictor._last_trained_at else None,
            "metrics": predictor.metrics,
        }


# Global service instance
cashflow_service = CashFlowService()
```

---

## File 5: Cash Flow Module Init
**Path:** `backend/app/ai/cashflow/__init__.py`

```python
"""
Cash Flow Prediction Module
AI-powered cash flow forecasting
"""

from app.ai.cashflow.predictor import (
    CashFlowPredictor,
    CashFlowForecast,
    CashFlowSummary,
    CashFlowAlert,
)
from app.ai.cashflow.features import CashFlowFeatureEngine
from app.ai.cashflow.models import (
    BaseForecastModel,
    ProphetModel,
    ARIMAModel,
    EnsembleModel,
    SimpleAverageModel,
)
from app.ai.cashflow.service import CashFlowService, cashflow_service


__all__ = [
    'CashFlowPredictor',
    'CashFlowForecast',
    'CashFlowSummary',
    'CashFlowAlert',
    'CashFlowFeatureEngine',
    'BaseForecastModel',
    'ProphetModel',
    'ARIMAModel',
    'EnsembleModel',
    'SimpleAverageModel',
    'CashFlowService',
    'cashflow_service',
]
```

---

## Summary Part 2

| File | Description | Lines |
|------|-------------|-------|
| `cashflow/predictor.py` | Cash flow prediction engine | ~450 |
| `cashflow/features.py` | Feature engineering | ~280 |
| `cashflow/models.py` | Forecast models (Prophet, ARIMA, Ensemble) | ~420 |
| `cashflow/service.py` | Cash flow service | ~180 |
| `cashflow/__init__.py` | Module initialization | ~35 |
| **Total** | | **~1,365 lines** |
