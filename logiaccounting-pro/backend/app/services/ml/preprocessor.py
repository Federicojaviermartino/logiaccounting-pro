"""
Data Preprocessor
Handles data cleaning, normalization, and transformation
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import math


class DataPreprocessor:
    """
    Data Preprocessing for ML Models

    Responsibilities:
    - Handle missing values
    - Detect and handle outliers
    - Normalize/scale data
    - Encode categorical variables
    """

    def __init__(self):
        self.scalers = {}
        self.encoders = {}

    def fill_missing_values(
        self,
        time_series: List[Dict],
        method: str = 'interpolate',
        value_key: str = 'value'
    ) -> List[Dict]:
        """
        Fill missing values in time series

        Methods:
        - 'zero': Fill with 0
        - 'mean': Fill with series mean
        - 'forward': Forward fill (last known value)
        - 'interpolate': Linear interpolation
        """
        if not time_series:
            return []

        values = [d.get(value_key, 0) for d in time_series]
        non_zero_values = [v for v in values if v != 0]

        if method == 'zero':
            return time_series

        elif method == 'mean':
            mean_val = sum(non_zero_values) / len(non_zero_values) if non_zero_values else 0
            return [
                {**d, value_key: d.get(value_key) or mean_val}
                for d in time_series
            ]

        elif method == 'forward':
            result = []
            last_value = 0
            for d in time_series:
                val = d.get(value_key, 0)
                if val == 0:
                    val = last_value
                else:
                    last_value = val
                result.append({**d, value_key: val})
            return result

        elif method == 'interpolate':
            result = list(time_series)

            # Find gaps and interpolate
            for i in range(len(result)):
                if result[i].get(value_key, 0) == 0:
                    # Find previous non-zero
                    prev_idx = i - 1
                    prev_val = 0
                    while prev_idx >= 0:
                        if result[prev_idx].get(value_key, 0) != 0:
                            prev_val = result[prev_idx][value_key]
                            break
                        prev_idx -= 1

                    # Find next non-zero
                    next_idx = i + 1
                    next_val = 0
                    while next_idx < len(result):
                        if result[next_idx].get(value_key, 0) != 0:
                            next_val = result[next_idx][value_key]
                            break
                        next_idx += 1

                    # Interpolate
                    if prev_val != 0 and next_val != 0:
                        steps = next_idx - prev_idx
                        step_val = (next_val - prev_val) / steps
                        result[i] = {**result[i], value_key: round(prev_val + step_val * (i - prev_idx), 2)}
                    elif prev_val != 0:
                        result[i] = {**result[i], value_key: prev_val}
                    elif next_val != 0:
                        result[i] = {**result[i], value_key: next_val}

            return result

        return time_series

    def detect_outliers(
        self,
        values: List[float],
        method: str = 'zscore',
        threshold: float = 3.0
    ) -> List[int]:
        """
        Detect outlier indices

        Methods:
        - 'zscore': Z-score method (default threshold: 3.0)
        - 'iqr': Interquartile range method (default threshold: 1.5)
        - 'mad': Median absolute deviation
        """
        if len(values) < 3:
            return []

        outlier_indices = []

        if method == 'zscore':
            mean = sum(values) / len(values)
            std = math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))

            if std == 0:
                return []

            for i, v in enumerate(values):
                z_score = abs((v - mean) / std)
                if z_score > threshold:
                    outlier_indices.append(i)

        elif method == 'iqr':
            sorted_vals = sorted(values)
            n = len(sorted_vals)
            q1 = sorted_vals[n // 4]
            q3 = sorted_vals[3 * n // 4]
            iqr = q3 - q1

            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr

            for i, v in enumerate(values):
                if v < lower_bound or v > upper_bound:
                    outlier_indices.append(i)

        elif method == 'mad':
            median = sorted(values)[len(values) // 2]
            deviations = [abs(v - median) for v in values]
            mad = sorted(deviations)[len(deviations) // 2]

            if mad == 0:
                return []

            for i, v in enumerate(values):
                modified_z = 0.6745 * (v - median) / mad
                if abs(modified_z) > threshold:
                    outlier_indices.append(i)

        return outlier_indices

    def handle_outliers(
        self,
        time_series: List[Dict],
        value_key: str = 'value',
        method: str = 'cap',
        detection_method: str = 'zscore'
    ) -> List[Dict]:
        """
        Handle outliers in time series

        Methods:
        - 'cap': Cap values at threshold
        - 'remove': Remove outlier points
        - 'interpolate': Replace with interpolated values
        """
        values = [d.get(value_key, 0) for d in time_series]
        outlier_indices = self.detect_outliers(values, method=detection_method)

        if not outlier_indices:
            return time_series

        result = list(time_series)

        if method == 'cap':
            # Calculate cap values
            non_outliers = [v for i, v in enumerate(values) if i not in outlier_indices]
            if non_outliers:
                upper_cap = max(non_outliers)
                lower_cap = min(non_outliers)

                for i in outlier_indices:
                    val = result[i].get(value_key, 0)
                    if val > upper_cap:
                        result[i] = {**result[i], value_key: upper_cap}
                    elif val < lower_cap:
                        result[i] = {**result[i], value_key: lower_cap}

        elif method == 'remove':
            result = [d for i, d in enumerate(result) if i not in outlier_indices]

        elif method == 'interpolate':
            for i in outlier_indices:
                # Get surrounding values
                prev_val = values[i - 1] if i > 0 else 0
                next_val = values[i + 1] if i < len(values) - 1 else 0

                if prev_val and next_val:
                    result[i] = {**result[i], value_key: round((prev_val + next_val) / 2, 2)}
                elif prev_val:
                    result[i] = {**result[i], value_key: prev_val}
                elif next_val:
                    result[i] = {**result[i], value_key: next_val}

        return result

    def normalize(
        self,
        values: List[float],
        method: str = 'minmax'
    ) -> Tuple[List[float], Dict]:
        """
        Normalize values

        Methods:
        - 'minmax': Scale to [0, 1]
        - 'zscore': Standardize to mean=0, std=1
        """
        if not values:
            return [], {}

        if method == 'minmax':
            min_val = min(values)
            max_val = max(values)
            range_val = max_val - min_val

            if range_val == 0:
                return [0.5] * len(values), {'method': 'minmax', 'min': min_val, 'max': max_val}

            normalized = [(v - min_val) / range_val for v in values]
            params = {'method': 'minmax', 'min': min_val, 'max': max_val}

        elif method == 'zscore':
            mean = sum(values) / len(values)
            std = math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))

            if std == 0:
                return [0] * len(values), {'method': 'zscore', 'mean': mean, 'std': std}

            normalized = [(v - mean) / std for v in values]
            params = {'method': 'zscore', 'mean': mean, 'std': std}

        else:
            return values, {}

        return [round(v, 6) for v in normalized], params

    def denormalize(
        self,
        values: List[float],
        params: Dict
    ) -> List[float]:
        """
        Reverse normalization
        """
        method = params.get('method')

        if method == 'minmax':
            min_val = params.get('min', 0)
            max_val = params.get('max', 1)
            range_val = max_val - min_val
            return [round(v * range_val + min_val, 2) for v in values]

        elif method == 'zscore':
            mean = params.get('mean', 0)
            std = params.get('std', 1)
            return [round(v * std + mean, 2) for v in values]

        return values

    def add_time_features(
        self,
        time_series: List[Dict],
        date_key: str = 'date'
    ) -> List[Dict]:
        """
        Add time-based features for ML models
        """
        result = []

        for item in time_series:
            date_str = item.get(date_key)
            try:
                date = datetime.fromisoformat(str(date_str)[:10])
            except (ValueError, AttributeError):
                result.append(item)
                continue

            enhanced = {
                **item,
                'day_of_week': date.weekday(),
                'day_of_month': date.day,
                'month': date.month,
                'quarter': (date.month - 1) // 3 + 1,
                'year': date.year,
                'is_weekend': 1 if date.weekday() >= 5 else 0,
                'is_month_start': 1 if date.day <= 5 else 0,
                'is_month_end': 1 if date.day >= 25 else 0,
                'is_quarter_end': 1 if date.month in [3, 6, 9, 12] and date.day >= 25 else 0
            }
            result.append(enhanced)

        return result
