# Phase 30: Workflow Automation - Part 4: API Routes & Service

## Overview
This part covers the backend API routes and workflow service for managing workflows.

---

## File 1: Workflow Service
**Path:** `backend/app/services/workflow_service.py`

```python
"""
Workflow Service
Business logic for workflow management
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4
import logging

from app.workflows.models import (
    Workflow, WorkflowNode, WorkflowEdge, WorkflowTrigger,
    WorkflowExecution, WorkflowStatus, ExecutionStatus, TriggerType, NodeType
)
from app.workflows.engine import workflow_engine
from app.workflows.triggers import trigger_registry
from app.workflows.scheduler import workflow_scheduler
from app.workflows.errors import WorkflowValidator, ValidationError

logger = logging.getLogger(__name__)


class WorkflowService:
    """Manages workflow CRUD and execution."""
    
    def __init__(self):
        self._workflows: Dict[str, Workflow] = {}
        self._templates: Dict[str, Dict] = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load workflow templates."""
        self._templates = {
            "invoice_reminder": {
                "id": "tpl_invoice_reminder",
                "name": "Invoice Reminder",
                "description": "Send email reminders for upcoming invoice due dates",
                "category": "invoices",
                "trigger": {"type": "schedule", "cron": "0 9 * * *"},
                "nodes": [
                    {"id": "n1", "type": "action", "action": "query_records", "config": {"entity": "invoices", "filter": {"status": "pending"}}},
                    {"id": "n2", "type": "loop", "collection": "{{records}}", "item_variable": "invoice", "body": ["n3"]},
                    {"id": "n3", "type": "action", "action": "send_email", "config": {"to": "{{invoice.customer.email}}", "template": "invoice_reminder"}},
                ],
            },
            "payment_notification": {
                "id": "tpl_payment_notification",
                "name": "Payment Received Notification",
                "description": "Notify team when payment is received",
                "category": "payments",
                "trigger": {"type": "event", "event": "payment.received"},
                "nodes": [
                    {"id": "n1", "type": "action", "action": "send_slack", "config": {"channel": "#payments", "message": "Payment of {{payment.amount|currency}} received"}},
                    {"id": "n2", "type": "action", "action": "send_email", "config": {"to": "{{payment.customer.email}}", "template": "payment_receipt"}},
                ],
            },
            "new_customer_welcome": {
                "id": "tpl_new_customer",
                "name": "New Customer Welcome",
                "description": "Send welcome email to new customers",
                "category": "customers",
                "trigger": {"type": "event", "event": "customer.created"},
                "nodes": [
                    {"id": "n1", "type": "action", "action": "send_email", "config": {"to": "{{customer.email}}", "template": "welcome"}},
                    {"id": "n2", "type": "action", "action": "send_notification", "config": {"user_id": "sales_team", "title": "New Customer", "message": "{{customer.name}} just signed up"}},
                ],
            },
            "ticket_escalation": {
                "id": "tpl_ticket_escalation",
                "name": "Ticket SLA Escalation",
                "description": "Escalate tickets approaching SLA breach",
                "category": "tickets",
                "trigger": {"type": "schedule", "cron": "*/15 * * * *"},
                "nodes": [
                    {"id": "n1", "type": "action", "action": "query_records", "config": {"entity": "tickets", "filter": {"status": "open", "created_hours_ago": {"$gt": 4}}}},
                    {"id": "n2", "type": "loop", "collection": "{{records}}", "item_variable": "ticket", "body": ["n3", "n4"]},
                    {"id": "n3", "type": "action", "action": "update_record", "config": {"entity": "ticket", "record_id": "{{ticket.id}}", "data": {"priority": "urgent"}}},
                    {"id": "n4", "type": "action", "action": "send_notification", "config": {"user_id": "{{ticket.assigned_to}}", "title": "SLA Alert", "message": "Ticket #{{ticket.number}} needs attention"}},
                ],
            },
            "overdue_invoice": {
                "id": "tpl_overdue_invoice",
                "name": "Overdue Invoice Handler",
                "description": "Handle invoices that become overdue",
                "category": "invoices",
                "trigger": {"type": "event", "event": "invoice.overdue"},
                "nodes": [
                    {"id": "n1", "type": "condition", "condition": {"field": "invoice.days_overdue", "operator": "greater_than", "value": 7}, "true_branch": ["n2"], "false_branch": ["n3"]},
                    {"id": "n2", "type": "action", "action": "send_email", "config": {"to": "{{invoice.customer.email}}", "template": "final_notice"}},
                    {"id": "n3", "type": "action", "action": "send_email", "config": {"to": "{{invoice.customer.email}}", "template": "reminder"}},
                ],
            },
        }
    
    # ==================== CRUD Operations ====================
    
    def create_workflow(self, data: Dict, customer_id: str, user_id: str) -> Workflow:
        """Create a new workflow."""
        # Validate
        errors = WorkflowValidator.validate(data)
        if errors:
            raise ValidationError("Invalid workflow", errors)
        
        # Build workflow
        workflow = Workflow(
            id=f"wf_{uuid4().hex[:12]}",
            name=data.get("name", "Untitled Workflow"),
            customer_id=customer_id,
            description=data.get("description", ""),
            status=WorkflowStatus.DRAFT,
            created_by=user_id,
        )
        
        # Parse trigger
        trigger_data = data.get("trigger", {})
        if trigger_data:
            workflow.trigger = WorkflowTrigger.from_dict(trigger_data)
        
        # Parse nodes
        for node_data in data.get("nodes", []):
            workflow.nodes.append(WorkflowNode.from_dict(node_data))
        
        # Parse edges
        for edge_data in data.get("edges", []):
            workflow.edges.append(WorkflowEdge(
                id=edge_data.get("id", f"edge_{uuid4().hex[:8]}"),
                source=edge_data.get("source"),
                target=edge_data.get("target"),
                label=edge_data.get("label"),
                condition=edge_data.get("condition"),
            ))
        
        # Store workflow
        self._workflows[workflow.id] = workflow
        
        logger.info(f"Created workflow {workflow.id}: {workflow.name}")
        return workflow
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID."""
        return self._workflows.get(workflow_id)
    
    def list_workflows(self, customer_id: str, status: str = None, limit: int = 50, offset: int = 0) -> Dict:
        """List workflows for a customer."""
        workflows = [
            wf for wf in self._workflows.values()
            if wf.customer_id == customer_id
        ]
        
        if status:
            workflows = [wf for wf in workflows if wf.status.value == status]
        
        # Sort by updated_at descending
        workflows = sorted(workflows, key=lambda w: w.updated_at, reverse=True)
        
        total = len(workflows)
        workflows = workflows[offset:offset + limit]
        
        return {
            "workflows": [wf.to_dict() for wf in workflows],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    
    def update_workflow(self, workflow_id: str, data: Dict) -> Optional[Workflow]:
        """Update a workflow."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return None
        
        # Update basic fields
        if "name" in data:
            workflow.name = data["name"]
        if "description" in data:
            workflow.description = data["description"]
        
        # Update trigger
        if "trigger" in data:
            workflow.trigger = WorkflowTrigger.from_dict(data["trigger"])
        
        # Update nodes
        if "nodes" in data:
            workflow.nodes = [WorkflowNode.from_dict(n) for n in data["nodes"]]
        
        # Update edges
        if "edges" in data:
            workflow.edges = [
                WorkflowEdge(
                    id=e.get("id", f"edge_{uuid4().hex[:8]}"),
                    source=e.get("source"),
                    target=e.get("target"),
                    label=e.get("label"),
                    condition=e.get("condition"),
                )
                for e in data["edges"]
            ]
        
        workflow.updated_at = datetime.utcnow()
        workflow.version += 1
        
        # Re-register triggers if active
        if workflow.status == WorkflowStatus.ACTIVE:
            self._register_workflow_triggers(workflow)
        
        logger.info(f"Updated workflow {workflow_id}")
        return workflow
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return False
        
        # Deactivate first
        if workflow.status == WorkflowStatus.ACTIVE:
            self.deactivate_workflow(workflow_id)
        
        del self._workflows[workflow_id]
        logger.info(f"Deleted workflow {workflow_id}")
        return True
    
    # ==================== Activation ====================
    
    def activate_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Activate a workflow."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return None
        
        # Validate before activation
        errors = WorkflowValidator.validate(workflow.to_dict())
        if errors:
            raise ValidationError("Cannot activate invalid workflow", errors)
        
        workflow.status = WorkflowStatus.ACTIVE
        workflow.updated_at = datetime.utcnow()
        
        # Register triggers
        self._register_workflow_triggers(workflow)
        
        logger.info(f"Activated workflow {workflow_id}")
        return workflow
    
    def deactivate_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Deactivate a workflow."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return None
        
        workflow.status = WorkflowStatus.PAUSED
        workflow.updated_at = datetime.utcnow()
        
        # Unregister triggers
        self._unregister_workflow_triggers(workflow)
        
        logger.info(f"Deactivated workflow {workflow_id}")
        return workflow
    
    def _register_workflow_triggers(self, workflow: Workflow):
        """Register workflow triggers."""
        if not workflow.trigger:
            return
        
        if workflow.trigger.type == TriggerType.EVENT:
            trigger_registry.subscribe_workflow(workflow.id, workflow.trigger.event)
        
        elif workflow.trigger.type == TriggerType.SCHEDULE:
            schedule_type = "cron" if workflow.trigger.cron else "interval"
            schedule_config = {}
            if workflow.trigger.cron:
                schedule_config["cron"] = workflow.trigger.cron
            elif workflow.trigger.interval_seconds:
                schedule_config["interval_seconds"] = workflow.trigger.interval_seconds
            
            workflow_scheduler.add_job(workflow.id, schedule_type, schedule_config)
    
    def _unregister_workflow_triggers(self, workflow: Workflow):
        """Unregister workflow triggers."""
        trigger_registry.unsubscribe_workflow(workflow.id)
        workflow_scheduler.remove_job(workflow.id)
    
    # ==================== Execution ====================
    
    async def execute_workflow(self, workflow_id: str, input_data: Dict = None, trigger_data: Dict = None) -> WorkflowExecution:
        """Execute a workflow."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        return await workflow_engine.execute(workflow, input_data, trigger_data)
    
    def get_executions(self, workflow_id: str, limit: int = 20) -> List[Dict]:
        """Get workflow execution history."""
        executions = workflow_engine.get_workflow_executions(workflow_id, limit)
        return [e.to_dict() for e in executions]
    
    def get_execution(self, execution_id: str) -> Optional[Dict]:
        """Get execution details."""
        execution = workflow_engine.get_execution(execution_id)
        return execution.to_dict() if execution else None
    
    # ==================== Templates ====================
    
    def get_templates(self, category: str = None) -> List[Dict]:
        """Get workflow templates."""
        templates = list(self._templates.values())
        
        if category:
            templates = [t for t in templates if t.get("category") == category]
        
        return templates
    
    def get_template(self, template_id: str) -> Optional[Dict]:
        """Get template by ID."""
        return self._templates.get(template_id)
    
    def create_from_template(self, template_id: str, customer_id: str, user_id: str, overrides: Dict = None) -> Workflow:
        """Create workflow from template."""
        template = self._templates.get(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        # Merge template with overrides
        data = {**template, **(overrides or {})}
        data.pop("id", None)  # Remove template ID
        
        return self.create_workflow(data, customer_id, user_id)
    
    # ==================== Statistics ====================
    
    def get_workflow_stats(self, workflow_id: str) -> Dict:
        """Get workflow statistics."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return {}
        
        executions = workflow_engine.get_workflow_executions(workflow_id, limit=100)
        
        completed = len([e for e in executions if e.status == ExecutionStatus.COMPLETED])
        failed = len([e for e in executions if e.status == ExecutionStatus.FAILED])
        
        avg_duration = 0
        if executions:
            durations = [e.duration_ms for e in executions if e.duration_ms]
            avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "workflow_id": workflow_id,
            "total_executions": workflow.run_count,
            "recent_executions": len(executions),
            "completed": completed,
            "failed": failed,
            "success_rate": (completed / len(executions) * 100) if executions else 0,
            "average_duration_ms": avg_duration,
            "last_executed_at": workflow.last_run_at.isoformat() if workflow.last_run_at else None,
        }
    
    def get_customer_stats(self, customer_id: str) -> Dict:
        """Get workflow stats for a customer."""
        workflows = [wf for wf in self._workflows.values() if wf.customer_id == customer_id]
        
        active = len([wf for wf in workflows if wf.status == WorkflowStatus.ACTIVE])
        total_executions = sum(wf.run_count for wf in workflows)
        
        return {
            "total_workflows": len(workflows),
            "active_workflows": active,
            "total_executions": total_executions,
        }


# Global service instance
workflow_service = WorkflowService()
```

---

## File 2: Workflow Routes
**Path:** `backend/app/routes/workflows.py`

```python
"""
Workflow API Routes
REST endpoints for workflow management
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from app.services.workflow_service import workflow_service
from app.workflows.errors import ValidationError
from app.auth.dependencies import get_current_user, get_current_customer_id

router = APIRouter(prefix="/workflows", tags=["Workflows"])


# ==================== Request/Response Models ====================

class TriggerConfig(BaseModel):
    type: str = Field(..., description="Trigger type: event, schedule, manual, webhook")
    event: Optional[str] = None
    cron: Optional[str] = None
    interval_seconds: Optional[int] = None
    webhook_path: Optional[str] = None


class NodePosition(BaseModel):
    x: int = 0
    y: int = 0


class WorkflowNode(BaseModel):
    id: str
    type: str
    name: Optional[str] = ""
    config: dict = {}
    position: Optional[NodePosition] = None
    action: Optional[str] = None
    condition: Optional[dict] = None
    true_branch: Optional[List[str]] = []
    false_branch: Optional[List[str]] = []
    collection: Optional[str] = None
    item_variable: Optional[str] = None
    body: Optional[List[str]] = []
    outputs: Optional[List[str]] = []


class WorkflowEdge(BaseModel):
    id: Optional[str] = None
    source: str
    target: str
    label: Optional[str] = None
    condition: Optional[str] = None


class CreateWorkflowRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = ""
    trigger: TriggerConfig
    nodes: List[WorkflowNode] = []
    edges: List[WorkflowEdge] = []


class UpdateWorkflowRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger: Optional[TriggerConfig] = None
    nodes: Optional[List[WorkflowNode]] = None
    edges: Optional[List[WorkflowEdge]] = None


class ExecuteWorkflowRequest(BaseModel):
    input_data: Optional[dict] = {}
    trigger_data: Optional[dict] = {}


class CreateFromTemplateRequest(BaseModel):
    template_id: str
    name: Optional[str] = None
    description: Optional[str] = None


# ==================== Routes ====================

@router.get("")
async def list_workflows(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    customer_id: str = Depends(get_current_customer_id),
):
    """List all workflows for the current customer."""
    return workflow_service.list_workflows(
        customer_id=customer_id,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.post("")
async def create_workflow(
    request: CreateWorkflowRequest,
    customer_id: str = Depends(get_current_customer_id),
    user = Depends(get_current_user),
):
    """Create a new workflow."""
    try:
        workflow = workflow_service.create_workflow(
            data=request.dict(),
            customer_id=customer_id,
            user_id=user.get("id"),
        )
        return workflow.to_dict()
    except ValidationError as e:
        raise HTTPException(status_code=400, detail={"message": e.message, "errors": e.details.get("errors", [])})


@router.get("/templates")
async def get_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
):
    """Get available workflow templates."""
    return {"templates": workflow_service.get_templates(category)}


@router.post("/from-template")
async def create_from_template(
    request: CreateFromTemplateRequest,
    customer_id: str = Depends(get_current_customer_id),
    user = Depends(get_current_user),
):
    """Create a workflow from a template."""
    try:
        overrides = {}
        if request.name:
            overrides["name"] = request.name
        if request.description:
            overrides["description"] = request.description
        
        workflow = workflow_service.create_from_template(
            template_id=request.template_id,
            customer_id=customer_id,
            user_id=user.get("id"),
            overrides=overrides,
        )
        return workflow.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/stats")
async def get_customer_stats(
    customer_id: str = Depends(get_current_customer_id),
):
    """Get workflow statistics for the customer."""
    return workflow_service.get_customer_stats(customer_id)


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    customer_id: str = Depends(get_current_customer_id),
):
    """Get a specific workflow."""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow or workflow.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow.to_dict()


@router.put("/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    request: UpdateWorkflowRequest,
    customer_id: str = Depends(get_current_customer_id),
):
    """Update a workflow."""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow or workflow.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    try:
        updated = workflow_service.update_workflow(
            workflow_id=workflow_id,
            data=request.dict(exclude_none=True),
        )
        return updated.to_dict()
    except ValidationError as e:
        raise HTTPException(status_code=400, detail={"message": e.message, "errors": e.details.get("errors", [])})


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    customer_id: str = Depends(get_current_customer_id),
):
    """Delete a workflow."""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow or workflow.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow_service.delete_workflow(workflow_id)
    return {"success": True, "message": "Workflow deleted"}


@router.post("/{workflow_id}/activate")
async def activate_workflow(
    workflow_id: str,
    customer_id: str = Depends(get_current_customer_id),
):
    """Activate a workflow."""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow or workflow.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    try:
        activated = workflow_service.activate_workflow(workflow_id)
        return {"success": True, "workflow": activated.to_dict()}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail={"message": e.message, "errors": e.details.get("errors", [])})


@router.post("/{workflow_id}/deactivate")
async def deactivate_workflow(
    workflow_id: str,
    customer_id: str = Depends(get_current_customer_id),
):
    """Deactivate a workflow."""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow or workflow.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    deactivated = workflow_service.deactivate_workflow(workflow_id)
    return {"success": True, "workflow": deactivated.to_dict()}


@router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    request: ExecuteWorkflowRequest,
    background_tasks: BackgroundTasks,
    customer_id: str = Depends(get_current_customer_id),
):
    """Manually execute a workflow."""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow or workflow.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Execute in background
    execution = await workflow_service.execute_workflow(
        workflow_id=workflow_id,
        input_data=request.input_data,
        trigger_data={"type": "manual", **request.trigger_data},
    )
    
    return {
        "execution_id": execution.id,
        "status": execution.status.value,
        "started_at": execution.started_at.isoformat() if execution.started_at else None,
    }


@router.get("/{workflow_id}/executions")
async def get_executions(
    workflow_id: str,
    limit: int = Query(20, ge=1, le=100),
    customer_id: str = Depends(get_current_customer_id),
):
    """Get workflow execution history."""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow or workflow.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    executions = workflow_service.get_executions(workflow_id, limit)
    return {"executions": executions}


@router.get("/{workflow_id}/executions/{execution_id}")
async def get_execution(
    workflow_id: str,
    execution_id: str,
    customer_id: str = Depends(get_current_customer_id),
):
    """Get execution details."""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow or workflow.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    execution = workflow_service.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return execution


@router.get("/{workflow_id}/stats")
async def get_workflow_stats(
    workflow_id: str,
    customer_id: str = Depends(get_current_customer_id),
):
    """Get workflow statistics."""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow or workflow.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return workflow_service.get_workflow_stats(workflow_id)


@router.post("/{workflow_id}/duplicate")
async def duplicate_workflow(
    workflow_id: str,
    customer_id: str = Depends(get_current_customer_id),
    user = Depends(get_current_user),
):
    """Duplicate a workflow."""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow or workflow.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Create copy
    data = workflow.to_dict()
    data["name"] = f"{data['name']} (Copy)"
    data.pop("id")
    data.pop("created_at")
    data.pop("updated_at")
    data.pop("run_count")
    data.pop("success_count")
    data.pop("failure_count")
    
    new_workflow = workflow_service.create_workflow(
        data=data,
        customer_id=customer_id,
        user_id=user.get("id"),
    )
    
    return new_workflow.to_dict()
```

---

## File 3: Workflow Metadata Routes
**Path:** `backend/app/routes/workflow_metadata.py`

```python
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
            {"name": "currency", "description": "Format as currency", "example": "{{amount|currency}} → $1,500.00"},
            {"name": "date", "description": "Format as date", "example": "{{created_at|date}} → Jan 15, 2024"},
            {"name": "length", "description": "Get length", "example": "{{items|length}} → 5"},
            {"name": "first", "description": "Get first item", "example": "{{items|first}}"},
            {"name": "last", "description": "Get last item", "example": "{{items|last}}"},
            {"name": "join", "description": "Join array", "example": "{{tags|join}} → tag1, tag2"},
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
```

---

## File 4: Actions Init
**Path:** `backend/app/workflows/actions/__init__.py`

```python
"""
Workflow Actions Module
Registers all available actions
"""

from app.workflows.actions.base import (
    BaseAction,
    ActionCategory,
    ActionInput,
    ActionOutput,
    action_registry,
    register_action,
)

# Import action modules to register them
from app.workflows.actions import communication
from app.workflows.actions import data
from app.workflows.actions import integration
from app.workflows.actions import flow


__all__ = [
    'BaseAction',
    'ActionCategory',
    'ActionInput',
    'ActionOutput',
    'action_registry',
    'register_action',
]


def register_default_actions(engine):
    """Register action handlers with the workflow engine."""
    for action_id, action in action_registry._actions.items():
        async def handler(config, context, action=action):
            return await action.execute(config, context)
        
        engine.register_action(action_id, handler)
    
    print(f"[Workflows] Registered {len(action_registry._actions)} actions")


def get_action(action_id: str) -> BaseAction:
    """Get action by ID."""
    return action_registry.get(action_id)


def list_actions() -> list:
    """List all registered actions."""
    return action_registry.list_all()
```

---

## Summary Part 4

| File | Description | Lines |
|------|-------------|-------|
| `workflow_service.py` | Workflow business logic | ~380 |
| `routes/workflows.py` | Workflow API routes | ~300 |
| `routes/workflow_metadata.py` | Metadata endpoints | ~150 |
| `actions/__init__.py` | Actions module init | ~50 |
| **Total** | | **~880 lines** |
