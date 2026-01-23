"""
CRM Workflow API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List

from app.utils.auth import get_current_user
from app.workflows.triggers.crm_trigger import CRM_EVENTS
from app.workflows.triggers.threshold_trigger import THRESHOLD_METRICS
from app.workflows.actions.crm_actions import CRM_ACTIONS
from app.workflows.rules.crm_conditions import CRM_CONDITION_TEMPLATES


router = APIRouter()


@router.get("/crm/events")
async def get_crm_events(current_user: dict = Depends(get_current_user)):
    """Get available CRM events for triggers"""
    return [{"type": event_type, **event_info} for event_type, event_info in CRM_EVENTS.items()]


@router.get("/crm/events/{entity}")
async def get_crm_events_by_entity(entity: str, current_user: dict = Depends(get_current_user)):
    """Get CRM events for a specific entity type"""
    return [{"type": event_type, **event_info} for event_type, event_info in CRM_EVENTS.items() if event_info.get("entity") == entity]


@router.get("/crm/actions")
async def get_crm_actions(current_user: dict = Depends(get_current_user)):
    """Get available CRM actions"""
    return [{"type": action_type, "name": action_class.__name__.replace("Action", ""), "description": action_class.__doc__} for action_type, action_class in CRM_ACTIONS.items()]


@router.get("/thresholds/metrics")
async def get_threshold_metrics(current_user: dict = Depends(get_current_user)):
    """Get available threshold metrics"""
    return [{"type": metric_type, **metric_info} for metric_type, metric_info in THRESHOLD_METRICS.items()]


@router.get("/crm/conditions/templates")
async def get_condition_templates(entity: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get pre-built condition templates"""
    templates = CRM_CONDITION_TEMPLATES
    if entity:
        templates = [t for t in templates if t.get("entity") == entity]
    return templates


@router.get("/crm/templates")
async def get_crm_workflow_templates(current_user: dict = Depends(get_current_user)):
    """Get pre-built CRM workflow templates"""
    return [
        {"id": "lead_assignment", "name": "Lead Assignment & Follow-up", "category": "crm", "trigger": {"type": "crm_event", "crm_event": "lead.created"}, "steps": [{"type": "crm.assign_owner"}, {"type": "crm.create_activity"}]},
        {"id": "deal_won_celebration", "name": "Deal Won Notification", "category": "crm", "trigger": {"type": "crm_event", "crm_event": "deal.won"}, "steps": [{"type": "notification"}, {"type": "send_email"}]},
        {"id": "quote_follow_up", "name": "Quote Follow-up Reminder", "category": "crm", "trigger": {"type": "crm_event", "crm_event": "quote.sent"}, "steps": [{"type": "delay"}, {"type": "crm.create_activity"}]},
        {"id": "hot_lead_alert", "name": "Hot Lead Alert", "category": "crm", "trigger": {"type": "crm_event", "crm_event": "lead.scored"}, "steps": [{"type": "notification"}, {"type": "send_email"}]},
        {"id": "at_risk_account", "name": "At-Risk Account Alert", "category": "crm", "trigger": {"type": "crm_event", "crm_event": "company.health_changed"}, "steps": [{"type": "crm.create_activity"}, {"type": "send_email"}]},
    ]
