"""
Workflow Metadata Routes
Endpoints for triggers, actions, and conditions metadata
"""

from fastapi import APIRouter
from typing import List

from app.workflows.triggers import TriggerRegistry, EventType
from app.workflows.actions.base import action_registry, ActionCategory
from app.workflows.conditions import ConditionBuilder, ConditionPresets
from app.workflows.scheduler import CronExpressionHelper

router = APIRouter(prefix="/workflows/metadata", tags=["Workflow Metadata"])


@router.get("/triggers")
async def get_available_triggers():
    """Get available trigger types and events."""
    return {
        "trigger_types": [
            {"id": "event", "name": "Event Trigger", "description": "Triggered when a specific event occurs"},
            {"id": "schedule", "name": "Schedule Trigger", "description": "Triggered on a schedule (cron or interval)"},
            {"id": "manual", "name": "Manual Trigger", "description": "Triggered manually via API or UI"},
            {"id": "webhook", "name": "Webhook Trigger", "description": "Triggered by external webhook"},
        ],
        "events": TriggerRegistry.get_events_by_category(),
        "schedule_presets": CronExpressionHelper.list_presets(),
    }


@router.get("/actions")
async def get_available_actions():
    """Get available workflow actions."""
    return {
        "categories": action_registry.get_categories(),
        "actions": action_registry.list_all(),
    }


@router.get("/actions/{action_id}")
async def get_action_details(action_id: str):
    """Get details for a specific action."""
    action = action_registry.get(action_id)
    if not action:
        return {"error": "Action not found"}
    return action.get_metadata()


@router.get("/conditions")
async def get_condition_metadata():
    """Get condition operators and presets."""
    return {
        "operators": {
            "string": ConditionBuilder.get_operators_for_type("string"),
            "number": ConditionBuilder.get_operators_for_type("number"),
            "boolean": ConditionBuilder.get_operators_for_type("boolean"),
            "date": ConditionBuilder.get_operators_for_type("date"),
            "array": ConditionBuilder.get_operators_for_type("array"),
        },
        "presets": ConditionPresets.list_presets(),
    }


@router.get("/variables")
async def get_available_variables():
    """Get available workflow variables."""
    return {
        "system_variables": [
            {"name": "now()", "description": "Current datetime", "example": "2024-01-15T10:30:00Z"},
            {"name": "today()", "description": "Today's date", "example": "2024-01-15"},
            {"name": "timestamp()", "description": "Current Unix timestamp", "example": "1705315800"},
            {"name": "uuid()", "description": "Generate unique ID", "example": "a1b2c3d4e5f6"},
        ],
        "context_variables": [
            {"category": "workflow", "variables": [
                {"name": "workflow.id", "description": "Workflow ID"},
                {"name": "workflow.name", "description": "Workflow name"},
                {"name": "execution.id", "description": "Current execution ID"},
            ]},
            {"category": "trigger", "variables": [
                {"name": "trigger.type", "description": "Trigger type (event, schedule, manual)"},
                {"name": "trigger.event", "description": "Event name (for event triggers)"},
                {"name": "trigger.timestamp", "description": "When triggered"},
            ]},
        ],
        "entity_variables": {
            "invoice": ["id", "number", "status", "total", "subtotal", "tax", "currency", "due_date", "customer_id", "customer.name", "customer.email"],
            "payment": ["id", "amount", "method", "status", "invoice_id", "customer_id"],
            "customer": ["id", "name", "email", "phone", "company_name", "tier"],
            "project": ["id", "name", "status", "progress", "due_date", "customer_id"],
            "ticket": ["id", "number", "subject", "status", "priority", "customer_id", "assigned_to"],
        },
        "pipe_functions": [
            {"name": "upper", "description": "Convert to uppercase", "example": "{{name|upper}}"},
            {"name": "lower", "description": "Convert to lowercase", "example": "{{name|lower}}"},
            {"name": "title", "description": "Title case", "example": "{{name|title}}"},
            {"name": "currency", "description": "Format as currency", "example": "{{amount|currency}} -> $1,500.00"},
            {"name": "date", "description": "Format as date", "example": "{{created_at|date}} -> Jan 15, 2024"},
            {"name": "length", "description": "Get length", "example": "{{items|length}} -> 5"},
            {"name": "first", "description": "Get first item", "example": "{{items|first}}"},
            {"name": "last", "description": "Get last item", "example": "{{items|last}}"},
            {"name": "join", "description": "Join array", "example": "{{tags|join}} -> tag1, tag2"},
        ],
    }


@router.post("/cron/validate")
async def validate_cron(cron: str):
    """Validate a cron expression."""
    valid, message = CronExpressionHelper.validate(cron)
    next_runs = CronExpressionHelper.get_next_runs(cron, 5) if valid else []

    return {
        "valid": valid,
        "message": message,
        "next_runs": [r.isoformat() for r in next_runs],
    }


@router.post("/cron/preview")
async def preview_cron(cron: str, count: int = 10):
    """Preview upcoming execution times for a cron expression."""
    valid, _ = CronExpressionHelper.validate(cron)
    if not valid:
        return {"error": "Invalid cron expression"}

    runs = CronExpressionHelper.get_next_runs(cron, count)
    return {"next_runs": [r.isoformat() for r in runs]}
