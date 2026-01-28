"""
Cache invalidation strategies and event-driven invalidation.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
from enum import Enum

from app.utils.datetime_utils import utc_now
from app.performance.caching.redis_client import redis_manager
from app.performance.caching.cache_manager import cache_manager
from app.performance.caching.cache_keys import CacheTags, cache_keys

logger = logging.getLogger(__name__)


class InvalidationEvent(str, Enum):
    """Events that trigger cache invalidation."""
    ENTITY_CREATED = "entity.created"
    ENTITY_UPDATED = "entity.updated"
    ENTITY_DELETED = "entity.deleted"

    BULK_IMPORT = "bulk.import"
    BULK_DELETE = "bulk.delete"

    USER_PERMISSIONS_CHANGED = "user.permissions.changed"
    USER_LOGGED_OUT = "user.logged.out"

    TENANT_SETTINGS_CHANGED = "tenant.settings.changed"
    SYSTEM_CONFIG_CHANGED = "system.config.changed"

    MANUAL_INVALIDATION = "manual.invalidation"


class InvalidationRule:
    """
    Rule defining what to invalidate based on an event.
    """

    def __init__(
        self,
        event: InvalidationEvent,
        tags: Optional[List[str]] = None,
        patterns: Optional[List[str]] = None,
        propagate_to: Optional[List[InvalidationEvent]] = None
    ):
        self.event = event
        self.tags = tags or []
        self.patterns = patterns or []
        self.propagate_to = propagate_to or []

    def get_tags(self, context: Dict[str, Any]) -> List[str]:
        """Generate tags from context."""
        return [tag.format(**context) for tag in self.tags]

    def get_patterns(self, context: Dict[str, Any]) -> List[str]:
        """Generate patterns from context."""
        return [pattern.format(**context) for pattern in self.patterns]


class CacheInvalidationService:
    """
    Centralized cache invalidation service with event-driven invalidation.

    Features:
    - Event-based invalidation rules
    - Cascading invalidation
    - Distributed invalidation via Redis Pub/Sub
    - Invalidation logging and metrics
    """

    PUBSUB_CHANNEL = "cache:invalidation"

    def __init__(self):
        self._rules: Dict[InvalidationEvent, List[InvalidationRule]] = {}
        self._subscriber_task: Optional[asyncio.Task] = None
        self._setup_default_rules()

    def _setup_default_rules(self) -> None:
        """Setup default invalidation rules."""

        self.register_rule(InvalidationRule(
            event=InvalidationEvent.ENTITY_CREATED,
            tags=[
                "{entity_type}:{tenant_id}",
                "dashboard:{tenant_id}"
            ],
            propagate_to=[InvalidationEvent.ENTITY_UPDATED]
        ))

        self.register_rule(InvalidationRule(
            event=InvalidationEvent.ENTITY_UPDATED,
            tags=[
                "{entity_type}:{entity_id}",
                "{entity_type}:{tenant_id}",
                "dashboard:{tenant_id}"
            ]
        ))

        self.register_rule(InvalidationRule(
            event=InvalidationEvent.ENTITY_DELETED,
            tags=[
                "{entity_type}:{entity_id}",
                "{entity_type}:{tenant_id}",
                "dashboard:{tenant_id}",
                "reports:{tenant_id}"
            ]
        ))

        self.register_rule(InvalidationRule(
            event=InvalidationEvent.USER_PERMISSIONS_CHANGED,
            tags=[
                "permissions:{tenant_id}",
                "user:{user_id}"
            ],
            patterns=[
                "logiaccounting:permission:*:{tenant_id}:{user_id}*"
            ]
        ))

        self.register_rule(InvalidationRule(
            event=InvalidationEvent.USER_LOGGED_OUT,
            tags=["user:{user_id}"],
            patterns=["logiaccounting:session:{user_id}*"]
        ))

        self.register_rule(InvalidationRule(
            event=InvalidationEvent.BULK_IMPORT,
            tags=[
                "{entity_type}:{tenant_id}",
                "dashboard:{tenant_id}",
                "reports:{tenant_id}"
            ]
        ))

        self.register_rule(InvalidationRule(
            event=InvalidationEvent.TENANT_SETTINGS_CHANGED,
            patterns=["logiaccounting:*:*:{tenant_id}:*"]
        ))

    def register_rule(self, rule: InvalidationRule) -> None:
        """Register an invalidation rule."""
        if rule.event not in self._rules:
            self._rules[rule.event] = []
        self._rules[rule.event].append(rule)

    async def invalidate(
        self,
        event: InvalidationEvent,
        context: Dict[str, Any],
        broadcast: bool = True
    ) -> int:
        """
        Trigger cache invalidation for an event.

        Args:
            event: The invalidation event
            context: Context with entity_type, entity_id, tenant_id, etc.
            broadcast: Whether to broadcast to other instances

        Returns:
            Number of cache entries invalidated
        """
        total_invalidated = 0
        processed_events: Set[InvalidationEvent] = set()
        events_to_process = [event]

        while events_to_process:
            current_event = events_to_process.pop(0)

            if current_event in processed_events:
                continue

            processed_events.add(current_event)
            rules = self._rules.get(current_event, [])

            for rule in rules:
                tags = rule.get_tags(context)
                for tag in tags:
                    count = await cache_manager.invalidate_by_tag(tag)
                    total_invalidated += count

                patterns = rule.get_patterns(context)
                for pattern in patterns:
                    count = await cache_manager.delete_pattern(pattern)
                    total_invalidated += count

                events_to_process.extend(rule.propagate_to)

        if broadcast and redis_manager.is_available:
            await self._broadcast_invalidation(event, context)

        logger.info(
            f"Cache invalidation completed: event={event.value}, "
            f"invalidated={total_invalidated}, context={context}"
        )

        return total_invalidated

    async def _broadcast_invalidation(
        self,
        event: InvalidationEvent,
        context: Dict[str, Any]
    ) -> None:
        """Broadcast invalidation to other instances via Pub/Sub."""
        try:
            redis_client = redis_manager.master
            import json
            message = json.dumps({
                "event": event.value,
                "context": context,
                "timestamp": utc_now().isoformat()
            })
            await redis_client.publish(
                self.PUBSUB_CHANNEL,
                message
            )
        except Exception as e:
            logger.error(f"Failed to broadcast invalidation: {e}")

    async def start_subscriber(self) -> None:
        """Start listening for invalidation events from other instances."""
        if self._subscriber_task is not None:
            return

        self._subscriber_task = asyncio.create_task(self._subscribe_loop())
        logger.info("Cache invalidation subscriber started")

    async def stop_subscriber(self) -> None:
        """Stop the invalidation subscriber."""
        if self._subscriber_task:
            self._subscriber_task.cancel()
            try:
                await self._subscriber_task
            except asyncio.CancelledError:
                pass
            self._subscriber_task = None
            logger.info("Cache invalidation subscriber stopped")

    async def _subscribe_loop(self) -> None:
        """Subscribe to invalidation events."""
        if not redis_manager.is_available:
            return

        redis_client = redis_manager.master
        pubsub = redis_client.pubsub()

        try:
            await pubsub.subscribe(self.PUBSUB_CHANNEL)

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        import json
                        data = json.loads(message["data"])
                        event = InvalidationEvent(data["event"])
                        context = data["context"]

                        await self.invalidate(event, context, broadcast=False)

                    except Exception as e:
                        logger.error(f"Error processing invalidation message: {e}")

        except asyncio.CancelledError:
            await pubsub.unsubscribe(self.PUBSUB_CHANNEL)
            raise
        except Exception as e:
            logger.error(f"Subscriber error: {e}")


invalidation_service = CacheInvalidationService()


async def invalidate_entity(
    entity_type: str,
    entity_id: str,
    tenant_id: str,
    action: str = "updated"
) -> int:
    """
    Helper to invalidate cache for an entity change.

    Args:
        entity_type: Type of entity (invoice, project, etc.)
        entity_id: Entity ID
        tenant_id: Tenant ID
        action: Action performed (created, updated, deleted)
    """
    event_map = {
        "created": InvalidationEvent.ENTITY_CREATED,
        "updated": InvalidationEvent.ENTITY_UPDATED,
        "deleted": InvalidationEvent.ENTITY_DELETED
    }

    event = event_map.get(action, InvalidationEvent.ENTITY_UPDATED)

    return await invalidation_service.invalidate(
        event,
        {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "tenant_id": tenant_id
        }
    )


async def invalidate_user_cache(user_id: str, tenant_id: str) -> int:
    """Helper to invalidate all cache for a user."""
    return await invalidation_service.invalidate(
        InvalidationEvent.USER_LOGGED_OUT,
        {"user_id": user_id, "tenant_id": tenant_id}
    )


async def invalidate_tenant_cache(tenant_id: str) -> int:
    """Helper to invalidate all cache for a tenant."""
    return await invalidation_service.invalidate(
        InvalidationEvent.TENANT_SETTINGS_CHANGED,
        {"tenant_id": tenant_id}
    )
