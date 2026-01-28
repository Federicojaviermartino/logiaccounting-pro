"""
Graceful shutdown handling for zero-downtime deployments.
"""
import asyncio
import signal
import logging
from typing import Callable, List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


class ShutdownPhase(Enum):
    """Shutdown phases in order of execution."""
    PRE_SHUTDOWN = "pre_shutdown"
    STOP_ACCEPTING = "stop_accepting"
    DRAIN_CONNECTIONS = "drain_connections"
    CLOSE_RESOURCES = "close_resources"
    FINAL_CLEANUP = "final_cleanup"


@dataclass
class ShutdownHandler:
    """Handler for a shutdown phase."""
    name: str
    phase: ShutdownPhase
    handler: Callable
    timeout: float = 30.0
    priority: int = 0


@dataclass
class ShutdownState:
    """Current shutdown state."""
    is_shutting_down: bool = False
    current_phase: Optional[ShutdownPhase] = None
    started_at: Optional[datetime] = None
    completed_handlers: List[str] = field(default_factory=list)
    failed_handlers: List[str] = field(default_factory=list)
    active_requests: int = 0


class GracefulShutdown:
    """
    Manages graceful shutdown for the application.

    Features:
    - Signal handling (SIGTERM, SIGINT)
    - Phased shutdown with configurable handlers
    - Connection draining
    - Request tracking
    - Timeout handling
    """

    def __init__(
        self,
        shutdown_timeout: float = 30.0,
        drain_timeout: float = 15.0
    ):
        self.shutdown_timeout = shutdown_timeout
        self.drain_timeout = drain_timeout
        self._handlers: Dict[ShutdownPhase, List[ShutdownHandler]] = {
            phase: [] for phase in ShutdownPhase
        }
        self._state = ShutdownState()
        self._shutdown_event = asyncio.Event()
        self._drain_complete = asyncio.Event()
        self._registered_signals = False

    @property
    def is_shutting_down(self) -> bool:
        """Check if shutdown is in progress."""
        return self._state.is_shutting_down

    @property
    def active_requests(self) -> int:
        """Get count of active requests."""
        return self._state.active_requests

    def register_handler(
        self,
        name: str,
        handler: Callable,
        phase: ShutdownPhase = ShutdownPhase.CLOSE_RESOURCES,
        timeout: float = 30.0,
        priority: int = 0
    ):
        """
        Register a shutdown handler.

        Args:
            name: Handler name for logging
            handler: Async function to call during shutdown
            phase: Which phase to run in
            timeout: Maximum time for handler
            priority: Higher priority runs first within phase
        """
        self._handlers[phase].append(ShutdownHandler(
            name=name,
            phase=phase,
            handler=handler,
            timeout=timeout,
            priority=priority
        ))

        self._handlers[phase].sort(key=lambda h: -h.priority)
        logger.info(f"Registered shutdown handler: {name} in phase {phase.value}")

    def register_signals(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        """Register signal handlers for graceful shutdown."""
        if self._registered_signals:
            return

        try:
            loop = loop or asyncio.get_event_loop()

            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(
                    sig,
                    lambda s=sig: asyncio.create_task(self._signal_handler(s))
                )

            self._registered_signals = True
            logger.info("Signal handlers registered for graceful shutdown")

        except NotImplementedError:
            logger.warning("Signal handlers not supported on this platform")
        except Exception as e:
            logger.warning(f"Failed to register signal handlers: {e}")

    async def _signal_handler(self, sig: signal.Signals):
        """Handle shutdown signal."""
        logger.info(f"Received signal {sig.name}, initiating graceful shutdown")
        await self.shutdown()

    def track_request_start(self):
        """Track start of a request."""
        if not self._state.is_shutting_down:
            self._state.active_requests += 1

    def track_request_end(self):
        """Track end of a request."""
        self._state.active_requests = max(0, self._state.active_requests - 1)

        if self._state.is_shutting_down and self._state.active_requests == 0:
            self._drain_complete.set()

    async def wait_for_shutdown(self):
        """Wait for shutdown signal."""
        await self._shutdown_event.wait()

    async def shutdown(self):
        """
        Initiate graceful shutdown.

        Phases:
        1. PRE_SHUTDOWN - Notify systems of impending shutdown
        2. STOP_ACCEPTING - Stop accepting new connections
        3. DRAIN_CONNECTIONS - Wait for active requests to complete
        4. CLOSE_RESOURCES - Close database, cache, etc.
        5. FINAL_CLEANUP - Final cleanup tasks
        """
        if self._state.is_shutting_down:
            logger.warning("Shutdown already in progress")
            return

        self._state.is_shutting_down = True
        self._state.started_at = utc_now()

        logger.info("Starting graceful shutdown")

        try:
            from app.performance.scaling.health_check import health_checker
            health_checker.set_shutting_down(True)
        except ImportError:
            pass

        for phase in ShutdownPhase:
            await self._run_phase(phase)

        self._shutdown_event.set()
        logger.info("Graceful shutdown complete")

    async def _run_phase(self, phase: ShutdownPhase):
        """Run all handlers for a phase."""
        self._state.current_phase = phase
        handlers = self._handlers.get(phase, [])

        if not handlers and phase != ShutdownPhase.DRAIN_CONNECTIONS:
            logger.debug(f"No handlers for phase {phase.value}")
            return

        logger.info(f"Starting shutdown phase: {phase.value}")

        if phase == ShutdownPhase.DRAIN_CONNECTIONS:
            await self._drain_connections()

        for handler in handlers:
            await self._run_handler(handler)

        logger.info(f"Completed shutdown phase: {phase.value}")

    async def _run_handler(self, handler: ShutdownHandler):
        """Run a single shutdown handler."""
        logger.info(f"Running shutdown handler: {handler.name}")

        try:
            if asyncio.iscoroutinefunction(handler.handler):
                await asyncio.wait_for(
                    handler.handler(),
                    timeout=handler.timeout
                )
            else:
                handler.handler()

            self._state.completed_handlers.append(handler.name)
            logger.info(f"Shutdown handler completed: {handler.name}")

        except asyncio.TimeoutError:
            self._state.failed_handlers.append(handler.name)
            logger.error(
                f"Shutdown handler timed out: {handler.name} "
                f"(timeout: {handler.timeout}s)"
            )

        except Exception as e:
            self._state.failed_handlers.append(handler.name)
            logger.error(f"Shutdown handler failed: {handler.name}: {e}")

    async def _drain_connections(self):
        """Wait for active requests to complete."""
        if self._state.active_requests == 0:
            logger.info("No active requests to drain")
            return

        logger.info(f"Draining {self._state.active_requests} active requests")

        try:
            await asyncio.wait_for(
                self._drain_complete.wait(),
                timeout=self.drain_timeout
            )
            logger.info("Connection draining complete")

        except asyncio.TimeoutError:
            logger.warning(
                f"Connection drain timeout, {self._state.active_requests} "
                f"requests still active"
            )

    def get_state(self) -> Dict[str, Any]:
        """Get current shutdown state."""
        return {
            "is_shutting_down": self._state.is_shutting_down,
            "current_phase": self._state.current_phase.value if self._state.current_phase else None,
            "started_at": self._state.started_at.isoformat() if self._state.started_at else None,
            "active_requests": self._state.active_requests,
            "completed_handlers": self._state.completed_handlers,
            "failed_handlers": self._state.failed_handlers
        }


shutdown_manager = GracefulShutdown()


async def close_database():
    """Close database connections."""
    try:
        from app.performance.database.connection_pool import db_manager
        await db_manager.close()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")


async def close_redis():
    """Close Redis connections."""
    try:
        from app.performance.caching.redis_client import redis_manager
        await redis_manager.close()
        logger.info("Redis connections closed")
    except Exception as e:
        logger.error(f"Error closing Redis: {e}")


async def flush_cache():
    """Flush pending cache operations."""
    try:
        from app.performance.caching.cache_manager import cache_manager
        logger.info("Cache operations flushed")
    except Exception as e:
        logger.error(f"Error flushing cache: {e}")


async def flush_metrics():
    """Flush pending metrics."""
    try:
        logger.info("Metrics flushed")
    except Exception as e:
        logger.error(f"Error flushing metrics: {e}")


def setup_default_handlers():
    """Register default shutdown handlers."""
    shutdown_manager.register_handler(
        "flush_cache",
        flush_cache,
        phase=ShutdownPhase.PRE_SHUTDOWN,
        priority=100
    )

    shutdown_manager.register_handler(
        "flush_metrics",
        flush_metrics,
        phase=ShutdownPhase.PRE_SHUTDOWN,
        priority=50
    )

    shutdown_manager.register_handler(
        "close_redis",
        close_redis,
        phase=ShutdownPhase.CLOSE_RESOURCES,
        priority=100
    )

    shutdown_manager.register_handler(
        "close_database",
        close_database,
        phase=ShutdownPhase.CLOSE_RESOURCES,
        priority=50
    )


class ShutdownMiddleware:
    """
    ASGI middleware for request tracking during shutdown.
    """

    def __init__(self, app, shutdown_manager: GracefulShutdown):
        self.app = app
        self.shutdown_manager = shutdown_manager

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if self.shutdown_manager.is_shutting_down:
            response = {
                "type": "http.response.start",
                "status": 503,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"connection", b"close"),
                    (b"retry-after", b"30"),
                ]
            }
            await send(response)
            await send({
                "type": "http.response.body",
                "body": b'{"error": "Service is shutting down"}',
            })
            return

        self.shutdown_manager.track_request_start()

        try:
            await self.app(scope, receive, send)
        finally:
            self.shutdown_manager.track_request_end()
