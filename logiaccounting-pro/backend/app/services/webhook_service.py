"""
Enhanced Webhook Integration Service
Phase 17 - Webhooks with event types, HMAC signatures, delivery management
"""

import httpx
import hashlib
import hmac
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import asyncio

from app.models.webhook_store import (
    webhook_db, get_event_definitions, get_event_types,
    get_events_by_category, get_all_categories, EVENT_DEFINITIONS
)
from app.middleware.tenant_context import TenantContext


class WebhookSignature:
    """Webhook signature generation and verification"""

    SIGNATURE_VERSION = "v1"
    TIMESTAMP_TOLERANCE = 300  # 5 minutes

    @classmethod
    def sign(cls, payload: str, secret: str, timestamp: int = None) -> tuple:
        """
        Sign a webhook payload

        Returns (signature, timestamp) tuple
        """
        if timestamp is None:
            timestamp = int(time.time())

        # Create signed payload (timestamp.payload)
        signed_payload = f"{timestamp}.{payload}"

        # Generate HMAC-SHA256
        signature = hmac.new(
            secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        return f"{cls.SIGNATURE_VERSION}={signature}", timestamp

    @classmethod
    def verify(cls, payload: str, signature: str, timestamp: str, secret: str) -> bool:
        """Verify a webhook signature"""
        try:
            # Check timestamp tolerance
            ts = int(timestamp)
            now = int(time.time())

            if abs(now - ts) > cls.TIMESTAMP_TOLERANCE:
                return False

            # Parse signature
            if not signature.startswith(f"{cls.SIGNATURE_VERSION}="):
                return False

            expected_sig = signature.split("=", 1)[1]

            # Generate expected signature
            signed_payload = f"{ts}.{payload}"
            computed_sig = hmac.new(
                secret.encode("utf-8"),
                signed_payload.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()

            # Constant-time comparison
            return hmac.compare_digest(expected_sig, computed_sig)

        except (ValueError, TypeError):
            return False

    @classmethod
    def get_headers(cls, payload: str, secret: str) -> dict:
        """Get webhook signature headers"""
        signature, timestamp = cls.sign(payload, secret)

        return {
            "X-Webhook-Signature": signature,
            "X-Webhook-Timestamp": str(timestamp)
        }


class WebhookService:
    """Enhanced webhook management and delivery service"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def EVENTS(self) -> List[str]:
        """Get all available event types"""
        return get_event_types()

    def get_event_definitions(self) -> Dict:
        """Get all event definitions with metadata"""
        return get_event_definitions()

    def get_events_by_category(self, category: str) -> List[Dict]:
        """Get events for a specific category"""
        return get_events_by_category(category)

    def get_all_categories(self) -> List[str]:
        """Get all event categories"""
        return get_all_categories()

    def create_webhook(
        self,
        url: str,
        events: List[str],
        name: str = None,
        description: str = None,
        custom_headers: Dict[str, str] = None,
        timeout_seconds: int = 30,
        max_retries: int = 5,
        user_id: str = None,
        tenant_id: str = None
    ) -> Dict:
        """Create a new webhook endpoint"""
        if tenant_id is None:
            tenant_id = TenantContext.get_tenant_id()

        # Validate events
        valid_events = self.EVENTS + ["*"]
        invalid = [e for e in events if e not in valid_events and not e.endswith(".*")]
        if invalid:
            raise ValueError(f"Invalid events: {invalid}")

        endpoint = webhook_db.endpoints.create({
            "tenant_id": tenant_id,
            "name": name or f"Webhook {url[:30]}",
            "description": description,
            "url": url,
            "events": events,
            "custom_headers": custom_headers or {},
            "timeout_seconds": timeout_seconds,
            "max_retries": max_retries,
            "created_by": user_id
        })

        return self._format_endpoint(endpoint, include_secret=True)

    def get_webhook(self, webhook_id: str, tenant_id: str = None) -> Optional[Dict]:
        """Get webhook by ID"""
        if tenant_id is None:
            tenant_id = TenantContext.get_tenant_id()

        endpoint = webhook_db.endpoints.find_by_id(webhook_id)

        if endpoint and endpoint.get("tenant_id") == tenant_id:
            return self._format_endpoint(endpoint)

        return None

    def list_webhooks(
        self,
        tenant_id: str = None,
        is_active: bool = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """List webhooks for tenant"""
        if tenant_id is None:
            tenant_id = TenantContext.get_tenant_id()

        filters = {"tenant_id": tenant_id}
        if is_active is not None:
            filters["is_active"] = is_active

        endpoints = webhook_db.endpoints.find_all(filters)

        # Pagination
        total = len(endpoints)
        start = (page - 1) * per_page
        end = start + per_page
        endpoints = endpoints[start:end]

        return {
            "webhooks": [self._format_endpoint(e) for e in endpoints],
            "total": total,
            "page": page,
            "per_page": per_page
        }

    # Alias methods for route compatibility
    def list_endpoints(
        self,
        tenant_id: str = None,
        is_active: bool = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """Alias for list_webhooks"""
        return self.list_webhooks(tenant_id, is_active, page, per_page)

    def create_endpoint(
        self,
        url: str,
        events: List[str],
        description: str = None,
        headers: Dict[str, str] = None,
        is_active: bool = True,
        created_by: str = None,
        tenant_id: str = None
    ) -> Dict:
        """Alias for create_webhook"""
        return self.create_webhook(
            url=url,
            events=events,
            description=description,
            custom_headers=headers,
            user_id=created_by,
            tenant_id=tenant_id
        )

    def get_endpoint(self, endpoint_id: str, tenant_id: str = None) -> Optional[Dict]:
        """Alias for get_webhook"""
        return self.get_webhook(endpoint_id, tenant_id)

    def update_endpoint(
        self,
        endpoint_id: str,
        url: str = None,
        events: List[str] = None,
        description: str = None,
        headers: Dict[str, str] = None,
        is_active: bool = None,
        tenant_id: str = None
    ) -> Optional[Dict]:
        """Alias for update_webhook"""
        return self.update_webhook(
            webhook_id=endpoint_id,
            url=url,
            events=events,
            description=description,
            custom_headers=headers,
            is_active=is_active,
            tenant_id=tenant_id
        )

    def delete_endpoint(self, endpoint_id: str, tenant_id: str = None) -> bool:
        """Alias for delete_webhook"""
        return self.delete_webhook(endpoint_id, tenant_id)

    def rotate_secret(self, endpoint_id: str, tenant_id: str = None) -> Optional[Dict]:
        """Rotate webhook signing secret and return new secret"""
        new_secret = self.regenerate_secret(endpoint_id, tenant_id)
        if new_secret:
            return {"secret": new_secret}
        return None

    async def send_test_event(self, endpoint_id: str, tenant_id: str = None) -> Dict:
        """Alias for test_webhook"""
        return await self.test_webhook(endpoint_id, tenant_id)

    def list_deliveries(
        self,
        endpoint_id: str = None,
        event_type: str = None,
        status: str = None,
        page: int = 1,
        per_page: int = 20,
        tenant_id: str = None
    ) -> Dict[str, Any]:
        """List webhook deliveries with filtering"""
        if tenant_id is None:
            tenant_id = TenantContext.get_tenant_id()

        if endpoint_id:
            return self.get_deliveries(endpoint_id, status, page, per_page, tenant_id)

        # Get all deliveries for tenant
        all_deliveries = []
        for endpoint in webhook_db.endpoints.find_by_tenant(tenant_id):
            all_deliveries.extend(
                webhook_db.deliveries.find_by_endpoint(endpoint["id"], limit=per_page * page * 10)
            )

        # Apply filters
        if event_type:
            all_deliveries = [d for d in all_deliveries if d.get("event_type") == event_type]
        if status:
            all_deliveries = [d for d in all_deliveries if d.get("status") == status]

        # Sort by created_at descending
        all_deliveries.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        total = len(all_deliveries)
        start = (page - 1) * per_page
        end = start + per_page

        return {
            "deliveries": [self._format_delivery(d) for d in all_deliveries[start:end]],
            "total": total,
            "page": page,
            "per_page": per_page
        }

    def get_endpoint_stats(
        self,
        endpoint_id: str,
        days: int = 30,
        tenant_id: str = None
    ) -> Optional[Dict]:
        """Get statistics for a webhook endpoint"""
        if tenant_id is None:
            tenant_id = TenantContext.get_tenant_id()

        endpoint = webhook_db.endpoints.find_by_id(endpoint_id)
        if not endpoint or endpoint.get("tenant_id") != tenant_id:
            return None

        # Get deliveries for stats calculation
        deliveries = webhook_db.deliveries.find_by_endpoint(endpoint_id, limit=1000)

        total_deliveries = len(deliveries)
        successful = sum(1 for d in deliveries if d.get("status") == "delivered")
        failed = sum(1 for d in deliveries if d.get("status") == "failed")
        pending = sum(1 for d in deliveries if d.get("status") == "pending")

        # Calculate average response time
        response_times = [d.get("response_time_ms", 0) for d in deliveries if d.get("response_time_ms")]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        # Get event type breakdown
        event_counts = {}
        for d in deliveries:
            event = d.get("event_type", "unknown")
            event_counts[event] = event_counts.get(event, 0) + 1

        return {
            "endpoint_id": endpoint_id,
            "period_days": days,
            "total_deliveries": total_deliveries,
            "successful": successful,
            "failed": failed,
            "pending": pending,
            "success_rate": round((successful / total_deliveries * 100) if total_deliveries > 0 else 0, 2),
            "avg_response_time_ms": round(avg_response_time, 2),
            "consecutive_failures": endpoint.get("consecutive_failures", 0),
            "last_success_at": endpoint.get("last_success_at"),
            "last_failure_at": endpoint.get("last_failure_at"),
            "events_breakdown": event_counts
        }

    def update_webhook(
        self,
        webhook_id: str,
        name: str = None,
        description: str = None,
        url: str = None,
        events: List[str] = None,
        custom_headers: Dict[str, str] = None,
        timeout_seconds: int = None,
        max_retries: int = None,
        is_active: bool = None,
        tenant_id: str = None
    ) -> Optional[Dict]:
        """Update a webhook endpoint"""
        if tenant_id is None:
            tenant_id = TenantContext.get_tenant_id()

        endpoint = webhook_db.endpoints.find_by_id(webhook_id)
        if not endpoint or endpoint.get("tenant_id") != tenant_id:
            return None

        # Validate events if provided
        if events:
            valid_events = self.EVENTS + ["*"]
            invalid = [e for e in events if e not in valid_events and not e.endswith(".*")]
            if invalid:
                raise ValueError(f"Invalid events: {invalid}")

        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if url is not None:
            update_data["url"] = url
        if events is not None:
            update_data["events"] = events
        if custom_headers is not None:
            update_data["custom_headers"] = custom_headers
        if timeout_seconds is not None:
            update_data["timeout_seconds"] = timeout_seconds
        if max_retries is not None:
            update_data["max_retries"] = max_retries
        if is_active is not None:
            update_data["is_active"] = is_active

        result = webhook_db.endpoints.update(webhook_id, update_data)
        return self._format_endpoint(result) if result else None

    def delete_webhook(self, webhook_id: str, tenant_id: str = None) -> bool:
        """Delete a webhook endpoint"""
        if tenant_id is None:
            tenant_id = TenantContext.get_tenant_id()

        endpoint = webhook_db.endpoints.find_by_id(webhook_id)
        if not endpoint or endpoint.get("tenant_id") != tenant_id:
            return False

        return webhook_db.endpoints.delete(webhook_id)

    def regenerate_secret(self, webhook_id: str, tenant_id: str = None) -> Optional[str]:
        """Regenerate webhook signing secret"""
        if tenant_id is None:
            tenant_id = TenantContext.get_tenant_id()

        endpoint = webhook_db.endpoints.find_by_id(webhook_id)
        if not endpoint or endpoint.get("tenant_id") != tenant_id:
            return None

        return webhook_db.endpoints.regenerate_secret(webhook_id)

    async def emit(
        self,
        event_type: str,
        payload: Dict[str, Any],
        tenant_id: str = None,
        entity_id: str = None
    ) -> Optional[str]:
        """
        Emit a webhook event

        Args:
            event_type: Type of event (e.g., 'invoice.created')
            payload: Event payload data
            tenant_id: Tenant context
            entity_id: ID of related entity

        Returns:
            Event ID if emitted successfully
        """
        if tenant_id is None:
            tenant_id = TenantContext.get_tenant_id()

        if not tenant_id:
            return None

        # Validate event type
        if event_type not in EVENT_DEFINITIONS and event_type != "test.ping":
            return None

        # Generate event ID
        from uuid import uuid4
        event_id = str(uuid4())

        # Build full payload
        full_payload = {
            "id": event_id,
            "type": event_type,
            "api_version": "v1",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "tenant_id": tenant_id,
            "data": payload
        }

        # Find matching endpoints
        endpoints = webhook_db.endpoints.find_active_for_event(tenant_id, event_type)

        if not endpoints:
            return event_id

        # Create delivery records and dispatch
        for endpoint in endpoints:
            delivery = webhook_db.deliveries.create({
                "endpoint_id": endpoint["id"],
                "tenant_id": tenant_id,
                "event_type": event_type,
                "event_id": event_id,
                "payload": full_payload,
                "max_attempts": endpoint.get("max_retries", 5)
            })

            # Dispatch delivery asynchronously
            asyncio.create_task(self._deliver(delivery["id"]))

        return event_id

    async def _deliver(self, delivery_id: str, is_retry: bool = False) -> bool:
        """
        Attempt to deliver a webhook

        Returns True if delivery successful
        """
        delivery = webhook_db.deliveries.find_by_id(delivery_id)

        if not delivery:
            return False

        if delivery.get("status") == "delivered":
            return True

        if delivery.get("status") == "cancelled":
            return False

        # Get endpoint
        endpoint = webhook_db.endpoints.find_by_id(delivery["endpoint_id"])

        if not endpoint or not endpoint.get("is_active"):
            webhook_db.deliveries.update_status(
                delivery_id, "failed",
                error_message="Endpoint inactive"
            )
            return False

        # Increment attempt counter
        webhook_db.deliveries.increment_attempt(delivery_id)

        # Prepare payload
        payload_json = json.dumps(delivery["payload"], separators=(",", ":"))

        # Generate signature
        signature_headers = WebhookSignature.get_headers(payload_json, endpoint["secret"])

        # Build headers
        headers = {
            "Content-Type": endpoint.get("content_type", "application/json"),
            "User-Agent": "LogiAccounting-Webhook/1.0",
            "X-Webhook-ID": endpoint["id"],
            "X-Webhook-Event": delivery["event_type"],
            **signature_headers,
            **(endpoint.get("custom_headers") or {})
        }

        # Record attempt
        attempt_start = datetime.utcnow()

        try:
            timeout = endpoint.get("timeout_seconds", 30)

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    endpoint["url"],
                    content=payload_json,
                    headers=headers
                )

            response_time_ms = int((datetime.utcnow() - attempt_start).total_seconds() * 1000)

            # Record attempt details
            webhook_db.deliveries.record_attempt({
                "delivery_id": delivery_id,
                "attempt_number": delivery.get("attempt_count", 0) + 1,
                "request_url": endpoint["url"],
                "request_headers": {k: v for k, v in headers.items() if k != "X-Webhook-Signature"},
                "request_body": payload_json[:1000],
                "response_status": response.status_code,
                "response_headers": dict(response.headers),
                "response_body": response.text[:5000],
                "response_time_ms": response_time_ms,
                "started_at": attempt_start.isoformat()
            })

            # Check success (2xx status)
            if 200 <= response.status_code < 300:
                webhook_db.deliveries.mark_delivered(
                    delivery_id,
                    response_status=response.status_code,
                    response_time_ms=response_time_ms,
                    response_body=response.text[:5000]
                )
                webhook_db.endpoints.record_success(endpoint["id"])
                return True
            else:
                # Non-2xx response
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                webhook_db.deliveries.mark_failed(delivery_id, error_msg, response.status_code)
                webhook_db.endpoints.record_failure(endpoint["id"], error_msg)
                return False

        except httpx.TimeoutException:
            webhook_db.deliveries.record_attempt({
                "delivery_id": delivery_id,
                "attempt_number": delivery.get("attempt_count", 0) + 1,
                "request_url": endpoint["url"],
                "request_headers": headers,
                "request_body": payload_json[:1000],
                "error_type": "timeout",
                "error_message": f"Request timed out after {timeout}s",
                "started_at": attempt_start.isoformat()
            })
            webhook_db.deliveries.mark_failed(delivery_id, f"Timeout after {timeout}s")
            webhook_db.endpoints.record_failure(endpoint["id"])
            return False

        except httpx.ConnectError as e:
            webhook_db.deliveries.record_attempt({
                "delivery_id": delivery_id,
                "attempt_number": delivery.get("attempt_count", 0) + 1,
                "request_url": endpoint["url"],
                "request_headers": headers,
                "request_body": payload_json[:1000],
                "error_type": "connection_error",
                "error_message": str(e),
                "started_at": attempt_start.isoformat()
            })
            webhook_db.deliveries.mark_failed(delivery_id, str(e))
            webhook_db.endpoints.record_failure(endpoint["id"])
            return False

        except Exception as e:
            webhook_db.deliveries.record_attempt({
                "delivery_id": delivery_id,
                "attempt_number": delivery.get("attempt_count", 0) + 1,
                "request_url": endpoint["url"],
                "request_headers": headers,
                "request_body": payload_json[:1000],
                "error_type": "unknown",
                "error_message": str(e),
                "started_at": attempt_start.isoformat()
            })
            webhook_db.deliveries.mark_failed(delivery_id, str(e))
            webhook_db.endpoints.record_failure(endpoint["id"])
            return False

    async def test_webhook(self, webhook_id: str, tenant_id: str = None) -> Dict:
        """Send a test event to a webhook"""
        if tenant_id is None:
            tenant_id = TenantContext.get_tenant_id()

        endpoint = webhook_db.endpoints.find_by_id(webhook_id)

        if not endpoint or endpoint.get("tenant_id") != tenant_id:
            return {"success": False, "error": "Webhook not found"}

        # Build test payload
        test_payload = {
            "message": "This is a test webhook from LogiAccounting Pro",
            "endpoint_id": webhook_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        payload_json = json.dumps({
            "id": f"test_{int(time.time())}",
            "type": "test.ping",
            "api_version": "v1",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "data": test_payload
        }, separators=(",", ":"))

        signature_headers = WebhookSignature.get_headers(payload_json, endpoint["secret"])

        headers = {
            "Content-Type": endpoint.get("content_type", "application/json"),
            "User-Agent": "LogiAccounting-Webhook/1.0",
            "X-Webhook-ID": webhook_id,
            "X-Webhook-Event": "test.ping",
            **signature_headers,
            **(endpoint.get("custom_headers") or {})
        }

        try:
            timeout = endpoint.get("timeout_seconds", 30)

            async with httpx.AsyncClient(timeout=timeout) as client:
                start_time = time.time()
                response = await client.post(
                    endpoint["url"],
                    content=payload_json,
                    headers=headers
                )
                response_time_ms = int((time.time() - start_time) * 1000)

            return {
                "success": 200 <= response.status_code < 300,
                "status_code": response.status_code,
                "response_time_ms": response_time_ms,
                "response_body": response.text[:1000]
            }

        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "timeout",
                "error_message": f"Request timed out after {timeout}s"
            }

        except httpx.ConnectError as e:
            return {
                "success": False,
                "error": "connection_error",
                "error_message": str(e)
            }

        except Exception as e:
            return {
                "success": False,
                "error": "unknown",
                "error_message": str(e)
            }

    def get_deliveries(
        self,
        webhook_id: str,
        status: str = None,
        page: int = 1,
        per_page: int = 20,
        tenant_id: str = None
    ) -> Dict[str, Any]:
        """Get delivery logs for a webhook"""
        if tenant_id is None:
            tenant_id = TenantContext.get_tenant_id()

        endpoint = webhook_db.endpoints.find_by_id(webhook_id)
        if not endpoint or endpoint.get("tenant_id") != tenant_id:
            return {"deliveries": [], "total": 0}

        deliveries = webhook_db.deliveries.find_by_endpoint(webhook_id, limit=per_page * page)

        if status:
            deliveries = [d for d in deliveries if d.get("status") == status]

        total = len(deliveries)
        start = (page - 1) * per_page
        end = start + per_page
        deliveries = deliveries[start:end]

        return {
            "deliveries": [self._format_delivery(d) for d in deliveries],
            "total": total,
            "page": page,
            "per_page": per_page
        }

    async def retry_delivery(
        self,
        delivery_id: str,
        tenant_id: str = None
    ) -> Optional[Dict]:
        """Retry a failed delivery"""
        if tenant_id is None:
            tenant_id = TenantContext.get_tenant_id()

        delivery = webhook_db.deliveries.find_by_id(delivery_id)
        if not delivery:
            return None

        endpoint = webhook_db.endpoints.find_by_id(delivery.get("endpoint_id"))
        if not endpoint or endpoint.get("tenant_id") != tenant_id:
            return None

        if delivery.get("status") == "delivered":
            return {"success": False, "error": "Already delivered"}

        # Reset status and dispatch
        webhook_db.deliveries.update_status(delivery_id, "pending", next_retry_at=None)

        success = await self._deliver(delivery_id, is_retry=True)

        # Get updated delivery
        updated = webhook_db.deliveries.find_by_id(delivery_id)
        return {
            "success": success,
            **self._format_delivery(updated) if updated else {}
        }

    def get_logs(
        self,
        webhook_id: str = None,
        event: str = None,
        success: bool = None,
        limit: int = 50,
        tenant_id: str = None
    ) -> List[Dict]:
        """Get webhook delivery logs (legacy compatibility)"""
        if tenant_id is None:
            tenant_id = TenantContext.get_tenant_id()

        if webhook_id:
            endpoint = webhook_db.endpoints.find_by_id(webhook_id)
            if not endpoint or endpoint.get("tenant_id") != tenant_id:
                return []

        # Get deliveries
        if webhook_id:
            deliveries = webhook_db.deliveries.find_by_endpoint(webhook_id, limit=limit)
        else:
            # Get all deliveries for tenant (would need tenant filter)
            deliveries = []
            for endpoint in webhook_db.endpoints.find_by_tenant(tenant_id):
                deliveries.extend(
                    webhook_db.deliveries.find_by_endpoint(endpoint["id"], limit=limit)
                )

        if event:
            deliveries = [d for d in deliveries if d.get("event_type") == event]

        if success is not None:
            deliveries = [
                d for d in deliveries
                if (d.get("status") == "delivered") == success
            ]

        return [self._format_delivery(d) for d in deliveries[:limit]]

    # Legacy compatibility method
    async def trigger(self, event: str, data: dict, metadata: Optional[dict] = None):
        """Trigger webhooks for an event (legacy compatibility)"""
        payload = {**data, **(metadata or {})}
        await self.emit(event, payload)

    def _format_endpoint(self, endpoint: Dict, include_secret: bool = False) -> Dict:
        """Format webhook endpoint for response"""
        result = {
            "id": endpoint.get("id"),
            "name": endpoint.get("name"),
            "description": endpoint.get("description"),
            "url": endpoint.get("url"),
            "events": endpoint.get("events", []),
            "custom_headers": endpoint.get("custom_headers", {}),
            "content_type": endpoint.get("content_type"),
            "timeout_seconds": endpoint.get("timeout_seconds"),
            "max_retries": endpoint.get("max_retries"),
            "is_active": endpoint.get("is_active", True),
            "is_healthy": self._is_healthy(endpoint),
            "last_success_at": endpoint.get("last_success_at"),
            "last_failure_at": endpoint.get("last_failure_at"),
            "consecutive_failures": endpoint.get("consecutive_failures", 0),
            "created_at": endpoint.get("created_at")
        }

        if include_secret:
            result["secret"] = endpoint.get("secret")

        return result

    def _is_healthy(self, endpoint: Dict) -> bool:
        """Check if webhook is healthy"""
        if not endpoint.get("is_active"):
            return False
        if endpoint.get("disabled_at"):
            return False
        return endpoint.get("consecutive_failures", 0) < endpoint.get("failure_threshold", 10)

    def _format_delivery(self, delivery: Dict) -> Dict:
        """Format delivery for response"""
        return {
            "id": delivery.get("id"),
            "webhook_id": delivery.get("endpoint_id"),
            "event": delivery.get("event_type"),
            "event_id": delivery.get("event_id"),
            "status": delivery.get("status"),
            "attempt_count": delivery.get("attempt_count", 0),
            "max_attempts": delivery.get("max_attempts"),
            "response_status": delivery.get("response_status"),
            "response_time_ms": delivery.get("response_time_ms"),
            "error_message": delivery.get("error_message"),
            "payload": delivery.get("payload"),
            "created_at": delivery.get("created_at"),
            "delivered_at": delivery.get("delivered_at"),
            "next_retry_at": delivery.get("next_retry_at"),
            "success": delivery.get("status") == "delivered"
        }


# Global service instance
webhook_service = WebhookService()


# Convenience functions for emitting events
async def emit_invoice_created(invoice_data: Dict, tenant_id: str = None):
    """Emit invoice.created event"""
    return await webhook_service.emit("invoice.created", invoice_data, tenant_id)


async def emit_invoice_paid(invoice_id: str, payment_data: Dict, tenant_id: str = None):
    """Emit invoice.paid event"""
    return await webhook_service.emit("invoice.paid", {
        "invoice_id": invoice_id,
        **payment_data
    }, tenant_id)


async def emit_payment_received(payment_data: Dict, tenant_id: str = None):
    """Emit payment.received event"""
    return await webhook_service.emit("payment.received", payment_data, tenant_id)


async def emit_product_created(product_data: Dict, tenant_id: str = None):
    """Emit product.created event"""
    return await webhook_service.emit("product.created", product_data, tenant_id)


async def emit_stock_low(product_id: str, current_stock: int, threshold: int, tenant_id: str = None):
    """Emit stock.low event"""
    return await webhook_service.emit("stock.low", {
        "product_id": product_id,
        "current_stock": current_stock,
        "threshold": threshold
    }, tenant_id)


async def emit_customer_created(customer_data: Dict, tenant_id: str = None):
    """Emit customer.created event"""
    return await webhook_service.emit("customer.created", customer_data, tenant_id)


async def emit_project_status_changed(
    project_id: str,
    old_status: str,
    new_status: str,
    tenant_id: str = None
):
    """Emit project.status_changed event"""
    return await webhook_service.emit("project.status_changed", {
        "project_id": project_id,
        "old_status": old_status,
        "new_status": new_status,
        "changed_at": datetime.utcnow().isoformat()
    }, tenant_id)
