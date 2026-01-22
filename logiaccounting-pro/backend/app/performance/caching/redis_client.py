"""
Redis client configuration with Sentinel support.
"""
import asyncio
from typing import Optional, List, Any
from contextlib import asynccontextmanager
import logging

try:
    import redis.asyncio as redis
    from redis.asyncio.sentinel import Sentinel
    from redis.asyncio.connection import ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    Sentinel = None
    ConnectionPool = None

from app.performance.config import settings

logger = logging.getLogger(__name__)


class RedisConfig:
    """Redis configuration settings."""

    MASTER_HOST: str = settings.REDIS_HOST
    MASTER_PORT: int = settings.REDIS_PORT
    PASSWORD: str = settings.REDIS_PASSWORD

    SENTINEL_ENABLED: bool = settings.REDIS_SENTINEL_ENABLED
    SENTINEL_HOSTS: List[tuple] = [
        ("redis-sentinel-1", 26379),
        ("redis-sentinel-2", 26379),
        ("redis-sentinel-3", 26379),
    ]
    SENTINEL_MASTER_NAME: str = "logiaccounting-master"

    MAX_CONNECTIONS: int = 100
    MIN_CONNECTIONS: int = 10
    SOCKET_TIMEOUT: float = 5.0
    SOCKET_CONNECT_TIMEOUT: float = 5.0
    RETRY_ON_TIMEOUT: bool = True

    DEFAULT_TTL: int = settings.CACHE_DEFAULT_TTL
    SESSION_TTL: int = settings.CACHE_SESSION_TTL
    LONG_TTL: int = settings.CACHE_LONG_TTL
    SHORT_TTL: int = settings.CACHE_SHORT_TTL


class RedisManager:
    """
    Redis connection manager with Sentinel support and read replica routing.
    """

    _instance: Optional['RedisManager'] = None
    _master: Optional[Any] = None
    _replica_pool: List[Any] = []
    _sentinel: Optional[Any] = None
    _replica_index: int = 0
    _lock: asyncio.Lock = None
    _initialized: bool = False

    def __new__(cls) -> 'RedisManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._lock = asyncio.Lock()
        return cls._instance

    async def initialize(self) -> None:
        """Initialize Redis connections."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis library not available, caching will be disabled")
            return

        if self._lock is None:
            self._lock = asyncio.Lock()

        async with self._lock:
            if self._initialized:
                return

            try:
                if RedisConfig.SENTINEL_ENABLED:
                    await self._init_sentinel()
                else:
                    await self._init_standalone()

                self._initialized = True
                logger.info("Redis connections initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis: {e}. Caching will be disabled.")
                self._initialized = False

    async def _init_sentinel(self) -> None:
        """Initialize Sentinel-based connections."""
        self._sentinel = Sentinel(
            RedisConfig.SENTINEL_HOSTS,
            socket_timeout=RedisConfig.SOCKET_TIMEOUT,
            password=RedisConfig.PASSWORD,
            sentinel_kwargs={"password": RedisConfig.PASSWORD}
        )

        self._master = self._sentinel.master_for(
            RedisConfig.SENTINEL_MASTER_NAME,
            socket_timeout=RedisConfig.SOCKET_TIMEOUT,
            password=RedisConfig.PASSWORD,
            decode_responses=True
        )

        self._replica_pool = [
            self._sentinel.slave_for(
                RedisConfig.SENTINEL_MASTER_NAME,
                socket_timeout=RedisConfig.SOCKET_TIMEOUT,
                password=RedisConfig.PASSWORD,
                decode_responses=True
            )
            for _ in range(3)
        ]

    async def _init_standalone(self) -> None:
        """Initialize standalone Redis connections."""
        pool = ConnectionPool(
            host=RedisConfig.MASTER_HOST,
            port=RedisConfig.MASTER_PORT,
            password=RedisConfig.PASSWORD or None,
            max_connections=RedisConfig.MAX_CONNECTIONS,
            socket_timeout=RedisConfig.SOCKET_TIMEOUT,
            socket_connect_timeout=RedisConfig.SOCKET_CONNECT_TIMEOUT,
            retry_on_timeout=RedisConfig.RETRY_ON_TIMEOUT,
            decode_responses=True
        )

        self._master = redis.Redis(connection_pool=pool)

        replica_hosts = [
            (settings.REDIS_REPLICA_1_HOST, settings.REDIS_REPLICA_1_PORT),
            (settings.REDIS_REPLICA_2_HOST, settings.REDIS_REPLICA_2_PORT),
        ]

        for host, port in replica_hosts:
            if host and host != "localhost":
                try:
                    replica_pool = ConnectionPool(
                        host=host,
                        port=port,
                        password=RedisConfig.PASSWORD or None,
                        max_connections=RedisConfig.MAX_CONNECTIONS // 2,
                        socket_timeout=RedisConfig.SOCKET_TIMEOUT,
                        decode_responses=True
                    )
                    self._replica_pool.append(redis.Redis(connection_pool=replica_pool))
                except Exception as e:
                    logger.warning(f"Failed to connect to replica {host}:{port}: {e}")

    @property
    def is_available(self) -> bool:
        """Check if Redis is available."""
        return REDIS_AVAILABLE and self._initialized and self._master is not None

    @property
    def master(self) -> Any:
        """Get master connection for writes."""
        if not self.is_available:
            raise RuntimeError("Redis not initialized or unavailable")
        return self._master

    @property
    def replica(self) -> Any:
        """Get replica connection for reads (round-robin)."""
        if not self._replica_pool:
            return self.master

        self._replica_index = (self._replica_index + 1) % len(self._replica_pool)
        return self._replica_pool[self._replica_index]

    async def close(self) -> None:
        """Close all Redis connections."""
        if self._lock is None:
            return

        async with self._lock:
            if self._master:
                await self._master.close()
                self._master = None

            for replica in self._replica_pool:
                await replica.close()
            self._replica_pool = []
            self._initialized = False

            logger.info("Redis connections closed")

    async def health_check(self) -> dict:
        """Check Redis cluster health."""
        result = {
            "available": REDIS_AVAILABLE,
            "initialized": self._initialized,
            "master": False,
            "replicas": [],
            "latency_ms": None
        }

        if not self.is_available:
            return result

        try:
            start = asyncio.get_event_loop().time()
            await self.master.ping()
            result["latency_ms"] = (asyncio.get_event_loop().time() - start) * 1000
            result["master"] = True

            for i, replica in enumerate(self._replica_pool):
                try:
                    await replica.ping()
                    result["replicas"].append({"index": i, "healthy": True})
                except Exception:
                    result["replicas"].append({"index": i, "healthy": False})

        except Exception as e:
            logger.error(f"Redis health check failed: {e}")

        return result


redis_manager = RedisManager()


async def get_redis_master() -> Any:
    """Dependency for write operations."""
    return redis_manager.master


async def get_redis_replica() -> Any:
    """Dependency for read operations."""
    return redis_manager.replica


@asynccontextmanager
async def redis_pipeline(master: bool = True):
    """
    Context manager for Redis pipeline operations.

    Usage:
        async with redis_pipeline() as pipe:
            pipe.set("key1", "value1")
            pipe.set("key2", "value2")
            results = await pipe.execute()
    """
    if not redis_manager.is_available:
        yield None
        return

    client = redis_manager.master if master else redis_manager.replica
    pipe = client.pipeline()
    try:
        yield pipe
        await pipe.execute()
    except Exception as e:
        logger.error(f"Redis pipeline error: {e}")
        raise
    finally:
        await pipe.reset()
