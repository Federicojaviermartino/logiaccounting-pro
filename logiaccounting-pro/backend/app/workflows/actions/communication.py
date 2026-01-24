"""
Communication Actions
Email, SMS, notifications, and messaging actions
"""

from typing import Dict, Any, List
from datetime import datetime
import logging

from app.workflows.actions.base import (
    BaseAction, ActionCategory, ActionInput, ActionOutput, register_action
)

logger = logging.getLogger(__name__)


@register_action
class SendEmailAction(BaseAction):
    """Send email action."""

    ACTION_ID = "send_email"
    ACTION_NAME = "Send Email"
    DESCRIPTION = "Send an email to one or more recipients"
    CATEGORY = ActionCategory.COMMUNICATION
    ICON = "📧"

    INPUTS = [
        ActionInput("to", "To", "email", required=True, description="Recipient email address"),
        ActionInput("cc", "CC", "email", required=False, description="CC recipients (comma-separated)"),
        ActionInput("bcc", "BCC", "email", required=False, description="BCC recipients"),
        ActionInput("subject", "Subject", "string", required=True, placeholder="Email subject"),
        ActionInput("body", "Body", "template", required=True, description="Email body (supports variables)"),
        ActionInput("template", "Template", "select", required=False, options=[
            {"value": "invoice_reminder", "label": "Invoice Reminder"},
            {"value": "payment_receipt", "label": "Payment Receipt"},
            {"value": "welcome", "label": "Welcome Email"},
            {"value": "project_update", "label": "Project Update"},
            {"value": "custom", "label": "Custom"},
        ]),
        ActionInput("attachments", "Attachments", "string", required=False, description="Attachment IDs"),
    ]

    OUTPUTS = [
        ActionOutput("message_id", "Message ID", "string", "Unique email message ID"),
        ActionOutput("sent_at", "Sent At", "datetime", "When email was sent"),
        ActionOutput("recipients", "Recipients", "array", "List of recipients"),
    ]

    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Send email."""
        to = config.get("to")
        cc = config.get("cc", "")
        bcc = config.get("bcc", "")
        subject = config.get("subject")
        body = config.get("body")
        template = config.get("template")

        # In production: use email service
        # await email_service.send(to=to, subject=subject, body=body, ...)

        message_id = f"msg_{datetime.utcnow().timestamp()}"

        logger.info(f"[SendEmail] Sending to {to}: {subject}")

        return {
            "message_id": message_id,
            "sent_at": datetime.utcnow().isoformat(),
            "recipients": [to] + [e.strip() for e in cc.split(",") if e.strip()],
            "success": True,
        }


@register_action
class SendSMSAction(BaseAction):
    """Send SMS action."""

    ACTION_ID = "send_sms"
    ACTION_NAME = "Send SMS"
    DESCRIPTION = "Send an SMS message"
    CATEGORY = ActionCategory.COMMUNICATION
    ICON = "📱"

    INPUTS = [
        ActionInput("to", "Phone Number", "string", required=True, placeholder="+1234567890"),
        ActionInput("message", "Message", "textarea", required=True, description="SMS message (max 160 chars)"),
    ]

    OUTPUTS = [
        ActionOutput("message_id", "Message ID", "string"),
        ActionOutput("status", "Status", "string"),
    ]

    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Send SMS."""
        to = config.get("to")
        message = config.get("message", "")[:160]

        # In production: use Twilio or similar
        message_id = f"sms_{datetime.utcnow().timestamp()}"

        logger.info(f"[SendSMS] Sending to {to}")

        return {
            "message_id": message_id,
            "status": "sent",
            "sent_at": datetime.utcnow().isoformat(),
        }


@register_action
class SendSlackMessageAction(BaseAction):
    """Send Slack message action."""

    ACTION_ID = "send_slack"
    ACTION_NAME = "Send Slack Message"
    DESCRIPTION = "Send a message to a Slack channel"
    CATEGORY = ActionCategory.COMMUNICATION
    ICON = "💬"

    INPUTS = [
        ActionInput("channel", "Channel", "string", required=True, placeholder="#general"),
        ActionInput("message", "Message", "textarea", required=True),
        ActionInput("username", "Username", "string", required=False, default="LogiAccounting"),
        ActionInput("icon_emoji", "Icon Emoji", "string", required=False, default=":robot_face:"),
    ]

    OUTPUTS = [
        ActionOutput("message_ts", "Message Timestamp", "string"),
        ActionOutput("channel_id", "Channel ID", "string"),
    ]

    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Send Slack message."""
        channel = config.get("channel")
        message = config.get("message")

        # In production: use Slack integration

        logger.info(f"[SendSlack] Sending to {channel}")

        return {
            "message_ts": str(datetime.utcnow().timestamp()),
            "channel_id": channel,
            "success": True,
        }


@register_action
class SendNotificationAction(BaseAction):
    """Send in-app notification action."""

    ACTION_ID = "send_notification"
    ACTION_NAME = "Send Notification"
    DESCRIPTION = "Send an in-app notification to a user"
    CATEGORY = ActionCategory.COMMUNICATION
    ICON = "🔔"

    INPUTS = [
        ActionInput("user_id", "User ID", "string", required=True),
        ActionInput("title", "Title", "string", required=True),
        ActionInput("message", "Message", "textarea", required=True),
        ActionInput("type", "Type", "select", required=False, default="info", options=[
            {"value": "info", "label": "Info"},
            {"value": "success", "label": "Success"},
            {"value": "warning", "label": "Warning"},
            {"value": "error", "label": "Error"},
        ]),
        ActionInput("link", "Link URL", "string", required=False),
        ActionInput("push", "Send Push", "boolean", required=False, default=True),
    ]

    OUTPUTS = [
        ActionOutput("notification_id", "Notification ID", "string"),
    ]

    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Send notification."""
        user_id = config.get("user_id")
        title = config.get("title")
        message = config.get("message")

        notification_id = f"notif_{datetime.utcnow().timestamp()}"

        logger.info(f"[SendNotification] Sending to user {user_id}: {title}")

        return {
            "notification_id": notification_id,
            "user_id": user_id,
            "success": True,
        }


@register_action
class SendPushNotificationAction(BaseAction):
    """Send push notification action."""

    ACTION_ID = "send_push"
    ACTION_NAME = "Send Push Notification"
    DESCRIPTION = "Send a push notification to user's devices"
    CATEGORY = ActionCategory.COMMUNICATION
    ICON = "📲"

    INPUTS = [
        ActionInput("user_id", "User ID", "string", required=True),
        ActionInput("title", "Title", "string", required=True),
        ActionInput("body", "Body", "string", required=True),
        ActionInput("icon", "Icon URL", "string", required=False),
        ActionInput("url", "Click URL", "string", required=False),
        ActionInput("tag", "Tag", "string", required=False, description="Replace notifications with same tag"),
    ]

    OUTPUTS = [
        ActionOutput("sent_count", "Sent Count", "number", "Number of devices notified"),
    ]

    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Send push notification."""
        user_id = config.get("user_id")
        title = config.get("title")

        # In production: use push notification service

        logger.info(f"[SendPush] Sending to user {user_id}: {title}")

        return {
            "sent_count": 1,
            "success": True,
        }
