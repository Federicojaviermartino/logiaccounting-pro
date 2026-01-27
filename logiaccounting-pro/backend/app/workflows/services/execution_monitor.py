"""
Real-time Execution Monitoring Service
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import asyncio

from app.workflows.models.store import workflow_store
from app.workflows.config import ExecutionStatus, StepStatus


logger = logging.getLogger(__name__)


class ExecutionMonitor:
    """Real-time monitoring of workflow executions."""

    def __init__(self):
        self._listeners: Dict[str, List[asyncio.Queue]] = defaultdict(list)
        self._stats_cache: Dict[str, Dict] = {}
        self._cache_ttl = 60  # seconds

    async def subscribe(self, execution_id: str) -> asyncio.Queue:
        """Subscribe to execution updates."""
        queue = asyncio.Queue()
        self._listeners[execution_id].append(queue)
        return queue

    async def unsubscribe(self, execution_id: str, queue: asyncio.Queue):
        """Unsubscribe from execution updates."""
        if execution_id in self._listeners:
            self._listeners[execution_id].remove(queue)
            if not self._listeners[execution_id]:
                del self._listeners[execution_id]

    async def notify(self, execution_id: str, event: Dict[str, Any]):
        """Notify subscribers of execution update."""
        if execution_id in self._listeners:
            for queue in self._listeners[execution_id]:
                await queue.put(event)

    def get_execution_timeline(self, execution_id: str) -> Dict[str, Any]:
        """Get execution timeline with step details."""
        execution = workflow_store.get_execution(execution_id)
        if not execution:
            return None

        steps = []
        for step in execution.steps:
            steps.append({
                "id": step.id,
                "node_id": step.node_id,
                "name": step.name,
                "status": step.status.value,
                "started_at": step.started_at.isoformat() if step.started_at else None,
                "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                "duration_ms": step.duration_ms,
                "input": step.input_data,
                "output": step.output_data,
                "error": step.error,
            })

        return {
            "execution_id": execution.id,
            "workflow_id": execution.workflow_id,
            "status": execution.status.value,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "duration_ms": execution.duration_ms,
            "trigger_type": execution.context.trigger_type if execution.context else None,
            "steps": steps,
            "current_step": next((s["id"] for s in steps if s["status"] == "running"), None),
            "error": execution.error,
        }

    def get_workflow_stats(self, workflow_id: str, days: int = 7) -> Dict[str, Any]:
        """Get workflow execution statistics."""
        cache_key = f"{workflow_id}:{days}"

        # Check cache
        if cache_key in self._stats_cache:
            cached = self._stats_cache[cache_key]
            if (datetime.utcnow() - cached["_cached_at"]).seconds < self._cache_ttl:
                return cached

        cutoff = datetime.utcnow() - timedelta(days=days)
        executions = workflow_store.list_executions(workflow_id=workflow_id)
        recent = [e for e in executions if e.started_at and e.started_at >= cutoff]

        total = len(recent)
        completed = len([e for e in recent if e.status == ExecutionStatus.COMPLETED])
        failed = len([e for e in recent if e.status == ExecutionStatus.FAILED])
        running = len([e for e in recent if e.status == ExecutionStatus.RUNNING])

        durations = [e.duration_ms for e in recent if e.duration_ms]
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Executions by day
        by_day = defaultdict(int)
        for e in recent:
            if e.started_at:
                day = e.started_at.strftime("%Y-%m-%d")
                by_day[day] += 1

        # Error breakdown
        errors = defaultdict(int)
        for e in recent:
            if e.status == ExecutionStatus.FAILED and e.error:
                error_type = e.error.split(":")[0] if ":" in e.error else "Unknown"
                errors[error_type] += 1

        stats = {
            "period_days": days,
            "total_executions": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "success_rate": round(completed / total * 100, 1) if total > 0 else 0,
            "avg_duration_ms": round(avg_duration, 0),
            "by_day": dict(by_day),
            "errors": dict(errors),
            "_cached_at": datetime.utcnow(),
        }

        self._stats_cache[cache_key] = stats
        return stats

    def get_active_executions(self, tenant_id: str = None, limit: int = 20) -> List[Dict]:
        """Get currently active executions."""
        executions = workflow_store.list_executions(status=ExecutionStatus.RUNNING, limit=limit)

        if tenant_id:
            executions = [e for e in executions if e.tenant_id == tenant_id]

        return [
            {
                "execution_id": e.id,
                "workflow_id": e.workflow_id,
                "workflow_name": workflow_store.get_workflow(e.workflow_id).name if workflow_store.get_workflow(e.workflow_id) else "Unknown",
                "started_at": e.started_at.isoformat() if e.started_at else None,
                "current_step": e.steps[-1].name if e.steps else None,
                "duration_ms": (datetime.utcnow() - e.started_at).total_seconds() * 1000 if e.started_at else 0,
            }
            for e in executions
        ]

    def get_recent_executions(self, tenant_id: str = None, workflow_id: str = None, status: str = None, limit: int = 50) -> List[Dict]:
        """Get recent executions with filters."""
        status_enum = ExecutionStatus(status) if status else None
        executions = workflow_store.list_executions(workflow_id=workflow_id, status=status_enum, limit=limit)

        if tenant_id:
            executions = [e for e in executions if e.tenant_id == tenant_id]

        return [
            {
                "execution_id": e.id,
                "workflow_id": e.workflow_id,
                "workflow_name": workflow_store.get_workflow(e.workflow_id).name if workflow_store.get_workflow(e.workflow_id) else "Unknown",
                "status": e.status.value,
                "started_at": e.started_at.isoformat() if e.started_at else None,
                "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                "duration_ms": e.duration_ms,
                "trigger_type": e.context.trigger_type if e.context else None,
                "error": e.error[:100] if e.error else None,
            }
            for e in executions
        ]

    def get_dashboard_stats(self, tenant_id: str, days: int = 7) -> Dict[str, Any]:
        """Get dashboard statistics."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        workflows = workflow_store.list_workflows(tenant_id=tenant_id)
        executions = workflow_store.list_executions(limit=10000)
        recent = [e for e in executions if e.tenant_id == tenant_id and e.started_at and e.started_at >= cutoff]

        total_workflows = len(workflows)
        active_workflows = len([w for w in workflows if w.status.value == "active"])

        total_executions = len(recent)
        successful = len([e for e in recent if e.status == ExecutionStatus.COMPLETED])
        failed = len([e for e in recent if e.status == ExecutionStatus.FAILED])

        # Top workflows by execution
        workflow_counts = defaultdict(int)
        for e in recent:
            workflow_counts[e.workflow_id] += 1

        top_workflows = sorted(workflow_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "period_days": days,
            "total_workflows": total_workflows,
            "active_workflows": active_workflows,
            "total_executions": total_executions,
            "successful_executions": successful,
            "failed_executions": failed,
            "success_rate": round(successful / total_executions * 100, 1) if total_executions > 0 else 0,
            "top_workflows": [
                {
                    "workflow_id": wid,
                    "name": workflow_store.get_workflow(wid).name if workflow_store.get_workflow(wid) else "Unknown",
                    "count": count,
                }
                for wid, count in top_workflows
            ],
        }


execution_monitor = ExecutionMonitor()
