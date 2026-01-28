"""
Cache warming service for preloading frequently accessed data.
"""
import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timedelta

from app.utils.datetime_utils import utc_now
from app.performance.caching.cache_manager import cache_manager
from app.performance.caching.cache_keys import CacheNamespace, CacheTTL, cache_keys

logger = logging.getLogger(__name__)


class CacheWarmupTask:
    """Definition of a cache warmup task."""

    def __init__(
        self,
        name: str,
        loader: Callable[[], Any],
        key_generator: Callable[[Any], str],
        ttl: int = CacheTTL.LONG,
        priority: int = 1,
        enabled: bool = True
    ):
        self.name = name
        self.loader = loader
        self.key_generator = key_generator
        self.ttl = ttl
        self.priority = priority
        self.enabled = enabled


class CacheWarmupService:
    """
    Service for warming up cache on application startup.

    Features:
    - Priority-based warming
    - Parallel execution
    - Progress tracking
    - Error handling with retries
    """

    def __init__(self):
        self._tasks: List[CacheWarmupTask] = []
        self._is_warming = False
        self._warmup_progress: Dict[str, Any] = {}

    def register_task(self, task: CacheWarmupTask) -> None:
        """Register a warmup task."""
        self._tasks.append(task)
        self._tasks.sort(key=lambda t: t.priority)

    async def warmup(
        self,
        parallel: int = 5,
        tenant_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute cache warmup.

        Args:
            parallel: Number of parallel tasks
            tenant_ids: Optional list of tenants to warm

        Returns:
            Warmup results and statistics
        """
        if self._is_warming:
            logger.warning("Cache warmup already in progress")
            return {"status": "already_running"}

        self._is_warming = True
        start_time = utc_now()
        results = {
            "status": "completed",
            "started_at": start_time.isoformat(),
            "tasks": {},
            "total_keys": 0,
            "errors": []
        }

        try:
            enabled_tasks = [t for t in self._tasks if t.enabled]

            semaphore = asyncio.Semaphore(parallel)

            async def execute_task(task: CacheWarmupTask) -> Dict[str, Any]:
                async with semaphore:
                    return await self._execute_warmup_task(task, tenant_ids)

            task_results = await asyncio.gather(
                *[execute_task(task) for task in enabled_tasks],
                return_exceptions=True
            )

            for task, result in zip(enabled_tasks, task_results):
                if isinstance(result, Exception):
                    results["errors"].append({
                        "task": task.name,
                        "error": str(result)
                    })
                    results["tasks"][task.name] = {"status": "failed"}
                else:
                    results["tasks"][task.name] = result
                    results["total_keys"] += result.get("keys_cached", 0)

            results["completed_at"] = utc_now().isoformat()
            results["duration_seconds"] = (
                utc_now() - start_time
            ).total_seconds()

        except Exception as e:
            logger.error(f"Cache warmup failed: {e}")
            results["status"] = "failed"
            results["error"] = str(e)

        finally:
            self._is_warming = False

        logger.info(
            f"Cache warmup completed: {results['total_keys']} keys cached "
            f"in {results.get('duration_seconds', 0):.2f}s"
        )

        return results

    async def _execute_warmup_task(
        self,
        task: CacheWarmupTask,
        tenant_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Execute a single warmup task."""
        start_time = utc_now()
        keys_cached = 0
        errors = []

        try:
            if asyncio.iscoroutinefunction(task.loader):
                data = await task.loader()
            else:
                data = task.loader()

            items = data if isinstance(data, list) else [data]

            for item in items:
                try:
                    cache_key = task.key_generator(item)

                    await cache_manager.set(
                        cache_key,
                        item,
                        ttl=task.ttl
                    )
                    keys_cached += 1

                except Exception as e:
                    errors.append(str(e))

            return {
                "status": "success",
                "keys_cached": keys_cached,
                "duration_seconds": (utc_now() - start_time).total_seconds(),
                "errors": errors if errors else None
            }

        except Exception as e:
            logger.error(f"Warmup task {task.name} failed: {e}")
            return {
                "status": "failed",
                "keys_cached": keys_cached,
                "error": str(e)
            }

    def get_progress(self) -> Dict[str, Any]:
        """Get current warmup progress."""
        return {
            "is_warming": self._is_warming,
            "progress": self._warmup_progress.copy()
        }


warmup_service = CacheWarmupService()


def setup_default_warmup_tasks(
    get_active_tenants: Callable,
    get_system_config: Callable,
    get_feature_flags: Callable
) -> None:
    """
    Setup default cache warmup tasks.

    Call this during application startup with appropriate loaders.
    """

    warmup_service.register_task(CacheWarmupTask(
        name="system_config",
        loader=get_system_config,
        key_generator=lambda _: "logiaccounting:system:config",
        ttl=CacheTTL.EXTENDED,
        priority=1
    ))

    warmup_service.register_task(CacheWarmupTask(
        name="feature_flags",
        loader=get_feature_flags,
        key_generator=lambda _: "logiaccounting:feature:flags",
        ttl=CacheTTL.MEDIUM,
        priority=1
    ))

    warmup_service.register_task(CacheWarmupTask(
        name="active_tenants",
        loader=get_active_tenants,
        key_generator=lambda tenant: f"logiaccounting:tenant:{tenant['id']}:info",
        ttl=CacheTTL.LONG,
        priority=2
    ))


async def warmup_cache_on_startup() -> None:
    """
    Cache warmup hook for application startup.

    Add to FastAPI lifespan:

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            await warmup_cache_on_startup()
            yield
    """
    logger.info("Starting cache warmup...")

    try:
        results = await warmup_service.warmup(parallel=10)
        logger.info(f"Cache warmup results: {results['total_keys']} keys cached")
    except Exception as e:
        logger.error(f"Cache warmup failed: {e}")
