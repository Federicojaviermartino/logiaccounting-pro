# Phase 26: Advanced Workflow Engine v2 - Part 4
## Enhanced Builder & Execution Monitor

---

## Task 17: Live Execution Monitor

### 17.1 Execution Monitor Service

**File: `backend/app/workflows/services/execution_monitor.py`**

```python
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
```

---

## Task 18: Execution Monitor API Routes

**File: `backend/app/routes/workflows/executions.py`**

```python
"""
Workflow Execution Monitoring API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket
from typing import Optional
import asyncio

from app.utils.auth import get_current_user
from app.workflows.services.execution_monitor import execution_monitor
from app.workflows.models.store import workflow_store
from app.workflows.config import ExecutionStatus


router = APIRouter()


@router.get("")
async def list_executions(
    workflow_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    """List recent executions."""
    return execution_monitor.get_recent_executions(
        tenant_id=current_user.get("tenant_id"),
        workflow_id=workflow_id,
        status=status,
        limit=limit,
    )


@router.get("/active")
async def get_active_executions(
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """Get currently running executions."""
    return execution_monitor.get_active_executions(
        tenant_id=current_user.get("tenant_id"),
        limit=limit,
    )


@router.get("/dashboard")
async def get_dashboard_stats(
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(get_current_user),
):
    """Get dashboard statistics."""
    return execution_monitor.get_dashboard_stats(
        tenant_id=current_user.get("tenant_id"),
        days=days,
    )


@router.get("/{execution_id}")
async def get_execution(
    execution_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get execution details."""
    execution = workflow_store.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution_monitor.get_execution_timeline(execution_id)


@router.get("/{execution_id}/timeline")
async def get_execution_timeline(
    execution_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get execution timeline with step details."""
    timeline = execution_monitor.get_execution_timeline(execution_id)
    if not timeline:
        raise HTTPException(status_code=404, detail="Execution not found")
    return timeline


@router.post("/{execution_id}/cancel")
async def cancel_execution(
    execution_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Cancel a running execution."""
    execution = workflow_store.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if execution.status != ExecutionStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Execution is not running")
    
    execution.status = ExecutionStatus.CANCELLED
    execution.error = f"Cancelled by {current_user['id']}"
    
    return {"success": True, "status": "cancelled"}


@router.post("/{execution_id}/retry")
async def retry_execution(
    execution_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Retry a failed execution."""
    execution = workflow_store.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if execution.status not in [ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Execution cannot be retried")
    
    from app.workflows.engine.core import workflow_engine
    from app.workflows.models.execution import ExecutionContext
    
    context = ExecutionContext(
        trigger_type="retry",
        trigger_data={
            "original_execution_id": execution_id,
            **(execution.context.trigger_data if execution.context else {}),
        },
        user_id=current_user["id"],
        tenant_id=execution.tenant_id,
    )
    
    new_execution = await workflow_engine.trigger_workflow(
        workflow_id=execution.workflow_id,
        context=context,
        run_async=True,
    )
    
    return {
        "success": True,
        "new_execution_id": new_execution.id,
        "original_execution_id": execution_id,
    }


@router.get("/workflows/{workflow_id}/stats")
async def get_workflow_stats(
    workflow_id: str,
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(get_current_user),
):
    """Get workflow execution statistics."""
    return execution_monitor.get_workflow_stats(workflow_id, days)


@router.websocket("/{execution_id}/live")
async def execution_live_updates(websocket: WebSocket, execution_id: str):
    """WebSocket for live execution updates."""
    await websocket.accept()
    
    queue = await execution_monitor.subscribe(execution_id)
    
    try:
        # Send initial state
        timeline = execution_monitor.get_execution_timeline(execution_id)
        if timeline:
            await websocket.send_json({"type": "initial", "data": timeline})
        
        # Send updates
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30)
                await websocket.send_json(event)
                
                # Check if execution is complete
                if event.get("type") == "completed":
                    break
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat"})
    except Exception as e:
        pass
    finally:
        await execution_monitor.unsubscribe(execution_id, queue)
```

---

## Task 19: Live Execution Monitor UI

**File: `frontend/src/features/workflows/pages/ExecutionMonitor.jsx`**

```jsx
import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, RotateCcw, X, Clock, CheckCircle, XCircle, AlertCircle, Activity, TrendingUp } from 'lucide-react';
import { useParams } from 'react-router-dom';
import { workflowAPI } from '../../../services/api';

export default function ExecutionMonitor() {
  const { executionId } = useParams();
  const [timeline, setTimeline] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedStep, setSelectedStep] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    loadTimeline();
    connectWebSocket();
    return () => wsRef.current?.close();
  }, [executionId]);

  const loadTimeline = async () => {
    try {
      const res = await workflowAPI.getExecutionTimeline(executionId);
      setTimeline(res.data);
    } catch (error) {
      console.error('Failed to load:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const connectWebSocket = () => {
    const ws = new WebSocket(`ws://${window.location.host}/api/v1/workflows/executions/${executionId}/live`);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'step_update' || data.type === 'initial') {
        setTimeline(data.data || data);
      }
    };
    wsRef.current = ws;
  };

  const handleCancel = async () => {
    if (confirm('Cancel this execution?')) {
      await workflowAPI.cancelExecution(executionId);
      loadTimeline();
    }
  };

  const handleRetry = async () => {
    const res = await workflowAPI.retryExecution(executionId);
    window.location.href = `/workflows/executions/${res.data.new_execution_id}`;
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed': return <XCircle className="w-5 h-5 text-red-500" />;
      case 'running': return <Activity className="w-5 h-5 text-blue-500 animate-pulse" />;
      case 'pending': return <Clock className="w-5 h-5 text-gray-400" />;
      case 'skipped': return <AlertCircle className="w-5 h-5 text-gray-400" />;
      default: return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-50 border-green-200';
      case 'failed': return 'bg-red-50 border-red-200';
      case 'running': return 'bg-blue-50 border-blue-200';
      default: return 'bg-gray-50 border-gray-200';
    }
  };

  const formatDuration = (ms) => {
    if (!ms) return '-';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  if (isLoading) return <div className="p-6">Loading...</div>;
  if (!timeline) return <div className="p-6">Execution not found</div>;

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            Execution Monitor
            {getStatusIcon(timeline.status)}
          </h1>
          <p className="text-gray-500 mt-1">
            {timeline.workflow_id} • Started {new Date(timeline.started_at).toLocaleString()}
          </p>
        </div>
        <div className="flex gap-2">
          {timeline.status === 'running' && (
            <button onClick={handleCancel} className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-gray-50">
              <X className="w-4 h-4" /> Cancel
            </button>
          )}
          {['failed', 'cancelled'].includes(timeline.status) && (
            <button onClick={handleRetry} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg">
              <RotateCcw className="w-4 h-4" /> Retry
            </button>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white border rounded-xl p-4">
          <div className="text-sm text-gray-500">Status</div>
          <div className={`text-lg font-semibold capitalize ${timeline.status === 'completed' ? 'text-green-600' : timeline.status === 'failed' ? 'text-red-600' : 'text-blue-600'}`}>
            {timeline.status}
          </div>
        </div>
        <div className="bg-white border rounded-xl p-4">
          <div className="text-sm text-gray-500">Duration</div>
          <div className="text-lg font-semibold">{formatDuration(timeline.duration_ms)}</div>
        </div>
        <div className="bg-white border rounded-xl p-4">
          <div className="text-sm text-gray-500">Steps</div>
          <div className="text-lg font-semibold">
            {timeline.steps.filter(s => s.status === 'completed').length} / {timeline.steps.length}
          </div>
        </div>
        <div className="bg-white border rounded-xl p-4">
          <div className="text-sm text-gray-500">Trigger</div>
          <div className="text-lg font-semibold">{timeline.trigger_type || 'manual'}</div>
        </div>
      </div>

      {/* Timeline */}
      <div className="bg-white border rounded-xl p-6">
        <h2 className="text-lg font-semibold mb-4">Execution Timeline</h2>
        
        <div className="space-y-4">
          {timeline.steps.map((step, index) => (
            <div
              key={step.id}
              className={`border rounded-lg p-4 cursor-pointer transition ${getStatusColor(step.status)} ${selectedStep?.id === step.id ? 'ring-2 ring-blue-500' : ''}`}
              onClick={() => setSelectedStep(step)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-white border">
                    {index + 1}
                  </div>
                  {getStatusIcon(step.status)}
                  <div>
                    <div className="font-medium">{step.name || step.node_id}</div>
                    <div className="text-sm text-gray-500">
                      {step.started_at && new Date(step.started_at).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-medium">{formatDuration(step.duration_ms)}</div>
                  {step.error && (
                    <div className="text-sm text-red-600 truncate max-w-xs">{step.error}</div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Error Display */}
        {timeline.error && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <h3 className="font-semibold text-red-800 mb-2">Execution Error</h3>
            <pre className="text-sm text-red-700 whitespace-pre-wrap">{timeline.error}</pre>
          </div>
        )}
      </div>

      {/* Step Detail Modal */}
      {selectedStep && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setSelectedStep(null)}>
          <div className="bg-white rounded-xl w-full max-w-2xl max-h-[80vh] overflow-auto" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-center p-4 border-b">
              <h2 className="text-lg font-semibold">{selectedStep.name || selectedStep.node_id}</h2>
              <button onClick={() => setSelectedStep(null)}><X className="w-5 h-5" /></button>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-500">Status</label>
                <div className="flex items-center gap-2 mt-1">
                  {getStatusIcon(selectedStep.status)}
                  <span className="capitalize">{selectedStep.status}</span>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Duration</label>
                <div className="mt-1">{formatDuration(selectedStep.duration_ms)}</div>
              </div>
              {selectedStep.input && (
                <div>
                  <label className="text-sm font-medium text-gray-500">Input</label>
                  <pre className="mt-1 p-3 bg-gray-50 rounded-lg text-sm overflow-auto">
                    {JSON.stringify(selectedStep.input, null, 2)}
                  </pre>
                </div>
              )}
              {selectedStep.output && (
                <div>
                  <label className="text-sm font-medium text-gray-500">Output</label>
                  <pre className="mt-1 p-3 bg-gray-50 rounded-lg text-sm overflow-auto">
                    {JSON.stringify(selectedStep.output, null, 2)}
                  </pre>
                </div>
              )}
              {selectedStep.error && (
                <div>
                  <label className="text-sm font-medium text-gray-500">Error</label>
                  <pre className="mt-1 p-3 bg-red-50 rounded-lg text-sm text-red-700 overflow-auto">
                    {selectedStep.error}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## Task 20: Workflow Dashboard

**File: `frontend/src/features/workflows/pages/WorkflowDashboard.jsx`**

```jsx
import React, { useState, useEffect } from 'react';
import { Zap, Play, CheckCircle, XCircle, Clock, TrendingUp, Activity, Settings } from 'lucide-react';
import { Link } from 'react-router-dom';
import { workflowAPI } from '../../../services/api';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend);

export default function WorkflowDashboard() {
  const [stats, setStats] = useState(null);
  const [activeExecutions, setActiveExecutions] = useState([]);
  const [recentExecutions, setRecentExecutions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [period, setPeriod] = useState(7);

  useEffect(() => { loadData(); }, [period]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [statsRes, activeRes, recentRes] = await Promise.all([
        workflowAPI.getDashboardStats({ days: period }),
        workflowAPI.getActiveExecutions(),
        workflowAPI.listExecutions({ limit: 10 }),
      ]);
      setStats(statsRes.data);
      setActiveExecutions(activeRes.data || []);
      setRecentExecutions(recentRes.data || []);
    } catch (error) {
      console.error('Failed to load:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const statusChartData = {
    labels: ['Successful', 'Failed'],
    datasets: [{
      data: [stats?.successful_executions || 0, stats?.failed_executions || 0],
      backgroundColor: ['#10b981', '#ef4444'],
      borderWidth: 0,
    }],
  };

  if (isLoading) return <div className="p-6">Loading...</div>;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">Workflow Dashboard</h1>
          <p className="text-gray-500">Automation overview and analytics</p>
        </div>
        <div className="flex gap-2">
          <select value={period} onChange={(e) => setPeriod(Number(e.target.value))} className="px-3 py-2 border rounded-lg">
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
          <Link to="/workflows/builder" className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg">
            <Zap className="w-4 h-4" /> New Workflow
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white border rounded-xl p-5">
          <div className="flex items-center justify-between">
            <Zap className="w-8 h-8 text-blue-500" />
            <span className="text-xs text-gray-400">{period}d</span>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold">{stats?.active_workflows || 0}</div>
            <div className="text-sm text-gray-500">Active Workflows</div>
          </div>
        </div>
        <div className="bg-white border rounded-xl p-5">
          <div className="flex items-center justify-between">
            <Play className="w-8 h-8 text-green-500" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold">{stats?.total_executions || 0}</div>
            <div className="text-sm text-gray-500">Total Executions</div>
          </div>
        </div>
        <div className="bg-white border rounded-xl p-5">
          <div className="flex items-center justify-between">
            <CheckCircle className="w-8 h-8 text-emerald-500" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold">{stats?.success_rate || 0}%</div>
            <div className="text-sm text-gray-500">Success Rate</div>
          </div>
        </div>
        <div className="bg-white border rounded-xl p-5">
          <div className="flex items-center justify-between">
            <XCircle className="w-8 h-8 text-red-500" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold">{stats?.failed_executions || 0}</div>
            <div className="text-sm text-gray-500">Failed</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Left Column */}
        <div className="col-span-2 space-y-6">
          {/* Active Executions */}
          {activeExecutions.length > 0 && (
            <div className="bg-white border rounded-xl p-5">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5 text-blue-500 animate-pulse" />
                Running Now
              </h2>
              <div className="space-y-3">
                {activeExecutions.map((exec) => (
                  <Link key={exec.execution_id} to={`/workflows/executions/${exec.execution_id}`} className="flex justify-between items-center p-3 bg-blue-50 rounded-lg hover:bg-blue-100">
                    <div>
                      <div className="font-medium">{exec.workflow_name}</div>
                      <div className="text-sm text-gray-500">{exec.current_step}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-blue-600">{(exec.duration_ms / 1000).toFixed(1)}s</div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Recent Executions */}
          <div className="bg-white border rounded-xl p-5">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">Recent Executions</h2>
              <Link to="/workflows/executions" className="text-sm text-blue-600">View All</Link>
            </div>
            <div className="space-y-2">
              {recentExecutions.map((exec) => (
                <Link key={exec.execution_id} to={`/workflows/executions/${exec.execution_id}`} className="flex justify-between items-center p-3 border rounded-lg hover:bg-gray-50">
                  <div className="flex items-center gap-3">
                    {exec.status === 'completed' ? <CheckCircle className="w-5 h-5 text-green-500" /> : exec.status === 'failed' ? <XCircle className="w-5 h-5 text-red-500" /> : <Clock className="w-5 h-5 text-gray-400" />}
                    <div>
                      <div className="font-medium">{exec.workflow_name}</div>
                      <div className="text-sm text-gray-500">{new Date(exec.started_at).toLocaleString()}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-sm ${exec.status === 'completed' ? 'text-green-600' : exec.status === 'failed' ? 'text-red-600' : 'text-gray-500'}`}>
                      {exec.duration_ms ? `${(exec.duration_ms / 1000).toFixed(2)}s` : '-'}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Status Chart */}
          <div className="bg-white border rounded-xl p-5">
            <h2 className="text-lg font-semibold mb-4">Execution Status</h2>
            <div className="h-48">
              <Doughnut data={statusChartData} options={{ maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }} />
            </div>
          </div>

          {/* Top Workflows */}
          <div className="bg-white border rounded-xl p-5">
            <h2 className="text-lg font-semibold mb-4">Top Workflows</h2>
            <div className="space-y-3">
              {stats?.top_workflows?.map((wf, i) => (
                <div key={wf.workflow_id} className="flex justify-between items-center">
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-gray-400">#{i + 1}</span>
                    <span className="font-medium truncate max-w-[150px]">{wf.name}</span>
                  </div>
                  <span className="text-sm text-gray-500">{wf.count} runs</span>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Links */}
          <div className="bg-white border rounded-xl p-5">
            <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
            <div className="space-y-2">
              <Link to="/workflows/builder" className="flex items-center gap-3 p-3 border rounded-lg hover:bg-gray-50">
                <Zap className="w-5 h-5 text-blue-500" />
                <span>Create Workflow</span>
              </Link>
              <Link to="/workflows/templates" className="flex items-center gap-3 p-3 border rounded-lg hover:bg-gray-50">
                <TrendingUp className="w-5 h-5 text-green-500" />
                <span>Browse Templates</span>
              </Link>
              <Link to="/workflows/dead-letter" className="flex items-center gap-3 p-3 border rounded-lg hover:bg-gray-50">
                <XCircle className="w-5 h-5 text-red-500" />
                <span>Dead Letter Queue</span>
              </Link>
              <Link to="/workflows/settings" className="flex items-center gap-3 p-3 border rounded-lg hover:bg-gray-50">
                <Settings className="w-5 h-5 text-gray-500" />
                <span>Settings</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## Task 21: Workflow Routes Configuration

**File: `frontend/src/features/workflows/routes.jsx`**

```jsx
import React from 'react';
import { Routes, Route } from 'react-router-dom';

import WorkflowDashboard from './pages/WorkflowDashboard';
import WorkflowBuilder from './pages/WorkflowBuilder';
import WorkflowList from './pages/WorkflowList';
import ExecutionMonitor from './pages/ExecutionMonitor';
import ExecutionList from './pages/ExecutionList';
import TemplateMarketplace from './pages/TemplateMarketplace';
import DeadLetterQueue from './pages/DeadLetterQueue';
import WorkflowSettings from './pages/WorkflowSettings';

export default function WorkflowRoutes() {
  return (
    <Routes>
      <Route index element={<WorkflowDashboard />} />
      <Route path="dashboard" element={<WorkflowDashboard />} />
      <Route path="builder" element={<WorkflowBuilder />} />
      <Route path="builder/:workflowId" element={<WorkflowBuilder />} />
      <Route path="list" element={<WorkflowList />} />
      <Route path="executions" element={<ExecutionList />} />
      <Route path="executions/:executionId" element={<ExecutionMonitor />} />
      <Route path="templates" element={<TemplateMarketplace />} />
      <Route path="dead-letter" element={<DeadLetterQueue />} />
      <Route path="settings" element={<WorkflowSettings />} />
    </Routes>
  );
}
```

---

## Task 22: Workflow API Service Updates

**File: `frontend/src/services/api/workflows.js`**

```javascript
/**
 * Workflow API Service
 */

import axios from 'axios';

const API_BASE = '/api/v1/workflows';

export const workflowAPI = {
  // Workflows
  listWorkflows: (params = {}) => axios.get(`${API_BASE}`, { params }),
  getWorkflow: (id) => axios.get(`${API_BASE}/${id}`),
  createWorkflow: (data) => axios.post(`${API_BASE}`, data),
  updateWorkflow: (id, data) => axios.put(`${API_BASE}/${id}`, data),
  deleteWorkflow: (id) => axios.delete(`${API_BASE}/${id}`),
  activateWorkflow: (id) => axios.post(`${API_BASE}/${id}/activate`),
  deactivateWorkflow: (id) => axios.post(`${API_BASE}/${id}/deactivate`),
  triggerWorkflow: (id, data = {}) => axios.post(`${API_BASE}/${id}/trigger`, data),

  // Executions
  listExecutions: (params = {}) => axios.get(`${API_BASE}/executions`, { params }),
  getActiveExecutions: (params = {}) => axios.get(`${API_BASE}/executions/active`, { params }),
  getExecution: (id) => axios.get(`${API_BASE}/executions/${id}`),
  getExecutionTimeline: (id) => axios.get(`${API_BASE}/executions/${id}/timeline`),
  cancelExecution: (id) => axios.post(`${API_BASE}/executions/${id}/cancel`),
  retryExecution: (id) => axios.post(`${API_BASE}/executions/${id}/retry`),
  getDashboardStats: (params = {}) => axios.get(`${API_BASE}/executions/dashboard`, { params }),
  getWorkflowStats: (id, params = {}) => axios.get(`${API_BASE}/executions/workflows/${id}/stats`, { params }),

  // Versions
  listVersions: (id, params = {}) => axios.get(`${API_BASE}/${id}/versions`, { params }),
  getVersion: (id, version) => axios.get(`${API_BASE}/${id}/versions/${version}`),
  createVersion: (id, data = {}) => axios.post(`${API_BASE}/${id}/versions`, data),
  rollbackVersion: (id, version) => axios.post(`${API_BASE}/${id}/versions/${version}/rollback`),
  compareVersions: (id, params) => axios.get(`${API_BASE}/${id}/versions/compare`, { params }),

  // Dead Letter Queue
  listDeadLetter: (params = {}) => axios.get(`${API_BASE}/dead-letter`, { params }),
  getDeadLetterStats: (params = {}) => axios.get(`${API_BASE}/dead-letter/stats`, { params }),
  getDeadLetterEntry: (id) => axios.get(`${API_BASE}/dead-letter/${id}`),
  retryDeadLetter: (id) => axios.post(`${API_BASE}/dead-letter/${id}/retry`),
  resolveDeadLetter: (id, data = {}) => axios.post(`${API_BASE}/dead-letter/${id}/resolve`, data),
  ignoreDeadLetter: (id, data = {}) => axios.post(`${API_BASE}/dead-letter/${id}/ignore`, data),

  // Templates
  listTemplates: (params = {}) => axios.get(`${API_BASE}/templates`, { params }),
  getTemplateCategories: () => axios.get(`${API_BASE}/templates/categories`),
  getTemplate: (id) => axios.get(`${API_BASE}/templates/${id}`),
  previewTemplate: (id) => axios.get(`${API_BASE}/templates/${id}/preview`),
  installTemplate: (id, data = {}) => axios.post(`${API_BASE}/templates/${id}/install`, data),
  publishTemplate: (data) => axios.post(`${API_BASE}/templates/publish`, data),
  rateTemplate: (id, data) => axios.post(`${API_BASE}/templates/${id}/rate`, data),

  // AI
  getSuggestions: () => axios.get(`${API_BASE}/templates/suggestions`),
  fromDescription: (data) => axios.post(`${API_BASE}/templates/from-description`, data),
  explainWorkflow: (data) => axios.post(`${API_BASE}/templates/explain`, data),

  // CRM Workflows
  getCRMEvents: () => axios.get(`${API_BASE}/crm/events`),
  getCRMActions: () => axios.get(`${API_BASE}/crm/actions`),
  getCRMConditionTemplates: (params = {}) => axios.get(`${API_BASE}/crm/conditions/templates`, { params }),
  getCRMWorkflowTemplates: () => axios.get(`${API_BASE}/crm/templates`),
  getThresholdMetrics: () => axios.get(`${API_BASE}/thresholds/metrics`),
};
```

---

## Summary: Part 4 Complete

### Files Created:

| File | Purpose | Lines |
|------|---------|-------|
| `execution_monitor.py` | Execution monitoring service | ~200 |
| `executions.py` | Execution API routes | ~120 |
| `ExecutionMonitor.jsx` | Live execution monitor UI | ~180 |
| `WorkflowDashboard.jsx` | Main dashboard | ~200 |
| `routes.jsx` | Workflow routes config | ~30 |
| `workflows.js` | API service | ~70 |
| **Total** | | **~800** |

### Features:

| Feature | Status |
|---------|--------|
| Execution timeline | ✅ |
| Live WebSocket updates | ✅ |
| Step-by-step details | ✅ |
| Cancel execution | ✅ |
| Retry execution | ✅ |
| Workflow statistics | ✅ |
| Active executions | ✅ |
| Dashboard analytics | ✅ |
| Success rate chart | ✅ |
| Top workflows | ✅ |
| Quick actions | ✅ |

---

## Phase 26 Complete Summary

### Total Files: 18 files, ~4,430 lines

| Part | Files | Lines | Focus |
|------|-------|-------|-------|
| Part 1 | 5 | ~1,100 | CRM Integration |
| Part 2 | 6 | ~1,090 | Sub-Workflows & Errors |
| Part 3 | 5 | ~650 | AI & Templates |
| Part 4 | 6 | ~800 | Monitoring & Dashboard |

### Feature Summary (114 features)

| Category | Implemented |
|----------|-------------|
| CRM Triggers | ✅ 6 event types |
| CRM Actions | ✅ 9 action types |
| Threshold Triggers | ✅ 6 metrics |
| Sub-Workflows | ✅ With recursion prevention |
| Error Handling | ✅ Try-catch, retry, fallback |
| Versioning | ✅ With rollback |
| Dead Letter Queue | ✅ With retry/resolve |
| AI Suggestions | ✅ With NL conversion |
| AI Actions | ✅ 5 action types |
| Template Marketplace | ✅ 6 built-in templates |
| Execution Monitor | ✅ Live WebSocket |
| Dashboard | ✅ With analytics |

### Competitive Position

| vs Competitor | Advantage |
|--------------|-----------|
| vs Zapier | Native CRM/accounting integration, no per-task pricing |
| vs Power Automate | Simpler, integrated AI, no user limits |
| vs n8n | AI-powered, template marketplace, better CRM |

**Phase 26: COMPLETE** 🎉
