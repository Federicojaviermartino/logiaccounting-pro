"""
Performance & Scalability Module - Phase 20

Enterprise-grade infrastructure for high availability:
- Multi-layer caching with Redis cluster
- Database optimization with read replicas
- Prometheus metrics and Grafana dashboards
- Distributed tracing with OpenTelemetry
- Kubernetes deployment with auto-scaling
"""

from app.performance.config import PerformanceConfig

from app.performance.caching import (
    cache_manager,
    redis_manager,
    CacheKeyBuilder,
    CacheNamespace,
    CacheTTL,
    cached,
    invalidate_cache,
    cache_invalidation_service,
    cache_warmup_service,
)

from app.performance.database import (
    db_manager,
    DatabaseRole,
    query_optimizer,
    partition_manager,
    mv_manager,
    route_to_replica,
    QueryRouter,
)

from app.performance.monitoring import (
    metrics_collector,
    track_request,
    track_db_query,
    track_cache_operation,
    setup_tracing,
    trace_span,
    get_current_trace_id,
    setup_logging,
    get_logger,
    LogContext,
)

from app.performance.scaling import (
    health_checker,
    shutdown_manager,
    HealthStatus,
    ShutdownPhase,
)

__all__ = [
    "PerformanceConfig",
    # Caching
    "cache_manager",
    "redis_manager",
    "CacheKeyBuilder",
    "CacheNamespace",
    "CacheTTL",
    "cached",
    "invalidate_cache",
    "cache_invalidation_service",
    "cache_warmup_service",
    # Database
    "db_manager",
    "DatabaseRole",
    "query_optimizer",
    "partition_manager",
    "mv_manager",
    "route_to_replica",
    "QueryRouter",
    # Monitoring
    "metrics_collector",
    "track_request",
    "track_db_query",
    "track_cache_operation",
    "setup_tracing",
    "trace_span",
    "get_current_trace_id",
    "setup_logging",
    "get_logger",
    "LogContext",
    # Scaling
    "health_checker",
    "shutdown_manager",
    "HealthStatus",
    "ShutdownPhase",
]
