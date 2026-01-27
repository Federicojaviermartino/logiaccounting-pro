"""
Scaling module for health checks, graceful shutdown, and auto-scaling support.
"""
from app.performance.scaling.health_check import (
    HealthChecker,
    health_checker,
    HealthStatus,
    ComponentHealth,
)
from app.performance.scaling.graceful_shutdown import (
    GracefulShutdown,
    shutdown_manager,
    ShutdownPhase,
)

__all__ = [
    # Health checks
    "HealthChecker",
    "health_checker",
    "HealthStatus",
    "ComponentHealth",
    # Graceful shutdown
    "GracefulShutdown",
    "shutdown_manager",
    "ShutdownPhase",
]
