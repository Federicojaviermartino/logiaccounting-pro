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


def get_ai_config() -> AIConfig:
    """Get the global AI configuration instance."""
    return ai_config


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
