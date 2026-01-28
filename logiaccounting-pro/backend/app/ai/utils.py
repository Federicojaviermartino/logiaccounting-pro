"""
AI/ML Utilities
Helper functions for data processing, feature engineering, and model operations
"""

from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import numpy as np
from app.utils.datetime_utils import utc_now
import pandas as pd
from collections import defaultdict
import json
import hashlib
import logging

logger = logging.getLogger(__name__)


# ==================== Data Processing ====================

def prepare_time_series(
    data: List[Dict],
    date_field: str,
    value_field: str,
    freq: str = "D",
    fill_method: str = "ffill",
) -> pd.DataFrame:
    """Prepare time series data for forecasting."""
    df = pd.DataFrame(data)

    # Convert date field
    df[date_field] = pd.to_datetime(df[date_field])
    df = df.set_index(date_field)

    # Resample to specified frequency
    df = df.resample(freq).sum()

    # Fill missing values
    if fill_method == "ffill":
        df = df.ffill()
    elif fill_method == "bfill":
        df = df.bfill()
    elif fill_method == "zero":
        df = df.fillna(0)
    elif fill_method == "interpolate":
        df = df.interpolate()

    return df


def calculate_features(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    """Calculate time series features."""
    features = pd.DataFrame(index=df.index)

    # Basic features
    features["value"] = df[value_col]
    features["day_of_week"] = df.index.dayofweek
    features["day_of_month"] = df.index.day
    features["month"] = df.index.month
    features["quarter"] = df.index.quarter
    features["is_weekend"] = df.index.dayofweek.isin([5, 6]).astype(int)
    features["is_month_start"] = df.index.is_month_start.astype(int)
    features["is_month_end"] = df.index.is_month_end.astype(int)

    # Lag features
    for lag in [1, 7, 14, 30]:
        features[f"lag_{lag}"] = df[value_col].shift(lag)

    # Rolling statistics
    for window in [7, 14, 30]:
        features[f"rolling_mean_{window}"] = df[value_col].rolling(window).mean()
        features[f"rolling_std_{window}"] = df[value_col].rolling(window).std()
        features[f"rolling_min_{window}"] = df[value_col].rolling(window).min()
        features[f"rolling_max_{window}"] = df[value_col].rolling(window).max()

    # Exponential moving averages
    for span in [7, 14, 30]:
        features[f"ema_{span}"] = df[value_col].ewm(span=span).mean()

    return features.dropna()


def detect_seasonality(data: pd.Series, periods: List[int] = [7, 30, 365]) -> Dict:
    """Detect seasonality patterns in time series."""
    from scipy import stats

    results = {}

    for period in periods:
        if len(data) < period * 2:
            continue

        # Calculate autocorrelation at this period
        autocorr = data.autocorr(lag=period)

        # Statistical significance test
        n = len(data)
        se = 1 / np.sqrt(n)
        z_score = autocorr / se
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))

        results[period] = {
            "autocorrelation": autocorr,
            "p_value": p_value,
            "significant": p_value < 0.05,
        }

    return results


# ==================== Anomaly Detection Helpers ====================

def calculate_z_scores(data: np.ndarray) -> np.ndarray:
    """Calculate Z-scores for anomaly detection."""
    mean = np.mean(data)
    std = np.std(data)

    if std == 0:
        return np.zeros_like(data)

    return (data - mean) / std


def calculate_iqr_bounds(data: np.ndarray, multiplier: float = 1.5) -> Tuple[float, float]:
    """Calculate IQR-based bounds for anomaly detection."""
    q1 = np.percentile(data, 25)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1

    lower_bound = q1 - multiplier * iqr
    upper_bound = q3 + multiplier * iqr

    return lower_bound, upper_bound


def detect_outliers(
    data: np.ndarray,
    method: str = "iqr",
    threshold: float = None,
) -> np.ndarray:
    """Detect outliers in data."""
    if method == "zscore":
        threshold = threshold or 3.0
        z_scores = calculate_z_scores(data)
        return np.abs(z_scores) > threshold

    elif method == "iqr":
        threshold = threshold or 1.5
        lower, upper = calculate_iqr_bounds(data, threshold)
        return (data < lower) | (data > upper)

    elif method == "mad":
        # Median Absolute Deviation
        threshold = threshold or 3.5
        median = np.median(data)
        mad = np.median(np.abs(data - median))

        if mad == 0:
            return np.zeros(len(data), dtype=bool)

        modified_z = 0.6745 * (data - median) / mad
        return np.abs(modified_z) > threshold

    else:
        raise ValueError(f"Unknown method: {method}")


# ==================== Text Processing ====================

def extract_numbers(text: str) -> List[float]:
    """Extract numbers from text."""
    import re

    # Pattern for numbers including decimals, commas, and currency
    pattern = r'[\$€£]?\s*[\d,]+\.?\d*'
    matches = re.findall(pattern, text)

    numbers = []
    for match in matches:
        # Clean and convert
        cleaned = re.sub(r'[\$€£,\s]', '', match)
        try:
            numbers.append(float(cleaned))
        except ValueError:
            pass

    return numbers


def extract_dates(text: str) -> List[datetime]:
    """Extract dates from text."""
    from dateutil import parser
    import re

    # Common date patterns
    patterns = [
        r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
        r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',
        r'[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}',
        r'\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}',
    ]

    dates = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                dates.append(parser.parse(match))
            except:
                pass

    return dates


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    import re

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove special characters but keep essential punctuation
    text = re.sub(r'[^\w\s.,;:!?@#$%&*()-]', '', text)

    return text.strip()


# ==================== Caching ====================

class AICache:
    """Simple in-memory cache for AI responses."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds

    def _hash_key(self, key: Union[str, Dict]) -> str:
        """Generate hash for cache key."""
        if isinstance(key, dict):
            key = json.dumps(key, sort_keys=True)
        return hashlib.md5(key.encode()).hexdigest()

    def get(self, key: Union[str, Dict]) -> Optional[Any]:
        """Get value from cache."""
        hash_key = self._hash_key(key)

        if hash_key not in self._cache:
            return None

        value, timestamp = self._cache[hash_key]

        # Check TTL
        if (utc_now() - timestamp).total_seconds() > self.ttl_seconds:
            del self._cache[hash_key]
            return None

        return value

    def set(self, key: Union[str, Dict], value: Any):
        """Set value in cache."""
        # Evict old entries if at capacity
        if len(self._cache) >= self.max_size:
            self._evict_oldest()

        hash_key = self._hash_key(key)
        self._cache[hash_key] = (value, utc_now())

    def _evict_oldest(self):
        """Evict oldest entries."""
        if not self._cache:
            return

        # Sort by timestamp and remove oldest 10%
        sorted_items = sorted(
            self._cache.items(),
            key=lambda x: x[1][1]
        )

        to_remove = max(1, len(sorted_items) // 10)
        for key, _ in sorted_items[:to_remove]:
            del self._cache[key]

    def clear(self):
        """Clear cache."""
        self._cache.clear()


# Global cache instance
ai_cache = AICache()


# ==================== Formatting ====================

def format_currency(amount: float, currency: str = "USD") -> str:
    """Format amount as currency."""
    symbols = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥"}
    symbol = symbols.get(currency, currency + " ")
    return f"{symbol}{amount:,.2f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format value as percentage."""
    return f"{value * 100:.{decimals}f}%"


def format_change(current: float, previous: float) -> Dict:
    """Format change between two values."""
    if previous == 0:
        change_pct = 0 if current == 0 else float('inf')
    else:
        change_pct = (current - previous) / previous

    return {
        "current": current,
        "previous": previous,
        "change": current - previous,
        "change_percent": change_pct,
        "direction": "up" if current > previous else "down" if current < previous else "flat",
    }
