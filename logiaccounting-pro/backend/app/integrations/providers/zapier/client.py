"""
Zapier Integration
Provides triggers and actions for Zapier webhooks
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4
import logging

from app.integrations.base import (
    BaseIntegration,
    IntegrationCategory,
    IntegrationCapability,
    IntegrationStatus,
)
from app.integrations.registry import register_integration

logger = logging.getLogger(__name__)


@register_integration
class ZapierIntegration(BaseIntegration):
    """Zapier integration for workflow automation."""

    PROVIDER_ID = "zapier"
    PROVIDER_NAME = "Zapier"
    DESCRIPTION = "Connect to 5,000+ apps with automated workflows"
    CATEGORY = IntegrationCategory.AUTOMATION
    ICON_URL = "/icons/integrations/zapier.svg"
    DOCS_URL = "https://zapier.com/developer"

    CAPABILITIES = [
        IntegrationCapability.API_KEY,
        IntegrationCapability.WEBHOOKS,
    ]

    # Available triggers
    TRIGGERS = [
        {
            "key": "new_invoice",
            "name": "New Invoice",
            "description": "Triggers when a new invoice is created",
        },
        {
            "key": "invoice_paid",
            "name": "Invoice Paid",
            "description": "Triggers when an invoice is marked as paid",
        },
        {
            "key": "new_customer",
            "name": "New Customer",
            "description": "Triggers when a new customer is added",
        },
        {
            "key": "new_payment",
            "name": "Payment Received",
            "description": "Triggers when a payment is received",
        },
        {
            "key": "project_completed",
            "name": "Project Completed",
            "description": "Triggers when a project is marked as complete",
        },
        {
            "key": "new_ticket",
            "name": "New Support Ticket",
            "description": "Triggers when a support ticket is created",
        },
        {
            "key": "ticket_resolved",
            "name": "Ticket Resolved",
            "description": "Triggers when a support ticket is resolved",
        },
    ]

    # Available actions
    ACTIONS = [
        {
            "key": "create_invoice",
            "name": "Create Invoice",
            "description": "Creates a new invoice",
        },
        {
            "key": "create_customer",
            "name": "Create Customer",
            "description": "Creates a new customer",
        },
        {
            "key": "create_project",
            "name": "Create Project",
            "description": "Creates a new project",
        },
        {
            "key": "send_notification",
            "name": "Send Notification",
            "description": "Sends a notification to a user",
        },
        {
            "key": "create_ticket",
            "name": "Create Support Ticket",
            "description": "Creates a new support ticket",
        },
    ]

    def __init__(self, credentials: Dict[str, Any] = None):
        super().__init__(credentials)
        self._api_key = None
        self._webhook_subscriptions: Dict[str, Dict] = {}

    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """Connect with API key."""
        self._validate_credentials(["api_key"])

        self._api_key = credentials.get("api_key")
        self.credentials = credentials

        self._set_status(IntegrationStatus.CONNECTED)
        return True

    async def disconnect(self) -> bool:
        """Disconnect from Zapier."""
        self._api_key = None
        self._webhook_subscriptions.clear()
        self.credentials = {}
        self._set_status(IntegrationStatus.DISCONNECTED)
        return True

    async def test_connection(self) -> bool:
        """Test connection."""
        return bool(self._api_key)

    async def refresh_credentials(self) -> Dict[str, Any]:
        """No refresh needed for API key."""
        return self.credentials

    def get_metadata(self) -> Dict[str, Any]:
        """Get integration metadata with triggers and actions."""
        metadata = super().get_metadata()
        metadata["triggers"] = self.TRIGGERS
        metadata["actions"] = self.ACTIONS
        return metadata

    # ==================== Trigger Subscriptions ====================

    def subscribe_trigger(self, trigger_key: str, webhook_url: str, customer_id: str) -> Dict:
        """Subscribe to a trigger (called by Zapier)."""
        if not any(t["key"] == trigger_key for t in self.TRIGGERS):
            raise ValueError(f"Unknown trigger: {trigger_key}")

        subscription_id = f"zap_sub_{uuid4().hex[:12]}"

        self._webhook_subscriptions[subscription_id] = {
            "id": subscription_id,
            "trigger": trigger_key,
            "webhook_url": webhook_url,
            "customer_id": customer_id,
            "created_at": datetime.utcnow().isoformat(),
            "active": True,
        }

        logger.info(f"[Zapier] Subscribed to trigger: {trigger_key} -> {webhook_url}")

        return {"id": subscription_id}

    def unsubscribe_trigger(self, subscription_id: str) -> bool:
        """Unsubscribe from a trigger."""
        if subscription_id in self._webhook_subscriptions:
            self._webhook_subscriptions[subscription_id]["active"] = False
            logger.info(f"[Zapier] Unsubscribed: {subscription_id}")
            return True
        return False

    def get_subscriptions(self, customer_id: str = None) -> List[Dict]:
        """Get active subscriptions."""
        subs = list(self._webhook_subscriptions.values())
        if customer_id:
            subs = [s for s in subs if s["customer_id"] == customer_id]
        return [s for s in subs if s["active"]]

    # ==================== Trigger Emission ====================

    async def emit_trigger(self, trigger_key: str, customer_id: str, data: Dict):
        """Emit trigger event to subscribed webhooks."""
        import aiohttp

        # Find matching subscriptions
        subscriptions = [
            s for s in self._webhook_subscriptions.values()
            if s["trigger"] == trigger_key
            and s["customer_id"] == customer_id
            and s["active"]
        ]

        for sub in subscriptions:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        sub["webhook_url"],
                        json=data,
                        timeout=30,
                    ) as response:
                        if response.status < 300:
                            logger.info(f"[Zapier] Trigger sent: {trigger_key} -> {sub['id']}")
                        else:
                            logger.warning(f"[Zapier] Trigger failed: {response.status}")
            except Exception as e:
                logger.error(f"[Zapier] Trigger error: {e}")

    # ==================== Actions ====================

    async def execute_action(self, action_key: str, data: Dict) -> Dict:
        """Execute an action (called by Zapier)."""
        handler = self._get_action_handler(action_key)
        if not handler:
            raise ValueError(f"Unknown action: {action_key}")

        return await handler(data)

    def _get_action_handler(self, action_key: str):
        """Get action handler."""
        handlers = {
            "create_invoice": self._action_create_invoice,
            "create_customer": self._action_create_customer,
            "create_project": self._action_create_project,
            "send_notification": self._action_send_notification,
            "create_ticket": self._action_create_ticket,
        }
        return handlers.get(action_key)

    async def _action_create_invoice(self, data: Dict) -> Dict:
        """Create invoice action."""
        # In production: call invoice service
        return {
            "id": f"inv_{uuid4().hex[:12]}",
            "number": data.get("invoice_number", f"INV-{int(datetime.utcnow().timestamp())}"),
            "customer_id": data.get("customer_id"),
            "amount": data.get("amount"),
            "status": "draft",
            "created_at": datetime.utcnow().isoformat(),
        }

    async def _action_create_customer(self, data: Dict) -> Dict:
        """Create customer action."""
        return {
            "id": f"cust_{uuid4().hex[:12]}",
            "name": data.get("name"),
            "email": data.get("email"),
            "created_at": datetime.utcnow().isoformat(),
        }

    async def _action_create_project(self, data: Dict) -> Dict:
        """Create project action."""
        return {
            "id": f"proj_{uuid4().hex[:12]}",
            "name": data.get("name"),
            "customer_id": data.get("customer_id"),
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
        }

    async def _action_send_notification(self, data: Dict) -> Dict:
        """Send notification action."""
        return {
            "id": f"notif_{uuid4().hex[:12]}",
            "recipient": data.get("recipient"),
            "message": data.get("message"),
            "sent_at": datetime.utcnow().isoformat(),
        }

    async def _action_create_ticket(self, data: Dict) -> Dict:
        """Create support ticket action."""
        return {
            "id": f"tkt_{uuid4().hex[:12]}",
            "subject": data.get("subject"),
            "description": data.get("description"),
            "priority": data.get("priority", "medium"),
            "status": "open",
            "created_at": datetime.utcnow().isoformat(),
        }

    # ==================== Sample Data ====================

    def get_sample_data(self, trigger_key: str) -> Dict:
        """Get sample data for a trigger (for Zapier testing)."""
        samples = {
            "new_invoice": {
                "id": "inv_sample123",
                "number": "INV-2024-0001",
                "customer_id": "cust_sample123",
                "customer_name": "Sample Customer",
                "customer_email": "customer@example.com",
                "amount": 1500.00,
                "currency": "USD",
                "status": "draft",
                "due_date": "2024-02-15",
                "created_at": datetime.utcnow().isoformat(),
            },
            "invoice_paid": {
                "id": "inv_sample123",
                "number": "INV-2024-0001",
                "customer_id": "cust_sample123",
                "amount": 1500.00,
                "paid_amount": 1500.00,
                "payment_method": "credit_card",
                "paid_at": datetime.utcnow().isoformat(),
            },
            "new_customer": {
                "id": "cust_sample123",
                "name": "Sample Customer",
                "email": "customer@example.com",
                "company": "Sample Corp",
                "phone": "+1-555-0123",
                "created_at": datetime.utcnow().isoformat(),
            },
            "new_payment": {
                "id": "pmt_sample123",
                "invoice_id": "inv_sample123",
                "amount": 1500.00,
                "currency": "USD",
                "method": "credit_card",
                "received_at": datetime.utcnow().isoformat(),
            },
            "project_completed": {
                "id": "proj_sample123",
                "name": "Sample Project",
                "customer_id": "cust_sample123",
                "completed_at": datetime.utcnow().isoformat(),
            },
            "new_ticket": {
                "id": "tkt_sample123",
                "number": "TKT-0001",
                "subject": "Sample Ticket",
                "description": "This is a sample ticket",
                "priority": "medium",
                "customer_id": "cust_sample123",
                "created_at": datetime.utcnow().isoformat(),
            },
            "ticket_resolved": {
                "id": "tkt_sample123",
                "number": "TKT-0001",
                "subject": "Sample Ticket",
                "resolution": "Issue resolved",
                "resolved_at": datetime.utcnow().isoformat(),
            },
        }
        return samples.get(trigger_key, {})
