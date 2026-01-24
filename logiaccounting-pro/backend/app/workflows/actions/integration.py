"""
Integration Actions
External API calls and third-party integrations
"""

from typing import Dict, Any, List
from datetime import datetime
import logging
import aiohttp

from app.workflows.actions.base import (
    BaseAction, ActionCategory, ActionInput, ActionOutput, register_action
)

logger = logging.getLogger(__name__)


@register_action
class HTTPRequestAction(BaseAction):
    """Make HTTP request to external API."""

    ACTION_ID = "http_request"
    ACTION_NAME = "HTTP Request"
    DESCRIPTION = "Make an HTTP request to an external API"
    CATEGORY = ActionCategory.INTEGRATION
    ICON = "🌐"

    INPUTS = [
        ActionInput("url", "URL", "string", required=True, placeholder="https://api.example.com/endpoint"),
        ActionInput("method", "Method", "select", required=True, default="GET", options=[
            {"value": "GET", "label": "GET"},
            {"value": "POST", "label": "POST"},
            {"value": "PUT", "label": "PUT"},
            {"value": "PATCH", "label": "PATCH"},
            {"value": "DELETE", "label": "DELETE"},
        ]),
        ActionInput("headers", "Headers", "string", required=False, description="JSON headers"),
        ActionInput("body", "Body", "textarea", required=False, description="Request body (JSON)"),
        ActionInput("timeout", "Timeout", "number", required=False, default=30),
    ]

    OUTPUTS = [
        ActionOutput("status_code", "Status Code", "number"),
        ActionOutput("response", "Response", "object"),
        ActionOutput("headers", "Response Headers", "object"),
    ]

    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Make HTTP request."""
        import json

        url = config.get("url")
        method = config.get("method", "GET")
        headers = config.get("headers", {})
        body = config.get("body")
        timeout = config.get("timeout", 30)

        if isinstance(headers, str):
            headers = json.loads(headers)
        if isinstance(body, str) and body:
            body = json.loads(body)

        logger.info(f"[HTTPRequest] {method} {url}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    headers=headers,
                    json=body if method != "GET" else None,
                    timeout=timeout,
                ) as response:
                    response_body = await response.text()
                    try:
                        response_json = json.loads(response_body)
                    except:
                        response_json = {"text": response_body}

                    return {
                        "status_code": response.status,
                        "response": response_json,
                        "headers": dict(response.headers),
                        "success": response.status < 400,
                    }
        except Exception as e:
            logger.error(f"[HTTPRequest] Failed: {e}")
            return {
                "status_code": 0,
                "response": {"error": str(e)},
                "headers": {},
                "success": False,
            }


@register_action
class SyncToQuickBooksAction(BaseAction):
    """Sync data to QuickBooks."""

    ACTION_ID = "sync_quickbooks"
    ACTION_NAME = "Sync to QuickBooks"
    DESCRIPTION = "Sync record to QuickBooks Online"
    CATEGORY = ActionCategory.INTEGRATION
    ICON = "📗"

    INPUTS = [
        ActionInput("entity", "Entity Type", "select", required=True, options=[
            {"value": "customer", "label": "Customer"},
            {"value": "invoice", "label": "Invoice"},
            {"value": "payment", "label": "Payment"},
        ]),
        ActionInput("record_id", "Record ID", "string", required=True),
        ActionInput("create_if_missing", "Create If Missing", "boolean", required=False, default=True),
    ]

    OUTPUTS = [
        ActionOutput("qb_id", "QuickBooks ID", "string"),
        ActionOutput("sync_status", "Sync Status", "string"),
    ]

    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Sync to QuickBooks."""
        entity = config.get("entity")
        record_id = config.get("record_id")

        # In production: use QuickBooks integration

        logger.info(f"[SyncQuickBooks] Syncing {entity} {record_id}")

        return {
            "qb_id": f"qb_{record_id}",
            "sync_status": "synced",
            "synced_at": datetime.utcnow().isoformat(),
        }


@register_action
class ChargeStripeAction(BaseAction):
    """Charge via Stripe."""

    ACTION_ID = "charge_stripe"
    ACTION_NAME = "Charge via Stripe"
    DESCRIPTION = "Create a Stripe charge or payment intent"
    CATEGORY = ActionCategory.INTEGRATION
    ICON = "💳"

    INPUTS = [
        ActionInput("customer_id", "Stripe Customer ID", "string", required=True),
        ActionInput("amount", "Amount (cents)", "number", required=True),
        ActionInput("currency", "Currency", "string", required=False, default="usd"),
        ActionInput("description", "Description", "string", required=False),
        ActionInput("invoice_id", "Invoice ID", "string", required=False),
    ]

    OUTPUTS = [
        ActionOutput("payment_intent_id", "Payment Intent ID", "string"),
        ActionOutput("status", "Status", "string"),
        ActionOutput("client_secret", "Client Secret", "string"),
    ]

    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Create Stripe charge."""
        customer_id = config.get("customer_id")
        amount = config.get("amount")
        currency = config.get("currency", "usd")

        # In production: use Stripe integration

        logger.info(f"[ChargeStripe] Charging {amount} {currency} to {customer_id}")

        return {
            "payment_intent_id": f"pi_{datetime.utcnow().timestamp()}",
            "status": "requires_confirmation",
            "client_secret": f"pi_secret_{datetime.utcnow().timestamp()}",
        }


@register_action
class TriggerZapierAction(BaseAction):
    """Trigger Zapier webhook."""

    ACTION_ID = "trigger_zapier"
    ACTION_NAME = "Trigger Zapier"
    DESCRIPTION = "Send data to Zapier webhook"
    CATEGORY = ActionCategory.INTEGRATION
    ICON = "⚡"

    INPUTS = [
        ActionInput("webhook_url", "Webhook URL", "string", required=True),
        ActionInput("data", "Data", "string", required=True, description="JSON data to send"),
    ]

    OUTPUTS = [
        ActionOutput("success", "Success", "boolean"),
        ActionOutput("response", "Response", "object"),
    ]

    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Trigger Zapier webhook."""
        import json

        webhook_url = config.get("webhook_url")
        data = config.get("data", {})

        if isinstance(data, str):
            data = json.loads(data)

        logger.info(f"[TriggerZapier] Sending to webhook")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=data) as response:
                    return {
                        "success": response.status < 400,
                        "response": {"status": response.status},
                    }
        except Exception as e:
            return {
                "success": False,
                "response": {"error": str(e)},
            }


@register_action
class GeneratePDFAction(BaseAction):
    """Generate PDF document."""

    ACTION_ID = "generate_pdf"
    ACTION_NAME = "Generate PDF"
    DESCRIPTION = "Generate a PDF document"
    CATEGORY = ActionCategory.INTEGRATION
    ICON = "📄"

    INPUTS = [
        ActionInput("template", "Template", "select", required=True, options=[
            {"value": "invoice", "label": "Invoice"},
            {"value": "quote", "label": "Quote"},
            {"value": "receipt", "label": "Receipt"},
            {"value": "report", "label": "Report"},
        ]),
        ActionInput("record_id", "Record ID", "string", required=True),
        ActionInput("options", "Options", "string", required=False, description="PDF options (JSON)"),
    ]

    OUTPUTS = [
        ActionOutput("file_id", "File ID", "string"),
        ActionOutput("file_url", "File URL", "string"),
    ]

    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Generate PDF."""
        template = config.get("template")
        record_id = config.get("record_id")

        # In production: use PDF generation service

        logger.info(f"[GeneratePDF] Generating {template} for {record_id}")

        file_id = f"pdf_{datetime.utcnow().timestamp()}"

        return {
            "file_id": file_id,
            "file_url": f"/files/{file_id}.pdf",
        }
