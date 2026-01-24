# Phase 30: Workflow Automation - Part 3: Actions Library

## Overview
This part covers the action system including communication actions, data operations, integration actions, and flow control.

---

## File 1: Action Registry & Base
**Path:** `backend/app/workflows/actions/base.py`

```python
"""
Action Base Classes and Registry
Foundation for workflow actions
"""

from typing import Dict, Any, List, Optional, Callable, Type
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ActionCategory(str, Enum):
    COMMUNICATION = "communication"
    DATA = "data"
    INTEGRATION = "integration"
    FLOW_CONTROL = "flow_control"
    UTILITY = "utility"


class ActionInput:
    """Describes an action input field."""
    
    def __init__(self, name: str, label: str, field_type: str, required: bool = False, default: Any = None, description: str = "", options: List[Dict] = None, placeholder: str = ""):
        self.name = name
        self.label = label
        self.field_type = field_type  # string, number, boolean, select, textarea, email, template
        self.required = required
        self.default = default
        self.description = description
        self.options = options  # For select type
        self.placeholder = placeholder
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "label": self.label,
            "type": self.field_type,
            "required": self.required,
            "default": self.default,
            "description": self.description,
            "options": self.options,
            "placeholder": self.placeholder,
        }


class ActionOutput:
    """Describes an action output."""
    
    def __init__(self, name: str, label: str, output_type: str, description: str = ""):
        self.name = name
        self.label = label
        self.output_type = output_type
        self.description = description
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "label": self.label,
            "type": self.output_type,
            "description": self.description,
        }


class BaseAction(ABC):
    """Abstract base class for all workflow actions."""
    
    # Action metadata (override in subclasses)
    ACTION_ID: str = ""
    ACTION_NAME: str = ""
    DESCRIPTION: str = ""
    CATEGORY: ActionCategory = ActionCategory.UTILITY
    ICON: str = "⚡"
    
    # Input/output definitions
    INPUTS: List[ActionInput] = []
    OUTPUTS: List[ActionOutput] = []
    
    def __init__(self):
        self._execution_count = 0
        self._last_execution = None
    
    def get_metadata(self) -> Dict:
        """Get action metadata."""
        return {
            "id": self.ACTION_ID,
            "name": self.ACTION_NAME,
            "description": self.DESCRIPTION,
            "category": self.CATEGORY.value,
            "icon": self.ICON,
            "inputs": [i.to_dict() for i in self.INPUTS],
            "outputs": [o.to_dict() for o in self.OUTPUTS],
        }
    
    def validate_inputs(self, config: Dict) -> List[str]:
        """Validate input configuration."""
        errors = []
        
        for input_def in self.INPUTS:
            if input_def.required and input_def.name not in config:
                errors.append(f"Missing required input: {input_def.name}")
        
        return errors
    
    @abstractmethod
    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Execute the action."""
        pass
    
    def _log_execution(self, config: Dict, result: Dict, error: str = None):
        """Log action execution."""
        self._execution_count += 1
        self._last_execution = datetime.utcnow()
        
        if error:
            logger.error(f"[{self.ACTION_ID}] Execution failed: {error}")
        else:
            logger.info(f"[{self.ACTION_ID}] Executed successfully")


class ActionRegistry:
    """Registry for all workflow actions."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._actions: Dict[str, BaseAction] = {}
        return cls._instance
    
    def register(self, action: BaseAction):
        """Register an action."""
        self._actions[action.ACTION_ID] = action
        logger.info(f"Registered action: {action.ACTION_ID}")
    
    def get(self, action_id: str) -> Optional[BaseAction]:
        """Get action by ID."""
        return self._actions.get(action_id)
    
    def list_all(self) -> List[Dict]:
        """List all registered actions."""
        return [action.get_metadata() for action in self._actions.values()]
    
    def list_by_category(self, category: ActionCategory) -> List[Dict]:
        """List actions by category."""
        return [
            action.get_metadata()
            for action in self._actions.values()
            if action.CATEGORY == category
        ]
    
    def get_categories(self) -> List[Dict]:
        """Get all categories with their actions."""
        categories = {}
        
        for action in self._actions.values():
            cat = action.CATEGORY.value
            if cat not in categories:
                categories[cat] = {
                    "id": cat,
                    "name": cat.replace("_", " ").title(),
                    "actions": [],
                }
            categories[cat]["actions"].append(action.get_metadata())
        
        return list(categories.values())


# Global registry instance
action_registry = ActionRegistry()


def register_action(cls: Type[BaseAction]) -> Type[BaseAction]:
    """Decorator to register an action."""
    action_registry.register(cls())
    return cls
```

---

## File 2: Communication Actions
**Path:** `backend/app/workflows/actions/communication.py`

```python
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
```

---

## File 3: Data Actions
**Path:** `backend/app/workflows/actions/data.py`

```python
"""
Data Actions
CRUD operations and data manipulation actions
"""

from typing import Dict, Any, List
from datetime import datetime
from uuid import uuid4
import logging

from app.workflows.actions.base import (
    BaseAction, ActionCategory, ActionInput, ActionOutput, register_action
)

logger = logging.getLogger(__name__)


@register_action
class QueryRecordsAction(BaseAction):
    """Query records from database."""
    
    ACTION_ID = "query_records"
    ACTION_NAME = "Query Records"
    DESCRIPTION = "Query records from a data entity"
    CATEGORY = ActionCategory.DATA
    ICON = "🔍"
    
    INPUTS = [
        ActionInput("entity", "Entity", "select", required=True, options=[
            {"value": "invoices", "label": "Invoices"},
            {"value": "customers", "label": "Customers"},
            {"value": "projects", "label": "Projects"},
            {"value": "payments", "label": "Payments"},
            {"value": "tickets", "label": "Tickets"},
            {"value": "products", "label": "Products"},
        ]),
        ActionInput("filter", "Filter", "string", required=False, description="JSON filter criteria"),
        ActionInput("sort_by", "Sort By", "string", required=False),
        ActionInput("sort_order", "Sort Order", "select", required=False, default="desc", options=[
            {"value": "asc", "label": "Ascending"},
            {"value": "desc", "label": "Descending"},
        ]),
        ActionInput("limit", "Limit", "number", required=False, default=100),
    ]
    
    OUTPUTS = [
        ActionOutput("records", "Records", "array", "List of matching records"),
        ActionOutput("count", "Count", "number", "Total count of records"),
    ]
    
    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Query records."""
        entity = config.get("entity")
        filter_criteria = config.get("filter", {})
        limit = config.get("limit", 100)
        
        # In production: query actual database
        # records = await db.query(entity, filter=filter_criteria, limit=limit)
        
        logger.info(f"[QueryRecords] Querying {entity}")
        
        # Demo response
        return {
            "records": [],
            "count": 0,
            "entity": entity,
        }


@register_action
class CreateRecordAction(BaseAction):
    """Create a new record."""
    
    ACTION_ID = "create_record"
    ACTION_NAME = "Create Record"
    DESCRIPTION = "Create a new record in a data entity"
    CATEGORY = ActionCategory.DATA
    ICON = "➕"
    
    INPUTS = [
        ActionInput("entity", "Entity", "select", required=True, options=[
            {"value": "invoice", "label": "Invoice"},
            {"value": "customer", "label": "Customer"},
            {"value": "project", "label": "Project"},
            {"value": "ticket", "label": "Ticket"},
            {"value": "note", "label": "Note"},
        ]),
        ActionInput("data", "Data", "string", required=True, description="JSON data for the record"),
    ]
    
    OUTPUTS = [
        ActionOutput("record_id", "Record ID", "string"),
        ActionOutput("record", "Record", "object", "Created record data"),
    ]
    
    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Create record."""
        entity = config.get("entity")
        data = config.get("data", {})
        
        if isinstance(data, str):
            import json
            data = json.loads(data)
        
        record_id = f"{entity}_{uuid4().hex[:12]}"
        
        logger.info(f"[CreateRecord] Creating {entity}")
        
        return {
            "record_id": record_id,
            "record": {**data, "id": record_id, "created_at": datetime.utcnow().isoformat()},
        }


@register_action
class UpdateRecordAction(BaseAction):
    """Update an existing record."""
    
    ACTION_ID = "update_record"
    ACTION_NAME = "Update Record"
    DESCRIPTION = "Update an existing record"
    CATEGORY = ActionCategory.DATA
    ICON = "✏️"
    
    INPUTS = [
        ActionInput("entity", "Entity", "select", required=True, options=[
            {"value": "invoice", "label": "Invoice"},
            {"value": "customer", "label": "Customer"},
            {"value": "project", "label": "Project"},
            {"value": "ticket", "label": "Ticket"},
        ]),
        ActionInput("record_id", "Record ID", "string", required=True),
        ActionInput("data", "Data", "string", required=True, description="JSON data to update"),
    ]
    
    OUTPUTS = [
        ActionOutput("success", "Success", "boolean"),
        ActionOutput("record", "Record", "object", "Updated record data"),
    ]
    
    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Update record."""
        entity = config.get("entity")
        record_id = config.get("record_id")
        data = config.get("data", {})
        
        if isinstance(data, str):
            import json
            data = json.loads(data)
        
        logger.info(f"[UpdateRecord] Updating {entity} {record_id}")
        
        return {
            "success": True,
            "record": {**data, "id": record_id, "updated_at": datetime.utcnow().isoformat()},
        }


@register_action
class DeleteRecordAction(BaseAction):
    """Delete a record."""
    
    ACTION_ID = "delete_record"
    ACTION_NAME = "Delete Record"
    DESCRIPTION = "Delete a record (soft delete)"
    CATEGORY = ActionCategory.DATA
    ICON = "🗑️"
    
    INPUTS = [
        ActionInput("entity", "Entity", "select", required=True, options=[
            {"value": "invoice", "label": "Invoice"},
            {"value": "customer", "label": "Customer"},
            {"value": "project", "label": "Project"},
            {"value": "ticket", "label": "Ticket"},
        ]),
        ActionInput("record_id", "Record ID", "string", required=True),
        ActionInput("hard_delete", "Hard Delete", "boolean", required=False, default=False),
    ]
    
    OUTPUTS = [
        ActionOutput("success", "Success", "boolean"),
        ActionOutput("deleted_at", "Deleted At", "datetime"),
    ]
    
    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Delete record."""
        entity = config.get("entity")
        record_id = config.get("record_id")
        
        logger.info(f"[DeleteRecord] Deleting {entity} {record_id}")
        
        return {
            "success": True,
            "deleted_at": datetime.utcnow().isoformat(),
        }


@register_action
class CalculateAction(BaseAction):
    """Perform calculations."""
    
    ACTION_ID = "calculate"
    ACTION_NAME = "Calculate"
    DESCRIPTION = "Perform mathematical calculations"
    CATEGORY = ActionCategory.DATA
    ICON = "🔢"
    
    INPUTS = [
        ActionInput("operation", "Operation", "select", required=True, options=[
            {"value": "sum", "label": "Sum"},
            {"value": "average", "label": "Average"},
            {"value": "min", "label": "Minimum"},
            {"value": "max", "label": "Maximum"},
            {"value": "count", "label": "Count"},
            {"value": "add", "label": "Add (a + b)"},
            {"value": "subtract", "label": "Subtract (a - b)"},
            {"value": "multiply", "label": "Multiply (a * b)"},
            {"value": "divide", "label": "Divide (a / b)"},
            {"value": "percentage", "label": "Percentage (a% of b)"},
        ]),
        ActionInput("values", "Values", "string", required=False, description="Array of values for aggregate operations"),
        ActionInput("a", "Value A", "number", required=False),
        ActionInput("b", "Value B", "number", required=False),
    ]
    
    OUTPUTS = [
        ActionOutput("result", "Result", "number"),
    ]
    
    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Perform calculation."""
        operation = config.get("operation")
        values = config.get("values", [])
        a = config.get("a", 0)
        b = config.get("b", 0)
        
        if isinstance(values, str):
            import json
            values = json.loads(values)
        
        result = 0
        
        if operation == "sum":
            result = sum(values)
        elif operation == "average":
            result = sum(values) / len(values) if values else 0
        elif operation == "min":
            result = min(values) if values else 0
        elif operation == "max":
            result = max(values) if values else 0
        elif operation == "count":
            result = len(values)
        elif operation == "add":
            result = float(a) + float(b)
        elif operation == "subtract":
            result = float(a) - float(b)
        elif operation == "multiply":
            result = float(a) * float(b)
        elif operation == "divide":
            result = float(a) / float(b) if b != 0 else 0
        elif operation == "percentage":
            result = (float(a) / 100) * float(b)
        
        return {"result": result}


@register_action
class TransformDataAction(BaseAction):
    """Transform data structure."""
    
    ACTION_ID = "transform_data"
    ACTION_NAME = "Transform Data"
    DESCRIPTION = "Transform data from one format to another"
    CATEGORY = ActionCategory.DATA
    ICON = "🔄"
    
    INPUTS = [
        ActionInput("input", "Input Data", "string", required=True, description="Input data (JSON)"),
        ActionInput("mapping", "Field Mapping", "string", required=True, description="Field mapping (JSON)"),
    ]
    
    OUTPUTS = [
        ActionOutput("output", "Output Data", "object"),
    ]
    
    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Transform data."""
        import json
        
        input_data = config.get("input", {})
        mapping = config.get("mapping", {})
        
        if isinstance(input_data, str):
            input_data = json.loads(input_data)
        if isinstance(mapping, str):
            mapping = json.loads(mapping)
        
        output = {}
        for target_key, source_key in mapping.items():
            if source_key in input_data:
                output[target_key] = input_data[source_key]
        
        return {"output": output}
```

---

## File 4: Integration Actions
**Path:** `backend/app/workflows/actions/integration.py`

```python
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
```

---

## File 5: Flow Control Actions
**Path:** `backend/app/workflows/actions/flow.py`

```python
"""
Flow Control Actions
Workflow control actions like delays, conditions, and stops
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import asyncio
import logging

from app.workflows.actions.base import (
    BaseAction, ActionCategory, ActionInput, ActionOutput, register_action
)

logger = logging.getLogger(__name__)


@register_action
class DelayAction(BaseAction):
    """Delay workflow execution."""
    
    ACTION_ID = "delay"
    ACTION_NAME = "Delay"
    DESCRIPTION = "Wait for a specified duration"
    CATEGORY = ActionCategory.FLOW_CONTROL
    ICON = "⏱️"
    
    INPUTS = [
        ActionInput("duration", "Duration", "number", required=True, description="Duration in seconds"),
        ActionInput("unit", "Unit", "select", required=False, default="seconds", options=[
            {"value": "seconds", "label": "Seconds"},
            {"value": "minutes", "label": "Minutes"},
            {"value": "hours", "label": "Hours"},
            {"value": "days", "label": "Days"},
        ]),
    ]
    
    OUTPUTS = [
        ActionOutput("waited_seconds", "Waited Seconds", "number"),
        ActionOutput("resumed_at", "Resumed At", "datetime"),
    ]
    
    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Wait for duration."""
        duration = config.get("duration", 0)
        unit = config.get("unit", "seconds")
        
        multipliers = {
            "seconds": 1,
            "minutes": 60,
            "hours": 3600,
            "days": 86400,
        }
        
        seconds = duration * multipliers.get(unit, 1)
        
        logger.info(f"[Delay] Waiting {seconds} seconds")
        
        await asyncio.sleep(seconds)
        
        return {
            "waited_seconds": seconds,
            "resumed_at": datetime.utcnow().isoformat(),
        }


@register_action
class WaitUntilAction(BaseAction):
    """Wait until specific time."""
    
    ACTION_ID = "wait_until"
    ACTION_NAME = "Wait Until"
    DESCRIPTION = "Wait until a specific date/time"
    CATEGORY = ActionCategory.FLOW_CONTROL
    ICON = "📅"
    
    INPUTS = [
        ActionInput("datetime", "Date/Time", "string", required=True, description="ISO datetime or variable"),
    ]
    
    OUTPUTS = [
        ActionOutput("target_time", "Target Time", "datetime"),
        ActionOutput("actual_time", "Actual Time", "datetime"),
    ]
    
    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Wait until time."""
        target_str = config.get("datetime")
        target = datetime.fromisoformat(target_str.replace("Z", "+00:00"))
        
        now = datetime.utcnow()
        if target > now:
            wait_seconds = (target - now).total_seconds()
            logger.info(f"[WaitUntil] Waiting until {target} ({wait_seconds}s)")
            await asyncio.sleep(wait_seconds)
        
        return {
            "target_time": target.isoformat(),
            "actual_time": datetime.utcnow().isoformat(),
        }


@register_action
class StopWorkflowAction(BaseAction):
    """Stop workflow execution."""
    
    ACTION_ID = "stop_workflow"
    ACTION_NAME = "Stop Workflow"
    DESCRIPTION = "Stop the workflow execution"
    CATEGORY = ActionCategory.FLOW_CONTROL
    ICON = "🛑"
    
    INPUTS = [
        ActionInput("reason", "Reason", "string", required=False, description="Reason for stopping"),
        ActionInput("success", "Success", "boolean", required=False, default=True, description="Mark as success or failure"),
    ]
    
    OUTPUTS = [
        ActionOutput("stopped_at", "Stopped At", "datetime"),
        ActionOutput("reason", "Reason", "string"),
    ]
    
    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Stop workflow."""
        reason = config.get("reason", "Manual stop")
        success = config.get("success", True)
        
        logger.info(f"[StopWorkflow] Stopping: {reason}")
        
        # Raise special exception to stop workflow
        from app.workflows.errors import WorkflowError, WorkflowErrorType
        
        raise WorkflowError(
            message=f"Workflow stopped: {reason}",
            error_type=WorkflowErrorType.CANCELLED if success else WorkflowErrorType.EXECUTION_ERROR,
            recoverable=False,
        )


@register_action
class SetVariableAction(BaseAction):
    """Set a variable value."""
    
    ACTION_ID = "set_variable"
    ACTION_NAME = "Set Variable"
    DESCRIPTION = "Set or update a workflow variable"
    CATEGORY = ActionCategory.FLOW_CONTROL
    ICON = "📝"
    
    INPUTS = [
        ActionInput("name", "Variable Name", "string", required=True),
        ActionInput("value", "Value", "string", required=True),
    ]
    
    OUTPUTS = [
        ActionOutput("name", "Name", "string"),
        ActionOutput("value", "Value", "string"),
    ]
    
    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Set variable."""
        name = config.get("name")
        value = config.get("value")
        
        logger.info(f"[SetVariable] {name} = {value}")
        
        return {
            "name": name,
            "value": value,
            name: value,  # This allows accessing the variable by name
        }


@register_action
class LogAction(BaseAction):
    """Log a message."""
    
    ACTION_ID = "log"
    ACTION_NAME = "Log Message"
    DESCRIPTION = "Log a message for debugging"
    CATEGORY = ActionCategory.FLOW_CONTROL
    ICON = "📋"
    
    INPUTS = [
        ActionInput("message", "Message", "textarea", required=True),
        ActionInput("level", "Level", "select", required=False, default="info", options=[
            {"value": "debug", "label": "Debug"},
            {"value": "info", "label": "Info"},
            {"value": "warning", "label": "Warning"},
            {"value": "error", "label": "Error"},
        ]),
        ActionInput("data", "Additional Data", "string", required=False, description="JSON data to log"),
    ]
    
    OUTPUTS = [
        ActionOutput("logged_at", "Logged At", "datetime"),
    ]
    
    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Log message."""
        message = config.get("message")
        level = config.get("level", "info")
        
        log_func = getattr(logger, level, logger.info)
        log_func(f"[WorkflowLog] {message}")
        
        return {
            "logged_at": datetime.utcnow().isoformat(),
            "message": message,
        }


@register_action
class ApprovalAction(BaseAction):
    """Request approval before continuing."""
    
    ACTION_ID = "request_approval"
    ACTION_NAME = "Request Approval"
    DESCRIPTION = "Pause workflow and request human approval"
    CATEGORY = ActionCategory.FLOW_CONTROL
    ICON = "✋"
    
    INPUTS = [
        ActionInput("approvers", "Approvers", "string", required=True, description="Comma-separated user IDs or emails"),
        ActionInput("title", "Title", "string", required=True),
        ActionInput("description", "Description", "textarea", required=False),
        ActionInput("timeout_hours", "Timeout (hours)", "number", required=False, default=24),
    ]
    
    OUTPUTS = [
        ActionOutput("approved", "Approved", "boolean"),
        ActionOutput("approved_by", "Approved By", "string"),
        ActionOutput("approved_at", "Approved At", "datetime"),
        ActionOutput("comments", "Comments", "string"),
    ]
    
    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Request approval."""
        approvers = config.get("approvers", "")
        title = config.get("title")
        
        logger.info(f"[RequestApproval] Requesting: {title}")
        
        # In production: create approval request and wait
        # For demo, auto-approve
        
        return {
            "approved": True,
            "approved_by": approvers.split(",")[0].strip(),
            "approved_at": datetime.utcnow().isoformat(),
            "comments": "Auto-approved (demo)",
        }
```

---

## Summary Part 3

| File | Description | Lines |
|------|-------------|-------|
| `actions/base.py` | Action registry & base class | ~200 |
| `actions/communication.py` | Email, SMS, Slack, notifications | ~260 |
| `actions/data.py` | CRUD, calculate, transform | ~300 |
| `actions/integration.py` | HTTP, QuickBooks, Stripe, Zapier | ~280 |
| `actions/flow.py` | Delay, wait, stop, log, approval | ~260 |
| **Total** | | **~1,300 lines** |
