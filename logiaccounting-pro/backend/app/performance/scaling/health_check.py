"""
Health check system for Kubernetes probes and monitoring.
"""
import asyncio
import logging
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status of a component."""
    name: str
    status: HealthStatus
    message: str = ""
    latency_ms: float = 0
    last_check: datetime = field(default_factory=utc_now)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthCheckResult:
    """Overall health check result."""
    status: HealthStatus
    components: Dict[str, ComponentHealth]
    timestamp: datetime
    version: str = "1.0.0"
    uptime_seconds: float = 0


class HealthChecker:
    """
    Comprehensive health checking system.

    Features:
    - Liveness probe (is the app running?)
    - Readiness probe (can the app serve requests?)
    - Component-level health checks
    - Configurable timeouts and thresholds
    """

    def __init__(self):
        self._checks: Dict[str, Callable] = {}
        self._start_time = utc_now()
        self._is_ready = False
        self._is_shutting_down = False
        self._last_results: Dict[str, ComponentHealth] = {}
        self._check_timeout = 5.0

    def register_check(
        self,
        name: str,
        check_func: Callable,
        critical: bool = True
    ):
        """
        Register a health check function.

        Args:
            name: Check name
            check_func: Async function that returns (bool, str) tuple
            critical: If True, failure makes system unhealthy
        """
        self._checks[name] = {
            'func': check_func,
            'critical': critical
        }
        logger.info(f"Registered health check: {name}")

    def unregister_check(self, name: str):
        """Remove a health check."""
        if name in self._checks:
            del self._checks[name]
            logger.info(f"Unregistered health check: {name}")

    def set_ready(self, ready: bool = True):
        """Set readiness status."""
        self._is_ready = ready
        logger.info(f"Readiness status set to: {ready}")

    def set_shutting_down(self, shutting_down: bool = True):
        """Set shutdown status."""
        self._is_shutting_down = shutting_down
        logger.info(f"Shutdown status set to: {shutting_down}")

    async def check_liveness(self) -> bool:
        """
        Simple liveness check.
        Returns True if the application is running.
        """
        return not self._is_shutting_down

    async def check_readiness(self) -> bool:
        """
        Readiness check.
        Returns True if the application can serve requests.
        """
        if self._is_shutting_down:
            return False

        if not self._is_ready:
            return False

        result = await self.check_health()
        return result.status != HealthStatus.UNHEALTHY

    async def check_health(self) -> HealthCheckResult:
        """
        Run all health checks and return aggregated result.
        """
        components: Dict[str, ComponentHealth] = {}
        overall_status = HealthStatus.HEALTHY

        for name, check_info in self._checks.items():
            try:
                start_time = time.perf_counter()

                result = await asyncio.wait_for(
                    check_info['func'](),
                    timeout=self._check_timeout
                )

                latency = (time.perf_counter() - start_time) * 1000

                if isinstance(result, tuple):
                    success, message = result
                    details = {}
                elif isinstance(result, dict):
                    success = result.get('success', result.get('healthy', True))
                    message = result.get('message', '')
                    details = result.get('details', {})
                else:
                    success = bool(result)
                    message = ""
                    details = {}

                status = HealthStatus.HEALTHY if success else HealthStatus.UNHEALTHY

                components[name] = ComponentHealth(
                    name=name,
                    status=status,
                    message=message,
                    latency_ms=round(latency, 2),
                    details=details
                )

                if not success:
                    if check_info['critical']:
                        overall_status = HealthStatus.UNHEALTHY
                    elif overall_status == HealthStatus.HEALTHY:
                        overall_status = HealthStatus.DEGRADED

            except asyncio.TimeoutError:
                components[name] = ComponentHealth(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check timed out after {self._check_timeout}s",
                    latency_ms=self._check_timeout * 1000
                )
                if check_info['critical']:
                    overall_status = HealthStatus.UNHEALTHY

            except Exception as e:
                components[name] = ComponentHealth(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=str(e),
                    latency_ms=0
                )
                if check_info['critical']:
                    overall_status = HealthStatus.UNHEALTHY

        self._last_results = components

        uptime = (utc_now() - self._start_time).total_seconds()

        return HealthCheckResult(
            status=overall_status,
            components=components,
            timestamp=utc_now(),
            uptime_seconds=uptime
        )

    async def get_startup_status(self) -> Dict[str, Any]:
        """Get startup status for debugging."""
        return {
            "is_ready": self._is_ready,
            "is_shutting_down": self._is_shutting_down,
            "registered_checks": list(self._checks.keys()),
            "uptime_seconds": (utc_now() - self._start_time).total_seconds()
        }


async def check_database() -> Dict[str, Any]:
    """Check database connectivity."""
    try:
        from app.performance.database.connection_pool import db_manager

        if not db_manager.is_available:
            return {
                "success": False,
                "message": "Database not configured"
            }

        health = await db_manager.health_check()

        return {
            "success": health.get("status") == "healthy",
            "message": health.get("message", ""),
            "details": {
                "primary": health.get("primary"),
                "replica": health.get("replica"),
                "pool_size": health.get("pool_size")
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


async def check_redis() -> Dict[str, Any]:
    """Check Redis connectivity."""
    try:
        from app.performance.caching.redis_client import redis_manager

        if not redis_manager.is_available:
            return {
                "success": False,
                "message": "Redis not configured"
            }

        health = await redis_manager.health_check()

        return {
            "success": health.get("status") == "healthy",
            "message": health.get("message", ""),
            "details": health.get("details", {})
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


async def check_cache() -> Dict[str, Any]:
    """Check cache system."""
    try:
        from app.performance.caching.cache_manager import cache_manager

        stats = await cache_manager.get_stats()

        return {
            "success": True,
            "message": "Cache operational",
            "details": stats
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


async def check_disk_space() -> Dict[str, Any]:
    """Check available disk space."""
    try:
        import shutil

        total, used, free = shutil.disk_usage("/")

        free_percent = (free / total) * 100
        threshold = 10

        return {
            "success": free_percent > threshold,
            "message": f"{free_percent:.1f}% disk space available",
            "details": {
                "total_gb": round(total / (1024**3), 2),
                "used_gb": round(used / (1024**3), 2),
                "free_gb": round(free / (1024**3), 2),
                "free_percent": round(free_percent, 2)
            }
        }
    except Exception as e:
        return {
            "success": True,
            "message": f"Could not check disk space: {e}"
        }


async def check_memory() -> Dict[str, Any]:
    """Check memory usage."""
    try:
        import psutil

        memory = psutil.virtual_memory()
        threshold = 90

        return {
            "success": memory.percent < threshold,
            "message": f"{memory.percent}% memory used",
            "details": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "percent_used": memory.percent
            }
        }
    except ImportError:
        return {
            "success": True,
            "message": "psutil not available"
        }
    except Exception as e:
        return {
            "success": True,
            "message": f"Could not check memory: {e}"
        }


health_checker = HealthChecker()


def setup_default_checks():
    """Register default health checks."""
    health_checker.register_check("database", check_database, critical=True)
    health_checker.register_check("redis", check_redis, critical=False)
    health_checker.register_check("cache", check_cache, critical=False)
    health_checker.register_check("disk", check_disk_space, critical=False)
    health_checker.register_check("memory", check_memory, critical=False)


def health_result_to_dict(result: HealthCheckResult) -> Dict[str, Any]:
    """Convert health result to dictionary for JSON response."""
    return {
        "status": result.status.value,
        "timestamp": result.timestamp.isoformat() + "Z",
        "version": result.version,
        "uptime_seconds": round(result.uptime_seconds, 2),
        "components": {
            name: {
                "status": comp.status.value,
                "message": comp.message,
                "latency_ms": comp.latency_ms,
                "last_check": comp.last_check.isoformat() + "Z",
                "details": comp.details
            }
            for name, comp in result.components.items()
        }
    }
