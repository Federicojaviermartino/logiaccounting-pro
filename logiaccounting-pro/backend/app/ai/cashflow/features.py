"""
Cash Flow Feature Engineering
Feature extraction for cash flow prediction models
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class CashFlowFeatureEngine:
    """Extracts features for cash flow prediction."""

    def __init__(self):
        self.feature_names = []

    def extract_features(
        self,
        df: pd.DataFrame,
        target_date: datetime = None,
    ) -> pd.DataFrame:
        """Extract all features from cash flow data."""
        features = pd.DataFrame(index=df.index)

        # Temporal features
        features = self._add_temporal_features(features, df)

        # Lag features
        features = self._add_lag_features(features, df)

        # Rolling statistics
        features = self._add_rolling_features(features, df)

        # Trend features
        features = self._add_trend_features(features, df)

        # Seasonality features
        features = self._add_seasonality_features(features, df)

        self.feature_names = list(features.columns)
        return features.dropna()

    def _add_temporal_features(self, features: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
        """Add time-based features."""
        date_index = pd.to_datetime(df.index) if not isinstance(df.index, pd.DatetimeIndex) else df.index

        features["day_of_week"] = date_index.dayofweek
        features["day_of_month"] = date_index.day
        features["week_of_year"] = date_index.isocalendar().week.values
        features["month"] = date_index.month
        features["quarter"] = date_index.quarter
        features["year"] = date_index.year

        # Binary features
        features["is_weekend"] = (date_index.dayofweek >= 5).astype(int)
        features["is_month_start"] = date_index.is_month_start.astype(int)
        features["is_month_end"] = date_index.is_month_end.astype(int)
        features["is_quarter_start"] = date_index.is_quarter_start.astype(int)
        features["is_quarter_end"] = date_index.is_quarter_end.astype(int)

        # Cyclical encoding
        features["day_sin"] = np.sin(2 * np.pi * date_index.dayofweek / 7)
        features["day_cos"] = np.cos(2 * np.pi * date_index.dayofweek / 7)
        features["month_sin"] = np.sin(2 * np.pi * date_index.month / 12)
        features["month_cos"] = np.cos(2 * np.pi * date_index.month / 12)

        return features

    def _add_lag_features(self, features: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
        """Add lagged features."""
        for col in ["inflows", "outflows", "net_flow"]:
            if col not in df.columns:
                continue

            for lag in [1, 2, 3, 7, 14, 21, 28, 30]:
                features[f"{col}_lag_{lag}"] = df[col].shift(lag)

            # Difference features
            features[f"{col}_diff_1"] = df[col].diff(1)
            features[f"{col}_diff_7"] = df[col].diff(7)

        return features

    def _add_rolling_features(self, features: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
        """Add rolling statistics."""
        for col in ["inflows", "outflows", "net_flow"]:
            if col not in df.columns:
                continue

            for window in [7, 14, 30, 60]:
                # Mean
                features[f"{col}_rolling_mean_{window}"] = df[col].rolling(window).mean()
                # Standard deviation
                features[f"{col}_rolling_std_{window}"] = df[col].rolling(window).std()
                # Min/Max
                features[f"{col}_rolling_min_{window}"] = df[col].rolling(window).min()
                features[f"{col}_rolling_max_{window}"] = df[col].rolling(window).max()
                # Median
                features[f"{col}_rolling_median_{window}"] = df[col].rolling(window).median()

            # Exponential weighted
            for span in [7, 14, 30]:
                features[f"{col}_ewm_{span}"] = df[col].ewm(span=span).mean()

        return features

    def _add_trend_features(self, features: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
        """Add trend indicators."""
        for col in ["inflows", "outflows", "net_flow"]:
            if col not in df.columns:
                continue

            # Trend direction
            rolling_7 = df[col].rolling(7).mean()
            rolling_30 = df[col].rolling(30).mean()

            features[f"{col}_trend_7_30"] = (rolling_7 - rolling_30) / rolling_30.replace(0, np.nan)

            # Momentum
            features[f"{col}_momentum_7"] = df[col] - df[col].shift(7)
            features[f"{col}_momentum_30"] = df[col] - df[col].shift(30)

            # Rate of change
            features[f"{col}_roc_7"] = df[col].pct_change(7)
            features[f"{col}_roc_30"] = df[col].pct_change(30)

        return features

    def _add_seasonality_features(self, features: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
        """Add seasonality-related features."""
        for col in ["inflows", "outflows"]:
            if col not in df.columns:
                continue

            # Day of week averages (relative to overall mean)
            col_mean = df[col].mean()
            if col_mean > 0:
                dow_means = df.groupby(df.index.dayofweek)[col].transform("mean")
                features[f"{col}_dow_factor"] = dow_means / col_mean

                # Day of month averages
                dom_means = df.groupby(df.index.day)[col].transform("mean")
                features[f"{col}_dom_factor"] = dom_means / col_mean

                # Month averages
                month_means = df.groupby(df.index.month)[col].transform("mean")
                features[f"{col}_month_factor"] = month_means / col_mean

        return features

    def get_feature_importance(self, model, top_n: int = 20) -> List[Tuple[str, float]]:
        """Get feature importance from trained model."""
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
        elif hasattr(model, "coef_"):
            importances = np.abs(model.coef_)
        else:
            return []

        importance_pairs = list(zip(self.feature_names, importances))
        importance_pairs.sort(key=lambda x: x[1], reverse=True)

        return importance_pairs[:top_n]

    def prepare_prediction_features(
        self,
        historical_df: pd.DataFrame,
        forecast_date: datetime,
    ) -> Dict[str, float]:
        """Prepare features for a single prediction date."""
        # Use the most recent data to calculate features
        features = {}

        # Temporal features
        features["day_of_week"] = forecast_date.weekday()
        features["day_of_month"] = forecast_date.day
        features["month"] = forecast_date.month
        features["quarter"] = (forecast_date.month - 1) // 3 + 1
        features["is_weekend"] = 1 if forecast_date.weekday() >= 5 else 0
        features["is_month_start"] = 1 if forecast_date.day == 1 else 0
        features["is_month_end"] = 1 if forecast_date.day >= 28 else 0

        # Cyclical
        features["day_sin"] = np.sin(2 * np.pi * forecast_date.weekday() / 7)
        features["day_cos"] = np.cos(2 * np.pi * forecast_date.weekday() / 7)

        # Use historical statistics
        for col in ["inflows", "outflows", "net_flow"]:
            if col in historical_df.columns:
                recent = historical_df[col].tail(30)
                features[f"{col}_rolling_mean_30"] = recent.mean()
                features[f"{col}_rolling_std_30"] = recent.std()

                recent_7 = historical_df[col].tail(7)
                features[f"{col}_rolling_mean_7"] = recent_7.mean()

        return features
