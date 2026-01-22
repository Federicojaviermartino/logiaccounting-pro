"""
Unified cache manager with multi-layer caching support.
"""
import asyncio
import hashlib
import json
import logging
from typing import Any, Optional, Union, List, Callable, TypeVar
from datetime import datetime, timedelta
from functools import wraps
import pickle

from pydantic import BaseModel

from app.performance.caching.redis_client import redis_manager, RedisConfig
from app.performance.caching.cache_keys import CacheKeyBuilder

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheStats(BaseModel):
    """Cache statistics model."""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0
    hit_rate: float = 0.0
    avg_latency_ms: float = 0.0


class CacheEntry(BaseModel):
    """Cache entry wrapper with metadata."""
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    tags: List[str] = []
    version: int = 1


class CacheManager:
    """
    Unified cache manager supporting multiple cache layers and strategies.

    Features:
    - Multi-layer caching (L1: local, L2: Redis)
    - Tag-based invalidation
    - Cache versioning
    - Statistics tracking
    - Automatic serialization
    """

    _instance: Optional['CacheManager'] = None
    _local_cache: dict = {}
    _local_cache_ttl: dict = {}
    _stats: CacheStats = None
    _latencies: List[float] = []

    def __new__(cls) -> 'CacheManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._stats = CacheStats()
            cls._instance._local_cache = {}
            cls._instance._local_cache_ttl = {}
            cls._instance._latencies = []
        return cls._instance

    def __init__(self):
        self.key_builder = CacheKeyBuilder()
        self._max_local_cache_size = 1000
        self._local_ttl = 60

    async def get(
        self,
        key: str,
        default: Any = None,
        use_local: bool = True
    ) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key
            default: Default value if not found
            use_local: Whether to check local cache first

        Returns:
            Cached value or default
        """
        start_time = asyncio.get_event_loop().time()

        try:
            if use_local:
                local_value = self._get_local(key)
                if local_value is not None:
                    self._record_hit(start_time)
                    return local_value

            if not redis_manager.is_available:
                self._record_miss()
                return default

            redis_client = redis_manager.replica
            raw_value = await redis_client.get(key)

            if raw_value is None:
                self._record_miss()
                return default

            value = self._deserialize(raw_value)

            if use_local:
                self._set_local(key, value)

            self._record_hit(start_time)
            return value

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self._stats.errors += 1
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None,
        use_local: bool = True
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
            tags: Tags for invalidation
            use_local: Whether to set in local cache

        Returns:
            Success status
        """
        try:
            ttl = ttl or RedisConfig.DEFAULT_TTL

            serialized = self._serialize(value)

            if redis_manager.is_available:
                redis_client = redis_manager.master
                await redis_client.setex(key, ttl, serialized)

                if tags:
                    await self._register_tags(key, tags, ttl)

            if use_local:
                self._set_local(key, value, min(ttl, self._local_ttl))

            self._stats.sets += 1
            return True

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            self._stats.errors += 1
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            self._delete_local(key)

            if redis_manager.is_available:
                redis_client = redis_manager.master
                await redis_client.delete(key)

            self._stats.deletes += 1
            return True

        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            self._stats.errors += 1
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.

        Args:
            pattern: Redis key pattern (e.g., "user:*:profile")

        Returns:
            Number of keys deleted
        """
        if not redis_manager.is_available:
            return 0

        try:
            redis_client = redis_manager.master

            deleted_count = 0
            cursor = 0

            while True:
                cursor, keys = await redis_client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )

                if keys:
                    await redis_client.delete(*keys)
                    deleted_count += len(keys)

                    for key in keys:
                        self._delete_local(key)

                if cursor == 0:
                    break

            logger.info(f"Deleted {deleted_count} keys matching pattern: {pattern}")
            return deleted_count

        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0

    async def _register_tags(
        self,
        key: str,
        tags: List[str],
        ttl: int
    ) -> None:
        """Register cache key with tags for invalidation."""
        if not redis_manager.is_available:
            return

        redis_client = redis_manager.master
        pipe = redis_client.pipeline()

        for tag in tags:
            tag_key = f"cache:tag:{tag}"
            pipe.sadd(tag_key, key)
            pipe.expire(tag_key, ttl + 60)

        await pipe.execute()

    async def invalidate_by_tag(self, tag: str) -> int:
        """
        Invalidate all cache entries with a specific tag.

        Args:
            tag: Tag to invalidate

        Returns:
            Number of entries invalidated
        """
        if not redis_manager.is_available:
            return 0

        try:
            redis_client = redis_manager.master
            tag_key = f"cache:tag:{tag}"

            keys = await redis_client.smembers(tag_key)

            if not keys:
                return 0

            pipe = redis_client.pipeline()
            for key in keys:
                pipe.delete(key)
                self._delete_local(key)
            pipe.delete(tag_key)
            await pipe.execute()

            logger.info(f"Invalidated {len(keys)} entries with tag: {tag}")
            return len(keys)

        except Exception as e:
            logger.error(f"Tag invalidation error for {tag}: {e}")
            return 0

    async def invalidate_by_tags(self, tags: List[str]) -> int:
        """Invalidate multiple tags."""
        total = 0
        for tag in tags:
            total += await self.invalidate_by_tag(tag)
        return total

    async def mget(self, keys: List[str]) -> dict:
        """
        Get multiple values at once.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary of key -> value
        """
        if not redis_manager.is_available:
            return {}

        try:
            redis_client = redis_manager.replica
            values = await redis_client.mget(keys)

            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    result[key] = self._deserialize(value)
                    self._record_hit(asyncio.get_event_loop().time())
                else:
                    self._record_miss()

            return result

        except Exception as e:
            logger.error(f"Cache mget error: {e}")
            return {}

    async def mset(
        self,
        mapping: dict,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set multiple values at once.

        Args:
            mapping: Dictionary of key -> value
            ttl: Time-to-live in seconds

        Returns:
            Success status
        """
        if not redis_manager.is_available:
            return False

        try:
            ttl = ttl or RedisConfig.DEFAULT_TTL
            redis_client = redis_manager.master
            pipe = redis_client.pipeline()

            for key, value in mapping.items():
                serialized = self._serialize(value)
                pipe.setex(key, ttl, serialized)
                self._set_local(key, value)

            await pipe.execute()
            self._stats.sets += len(mapping)
            return True

        except Exception as e:
            logger.error(f"Cache mset error: {e}")
            return False

    def _get_local(self, key: str) -> Optional[Any]:
        """Get from local cache."""
        if key not in self._local_cache:
            return None

        if key in self._local_cache_ttl:
            if datetime.now() > self._local_cache_ttl[key]:
                del self._local_cache[key]
                del self._local_cache_ttl[key]
                return None

        return self._local_cache[key]

    def _set_local(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """Set in local cache with LRU eviction."""
        if len(self._local_cache) >= self._max_local_cache_size:
            keys_to_remove = list(self._local_cache.keys())[:100]
            for k in keys_to_remove:
                self._local_cache.pop(k, None)
                self._local_cache_ttl.pop(k, None)

        self._local_cache[key] = value

        if ttl:
            self._local_cache_ttl[key] = datetime.now() + timedelta(seconds=ttl)

    def _delete_local(self, key: str) -> None:
        """Delete from local cache."""
        self._local_cache.pop(key, None)
        self._local_cache_ttl.pop(key, None)

    def clear_local_cache(self) -> None:
        """Clear entire local cache."""
        self._local_cache.clear()
        self._local_cache_ttl.clear()

    def _serialize(self, value: Any) -> str:
        """Serialize value for Redis storage."""
        if isinstance(value, (str, int, float, bool)):
            return json.dumps({"_type": "simple", "value": value})

        if isinstance(value, BaseModel):
            return json.dumps({
                "_type": "pydantic",
                "_class": f"{value.__class__.__module__}.{value.__class__.__name__}",
                "value": value.model_dump()
            })

        if isinstance(value, (dict, list)):
            return json.dumps({"_type": "json", "value": value})

        return json.dumps({
            "_type": "pickle",
            "value": pickle.dumps(value).hex()
        })

    def _deserialize(self, raw: str) -> Any:
        """Deserialize value from Redis."""
        try:
            data = json.loads(raw)
            type_hint = data.get("_type", "simple")

            if type_hint == "simple":
                return data["value"]

            if type_hint == "json":
                return data["value"]

            if type_hint == "pydantic":
                return data["value"]

            if type_hint == "pickle":
                return pickle.loads(bytes.fromhex(data["value"]))

            return data.get("value")

        except json.JSONDecodeError:
            return raw

    def _record_hit(self, start_time: float) -> None:
        """Record cache hit."""
        self._stats.hits += 1
        latency = (asyncio.get_event_loop().time() - start_time) * 1000
        self._latencies.append(latency)
        if len(self._latencies) > 1000:
            self._latencies = self._latencies[-1000:]
        self._update_stats()

    def _record_miss(self) -> None:
        """Record cache miss."""
        self._stats.misses += 1
        self._update_stats()

    def _update_stats(self) -> None:
        """Update calculated statistics."""
        total = self._stats.hits + self._stats.misses
        if total > 0:
            self._stats.hit_rate = self._stats.hits / total

        if self._latencies:
            self._stats.avg_latency_ms = sum(self._latencies) / len(self._latencies)

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self._stats.model_copy()

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self._stats = CacheStats()
        self._latencies = []


cache_manager = CacheManager()
