# Phase 29: Integration Hub - Part 4: Automation & Communication

## Overview
This part covers automation platform integration (Zapier) and communication integration (Slack) for workflow automation and notifications.

---

## File 1: Zapier Integration
**Path:** `backend/app/integrations/providers/zapier/client.py`

```python
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
```

---

## File 2: Zapier Routes
**Path:** `backend/app/integrations/providers/zapier/triggers.py`

```python
"""
Zapier Trigger & Action Handlers
REST API endpoints for Zapier integration
"""

from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ZapierTriggerHandler:
    """Handles Zapier trigger subscriptions and polling."""
    
    def __init__(self, integration):
        self.integration = integration
    
    async def handle_subscribe(self, trigger_key: str, data: Dict) -> Dict:
        """Handle subscribe request from Zapier."""
        webhook_url = data.get("hookUrl") or data.get("targetUrl")
        customer_id = data.get("customer_id")
        
        if not webhook_url:
            raise ValueError("hookUrl or targetUrl is required")
        
        result = self.integration.subscribe_trigger(
            trigger_key=trigger_key,
            webhook_url=webhook_url,
            customer_id=customer_id,
        )
        
        return result
    
    async def handle_unsubscribe(self, subscription_id: str) -> Dict:
        """Handle unsubscribe request from Zapier."""
        success = self.integration.unsubscribe_trigger(subscription_id)
        return {"success": success}
    
    async def handle_poll(self, trigger_key: str, customer_id: str) -> List[Dict]:
        """Handle polling request from Zapier (for instant triggers)."""
        # Return recent items for the trigger
        # In production: fetch real data from database
        
        sample = self.integration.get_sample_data(trigger_key)
        if sample:
            return [sample]
        return []
    
    async def handle_perform_list(self, trigger_key: str, customer_id: str) -> List[Dict]:
        """Handle perform_list for trigger testing."""
        sample = self.integration.get_sample_data(trigger_key)
        return [sample] if sample else []


class ZapierActionHandler:
    """Handles Zapier action execution."""
    
    def __init__(self, integration):
        self.integration = integration
    
    async def handle_action(self, action_key: str, data: Dict) -> Dict:
        """Handle action request from Zapier."""
        result = await self.integration.execute_action(action_key, data)
        return result
    
    def get_input_fields(self, action_key: str) -> List[Dict]:
        """Get input fields for an action."""
        fields = {
            "create_invoice": [
                {"key": "customer_id", "label": "Customer ID", "type": "string", "required": True},
                {"key": "amount", "label": "Amount", "type": "number", "required": True},
                {"key": "currency", "label": "Currency", "type": "string", "default": "USD"},
                {"key": "due_date", "label": "Due Date", "type": "datetime"},
                {"key": "description", "label": "Description", "type": "text"},
            ],
            "create_customer": [
                {"key": "name", "label": "Name", "type": "string", "required": True},
                {"key": "email", "label": "Email", "type": "string", "required": True},
                {"key": "company", "label": "Company Name", "type": "string"},
                {"key": "phone", "label": "Phone", "type": "string"},
            ],
            "create_project": [
                {"key": "name", "label": "Project Name", "type": "string", "required": True},
                {"key": "customer_id", "label": "Customer ID", "type": "string", "required": True},
                {"key": "description", "label": "Description", "type": "text"},
                {"key": "budget", "label": "Budget", "type": "number"},
            ],
            "send_notification": [
                {"key": "recipient", "label": "Recipient (User ID or Email)", "type": "string", "required": True},
                {"key": "message", "label": "Message", "type": "text", "required": True},
                {"key": "type", "label": "Type", "type": "string", "choices": ["info", "warning", "success"]},
            ],
            "create_ticket": [
                {"key": "subject", "label": "Subject", "type": "string", "required": True},
                {"key": "description", "label": "Description", "type": "text", "required": True},
                {"key": "priority", "label": "Priority", "type": "string", "choices": ["low", "medium", "high", "urgent"]},
                {"key": "customer_id", "label": "Customer ID", "type": "string"},
            ],
        }
        return fields.get(action_key, [])
```

---

## File 3: Zapier Init
**Path:** `backend/app/integrations/providers/zapier/__init__.py`

```python
"""
Zapier Integration Provider
"""

from app.integrations.providers.zapier.client import ZapierIntegration
from app.integrations.providers.zapier.triggers import ZapierTriggerHandler, ZapierActionHandler


__all__ = [
    'ZapierIntegration',
    'ZapierTriggerHandler',
    'ZapierActionHandler',
]
```

---

## File 4: Slack Client
**Path:** `backend/app/integrations/providers/slack/client.py`

```python
"""
Slack Integration Client
Handles Slack API communication
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.integrations.base import (
    BaseIntegration,
    IntegrationCategory,
    IntegrationCapability,
    IntegrationStatus,
    IntegrationError,
)
from app.integrations.registry import register_integration

logger = logging.getLogger(__name__)


@register_integration
class SlackIntegration(BaseIntegration):
    """Slack integration for notifications and commands."""
    
    PROVIDER_ID = "slack"
    PROVIDER_NAME = "Slack"
    DESCRIPTION = "Send notifications and use slash commands in Slack"
    CATEGORY = IntegrationCategory.COMMUNICATION
    ICON_URL = "/icons/integrations/slack.svg"
    DOCS_URL = "https://api.slack.com/docs"
    
    CAPABILITIES = [
        IntegrationCapability.OAUTH,
        IntegrationCapability.WEBHOOKS,
        IntegrationCapability.REALTIME,
    ]
    
    # OAuth URLs
    OAUTH_AUTHORIZE_URL = "https://slack.com/oauth/v2/authorize"
    OAUTH_TOKEN_URL = "https://slack.com/api/oauth.v2.access"
    OAUTH_SCOPES = [
        "chat:write",
        "chat:write.public",
        "channels:read",
        "users:read",
        "commands",
        "incoming-webhook",
    ]
    
    # API URL
    API_URL = "https://slack.com/api"
    
    def __init__(self, credentials: Dict[str, Any] = None):
        super().__init__(credentials)
        self._bot_token = None
        self._webhook_url = None
        self._team_id = None
        self._team_name = None
        self._channels: Dict[str, str] = {}  # name -> id mapping
    
    def get_oauth_url(self, redirect_uri: str, state: str) -> str:
        """Generate OAuth authorization URL."""
        params = {
            "client_id": self.credentials.get("client_id"),
            "redirect_uri": redirect_uri,
            "scope": ",".join(self.OAUTH_SCOPES),
            "state": state,
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.OAUTH_AUTHORIZE_URL}?{query}"
    
    async def handle_oauth_callback(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Handle OAuth callback."""
        # Demo response
        return {
            "access_token": f"xoxb-slack-token-{datetime.utcnow().timestamp()}",
            "team": {"id": "T12345", "name": "Demo Workspace"},
            "incoming_webhook": {"url": "https://hooks.slack.com/services/..."},
        }
    
    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """Connect to Slack."""
        self._bot_token = credentials.get("access_token") or credentials.get("bot_token")
        self._webhook_url = credentials.get("webhook_url")
        self._team_id = credentials.get("team_id")
        self._team_name = credentials.get("team_name")
        self.credentials = credentials
        
        if self._bot_token or self._webhook_url:
            if await self.test_connection():
                self._set_status(IntegrationStatus.CONNECTED)
                return True
        
        self._set_status(IntegrationStatus.ERROR, "Invalid credentials")
        return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Slack."""
        self._bot_token = None
        self._webhook_url = None
        self.credentials = {}
        self._set_status(IntegrationStatus.DISCONNECTED)
        return True
    
    async def test_connection(self) -> bool:
        """Test Slack connection."""
        try:
            if self._bot_token:
                # In production: await self._api_call("auth.test")
                return True
            elif self._webhook_url:
                return True
            return False
        except Exception as e:
            self._log_error(f"Connection test failed: {e}")
            return False
    
    async def refresh_credentials(self) -> Dict[str, Any]:
        """Slack tokens don't expire, no refresh needed."""
        return self.credentials
    
    # ==================== Messaging ====================
    
    async def send_message(self, channel: str, text: str, blocks: List[Dict] = None, attachments: List[Dict] = None) -> Dict:
        """Send a message to a channel."""
        data = {
            "channel": channel,
            "text": text,
        }
        
        if blocks:
            data["blocks"] = blocks
        if attachments:
            data["attachments"] = attachments
        
        # Demo response
        return {
            "ok": True,
            "channel": channel,
            "ts": str(datetime.utcnow().timestamp()),
            "message": {"text": text},
        }
    
    async def send_webhook_message(self, text: str, blocks: List[Dict] = None, attachments: List[Dict] = None) -> bool:
        """Send message via incoming webhook."""
        import aiohttp
        
        if not self._webhook_url:
            raise IntegrationError(
                message="Webhook URL not configured",
                provider=self.PROVIDER_ID,
            )
        
        payload = {"text": text}
        if blocks:
            payload["blocks"] = blocks
        if attachments:
            payload["attachments"] = attachments
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self._webhook_url, json=payload) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"[Slack] Webhook failed: {e}")
            return False
    
    async def update_message(self, channel: str, ts: str, text: str, blocks: List[Dict] = None) -> Dict:
        """Update an existing message."""
        data = {
            "channel": channel,
            "ts": ts,
            "text": text,
        }
        if blocks:
            data["blocks"] = blocks
        
        return {"ok": True, "ts": ts}
    
    async def delete_message(self, channel: str, ts: str) -> Dict:
        """Delete a message."""
        return {"ok": True}
    
    # ==================== Notification Helpers ====================
    
    async def send_invoice_notification(self, channel: str, invoice: Dict) -> Dict:
        """Send invoice notification with rich formatting."""
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"📄 New Invoice: {invoice.get('number')}"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Customer:*\n{invoice.get('customer_name')}"},
                    {"type": "mrkdwn", "text": f"*Amount:*\n${invoice.get('amount'):,.2f}"},
                    {"type": "mrkdwn", "text": f"*Due Date:*\n{invoice.get('due_date')}"},
                    {"type": "mrkdwn", "text": f"*Status:*\n{invoice.get('status', 'Draft').title()}"},
                ],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Invoice"},
                        "url": f"https://app.logiaccounting.com/invoices/{invoice.get('id')}",
                        "action_id": "view_invoice",
                    },
                ],
            },
        ]
        
        return await self.send_message(
            channel=channel,
            text=f"New invoice {invoice.get('number')} created for ${invoice.get('amount'):,.2f}",
            blocks=blocks,
        )
    
    async def send_payment_notification(self, channel: str, payment: Dict) -> Dict:
        """Send payment received notification."""
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "💰 Payment Received"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Amount:*\n${payment.get('amount'):,.2f}"},
                    {"type": "mrkdwn", "text": f"*Invoice:*\n{payment.get('invoice_number')}"},
                    {"type": "mrkdwn", "text": f"*Customer:*\n{payment.get('customer_name')}"},
                    {"type": "mrkdwn", "text": f"*Method:*\n{payment.get('method', 'N/A').title()}"},
                ],
            },
        ]
        
        return await self.send_message(
            channel=channel,
            text=f"Payment of ${payment.get('amount'):,.2f} received",
            blocks=blocks,
        )
    
    async def send_daily_summary(self, channel: str, summary: Dict) -> Dict:
        """Send daily business summary."""
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "📊 Daily Summary"},
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*{summary.get('date', 'Today')}*"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*New Invoices:*\n{summary.get('new_invoices', 0)}"},
                    {"type": "mrkdwn", "text": f"*Revenue:*\n${summary.get('revenue', 0):,.2f}"},
                    {"type": "mrkdwn", "text": f"*Payments:*\n{summary.get('payments_count', 0)}"},
                    {"type": "mrkdwn", "text": f"*Open Tickets:*\n{summary.get('open_tickets', 0)}"},
                ],
            },
        ]
        
        return await self.send_message(
            channel=channel,
            text=f"Daily summary for {summary.get('date', 'today')}",
            blocks=blocks,
        )
    
    # ==================== Channels ====================
    
    async def list_channels(self) -> List[Dict]:
        """List available channels."""
        # Demo response
        return [
            {"id": "C12345", "name": "general", "is_private": False},
            {"id": "C12346", "name": "finance", "is_private": False},
            {"id": "C12347", "name": "support", "is_private": False},
        ]
    
    async def get_channel_id(self, channel_name: str) -> Optional[str]:
        """Get channel ID by name."""
        if channel_name in self._channels:
            return self._channels[channel_name]
        
        channels = await self.list_channels()
        for ch in channels:
            self._channels[ch["name"]] = ch["id"]
            if ch["name"] == channel_name:
                return ch["id"]
        
        return None
    
    # ==================== API Helper ====================
    
    async def _api_call(self, method: str, data: Dict = None) -> Dict:
        """Make Slack API call."""
        import aiohttp
        
        url = f"{self.API_URL}/{method}"
        headers = {
            "Authorization": f"Bearer {self._bot_token}",
            "Content-Type": "application/json",
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data or {}) as response:
                result = await response.json()
                
                if not result.get("ok"):
                    raise IntegrationError(
                        message=result.get("error", "Unknown error"),
                        provider=self.PROVIDER_ID,
                        details=result,
                    )
                
                return result
```

---

## File 5: Slack Commands Handler
**Path:** `backend/app/integrations/providers/slack/commands.py`

```python
"""
Slack Slash Commands Handler
Handles /invoice, /customer, /project commands
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SlackCommandHandler:
    """Handles Slack slash commands."""
    
    COMMANDS = {
        "/invoice": "Look up or create invoices",
        "/customer": "Look up customer information",
        "/project": "Check project status",
        "/balance": "Check outstanding balance",
        "/help": "Show available commands",
    }
    
    def __init__(self, integration):
        self.integration = integration
    
    def verify_request(self, timestamp: str, signature: str, body: str, signing_secret: str) -> bool:
        """Verify Slack request signature."""
        import hmac
        import hashlib
        
        # Check timestamp is recent (within 5 minutes)
        request_time = int(timestamp)
        current_time = int(datetime.utcnow().timestamp())
        if abs(current_time - request_time) > 300:
            return False
        
        # Compute signature
        sig_basestring = f"v0:{timestamp}:{body}"
        computed_sig = "v0=" + hmac.new(
            signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256,
        ).hexdigest()
        
        return hmac.compare_digest(computed_sig, signature)
    
    async def handle_command(self, command: str, text: str, user_id: str, channel_id: str, response_url: str) -> Dict:
        """Handle incoming slash command."""
        handler = self._get_handler(command)
        if not handler:
            return self._error_response(f"Unknown command: {command}")
        
        try:
            return await handler(text, user_id, channel_id, response_url)
        except Exception as e:
            logger.error(f"[Slack Command] Error: {e}")
            return self._error_response(f"Error: {str(e)}")
    
    def _get_handler(self, command: str):
        """Get command handler."""
        handlers = {
            "/invoice": self._handle_invoice,
            "/customer": self._handle_customer,
            "/project": self._handle_project,
            "/balance": self._handle_balance,
            "/help": self._handle_help,
        }
        return handlers.get(command)
    
    async def _handle_invoice(self, text: str, user_id: str, channel_id: str, response_url: str) -> Dict:
        """Handle /invoice command."""
        parts = text.strip().split()
        
        if not parts:
            return self._help_response("/invoice", "Usage: /invoice [number] or /invoice create [customer]")
        
        action = parts[0].lower()
        
        if action == "create":
            # Create new invoice flow
            return {
                "response_type": "ephemeral",
                "text": "📝 Opening invoice creation dialog...",
                "blocks": [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": "To create an invoice, please use the web app or provide customer details."},
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "Create Invoice"},
                                "url": "https://app.logiaccounting.com/invoices/new",
                                "action_id": "create_invoice",
                            },
                        ],
                    },
                ],
            }
        else:
            # Look up invoice
            invoice_number = action.upper()
            
            # In production: look up actual invoice
            return {
                "response_type": "ephemeral",
                "text": f"Looking up invoice {invoice_number}...",
                "blocks": [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*Invoice:* {invoice_number}\n*Customer:* Sample Customer\n*Amount:* $1,500.00\n*Status:* Pending"},
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "View Details"},
                                "url": f"https://app.logiaccounting.com/invoices/{invoice_number}",
                            },
                        ],
                    },
                ],
            }
    
    async def _handle_customer(self, text: str, user_id: str, channel_id: str, response_url: str) -> Dict:
        """Handle /customer command."""
        if not text.strip():
            return self._help_response("/customer", "Usage: /customer [name or email]")
        
        search_term = text.strip()
        
        # In production: search customers
        return {
            "response_type": "ephemeral",
            "text": f"Searching for customer: {search_term}",
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Customer Found:*\n• Name: Sample Customer\n• Email: customer@example.com\n• Balance: $2,500.00"},
                },
            ],
        }
    
    async def _handle_project(self, text: str, user_id: str, channel_id: str, response_url: str) -> Dict:
        """Handle /project command."""
        if not text.strip():
            return self._help_response("/project", "Usage: /project [name or ID]")
        
        project_name = text.strip()
        
        return {
            "response_type": "ephemeral",
            "text": f"Project status for: {project_name}",
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Project:* {project_name}\n*Progress:* 65%\n*Status:* Active\n*Due:* Feb 28, 2024"},
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "```\n████████████████░░░░░░░░░ 65%\n```"},
                },
            ],
        }
    
    async def _handle_balance(self, text: str, user_id: str, channel_id: str, response_url: str) -> Dict:
        """Handle /balance command."""
        return {
            "response_type": "ephemeral",
            "text": "Outstanding Balance Summary",
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "💰 Balance Summary"},
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": "*Total Outstanding:*\n$45,250.00"},
                        {"type": "mrkdwn", "text": "*Overdue:*\n$5,500.00"},
                        {"type": "mrkdwn", "text": "*Due This Week:*\n$12,000.00"},
                        {"type": "mrkdwn", "text": "*Invoices:*\n15 open"},
                    ],
                },
            ],
        }
    
    async def _handle_help(self, text: str, user_id: str, channel_id: str, response_url: str) -> Dict:
        """Handle /help command."""
        commands_text = "\n".join([f"• `{cmd}` - {desc}" for cmd, desc in self.COMMANDS.items()])
        
        return {
            "response_type": "ephemeral",
            "text": "LogiAccounting Commands",
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "📚 Available Commands"},
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": commands_text},
                },
            ],
        }
    
    def _help_response(self, command: str, usage: str) -> Dict:
        """Generate help response for a command."""
        return {
            "response_type": "ephemeral",
            "text": usage,
        }
    
    def _error_response(self, message: str) -> Dict:
        """Generate error response."""
        return {
            "response_type": "ephemeral",
            "text": f"❌ {message}",
        }
```

---

## File 6: Slack Init
**Path:** `backend/app/integrations/providers/slack/__init__.py`

```python
"""
Slack Integration Provider
"""

from app.integrations.providers.slack.client import SlackIntegration
from app.integrations.providers.slack.commands import SlackCommandHandler


__all__ = [
    'SlackIntegration',
    'SlackCommandHandler',
]
```

---

## Summary Part 4

| File | Description | Lines |
|------|-------------|-------|
| `zapier/client.py` | Zapier integration | ~280 |
| `zapier/triggers.py` | Trigger & action handlers | ~120 |
| `zapier/__init__.py` | Zapier init | ~15 |
| `slack/client.py` | Slack API client | ~320 |
| `slack/commands.py` | Slash commands handler | ~250 |
| `slack/__init__.py` | Slack init | ~15 |
| **Total** | | **~1,000 lines** |
