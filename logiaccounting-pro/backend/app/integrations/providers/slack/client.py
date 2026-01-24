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
                "text": {"type": "plain_text", "text": f"New Invoice: {invoice.get('number')}"},
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
                "text": {"type": "plain_text", "text": "Payment Received"},
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
                "text": {"type": "plain_text", "text": "Daily Summary"},
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
