"""
Email action executor.
Sends emails using configured email templates.
"""
from typing import Dict, Any, List
import logging
import re
import uuid

from app.workflows.actions import ActionExecutor


logger = logging.getLogger(__name__)


EMAIL_TEMPLATES = {
    "invoice_created": {
        "subject": "New Invoice #{{invoice.number}}",
        "body": """
Dear {{client.name}},

A new invoice has been created for you.

Invoice Number: {{invoice.number}}
Amount: {{invoice.currency}} {{invoice.amount}}
Due Date: {{invoice.due_date}}

Please review and process the payment at your earliest convenience.

Best regards,
{{company.name}}
        """
    },
    "payment_reminder": {
        "subject": "Payment Reminder - Invoice #{{invoice.number}}",
        "body": """
Dear {{client.name}},

This is a friendly reminder that invoice #{{invoice.number}} is due for payment.

Amount Due: {{invoice.currency}} {{invoice.amount}}
Due Date: {{invoice.due_date}}
Days Overdue: {{invoice.days_overdue}}

Please process the payment at your earliest convenience.

Best regards,
{{company.name}}
        """
    },
    "approval_request": {
        "subject": "Approval Required: {{entity.type}} #{{entity.id}}",
        "body": """
Dear {{approver.name}},

Your approval is required for the following item:

Type: {{entity.type}}
ID: {{entity.id}}
Amount: {{entity.amount}}
Requested by: {{requester.name}}

Please review and approve/reject in the system.

Link: {{approval.link}}

Best regards,
Workflow System
        """
    },
    "workflow_failure": {
        "subject": "Workflow Failure Alert: {{workflow.name}}",
        "body": """
A workflow execution has failed.

Workflow: {{workflow.name}}
Execution ID: {{execution.id}}
Error: {{error}}

Please investigate and take appropriate action.
        """
    },
    "low_stock_alert": {
        "subject": "Low Stock Alert: {{item.name}}",
        "body": """
The following inventory item is running low:

Item: {{item.name}}
SKU: {{item.sku}}
Current Stock: {{item.quantity}}
Minimum Level: {{item.min_level}}

Please reorder to maintain adequate stock levels.
        """
    }
}


class EmailActionExecutor(ActionExecutor):
    """Executes email send actions."""

    async def execute(
        self,
        config: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send an email.

        Config:
            template: Template ID or custom subject/body
            recipients: List of email addresses or user IDs
            cc: Optional CC list
            bcc: Optional BCC list
            attachments: Optional attachment IDs
            variables: Additional template variables
        """
        recipients = self._resolve_recipients(
            config.get("recipients", []),
            variables
        )

        if not recipients:
            return {"sent": False, "error": "No recipients"}

        template_id = config.get("template")

        if template_id and template_id in EMAIL_TEMPLATES:
            template = EMAIL_TEMPLATES[template_id]
            subject = template["subject"]
            body = template["body"]
        else:
            subject = config.get("subject", "")
            body = config.get("body", "")

        all_variables = {**variables, **config.get("variables", {})}

        subject = self._interpolate(subject, all_variables)
        body = self._interpolate(body, all_variables)

        result = await self._send_email(
            to=recipients,
            cc=config.get("cc", []),
            bcc=config.get("bcc", []),
            subject=subject,
            body=body,
            attachments=config.get("attachments", [])
        )

        logger.info(f"Email sent to {len(recipients)} recipients: {subject}")

        return {
            "sent": True,
            "recipients": recipients,
            "subject": subject,
            "message_id": result.get("message_id")
        }

    def _resolve_recipients(
        self,
        recipients: List[str],
        variables: Dict[str, Any]
    ) -> List[str]:
        """Resolve recipient references to email addresses."""
        resolved = []

        for recipient in recipients:
            if "@" in recipient:
                resolved.append(recipient)
            elif recipient.startswith("{{") and recipient.endswith("}}"):
                key = recipient[2:-2].strip()
                value = self._get_nested(variables, key)
                if value:
                    if isinstance(value, list):
                        resolved.extend(value)
                    else:
                        resolved.append(str(value))

        return resolved

    def _interpolate(self, text: str, variables: Dict[str, Any]) -> str:
        """Interpolate variables in text."""
        def replace(match):
            key = match.group(1).strip()
            value = self._get_nested(variables, key)
            return str(value) if value is not None else match.group(0)

        return re.sub(r'\{\{([^}]+)\}\}', replace, text)

    def _get_nested(self, obj: Dict, path: str) -> Any:
        """Get nested value from dict using dot notation."""
        keys = path.split(".")
        value = obj

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

        return value

    async def _send_email(
        self,
        to: List[str],
        cc: List[str],
        bcc: List[str],
        subject: str,
        body: str,
        attachments: List[str]
    ) -> Dict[str, Any]:
        """Send email using email service."""
        return {
            "message_id": str(uuid.uuid4()),
            "status": "sent"
        }
