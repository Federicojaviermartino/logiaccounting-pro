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
