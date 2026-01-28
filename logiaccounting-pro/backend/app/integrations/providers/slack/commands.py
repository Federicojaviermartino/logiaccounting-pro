"""
Slack Slash Commands Handler
Handles /invoice, /customer, /project commands
"""

from typing import Dict, Any, Optional
import logging

from app.utils.datetime_utils import utc_now

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
        current_time = int(utc_now().timestamp())
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
                "text": "Opening invoice creation dialog...",
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
                    "text": {"type": "mrkdwn", "text": f"*Customer Found:*\n- Name: Sample Customer\n- Email: customer@example.com\n- Balance: $2,500.00"},
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
                    "text": {"type": "plain_text", "text": "Balance Summary"},
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
        commands_text = "\n".join([f"- `{cmd}` - {desc}" for cmd, desc in self.COMMANDS.items()])

        return {
            "response_type": "ephemeral",
            "text": "LogiAccounting Commands",
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "Available Commands"},
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
            "text": f"Error: {message}",
        }
