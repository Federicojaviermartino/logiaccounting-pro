"""
Monitoring module for metrics, tracing, and logging.
"""
from app.performance.monitoring.metrics import (
    MetricsCollector,
    metrics_collector,
    track_request,
    track_db_query,
    track_cache_operation,
    REQUEST_LATENCY,
    REQUEST_COUNT,
    DB_QUERY_LATENCY,
    CACHE_HIT_TOTAL,
    CACHE_MISS_TOTAL,
    ACTIVE_CONNECTIONS,
)
from app.performance.monitoring.tracing import (
    TracingMiddleware,
    trace_span,
    get_current_trace_id,
    setup_tracing,
)
from app.performance.monitoring.logging_config import (
    setup_logging,
    get_logger,
    LogContext,
    StructuredLogger,
)

__all__ = [
    # Metrics
    "MetricsCollector",
    "metrics_collector",
    "track_request",
    "track_db_query",
    "track_cache_operation",
    "REQUEST_LATENCY",
    "REQUEST_COUNT",
    "DB_QUERY_LATENCY",
    "CACHE_HIT_TOTAL",
    "CACHE_MISS_TOTAL",
    "ACTIVE_CONNECTIONS",
    # Tracing
    "TracingMiddleware",
    "trace_span",
    "get_current_trace_id",
    "setup_tracing",
    # Logging
    "setup_logging",
    "get_logger",
    "LogContext",
    "StructuredLogger",
]
