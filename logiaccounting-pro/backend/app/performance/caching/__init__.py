"""
Caching Module - Multi-layer caching with Redis cluster support.

Components:
- redis_client: Redis connection manager with Sentinel support
- cache_manager: Unified cache interface with L1/L2 caching
- cache_keys: Key generation and pattern management
- decorators: @cached and @invalidate_cache decorators
- invalidation: Event-driven cache invalidation
- warmup: Cache warming service
"""

from app.performance.caching.redis_client import RedisManager, redis_manager
from app.performance.caching.cache_manager import CacheManager, cache_manager
from app.performance.caching.cache_keys import CacheKeyBuilder, cache_keys, CacheTags, CacheTTL, CacheNamespace
from app.performance.caching.decorators import cached, invalidate_cache, cache_aside
from app.performance.caching.invalidation import invalidation_service, invalidate_entity
from app.performance.caching.invalidation import invalidation_service as cache_invalidation_service
from app.performance.caching.warmup import warmup_service
from app.performance.caching.warmup import warmup_service as cache_warmup_service

__all__ = [
    "RedisManager",
    "redis_manager",
    "CacheManager",
    "cache_manager",
    "CacheKeyBuilder",
    "cache_keys",
    "CacheTags",
    "CacheTTL",
    "cached",
    "invalidate_cache",
    "cache_aside",
    "invalidation_service",
    "invalidate_entity",
    "warmup_service",
    "CacheNamespace",
    "cache_invalidation_service",
    "cache_warmup_service",
]
