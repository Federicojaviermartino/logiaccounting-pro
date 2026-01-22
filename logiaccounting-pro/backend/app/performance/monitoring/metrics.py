"""
Prometheus metrics collection and exposition.
"""
import time
import functools
import logging
from typing import Optional, Callable, Any, Dict, List
from contextlib import contextmanager

logger = logging.getLogger(__name__)

try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        Summary,
        Info,
        CollectorRegistry,
        generate_latest,
        CONTENT_TYPE_LATEST,
        multiprocess,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    CollectorRegistry = None


REGISTRY = CollectorRegistry() if PROMETHEUS_AVAILABLE else None


if PROMETHEUS_AVAILABLE:
    REQUEST_COUNT = Counter(
        'http_requests_total',
        'Total HTTP requests',
        ['method', 'endpoint', 'status_code', 'tenant_id'],
        registry=REGISTRY
    )

    REQUEST_LATENCY = Histogram(
        'http_request_duration_seconds',
        'HTTP request latency',
        ['method', 'endpoint'],
        buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
        registry=REGISTRY
    )

    DB_QUERY_LATENCY = Histogram(
        'db_query_duration_seconds',
        'Database query latency',
        ['operation', 'table'],
        buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
        registry=REGISTRY
    )

    DB_QUERY_COUNT = Counter(
        'db_queries_total',
        'Total database queries',
        ['operation', 'table', 'status'],
        registry=REGISTRY
    )

    CACHE_HIT_TOTAL = Counter(
        'cache_hits_total',
        'Total cache hits',
        ['cache_type', 'namespace'],
        registry=REGISTRY
    )

    CACHE_MISS_TOTAL = Counter(
        'cache_misses_total',
        'Total cache misses',
        ['cache_type', 'namespace'],
        registry=REGISTRY
    )

    CACHE_OPERATION_LATENCY = Histogram(
        'cache_operation_duration_seconds',
        'Cache operation latency',
        ['operation', 'cache_type'],
        buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1],
        registry=REGISTRY
    )

    ACTIVE_CONNECTIONS = Gauge(
        'active_connections',
        'Active connections',
        ['type'],
        registry=REGISTRY
    )

    ACTIVE_REQUESTS = Gauge(
        'active_requests',
        'Currently processing requests',
        ['method', 'endpoint'],
        registry=REGISTRY
    )

    INVOICE_COUNT = Gauge(
        'invoices_total',
        'Total invoices by status',
        ['tenant_id', 'status'],
        registry=REGISTRY
    )

    TRANSACTION_AMOUNT = Counter(
        'transaction_amount_total',
        'Total transaction amount',
        ['tenant_id', 'type'],
        registry=REGISTRY
    )

    BACKGROUND_TASK_DURATION = Histogram(
        'background_task_duration_seconds',
        'Background task execution time',
        ['task_name'],
        buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0],
        registry=REGISTRY
    )

    BACKGROUND_TASK_COUNT = Counter(
        'background_tasks_total',
        'Total background tasks executed',
        ['task_name', 'status'],
        registry=REGISTRY
    )

    ERROR_COUNT = Counter(
        'errors_total',
        'Total errors',
        ['error_type', 'endpoint'],
        registry=REGISTRY
    )

    APP_INFO = Info(
        'app',
        'Application information',
        registry=REGISTRY
    )

    MEMORY_USAGE = Gauge(
        'memory_usage_bytes',
        'Memory usage in bytes',
        ['type'],
        registry=REGISTRY
    )

    CPU_USAGE = Gauge(
        'cpu_usage_percent',
        'CPU usage percentage',
        registry=REGISTRY
    )
else:
    REQUEST_COUNT = None
    REQUEST_LATENCY = None
    DB_QUERY_LATENCY = None
    DB_QUERY_COUNT = None
    CACHE_HIT_TOTAL = None
    CACHE_MISS_TOTAL = None
    CACHE_OPERATION_LATENCY = None
    ACTIVE_CONNECTIONS = None
    ACTIVE_REQUESTS = None
    INVOICE_COUNT = None
    TRANSACTION_AMOUNT = None
    BACKGROUND_TASK_DURATION = None
    BACKGROUND_TASK_COUNT = None
    ERROR_COUNT = None
    APP_INFO = None
    MEMORY_USAGE = None
    CPU_USAGE = None


def track_request(method: str, endpoint: str, status_code: int, duration: float, tenant_id: str = "unknown"):
    """Track HTTP request metrics."""
    if not PROMETHEUS_AVAILABLE:
        return

    REQUEST_COUNT.labels(
        method=method,
        endpoint=endpoint,
        status_code=str(status_code),
        tenant_id=tenant_id
    ).inc()

    REQUEST_LATENCY.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)


def track_db_query(operation: str, table: str, duration: float, success: bool = True):
    """Track database query metrics."""
    if not PROMETHEUS_AVAILABLE:
        return

    DB_QUERY_COUNT.labels(
        operation=operation,
        table=table,
        status="success" if success else "error"
    ).inc()

    DB_QUERY_LATENCY.labels(
        operation=operation,
        table=table
    ).observe(duration)


def track_cache_operation(
    operation: str,
    cache_type: str,
    namespace: str,
    hit: Optional[bool] = None,
    duration: float = 0
):
    """Track cache operation metrics."""
    if not PROMETHEUS_AVAILABLE:
        return

    CACHE_OPERATION_LATENCY.labels(
        operation=operation,
        cache_type=cache_type
    ).observe(duration)

    if hit is not None:
        if hit:
            CACHE_HIT_TOTAL.labels(
                cache_type=cache_type,
                namespace=namespace
            ).inc()
        else:
            CACHE_MISS_TOTAL.labels(
                cache_type=cache_type,
                namespace=namespace
            ).inc()


@contextmanager
def track_request_context(method: str, endpoint: str):
    """Context manager for tracking request metrics."""
    if not PROMETHEUS_AVAILABLE:
        yield
        return

    ACTIVE_REQUESTS.labels(method=method, endpoint=endpoint).inc()
    start_time = time.perf_counter()

    try:
        yield
    finally:
        duration = time.perf_counter() - start_time
        ACTIVE_REQUESTS.labels(method=method, endpoint=endpoint).dec()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)


def timed(metric: Any = None, labels: Dict[str, str] = None):
    """Decorator to time function execution."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not PROMETHEUS_AVAILABLE or metric is None:
                return await func(*args, **kwargs)

            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not PROMETHEUS_AVAILABLE or metric is None:
                return func(*args, **kwargs)

            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class MetricsCollector:
    """
    Centralized metrics collector with business metrics.
    """

    def __init__(self):
        self._initialized = False

    def initialize(self, app_version: str, environment: str):
        """Initialize application info metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        APP_INFO.info({
            'version': app_version,
            'environment': environment
        })
        self._initialized = True

    def record_invoice_metric(self, tenant_id: str, status: str, count: int):
        """Record invoice count by status."""
        if not PROMETHEUS_AVAILABLE:
            return

        INVOICE_COUNT.labels(
            tenant_id=tenant_id,
            status=status
        ).set(count)

    def record_transaction(self, tenant_id: str, transaction_type: str, amount: float):
        """Record transaction amount."""
        if not PROMETHEUS_AVAILABLE:
            return

        TRANSACTION_AMOUNT.labels(
            tenant_id=tenant_id,
            type=transaction_type
        ).inc(amount)

    def record_background_task(self, task_name: str, duration: float, success: bool = True):
        """Record background task execution."""
        if not PROMETHEUS_AVAILABLE:
            return

        BACKGROUND_TASK_DURATION.labels(task_name=task_name).observe(duration)
        BACKGROUND_TASK_COUNT.labels(
            task_name=task_name,
            status="success" if success else "error"
        ).inc()

    def record_error(self, error_type: str, endpoint: str):
        """Record error occurrence."""
        if not PROMETHEUS_AVAILABLE:
            return

        ERROR_COUNT.labels(
            error_type=error_type,
            endpoint=endpoint
        ).inc()

    def set_connection_count(self, connection_type: str, count: int):
        """Set active connection count."""
        if not PROMETHEUS_AVAILABLE:
            return

        ACTIVE_CONNECTIONS.labels(type=connection_type).set(count)

    def update_resource_metrics(self):
        """Update memory and CPU metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            import psutil
            process = psutil.Process()

            memory_info = process.memory_info()
            MEMORY_USAGE.labels(type="rss").set(memory_info.rss)
            MEMORY_USAGE.labels(type="vms").set(memory_info.vms)

            CPU_USAGE.set(process.cpu_percent())

        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Failed to update resource metrics: {e}")

    def get_metrics(self) -> bytes:
        """Generate metrics output for Prometheus scraping."""
        if not PROMETHEUS_AVAILABLE:
            return b""

        return generate_latest(REGISTRY)

    def get_content_type(self) -> str:
        """Get content type for metrics response."""
        if not PROMETHEUS_AVAILABLE:
            return "text/plain"

        return CONTENT_TYPE_LATEST


metrics_collector = MetricsCollector()


class MetricsMiddleware:
    """
    ASGI middleware for automatic request metrics.
    """

    def __init__(self, app, excluded_paths: List[str] = None):
        self.app = app
        self.excluded_paths = excluded_paths or ["/metrics", "/health", "/ready"]

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        if any(path.startswith(excluded) for excluded in self.excluded_paths):
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "UNKNOWN")
        endpoint = self._normalize_path(path)
        start_time = time.perf_counter()

        status_code = 500
        tenant_id = "unknown"

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
            await send(message)

        try:
            headers = dict(scope.get("headers", []))
            tenant_header = headers.get(b"x-tenant-id", b"unknown")
            tenant_id = tenant_header.decode() if isinstance(tenant_header, bytes) else str(tenant_header)

            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.perf_counter() - start_time
            track_request(method, endpoint, status_code, duration, tenant_id)

    def _normalize_path(self, path: str) -> str:
        """Normalize path by replacing IDs with placeholders."""
        import re

        path = re.sub(
            r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '/{id}',
            path,
            flags=re.IGNORECASE
        )

        path = re.sub(r'/\d+', '/{id}', path)

        return path


GRAFANA_DASHBOARD = {
    "dashboard": {
        "title": "LogiAccounting Pro - Performance Dashboard",
        "panels": [
            {
                "title": "Request Rate",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(http_requests_total[5m])",
                        "legendFormat": "{{method}} {{endpoint}}"
                    }
                ]
            },
            {
                "title": "Request Latency (p95)",
                "type": "graph",
                "targets": [
                    {
                        "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
                        "legendFormat": "p95"
                    }
                ]
            },
            {
                "title": "Cache Hit Rate",
                "type": "gauge",
                "targets": [
                    {
                        "expr": "sum(rate(cache_hits_total[5m])) / (sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m])))",
                        "legendFormat": "Hit Rate"
                    }
                ]
            },
            {
                "title": "Database Query Latency",
                "type": "graph",
                "targets": [
                    {
                        "expr": "histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m]))",
                        "legendFormat": "{{operation}} {{table}}"
                    }
                ]
            },
            {
                "title": "Active Connections",
                "type": "graph",
                "targets": [
                    {
                        "expr": "active_connections",
                        "legendFormat": "{{type}}"
                    }
                ]
            },
            {
                "title": "Error Rate",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(errors_total[5m])",
                        "legendFormat": "{{error_type}}"
                    }
                ]
            },
            {
                "title": "Memory Usage",
                "type": "graph",
                "targets": [
                    {
                        "expr": "memory_usage_bytes",
                        "legendFormat": "{{type}}"
                    }
                ]
            }
        ]
    }
}
