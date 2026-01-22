"""
Performance configuration settings.
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class PerformanceConfig(BaseSettings):
    """Performance and scalability configuration."""

    # Application
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./logiaccounting.db")
    DATABASE_REPLICA_1_URL: str = os.getenv("DATABASE_REPLICA_1_URL", "")
    DATABASE_REPLICA_2_URL: str = os.getenv("DATABASE_REPLICA_2_URL", "")

    # Database Pool
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "20"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "30"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "1800"))

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_SENTINEL_ENABLED: bool = os.getenv("REDIS_SENTINEL_ENABLED", "false").lower() == "true"
    REDIS_REPLICA_1_HOST: str = os.getenv("REDIS_REPLICA_1_HOST", "localhost")
    REDIS_REPLICA_1_PORT: int = int(os.getenv("REDIS_REPLICA_1_PORT", "6380"))
    REDIS_REPLICA_2_HOST: str = os.getenv("REDIS_REPLICA_2_HOST", "localhost")
    REDIS_REPLICA_2_PORT: int = int(os.getenv("REDIS_REPLICA_2_PORT", "6381"))

    # Cache TTLs (seconds)
    CACHE_DEFAULT_TTL: int = int(os.getenv("CACHE_DEFAULT_TTL", "300"))
    CACHE_SESSION_TTL: int = int(os.getenv("CACHE_SESSION_TTL", "86400"))
    CACHE_SHORT_TTL: int = int(os.getenv("CACHE_SHORT_TTL", "60"))
    CACHE_LONG_TTL: int = int(os.getenv("CACHE_LONG_TTL", "3600"))

    # Tracing
    TRACING_ENABLED: bool = os.getenv("TRACING_ENABLED", "false").lower() == "true"
    JAEGER_AGENT_HOST: str = os.getenv("JAEGER_AGENT_HOST", "localhost")
    JAEGER_AGENT_PORT: int = int(os.getenv("JAEGER_AGENT_PORT", "6831"))

    # Metrics
    METRICS_ENABLED: bool = os.getenv("METRICS_ENABLED", "true").lower() == "true"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = PerformanceConfig()
