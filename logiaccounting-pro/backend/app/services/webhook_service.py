"""
Webhook Integration Service
"""

import httpx
import hashlib
import hmac
import json
from datetime import datetime
from typing import Dict, List, Optional
import asyncio


class WebhookService:
    """Manages webhook configurations and deliveries"""

    _instance = None
    _webhooks: Dict[str, dict] = {}
    _logs: List[dict] = []
    _counter = 0
    _log_counter = 0

    EVENTS = [
        "transaction.created",
        "transaction.updated",
        "transaction.deleted",
        "payment.created",
        "payment.due_soon",
        "payment.overdue",
        "payment.paid",
        "inventory.low_stock",
        "project.status_changed",
        "anomaly.detected"
    ]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._webhooks = {}
            cls._logs = []
            cls._counter = 0
            cls._log_counter = 0
        return cls._instance

    def create_webhook(
        self,
        url: str,
        events: List[str],
        headers: Optional[Dict[str, str]] = None,
        secret: Optional[str] = None,
        user_id: str = None
    ) -> dict:
        """Create a new webhook configuration"""
        self._counter += 1
        webhook_id = f"WH-{self._counter:04d}"

        webhook = {
            "id": webhook_id,
            "url": url,
            "events": events,
            "headers": headers or {},
            "secret": secret,
            "active": True,
            "created_by": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_triggered": None,
            "success_count": 0,
            "failure_count": 0
        }

        self._webhooks[webhook_id] = webhook
        return {k: v for k, v in webhook.items() if k != 'secret'}

    def update_webhook(
        self,
        webhook_id: str,
        url: Optional[str] = None,
        events: Optional[List[str]] = None,
        headers: Optional[Dict[str, str]] = None,
        active: Optional[bool] = None
    ) -> Optional[dict]:
        """Update a webhook configuration"""
        if webhook_id not in self._webhooks:
            return None

        webhook = self._webhooks[webhook_id]

        if url is not None:
            webhook["url"] = url
        if events is not None:
            webhook["events"] = events
        if headers is not None:
            webhook["headers"] = headers
        if active is not None:
            webhook["active"] = active

        return {k: v for k, v in webhook.items() if k != 'secret'}

    def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook"""
        if webhook_id in self._webhooks:
            del self._webhooks[webhook_id]
            return True
        return False

    def list_webhooks(self, user_id: Optional[str] = None) -> List[dict]:
        """List all webhooks"""
        webhooks = []
        for wh in self._webhooks.values():
            if user_id is None or wh.get("created_by") == user_id:
                webhooks.append({k: v for k, v in wh.items() if k != 'secret'})
        return webhooks

    def get_webhook(self, webhook_id: str) -> Optional[dict]:
        """Get a specific webhook"""
        webhook = self._webhooks.get(webhook_id)
        if webhook:
            return {k: v for k, v in webhook.items() if k != 'secret'}
        return None

    async def trigger(self, event: str, data: dict, metadata: Optional[dict] = None):
        """Trigger webhooks for an event"""
        payload = {
            "event": event,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "metadata": metadata or {}
        }

        for webhook in self._webhooks.values():
            if not webhook["active"]:
                continue
            if event not in webhook["events"]:
                continue

            asyncio.create_task(self._deliver(webhook, payload))

    async def _deliver(self, webhook: dict, payload: dict, retries: int = 3):
        """Deliver a webhook payload"""
        self._log_counter += 1
        log_id = f"WHL-{self._log_counter:06d}"

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-ID": webhook["id"],
            "X-Webhook-Event": payload["event"],
            **webhook.get("headers", {})
        }

        if webhook.get("secret"):
            signature = hmac.new(
                webhook["secret"].encode(),
                json.dumps(payload).encode(),
                hashlib.sha256
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={signature}"

        log_entry = {
            "id": log_id,
            "webhook_id": webhook["id"],
            "event": payload["event"],
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
            "attempts": 0,
            "success": False,
            "response_status": None,
            "response_body": None,
            "error": None
        }

        for attempt in range(retries):
            log_entry["attempts"] = attempt + 1

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        webhook["url"],
                        json=payload,
                        headers=headers
                    )

                    log_entry["response_status"] = response.status_code
                    log_entry["response_body"] = response.text[:500]

                    if response.status_code < 300:
                        log_entry["success"] = True
                        webhook["success_count"] += 1
                        webhook["last_triggered"] = datetime.utcnow().isoformat()
                        break

            except Exception as e:
                log_entry["error"] = str(e)

            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)

        if not log_entry["success"]:
            webhook["failure_count"] += 1

        self._logs.insert(0, log_entry)

        if len(self._logs) > 1000:
            self._logs = self._logs[:1000]

    def get_logs(
        self,
        webhook_id: Optional[str] = None,
        event: Optional[str] = None,
        success: Optional[bool] = None,
        limit: int = 50
    ) -> List[dict]:
        """Get webhook delivery logs"""
        logs = self._logs

        if webhook_id:
            logs = [l for l in logs if l["webhook_id"] == webhook_id]
        if event:
            logs = [l for l in logs if l["event"] == event]
        if success is not None:
            logs = [l for l in logs if l["success"] == success]

        return logs[:limit]

    async def test_webhook(self, webhook_id: str) -> dict:
        """Send a test event to a webhook"""
        webhook = self._webhooks.get(webhook_id)
        if not webhook:
            return {"error": "Webhook not found"}

        test_payload = {
            "event": "test",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {"message": "Test webhook delivery"},
            "metadata": {"test": True}
        }

        await self._deliver(webhook, test_payload, retries=1)

        for log in self._logs:
            if log["webhook_id"] == webhook_id and log["payload"]["event"] == "test":
                return log

        return {"error": "Test delivery failed"}


webhook_service = WebhookService()
