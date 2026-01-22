"""
AI Service Configuration
Centralized configuration for all AI features
"""

import os
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    ANTHROPIC = 'anthropic'
    OPENAI = 'openai'


class ModelTier(str, Enum):
    """Model tiers for different use cases"""
    FAST = 'fast'
    BALANCED = 'balanced'
    POWERFUL = 'powerful'


@dataclass
class LLMConfig:
    """LLM configuration"""
    provider: LLMProvider
    model_fast: str
    model_balanced: str
    model_powerful: str
    api_key: str
    max_tokens: int = 4096
    temperature: float = 0.1

    def get_model(self, tier: ModelTier) -> str:
        """Get model name for tier"""
        if tier == ModelTier.FAST:
            return self.model_fast
        elif tier == ModelTier.BALANCED:
            return self.model_balanced
        return self.model_powerful


@dataclass
class OCRConfig:
    """OCR configuration"""
    tesseract_path: str
    language: str = 'eng'
    dpi: int = 300
    psm: int = 3


@dataclass
class CashFlowConfig:
    """Cash flow prediction configuration"""
    min_history_days: int = 90
    forecast_horizons: list = None
    seasonality_mode: str = 'multiplicative'
    confidence_interval: float = 0.95

    def __post_init__(self):
        if self.forecast_horizons is None:
            self.forecast_horizons = [30, 60, 90]


@dataclass
class AnomalyConfig:
    """Anomaly detection configuration"""
    zscore_threshold: float = 3.0
    min_samples: int = 30
    duplicate_similarity_threshold: float = 0.9
    unusual_amount_multiplier: float = 3.0


class AIConfig:
    """Main AI configuration"""

    def __init__(self):
        self.llm = self._load_llm_config()
        self.ocr = self._load_ocr_config()
        self.cashflow = CashFlowConfig()
        self.anomaly = AnomalyConfig()

        self.rate_limit_requests_per_minute = int(
            os.getenv('AI_RATE_LIMIT_RPM', '60')
        )
        self.rate_limit_tokens_per_minute = int(
            os.getenv('AI_RATE_LIMIT_TPM', '100000')
        )

        self.cache_ttl_seconds = int(os.getenv('AI_CACHE_TTL', '3600'))

    def _load_llm_config(self) -> LLMConfig:
        """Load LLM configuration"""
        provider = os.getenv('LLM_PROVIDER', 'anthropic')

        if provider == 'anthropic':
            return LLMConfig(
                provider=LLMProvider.ANTHROPIC,
                model_fast='claude-3-haiku-20240307',
                model_balanced='claude-3-5-sonnet-20241022',
                model_powerful='claude-3-opus-20240229',
                api_key=os.getenv('ANTHROPIC_API_KEY', ''),
            )
        else:
            return LLMConfig(
                provider=LLMProvider.OPENAI,
                model_fast='gpt-4o-mini',
                model_balanced='gpt-4o',
                model_powerful='gpt-4-turbo',
                api_key=os.getenv('OPENAI_API_KEY', ''),
            )

    def _load_ocr_config(self) -> OCRConfig:
        """Load OCR configuration"""
        return OCRConfig(
            tesseract_path=os.getenv('TESSERACT_PATH', '/usr/bin/tesseract'),
            language=os.getenv('OCR_LANGUAGE', 'eng'),
        )


_config: Optional[AIConfig] = None


def get_ai_config() -> AIConfig:
    """Get AI configuration singleton"""
    global _config
    if _config is None:
        _config = AIConfig()
    return _config
