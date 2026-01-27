"""
In-memory workflow storage.
For production, replace with PostgreSQL/Redis.
"""
from typing import Dict, List, Optional
from datetime import datetime
from copy import deepcopy

from app.workflows.models.workflow import Workflow, WorkflowVersion
from app.workflows.models.execution import WorkflowExecution, ExecutionLog
from app.workflows.models.rule import BusinessRule
from app.workflows.config import WorkflowStatus, ExecutionStatus


class WorkflowStore:
    """In-memory workflow storage."""

    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.versions: Dict[str, List[WorkflowVersion]] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.execution_logs: Dict[str, List[ExecutionLog]] = {}
        self.rules: Dict[str, BusinessRule] = {}

    def save_workflow(self, workflow: Workflow) -> Workflow:
        """Save a workflow."""
        self.workflows[workflow.id] = workflow
        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID."""
        return self.workflows.get(workflow_id)

    def get_workflows_by_tenant(
        self,
        tenant_id: str,
        status: Optional[WorkflowStatus] = None,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Workflow]:
        """Get workflows for a tenant."""
        workflows = [
            w for w in self.workflows.values()
            if w.tenant_id == tenant_id
        ]

        if status:
            workflows = [w for w in workflows if w.status == status]

        if category:
            workflows = [w for w in workflows if w.metadata.category == category]

        workflows.sort(key=lambda w: w.metadata.created_at, reverse=True)
        return workflows[skip:skip + limit]

    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            return True
        return False

    def get_active_workflows_by_trigger(
        self,
        trigger_type: str,
        entity: Optional[str] = None,
        event: Optional[str] = None
    ) -> List[Workflow]:
        """Get active workflows matching trigger criteria."""
        workflows = []

        for w in self.workflows.values():
            if w.status != WorkflowStatus.ACTIVE:
                continue

            if w.trigger.type.value != trigger_type:
                continue

            if entity and w.trigger.entity != entity:
                continue

            if event and w.trigger.event != event:
                continue

            workflows.append(w)

        return workflows

    def save_version(self, version: WorkflowVersion) -> WorkflowVersion:
        """Save a workflow version."""
        if version.workflow_id not in self.versions:
            self.versions[version.workflow_id] = []
        self.versions[version.workflow_id].append(version)
        return version

    def get_versions(self, workflow_id: str) -> List[WorkflowVersion]:
        """Get all versions of a workflow."""
        return self.versions.get(workflow_id, [])

    def get_version(
        self,
        workflow_id: str,
        version: int
    ) -> Optional[WorkflowVersion]:
        """Get a specific version."""
        versions = self.versions.get(workflow_id, [])
        for v in versions:
            if v.version == version:
                return v
        return None

    def save_execution(self, execution: WorkflowExecution) -> WorkflowExecution:
        """Save an execution."""
        self.executions[execution.id] = execution
        return execution

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get an execution by ID."""
        return self.executions.get(execution_id)

    def get_executions_by_workflow(
        self,
        workflow_id: str,
        status: Optional[ExecutionStatus] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[WorkflowExecution]:
        """Get executions for a workflow."""
        executions = [
            e for e in self.executions.values()
            if e.workflow_id == workflow_id
        ]

        if status:
            executions = [e for e in executions if e.status == status]

        executions.sort(key=lambda e: e.started_at, reverse=True)
        return executions[skip:skip + limit]

    def get_executions_by_tenant(
        self,
        tenant_id: str,
        status: Optional[ExecutionStatus] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[WorkflowExecution]:
        """Get executions for a tenant."""
        executions = [
            e for e in self.executions.values()
            if e.tenant_id == tenant_id
        ]

        if status:
            executions = [e for e in executions if e.status == status]

        executions.sort(key=lambda e: e.started_at, reverse=True)
        return executions[skip:skip + limit]

    def get_waiting_executions(self) -> List[WorkflowExecution]:
        """Get executions waiting for resume."""
        now = datetime.utcnow()
        return [
            e for e in self.executions.values()
            if e.status == ExecutionStatus.WAITING
            and e.resume_at
            and e.resume_at <= now
        ]

    def add_log(self, log: ExecutionLog) -> ExecutionLog:
        """Add an execution log entry."""
        if log.execution_id not in self.execution_logs:
            self.execution_logs[log.execution_id] = []
        self.execution_logs[log.execution_id].append(log)
        return log

    def get_logs(self, execution_id: str) -> List[ExecutionLog]:
        """Get logs for an execution."""
        return self.execution_logs.get(execution_id, [])

    def save_rule(self, rule: BusinessRule) -> BusinessRule:
        """Save a business rule."""
        self.rules[rule.id] = rule
        return rule

    def get_rule(self, rule_id: str) -> Optional[BusinessRule]:
        """Get a rule by ID."""
        return self.rules.get(rule_id)

    def get_rules_by_tenant(
        self,
        tenant_id: str,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[BusinessRule]:
        """Get rules for a tenant."""
        rules = [
            r for r in self.rules.values()
            if r.tenant_id == tenant_id
        ]

        if status:
            rules = [r for r in rules if r.status == status]

        rules.sort(key=lambda r: r.priority, reverse=True)
        return rules[skip:skip + limit]

    def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False

    def get_active_rules_by_trigger(
        self,
        trigger_type: str,
        entity: Optional[str] = None
    ) -> List[BusinessRule]:
        """Get active rules matching trigger criteria."""
        rules = []

        for r in self.rules.values():
            if r.status != "active":
                continue

            if r.trigger.type.value != trigger_type:
                continue

            if entity and r.scope.entity != entity:
                continue

            rules.append(r)

        rules.sort(key=lambda r: r.priority, reverse=True)
        return rules


workflow_store = WorkflowStore()


def init_workflow_database():
    """Initialize workflow database."""
    pass
