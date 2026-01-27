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
