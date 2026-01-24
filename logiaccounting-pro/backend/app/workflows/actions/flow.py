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
