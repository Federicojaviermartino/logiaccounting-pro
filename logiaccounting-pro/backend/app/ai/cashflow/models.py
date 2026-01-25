"""
Cash Flow Prediction Models
Various forecasting models for cash flow
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class BaseForecastModel(ABC):
    """Base class for forecast models."""

    @abstractmethod
    def fit(self, df: pd.DataFrame, target_col: str):
        """Fit the model to historical data."""
        pass

    @abstractmethod
    def predict(self, periods: int) -> pd.DataFrame:
        """Generate predictions for future periods."""
        pass

    @abstractmethod
    def get_confidence_intervals(self, periods: int) -> Tuple[pd.Series, pd.Series]:
        """Get confidence intervals for predictions."""
        pass


class SimpleAverageModel(BaseForecastModel):
    """Simple moving average model."""

    def __init__(self, window: int = 30):
        self.window = window
        self._historical_data = None
        self._target_col = None
        self._mean = 0
        self._std = 0

    def fit(self, df: pd.DataFrame, target_col: str):
        """Fit by calculating historical averages."""
        self._historical_data = df.copy()
        self._target_col = target_col

        recent = df[target_col].tail(self.window)
        self._mean = recent.mean()
        self._std = recent.std()

    def predict(self, periods: int) -> pd.DataFrame:
        """Predict using the mean."""
        last_date = self._historical_data.index[-1]
        future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=periods, freq="D")

        predictions = pd.DataFrame({
            "date": future_dates,
            "predicted": [self._mean] * periods,
        })
        predictions = predictions.set_index("date")

        return predictions

    def get_confidence_intervals(self, periods: int) -> Tuple[pd.Series, pd.Series]:
        """Get confidence intervals."""
        predictions = self.predict(periods)

        # Wider intervals further out
        intervals = []
        for i in range(periods):
            factor = 1 + (i / periods) * 0.5  # 50% wider at end
            intervals.append(self._std * 1.96 * factor)

        intervals = np.array(intervals)
        lower = predictions["predicted"] - intervals
        upper = predictions["predicted"] + intervals

        return lower, upper


class ProphetModel(BaseForecastModel):
    """Facebook Prophet-style model (simplified implementation)."""

    def __init__(self, seasonality_mode: str = "multiplicative"):
        self.seasonality_mode = seasonality_mode
        self._historical_data = None
        self._target_col = None
        self._trend = None
        self._weekly_seasonality = None
        self._monthly_seasonality = None
        self._base_value = 0

    def fit(self, df: pd.DataFrame, target_col: str):
        """Fit Prophet-style components."""
        self._historical_data = df.copy()
        self._target_col = target_col

        # Calculate base value
        self._base_value = df[target_col].mean()

        # Calculate trend (simple linear)
        x = np.arange(len(df))
        y = df[target_col].values
        if len(x) > 1:
            slope, intercept = np.polyfit(x, y, 1)
            self._trend = {"slope": slope, "intercept": intercept}
        else:
            self._trend = {"slope": 0, "intercept": self._base_value}

        # Weekly seasonality
        df_temp = df.copy()
        df_temp["dow"] = df_temp.index.dayofweek
        weekly = df_temp.groupby("dow")[target_col].mean()
        self._weekly_seasonality = (weekly / weekly.mean()).to_dict()

        # Monthly day seasonality
        df_temp["dom"] = df_temp.index.day
        monthly = df_temp.groupby("dom")[target_col].mean()
        self._monthly_seasonality = (monthly / monthly.mean()).to_dict()

    def predict(self, periods: int) -> pd.DataFrame:
        """Generate predictions with trend and seasonality."""
        last_date = self._historical_data.index[-1]
        future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=periods, freq="D")

        predictions = []
        n_historical = len(self._historical_data)

        for i, date in enumerate(future_dates):
            # Trend component
            x = n_historical + i
            trend = self._trend["slope"] * x + self._trend["intercept"]

            # Seasonality components
            dow = date.dayofweek
            dom = date.day

            weekly_factor = self._weekly_seasonality.get(dow, 1.0)
            monthly_factor = self._monthly_seasonality.get(dom, 1.0)

            if self.seasonality_mode == "multiplicative":
                prediction = trend * weekly_factor * monthly_factor
            else:
                prediction = trend + (weekly_factor - 1) * self._base_value + (monthly_factor - 1) * self._base_value

            predictions.append(max(0, prediction))

        result = pd.DataFrame({
            "date": future_dates,
            "predicted": predictions,
        })
        result = result.set_index("date")

        return result

    def get_confidence_intervals(self, periods: int) -> Tuple[pd.Series, pd.Series]:
        """Get confidence intervals."""
        predictions = self.predict(periods)
        residual_std = self._historical_data[self._target_col].std()

        intervals = []
        for i in range(periods):
            factor = 1 + (i / periods) * 0.5
            intervals.append(residual_std * 1.96 * factor)

        intervals = np.array(intervals)
        lower = predictions["predicted"] - intervals
        upper = predictions["predicted"] + intervals

        return lower, upper


class ARIMAModel(BaseForecastModel):
    """ARIMA-style model (simplified implementation)."""

    def __init__(self, order: Tuple[int, int, int] = (1, 1, 1)):
        self.order = order
        self._historical_data = None
        self._target_col = None
        self._differenced_mean = 0
        self._differenced_std = 0
        self._last_values = []

    def fit(self, df: pd.DataFrame, target_col: str):
        """Fit ARIMA components."""
        self._historical_data = df.copy()
        self._target_col = target_col

        # Simple differencing
        differenced = df[target_col].diff().dropna()
        self._differenced_mean = differenced.mean()
        self._differenced_std = differenced.std()

        # Store last values for prediction
        self._last_values = df[target_col].tail(5).tolist()

    def predict(self, periods: int) -> pd.DataFrame:
        """Generate ARIMA-style predictions."""
        last_date = self._historical_data.index[-1]
        future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=periods, freq="D")

        predictions = []
        current_value = self._last_values[-1]

        for i in range(periods):
            # Predict next difference
            next_diff = self._differenced_mean

            # Add autoregressive component
            if len(predictions) > 0:
                ar_term = 0.5 * (predictions[-1] - (current_value if len(predictions) == 1 else predictions[-2]))
                next_diff += ar_term * 0.3

            # Apply difference to get prediction
            next_value = current_value + next_diff
            predictions.append(max(0, next_value))
            current_value = next_value

        result = pd.DataFrame({
            "date": future_dates,
            "predicted": predictions,
        })
        result = result.set_index("date")

        return result

    def get_confidence_intervals(self, periods: int) -> Tuple[pd.Series, pd.Series]:
        """Get confidence intervals."""
        predictions = self.predict(periods)

        intervals = []
        cumulative_std = 0
        for i in range(periods):
            cumulative_std = np.sqrt(cumulative_std**2 + self._differenced_std**2)
            intervals.append(cumulative_std * 1.96)

        intervals = np.array(intervals)
        lower = predictions["predicted"] - intervals
        upper = predictions["predicted"] + intervals

        return lower, upper


class EnsembleModel(BaseForecastModel):
    """Ensemble of multiple models."""

    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or {"prophet": 0.4, "arima": 0.3, "average": 0.3}
        self.models = {
            "prophet": ProphetModel(),
            "arima": ARIMAModel(),
            "average": SimpleAverageModel(),
        }
        self._target_col = None

    def fit(self, df: pd.DataFrame, target_col: str):
        """Fit all ensemble models."""
        self._target_col = target_col
        for name, model in self.models.items():
            try:
                model.fit(df, target_col)
            except Exception as e:
                logger.warning(f"Failed to fit {name} model: {e}")

    def predict(self, periods: int) -> pd.DataFrame:
        """Generate weighted ensemble predictions."""
        predictions_list = []
        total_weight = 0

        for name, model in self.models.items():
            try:
                pred = model.predict(periods)
                predictions_list.append((pred["predicted"].values, self.weights.get(name, 0.33)))
                total_weight += self.weights.get(name, 0.33)
            except Exception as e:
                logger.warning(f"Failed to predict with {name} model: {e}")

        if not predictions_list:
            raise ValueError("All models failed to generate predictions")

        # Weighted average
        ensemble_pred = np.zeros(periods)
        for pred, weight in predictions_list:
            ensemble_pred += pred * (weight / total_weight)

        # Get dates from first successful model
        last_date = list(self.models.values())[0]._historical_data.index[-1]
        future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=periods, freq="D")

        result = pd.DataFrame({
            "date": future_dates,
            "predicted": ensemble_pred,
        })
        result = result.set_index("date")

        return result

    def get_confidence_intervals(self, periods: int) -> Tuple[pd.Series, pd.Series]:
        """Get ensemble confidence intervals."""
        all_lowers = []
        all_uppers = []

        for name, model in self.models.items():
            try:
                lower, upper = model.get_confidence_intervals(periods)
                all_lowers.append(lower.values)
                all_uppers.append(upper.values)
            except Exception:
                pass

        if not all_lowers:
            pred = self.predict(periods)
            return pred["predicted"] * 0.8, pred["predicted"] * 1.2

        # Take the widest intervals
        lower = pd.Series(np.min(all_lowers, axis=0))
        upper = pd.Series(np.max(all_uppers, axis=0))

        return lower, upper
