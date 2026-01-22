"""
Cache decorators for automatic caching and invalidation.
"""
import asyncio
import functools
import inspect
import logging
from typing import Any, Callable, List, Optional, Union, TypeVar
from datetime import datetime

from app.performance.caching.cache_manager import cache_manager
from app.performance.caching.cache_keys import (
    CacheKeyBuilder,
    CacheNamespace,
    CacheTTL,
    CacheTags
)

logger = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])


def cached(
    namespace: CacheNamespace = CacheNamespace.API,
    ttl: int = CacheTTL.MEDIUM,
    key_builder: Optional[Callable[..., str]] = None,
    tags_builder: Optional[Callable[..., List[str]]] = None,
    skip_cache_if: Optional[Callable[..., bool]] = None,
    use_local: bool = True,
    tenant_from: str = "tenant_id",
    prefix: Optional[str] = None
) -> Callable[[F], F]:
    """
    Decorator for automatic caching of function results.

    Args:
        namespace: Cache namespace
        ttl: Time-to-live in seconds
        key_builder: Custom function to build cache key
        tags_builder: Function to generate cache tags
        skip_cache_if: Condition to skip caching
        use_local: Use local L1 cache
        tenant_from: Parameter name for tenant_id
        prefix: Custom key prefix

    Usage:
        @cached(namespace=CacheNamespace.API, ttl=300)
        async def get_invoices(tenant_id: str, page: int = 1):
            ...

        @cached(
            key_builder=lambda tenant_id, invoice_id: f"invoice:{tenant_id}:{invoice_id}",
            tags_builder=lambda tenant_id, invoice_id: [f"invoice:{invoice_id}"]
        )
        async def get_invoice(tenant_id: str, invoice_id: str):
            ...
    """
    cache_key_builder = CacheKeyBuilder()

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            params = dict(bound.arguments)

            if skip_cache_if and skip_cache_if(**params):
                return await func(*args, **kwargs)

            if key_builder:
                cache_key = key_builder(**params)
            else:
                tenant_id = params.get(tenant_from, "global")
                func_name = prefix or func.__name__

                hashable_params = {
                    k: v for k, v in params.items()
                    if k != tenant_from and isinstance(v, (str, int, float, bool, type(None)))
                }

                cache_key = cache_key_builder.build(
                    namespace,
                    str(tenant_id),
                    func_name,
                    params=hashable_params
                )

            cached_value = await cache_manager.get(cache_key, use_local=use_local)
            if cached_value is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_value

            logger.debug(f"Cache MISS: {cache_key}")

            result = await func(*args, **kwargs)

            tags = []
            if tags_builder:
                tags = tags_builder(**params)

            await cache_manager.set(
                cache_key,
                result,
                ttl=ttl,
                tags=tags,
                use_local=use_local
            )

            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            return asyncio.get_event_loop().run_until_complete(
                async_wrapper(*args, **kwargs)
            )

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def invalidate_cache(
    keys: Optional[List[str]] = None,
    patterns: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    key_builder: Optional[Callable[..., List[str]]] = None,
    tag_builder: Optional[Callable[..., List[str]]] = None
) -> Callable[[F], F]:
    """
    Decorator to invalidate cache after function execution.

    Args:
        keys: Specific cache keys to invalidate
        patterns: Key patterns to invalidate
        tags: Cache tags to invalidate
        key_builder: Function to build keys from arguments
        tag_builder: Function to build tags from arguments

    Usage:
        @invalidate_cache(tags=["invoices"])
        async def create_invoice(tenant_id: str, data: dict):
            ...

        @invalidate_cache(
            tag_builder=lambda tenant_id, invoice_id: [
                f"invoice:{invoice_id}",
                f"invoices:{tenant_id}"
            ]
        )
        async def update_invoice(tenant_id: str, invoice_id: str, data: dict):
            ...
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            result = await func(*args, **kwargs)

            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            params = dict(bound.arguments)

            if keys:
                for key in keys:
                    await cache_manager.delete(key)

            if patterns:
                for pattern in patterns:
                    await cache_manager.delete_pattern(pattern)

            all_tags = list(tags or [])

            if tag_builder:
                all_tags.extend(tag_builder(**params))

            if all_tags:
                await cache_manager.invalidate_by_tags(all_tags)

            if key_builder:
                custom_keys = key_builder(**params)
                for key in custom_keys:
                    await cache_manager.delete(key)

            logger.debug(f"Cache invalidated after {func.__name__}")
            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            return asyncio.get_event_loop().run_until_complete(
                async_wrapper(*args, **kwargs)
            )

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def cache_aside(
    key_builder: Callable[..., str],
    ttl: int = CacheTTL.MEDIUM,
    loader: Optional[Callable[..., Any]] = None
) -> Callable[[F], F]:
    """
    Cache-aside pattern decorator.

    1. Check cache
    2. If miss, load from source
    3. Store in cache
    4. Return result

    Usage:
        @cache_aside(
            key_builder=lambda user_id: f"user:{user_id}:profile",
            loader=lambda user_id: db.get_user(user_id)
        )
        async def get_user_profile(user_id: str):
            ...
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            params = dict(bound.arguments)

            cache_key = key_builder(**params)

            cached_value = await cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value

            if loader:
                result = await loader(**params) if asyncio.iscoroutinefunction(loader) else loader(**params)
            else:
                result = await func(*args, **kwargs)

            if result is not None:
                await cache_manager.set(cache_key, result, ttl=ttl)

            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return functools.wraps(func)(
            lambda *args, **kwargs: asyncio.get_event_loop().run_until_complete(
                async_wrapper(*args, **kwargs)
            )
        )

    return decorator


class CacheRefresh:
    """
    Context manager for cache refresh operations.

    Usage:
        async with CacheRefresh(tenant_id, ["invoices", "dashboard"]) as refresh:
            # Perform data updates
            await update_invoice(...)

        # Cache automatically invalidated on exit
    """

    def __init__(
        self,
        tenant_id: str,
        entity_types: List[str],
        user_id: Optional[str] = None
    ):
        self.tenant_id = tenant_id
        self.entity_types = entity_types
        self.user_id = user_id
        self._tags_to_invalidate = []

    async def __aenter__(self):
        for entity_type in self.entity_types:
            self._tags_to_invalidate.append(f"{entity_type}:{self.tenant_id}")

        if self.user_id:
            self._tags_to_invalidate.append(f"user:{self.user_id}")

        self._tags_to_invalidate.append(f"dashboard:{self.tenant_id}")

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await cache_manager.invalidate_by_tags(self._tags_to_invalidate)
            logger.info(f"Cache refreshed for tenant {self.tenant_id}: {self.entity_types}")

        return False
