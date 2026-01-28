"""
Webhook Service
Handles incoming and outgoing webhooks
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from uuid import uuid4
from app.utils.datetime_utils import utc_now
import hmac
import hashlib
import logging
import asyncio

logger = logging.getLogger(__name__)


class WebhookSubscription:
    """Represents a webhook subscription."""

    def __init__(self, customer_id: str, url: str, events: List[str]):
        self.id = f"whsub_{uuid4().hex[:12]}"
        self.customer_id = customer_id
        self.url = url
        self.events = events
        self.secret = uuid4().hex
        self.is_active = True
        self.created_at = utc_now()
        self.last_triggered_at: Optional[datetime] = None
        self.failure_count = 0


class WebhookDelivery:
    """Represents a webhook delivery attempt."""

    def __init__(self, subscription_id: str, event_type: str, payload: Dict):
        self.id = f"whdel_{uuid4().hex[:12]}"
        self.subscription_id = subscription_id
        self.event_type = event_type
        self.payload = payload
        self.status = "pending"
        self.attempts = 0
        self.response_code: Optional[int] = None
        self.response_body: Optional[str] = None
        self.created_at = utc_now()
        self.delivered_at: Optional[datetime] = None
        self.next_retry_at: Optional[datetime] = None


class WebhookService:
    """Manages webhooks for the platform."""

    # Event types we can emit
    EVENT_TYPES = [
        "invoice.created",
        "invoice.updated",
        "invoice.paid",
        "invoice.overdue",
        "invoice.cancelled",
        "payment.received",
        "payment.failed",
        "payment.refunded",
        "customer.created",
        "customer.updated",
        "customer.deleted",
        "project.created",
        "project.updated",
        "project.completed",
        "ticket.created",
        "ticket.updated",
        "ticket.resolved",
        "quote.created",
        "quote.accepted",
        "quote.rejected",
        "quote.expired",
    ]

    def __init__(self):
        self._subscriptions: Dict[str, WebhookSubscription] = {}
        self._deliveries: List[WebhookDelivery] = []
        self._event_handlers: Dict[str, List[Callable]] = {}

    # ==================== Subscriptions ====================

    def create_subscription(self, customer_id: str, url: str, events: List[str]) -> WebhookSubscription:
        """Create a new webhook subscription."""
        # Validate events
        invalid_events = [e for e in events if e not in self.EVENT_TYPES and e != "*"]
        if invalid_events:
            raise ValueError(f"Invalid event types: {invalid_events}")

        subscription = WebhookSubscription(customer_id, url, events)
        self._subscriptions[subscription.id] = subscription

        logger.info(f"Created webhook subscription {subscription.id} for {customer_id}")
        return subscription

    def get_subscription(self, subscription_id: str) -> Optional[WebhookSubscription]:
        """Get subscription by ID."""
        return self._subscriptions.get(subscription_id)

    def get_customer_subscriptions(self, customer_id: str) -> List[WebhookSubscription]:
        """Get all subscriptions for a customer."""
        return [
            s for s in self._subscriptions.values()
            if s.customer_id == customer_id and s.is_active
        ]

    def update_subscription(self, subscription_id: str, url: str = None, events: List[str] = None) -> Optional[WebhookSubscription]:
        """Update a subscription."""
        subscription = self._subscriptions.get(subscription_id)
        if not subscription:
            return None

        if url:
            subscription.url = url
        if events:
            subscription.events = events

        return subscription

    def delete_subscription(self, subscription_id: str) -> bool:
        """Delete (deactivate) a subscription."""
        subscription = self._subscriptions.get(subscription_id)
        if subscription:
            subscription.is_active = False
            return True
        return False

    def regenerate_secret(self, subscription_id: str) -> Optional[str]:
        """Regenerate webhook secret."""
        subscription = self._subscriptions.get(subscription_id)
        if subscription:
            subscription.secret = uuid4().hex
            return subscription.secret
        return None

    # ==================== Event Emission ====================

    async def emit(self, event_type: str, customer_id: str, payload: Dict):
        """Emit an event to all subscribed webhooks."""
        if event_type not in self.EVENT_TYPES:
            logger.warning(f"Unknown event type: {event_type}")
            return

        # Find matching subscriptions
        subscriptions = [
            s for s in self._subscriptions.values()
            if s.customer_id == customer_id
            and s.is_active
            and (event_type in s.events or "*" in s.events)
        ]

        # Create deliveries
        for subscription in subscriptions:
            delivery = WebhookDelivery(subscription.id, event_type, payload)
            self._deliveries.append(delivery)

            # Attempt delivery asynchronously
            asyncio.create_task(self._deliver(delivery, subscription))

        # Call internal handlers
        await self._call_handlers(event_type, payload)

        logger.info(f"Emitted {event_type} to {len(subscriptions)} subscribers")

    async def _deliver(self, delivery: WebhookDelivery, subscription: WebhookSubscription):
        """Deliver webhook to subscriber."""
        import aiohttp

        max_retries = 3
        retry_delays = [60, 300, 900]  # 1min, 5min, 15min

        while delivery.attempts < max_retries:
            delivery.attempts += 1

            try:
                # Prepare payload
                webhook_payload = {
                    "id": delivery.id,
                    "event": delivery.event_type,
                    "created_at": delivery.created_at.isoformat(),
                    "data": delivery.payload,
                }

                # Generate signature
                signature = self._generate_signature(
                    subscription.secret,
                    webhook_payload,
                )

                # Send request
                headers = {
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": signature,
                    "X-Webhook-ID": delivery.id,
                    "X-Webhook-Event": delivery.event_type,
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        subscription.url,
                        json=webhook_payload,
                        headers=headers,
                        timeout=30,
                    ) as response:
                        delivery.response_code = response.status
                        delivery.response_body = await response.text()

                        if response.status < 300:
                            delivery.status = "delivered"
                            delivery.delivered_at = utc_now()
                            subscription.last_triggered_at = utc_now()
                            subscription.failure_count = 0
                            logger.info(f"Webhook {delivery.id} delivered successfully")
                            return
                        else:
                            logger.warning(f"Webhook {delivery.id} returned {response.status}")

            except Exception as e:
                logger.error(f"Webhook delivery failed: {e}")
                delivery.response_body = str(e)

            # Retry logic
            if delivery.attempts < max_retries:
                delay = retry_delays[delivery.attempts - 1]
                delivery.next_retry_at = utc_now()
                await asyncio.sleep(delay)

        # Mark as failed after all retries
        delivery.status = "failed"
        subscription.failure_count += 1

        # Disable subscription after too many failures
        if subscription.failure_count >= 10:
            subscription.is_active = False
            logger.warning(f"Subscription {subscription.id} disabled due to failures")

    def _generate_signature(self, secret: str, payload: Dict) -> str:
        """Generate HMAC signature for webhook payload."""
        import json
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={signature}"

    def verify_signature(self, secret: str, payload: Dict, signature: str) -> bool:
        """Verify webhook signature."""
        expected = self._generate_signature(secret, payload)
        return hmac.compare_digest(expected, signature)

    # ==================== Internal Handlers ====================

    def register_handler(self, event_type: str, handler: Callable):
        """Register internal event handler."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    async def _call_handlers(self, event_type: str, payload: Dict):
        """Call internal handlers for event."""
        handlers = self._event_handlers.get(event_type, [])
        handlers.extend(self._event_handlers.get("*", []))

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_type, payload)
                else:
                    handler(event_type, payload)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

    # ==================== Delivery History ====================

    def get_deliveries(self, subscription_id: str = None, limit: int = 50) -> List[Dict]:
        """Get webhook delivery history."""
        deliveries = self._deliveries

        if subscription_id:
            deliveries = [d for d in deliveries if d.subscription_id == subscription_id]

        deliveries = sorted(deliveries, key=lambda d: d.created_at, reverse=True)

        return [
            {
                "id": d.id,
                "subscription_id": d.subscription_id,
                "event_type": d.event_type,
                "status": d.status,
                "attempts": d.attempts,
                "response_code": d.response_code,
                "created_at": d.created_at.isoformat(),
                "delivered_at": d.delivered_at.isoformat() if d.delivered_at else None,
            }
            for d in deliveries[:limit]
        ]

    def subscription_to_dict(self, subscription: WebhookSubscription) -> Dict:
        """Convert subscription to dictionary."""
        return {
            "id": subscription.id,
            "url": subscription.url,
            "events": subscription.events,
            "is_active": subscription.is_active,
            "created_at": subscription.created_at.isoformat(),
            "last_triggered_at": subscription.last_triggered_at.isoformat() if subscription.last_triggered_at else None,
        }


# Service instance
webhook_service = WebhookService()
