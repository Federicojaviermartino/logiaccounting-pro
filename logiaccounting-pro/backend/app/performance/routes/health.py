"""
Health check endpoints for Kubernetes probes.
"""
import logging
from typing import Dict, Any

try:
    from fastapi import APIRouter, Response, status
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    APIRouter = None

from app.performance.scaling.health_check import (
    health_checker,
    health_result_to_dict,
    HealthStatus
)
from app.performance.scaling.graceful_shutdown import shutdown_manager

logger = logging.getLogger(__name__)

if FASTAPI_AVAILABLE:
    router = APIRouter(tags=["Health"])

    @router.get("/health")
    async def health() -> Dict[str, Any]:
        """
        Full health check endpoint.

        Returns detailed health status of all components.
        """
        result = await health_checker.check_health()

        status_code = status.HTTP_200_OK
        if result.status == HealthStatus.DEGRADED:
            status_code = status.HTTP_200_OK
        elif result.status == HealthStatus.UNHEALTHY:
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return JSONResponse(
            content=health_result_to_dict(result),
            status_code=status_code
        )

    @router.get("/health/live")
    async def liveness() -> Response:
        """
        Kubernetes liveness probe endpoint.

        Returns 200 if the application is running.
        Used by Kubernetes to determine if the container should be restarted.
        """
        is_alive = await health_checker.check_liveness()

        if is_alive:
            return Response(
                content='{"status": "alive"}',
                media_type="application/json",
                status_code=status.HTTP_200_OK
            )
        else:
            return Response(
                content='{"status": "dead"}',
                media_type="application/json",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    @router.get("/health/ready")
    async def readiness() -> Response:
        """
        Kubernetes readiness probe endpoint.

        Returns 200 if the application can serve requests.
        Used by Kubernetes to determine if traffic should be sent to this pod.
        """
        is_ready = await health_checker.check_readiness()

        if is_ready:
            return Response(
                content='{"status": "ready"}',
                media_type="application/json",
                status_code=status.HTTP_200_OK
            )
        else:
            return Response(
                content='{"status": "not_ready"}',
                media_type="application/json",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    @router.get("/health/startup")
    async def startup_status() -> Dict[str, Any]:
        """
        Startup status endpoint for debugging.

        Returns detailed startup information.
        """
        startup_info = await health_checker.get_startup_status()
        shutdown_info = shutdown_manager.get_state()

        return {
            "startup": startup_info,
            "shutdown": shutdown_info
        }

    @router.get("/metrics")
    async def metrics() -> Response:
        """
        Prometheus metrics endpoint.

        Returns metrics in Prometheus exposition format.
        """
        try:
            from app.performance.monitoring.metrics import metrics_collector

            content = metrics_collector.get_metrics()
            content_type = metrics_collector.get_content_type()

            return Response(
                content=content,
                media_type=content_type,
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
            return Response(
                content=f"Error: {e}",
                media_type="text/plain",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

else:
    router = None
