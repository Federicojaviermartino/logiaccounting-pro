# Phase 31: AI/ML Features - Part 1: AI Core Infrastructure

## Overview
This part covers the core AI infrastructure including configuration, base classes, utilities, and shared components.

---

## File 1: AI Configuration
**Path:** `backend/app/ai/config.py`

```python
"""
AI Configuration
Central configuration for all AI/ML features
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import os


class AIProvider(str, Enum):
    """Supported AI providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class ModelType(str, Enum):
    """Model types for different tasks."""
    CHAT = "chat"
    EMBEDDING = "embedding"
    VISION = "vision"
    COMPLETION = "completion"


@dataclass
class ModelConfig:
    """Configuration for an AI model."""
    provider: AIProvider
    model_name: str
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 30
    retry_attempts: int = 3
    rate_limit_rpm: int = 60


@dataclass
class AIConfig:
    """Central AI configuration."""
    
    # Provider API Keys
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    
    # Default provider
    default_provider: AIProvider = AIProvider.ANTHROPIC
    
    # Model configurations
    chat_model: ModelConfig = field(default_factory=lambda: ModelConfig(
        provider=AIProvider.ANTHROPIC,
        model_name="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        temperature=0.7,
    ))
    
    vision_model: ModelConfig = field(default_factory=lambda: ModelConfig(
        provider=AIProvider.ANTHROPIC,
        model_name="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        temperature=0.3,
    ))
    
    embedding_model: ModelConfig = field(default_factory=lambda: ModelConfig(
        provider=AIProvider.OPENAI,
        model_name="text-embedding-3-small",
        max_tokens=8191,
    ))
    
    # Feature toggles
    features: Dict[str, bool] = field(default_factory=lambda: {
        "cashflow_predictor": True,
        "invoice_ocr": True,
        "ai_assistant": True,
        "anomaly_detection": True,
        "payment_optimizer": True,
        "recommendations": True,
    })
    
    # Cache settings
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600
    
    # Logging
    log_requests: bool = True
    log_responses: bool = False
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled."""
        return self.features.get(feature, False)
    
    def get_api_key(self, provider: AIProvider) -> str:
        """Get API key for provider."""
        if provider == AIProvider.OPENAI:
            return self.openai_api_key
        elif provider == AIProvider.ANTHROPIC:
            return self.anthropic_api_key
        return ""


# Global configuration instance
ai_config = AIConfig()


# Model presets for different use cases
MODEL_PRESETS = {
    "fast": ModelConfig(
        provider=AIProvider.ANTHROPIC,
        model_name="claude-3-haiku-20240307",
        max_tokens=2048,
        temperature=0.5,
        timeout=15,
    ),
    "balanced": ModelConfig(
        provider=AIProvider.ANTHROPIC,
        model_name="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        temperature=0.7,
        timeout=30,
    ),
    "powerful": ModelConfig(
        provider=AIProvider.ANTHROPIC,
        model_name="claude-3-opus-20240229",
        max_tokens=4096,
        temperature=0.7,
        timeout=60,
    ),
    "vision": ModelConfig(
        provider=AIProvider.ANTHROPIC,
        model_name="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        temperature=0.3,
        timeout=45,
    ),
}


def get_model_config(preset: str = "balanced") -> ModelConfig:
    """Get model configuration by preset name."""
    return MODEL_PRESETS.get(preset, MODEL_PRESETS["balanced"])
```

---

## File 2: AI Client Manager
**Path:** `backend/app/ai/client.py`

```python
"""
AI Client Manager
Unified interface for different AI providers
"""

from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod
import asyncio
import logging
import time
from datetime import datetime

import httpx
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from app.ai.config import AIConfig, AIProvider, ModelConfig, ai_config

logger = logging.getLogger(__name__)


class AIClient(ABC):
    """Abstract base class for AI clients."""
    
    @abstractmethod
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        """Send chat messages and get response."""
        pass
    
    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> str:
        """Complete a prompt."""
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embeddings for text."""
        pass
    
    @abstractmethod
    async def vision(self, image_data: bytes, prompt: str, **kwargs) -> str:
        """Process image with vision model."""
        pass


class AnthropicClient(AIClient):
    """Anthropic Claude API client."""
    
    def __init__(self, config: AIConfig):
        self.config = config
        self.client = AsyncAnthropic(api_key=config.anthropic_api_key)
    
    async def chat(self, messages: List[Dict], model_config: ModelConfig = None, system: str = None, **kwargs) -> str:
        """Send chat messages to Claude."""
        model_config = model_config or self.config.chat_model
        
        try:
            response = await self.client.messages.create(
                model=model_config.model_name,
                max_tokens=model_config.max_tokens,
                temperature=model_config.temperature,
                system=system or "",
                messages=messages,
                **kwargs,
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Anthropic chat error: {e}")
            raise
    
    async def complete(self, prompt: str, model_config: ModelConfig = None, **kwargs) -> str:
        """Complete a prompt using Claude."""
        return await self.chat(
            messages=[{"role": "user", "content": prompt}],
            model_config=model_config,
            **kwargs,
        )
    
    async def embed(self, text: str) -> List[float]:
        """Anthropic doesn't have embeddings - use OpenAI fallback."""
        raise NotImplementedError("Use OpenAI for embeddings")
    
    async def vision(self, image_data: bytes, prompt: str, model_config: ModelConfig = None, **kwargs) -> str:
        """Process image with Claude Vision."""
        import base64
        
        model_config = model_config or self.config.vision_model
        
        # Encode image to base64
        image_b64 = base64.b64encode(image_data).decode("utf-8")
        
        # Detect image type
        if image_data[:8] == b'\x89PNG\r\n\x1a\n':
            media_type = "image/png"
        elif image_data[:2] == b'\xff\xd8':
            media_type = "image/jpeg"
        else:
            media_type = "image/png"  # Default
        
        try:
            response = await self.client.messages.create(
                model=model_config.model_name,
                max_tokens=model_config.max_tokens,
                temperature=model_config.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
                **kwargs,
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Anthropic vision error: {e}")
            raise


class OpenAIClient(AIClient):
    """OpenAI API client."""
    
    def __init__(self, config: AIConfig):
        self.config = config
        self.client = AsyncOpenAI(api_key=config.openai_api_key)
    
    async def chat(self, messages: List[Dict], model_config: ModelConfig = None, system: str = None, **kwargs) -> str:
        """Send chat messages to GPT."""
        model_config = model_config or self.config.chat_model
        
        # Add system message if provided
        all_messages = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(messages)
        
        try:
            response = await self.client.chat.completions.create(
                model=model_config.model_name,
                max_tokens=model_config.max_tokens,
                temperature=model_config.temperature,
                messages=all_messages,
                **kwargs,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            raise
    
    async def complete(self, prompt: str, model_config: ModelConfig = None, **kwargs) -> str:
        """Complete a prompt."""
        return await self.chat(
            messages=[{"role": "user", "content": prompt}],
            model_config=model_config,
            **kwargs,
        )
    
    async def embed(self, text: str, model: str = None) -> List[float]:
        """Generate embeddings."""
        model = model or self.config.embedding_model.model_name
        
        try:
            response = await self.client.embeddings.create(
                model=model,
                input=text,
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise
    
    async def vision(self, image_data: bytes, prompt: str, model_config: ModelConfig = None, **kwargs) -> str:
        """Process image with GPT-4 Vision."""
        import base64
        
        model_config = model_config or self.config.vision_model
        image_b64 = base64.b64encode(image_data).decode("utf-8")
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                max_tokens=model_config.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_b64}",
                                },
                            },
                        ],
                    }
                ],
                **kwargs,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI vision error: {e}")
            raise


class AIClientManager:
    """Manages AI client instances."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.config = ai_config
        self._clients: Dict[AIProvider, AIClient] = {}
        self._request_counts: Dict[str, int] = {}
        self._last_request_time: Dict[str, float] = {}
        self._initialized = True
    
    def get_client(self, provider: AIProvider = None) -> AIClient:
        """Get AI client for provider."""
        provider = provider or self.config.default_provider
        
        if provider not in self._clients:
            if provider == AIProvider.ANTHROPIC:
                self._clients[provider] = AnthropicClient(self.config)
            elif provider == AIProvider.OPENAI:
                self._clients[provider] = OpenAIClient(self.config)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
        
        return self._clients[provider]
    
    async def chat(self, messages: List[Dict], provider: AIProvider = None, **kwargs) -> str:
        """Send chat request to default or specified provider."""
        client = self.get_client(provider)
        return await client.chat(messages, **kwargs)
    
    async def complete(self, prompt: str, provider: AIProvider = None, **kwargs) -> str:
        """Send completion request."""
        client = self.get_client(provider)
        return await client.complete(prompt, **kwargs)
    
    async def embed(self, text: str) -> List[float]:
        """Generate embeddings (uses OpenAI)."""
        client = self.get_client(AIProvider.OPENAI)
        return await client.embed(text)
    
    async def vision(self, image_data: bytes, prompt: str, provider: AIProvider = None, **kwargs) -> str:
        """Process image with vision model."""
        client = self.get_client(provider)
        return await client.vision(image_data, prompt, **kwargs)


# Global client manager
ai_client = AIClientManager()
```

---

## File 3: ML Utilities
**Path:** `backend/app/ai/utils.py`

```python
"""
AI/ML Utilities
Helper functions for data processing, feature engineering, and model operations
"""

from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import numpy as np
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
        if (datetime.utcnow() - timestamp).total_seconds() > self.ttl_seconds:
            del self._cache[hash_key]
            return None
        
        return value
    
    def set(self, key: Union[str, Dict], value: Any):
        """Set value in cache."""
        # Evict old entries if at capacity
        if len(self._cache) >= self.max_size:
            self._evict_oldest()
        
        hash_key = self._hash_key(key)
        self._cache[hash_key] = (value, datetime.utcnow())
    
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
```

---

## File 4: Base Models
**Path:** `backend/app/ai/base.py`

```python
"""
AI Base Models and Classes
Abstract base classes for AI features
"""

from typing import Dict, Any, List, Optional, Generic, TypeVar
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class PredictionConfidence(str, Enum):
    """Confidence levels for predictions."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class AIResult(Generic[T]):
    """Generic result container for AI operations."""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    confidence: Optional[float] = None
    processing_time_ms: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "confidence": self.confidence,
            "processing_time_ms": self.processing_time_ms,
            "metadata": self.metadata,
        }


@dataclass
class Prediction:
    """Base prediction result."""
    value: float
    confidence: float
    confidence_level: PredictionConfidence
    timestamp: datetime = field(default_factory=datetime.utcnow)
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    factors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "value": self.value,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level.value,
            "timestamp": self.timestamp.isoformat(),
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "factors": self.factors,
        }


@dataclass
class Anomaly:
    """Detected anomaly."""
    id: str
    entity_type: str
    entity_id: str
    anomaly_type: str
    severity: AlertSeverity
    score: float
    description: str
    detected_at: datetime = field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending_review"
    recommended_action: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "anomaly_type": self.anomaly_type,
            "severity": self.severity.value,
            "score": self.score,
            "description": self.description,
            "detected_at": self.detected_at.isoformat(),
            "details": self.details,
            "status": self.status,
            "recommended_action": self.recommended_action,
        }


@dataclass
class Recommendation:
    """AI recommendation."""
    id: str
    type: str
    title: str
    description: str
    priority: int  # 1-10
    confidence: float
    potential_impact: Optional[str] = None
    actions: List[Dict] = field(default_factory=list)
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "confidence": self.confidence,
            "potential_impact": self.potential_impact,
            "actions": self.actions,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat(),
        }


class BasePredictor(ABC):
    """Abstract base class for predictors."""
    
    def __init__(self, name: str):
        self.name = name
        self._is_trained = False
        self._last_trained_at: Optional[datetime] = None
        self._metrics: Dict[str, float] = {}
    
    @abstractmethod
    async def train(self, data: List[Dict], **kwargs) -> bool:
        """Train the model."""
        pass
    
    @abstractmethod
    async def predict(self, input_data: Dict, **kwargs) -> Prediction:
        """Make a prediction."""
        pass
    
    @abstractmethod
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores."""
        pass
    
    @property
    def is_trained(self) -> bool:
        return self._is_trained
    
    @property
    def metrics(self) -> Dict[str, float]:
        return self._metrics


class BaseDetector(ABC):
    """Abstract base class for anomaly detectors."""
    
    def __init__(self, name: str, threshold: float = 0.5):
        self.name = name
        self.threshold = threshold
        self._is_fitted = False
    
    @abstractmethod
    async def fit(self, data: List[Dict], **kwargs):
        """Fit the detector to normal data."""
        pass
    
    @abstractmethod
    async def detect(self, data: Dict) -> List[Anomaly]:
        """Detect anomalies in data."""
        pass
    
    @abstractmethod
    async def detect_batch(self, data: List[Dict]) -> List[Anomaly]:
        """Detect anomalies in batch."""
        pass
    
    @property
    def is_fitted(self) -> bool:
        return self._is_fitted


class BaseExtractor(ABC):
    """Abstract base class for data extractors."""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def extract(self, source: Any, **kwargs) -> Dict[str, Any]:
        """Extract data from source."""
        pass
    
    @abstractmethod
    def validate(self, extracted_data: Dict) -> List[str]:
        """Validate extracted data, return list of errors."""
        pass


class BaseAssistant(ABC):
    """Abstract base class for AI assistants."""
    
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self._conversation_history: List[Dict] = []
    
    @abstractmethod
    async def process_message(self, message: str, context: Dict = None) -> str:
        """Process user message and return response."""
        pass
    
    @abstractmethod
    async def process_with_tools(self, message: str, tools: List[Dict], context: Dict = None) -> Dict:
        """Process message with tool use."""
        pass
    
    def add_to_history(self, role: str, content: str):
        """Add message to conversation history."""
        self._conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    def clear_history(self):
        """Clear conversation history."""
        self._conversation_history = []
    
    @property
    def history(self) -> List[Dict]:
        return self._conversation_history
```

---

## File 5: AI Module Init
**Path:** `backend/app/ai/__init__.py`

```python
"""
AI/ML Features Module
Intelligent features for LogiAccounting Pro
"""

from app.ai.config import (
    AIConfig,
    AIProvider,
    ModelType,
    ModelConfig,
    ai_config,
    get_model_config,
    MODEL_PRESETS,
)

from app.ai.client import (
    AIClient,
    AnthropicClient,
    OpenAIClient,
    AIClientManager,
    ai_client,
)

from app.ai.base import (
    AIResult,
    Prediction,
    Anomaly,
    Recommendation,
    PredictionConfidence,
    AlertSeverity,
    BasePredictor,
    BaseDetector,
    BaseExtractor,
    BaseAssistant,
)

from app.ai.utils import (
    prepare_time_series,
    calculate_features,
    detect_seasonality,
    calculate_z_scores,
    calculate_iqr_bounds,
    detect_outliers,
    extract_numbers,
    extract_dates,
    clean_text,
    AICache,
    ai_cache,
    format_currency,
    format_percentage,
    format_change,
)


__all__ = [
    # Config
    'AIConfig',
    'AIProvider',
    'ModelType',
    'ModelConfig',
    'ai_config',
    'get_model_config',
    'MODEL_PRESETS',
    
    # Client
    'AIClient',
    'AnthropicClient',
    'OpenAIClient',
    'AIClientManager',
    'ai_client',
    
    # Base classes
    'AIResult',
    'Prediction',
    'Anomaly',
    'Recommendation',
    'PredictionConfidence',
    'AlertSeverity',
    'BasePredictor',
    'BaseDetector',
    'BaseExtractor',
    'BaseAssistant',
    
    # Utilities
    'prepare_time_series',
    'calculate_features',
    'detect_seasonality',
    'calculate_z_scores',
    'calculate_iqr_bounds',
    'detect_outliers',
    'extract_numbers',
    'extract_dates',
    'clean_text',
    'AICache',
    'ai_cache',
    'format_currency',
    'format_percentage',
    'format_change',
]


def init_ai_module():
    """Initialize AI module."""
    logger_name = "app.ai"
    import logging
    
    logger = logging.getLogger(logger_name)
    logger.info("AI/ML module initialized")
    
    # Verify configuration
    if not ai_config.anthropic_api_key and not ai_config.openai_api_key:
        logger.warning("No AI API keys configured - AI features will be limited")
    
    # Log enabled features
    enabled = [f for f, v in ai_config.features.items() if v]
    logger.info(f"Enabled AI features: {', '.join(enabled)}")
    
    return True
```

---

## Summary Part 1

| File | Description | Lines |
|------|-------------|-------|
| `config.py` | AI configuration & presets | ~150 |
| `client.py` | AI client manager (Anthropic, OpenAI) | ~300 |
| `utils.py` | ML utilities & helpers | ~320 |
| `base.py` | Base classes & data models | ~250 |
| `__init__.py` | Module initialization | ~100 |
| **Total** | | **~1,120 lines** |
