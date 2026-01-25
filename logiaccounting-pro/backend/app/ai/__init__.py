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

# Import submodules
from app.ai import cashflow
from app.ai import ocr
from app.ai import assistant
from app.ai import anomaly

# Service aggregator
from app.ai.service import ai_service

# Recommendations
from app.ai.recommendations.engine import recommendation_engine


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

    # Submodules
    'cashflow',
    'ocr',
    'assistant',
    'anomaly',

    # Services
    'ai_service',
    'recommendation_engine',
]


def init_ai_module():
    """Initialize AI module."""
    import logging

    logger = logging.getLogger("app.ai")
    logger.info("AI/ML module initialized")

    # Verify configuration
    if not ai_config.anthropic_api_key and not ai_config.openai_api_key:
        logger.warning("No AI API keys configured - AI features will be limited")

    # Log enabled features
    enabled = [f for f, v in ai_config.features.items() if v]
    logger.info(f"Enabled AI features: {', '.join(enabled)}")

    return True
