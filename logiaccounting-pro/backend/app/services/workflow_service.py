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
