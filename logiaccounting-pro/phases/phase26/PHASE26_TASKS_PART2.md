# Phase 26: Advanced Workflow Engine v2 - Part 2
## Sub-Workflows & Error Handling

---

## Task 6: Sub-Workflow Node

### 6.1 Sub-Workflow Executor

**File: `backend/app/workflows/actions/subworkflow_action.py`**

```python
"""
Sub-Workflow Action Executor
Allows workflows to call other workflows as reusable components
"""

from typing import Dict, Any, Optional, Set
from datetime import datetime
import asyncio
import logging

from app.workflows.actions.base import ActionExecutor, ActionResult
from app.workflows.models.store import workflow_store
from app.workflows.config import WorkflowStatus, ExecutionStatus


logger = logging.getLogger(__name__)

_active_call_stacks: Dict[str, Set[str]] = {}


class SubWorkflowAction(ActionExecutor):
    """Execute another workflow as a sub-workflow."""
    
    action_type = "subworkflow"
    MAX_DEPTH = 10
    
    async def execute(self, config: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            workflow_id = config.get("workflow_id")
            parameters = config.get("parameters", {})
            wait_for_completion = config.get("wait_for_completion", True)
            timeout_seconds = config.get("timeout_seconds", 300)
            
            if not workflow_id:
                return ActionResult(success=False, error="workflow_id is required")
            
            parent_execution_id = context.get("execution_id")
            current_depth = context.get("subworkflow_depth", 0)
            
            if current_depth >= self.MAX_DEPTH:
                return ActionResult(success=False, error=f"Max depth ({self.MAX_DEPTH}) exceeded")
            
            if self._detect_circular(parent_execution_id, workflow_id):
                return ActionResult(success=False, error="Circular reference detected")
            
            sub_workflow = workflow_store.get_workflow(workflow_id)
            if not sub_workflow or sub_workflow.status != WorkflowStatus.ACTIVE:
                return ActionResult(success=False, error=f"Workflow not found or inactive")
            
            interpolated_params = {
                k: self.interpolate(v, context) if isinstance(v, str) else v
                for k, v in parameters.items()
            }
            
            from app.workflows.models.execution import ExecutionContext
            sub_context = ExecutionContext(
                trigger_type="subworkflow",
                trigger_data={"parent_execution_id": parent_execution_id, "parameters": interpolated_params},
                user_id=context.get("user_id"),
                tenant_id=context.get("tenant_id"),
                variables={**context.get("variables", {}), **interpolated_params},
            )
            
            self._add_to_stack(parent_execution_id, workflow_id)
            
            try:
                from app.workflows.engine.core import workflow_engine
                execution = await workflow_engine.trigger_workflow(
                    workflow_id=workflow_id,
                    context=sub_context,
                    run_async=not wait_for_completion,
                    subworkflow_depth=current_depth + 1,
                )
                
                if wait_for_completion:
                    result = await self._wait_completion(execution.id, timeout_seconds)
                    success = result["status"] == ExecutionStatus.COMPLETED
                    return ActionResult(
                        success=success,
                        data={"execution_id": execution.id, "output": result.get("output", {})},
                        error=result.get("error") if not success else None,
                    )
                return ActionResult(success=True, data={"execution_id": execution.id, "status": "started"})
            finally:
                self._remove_from_stack(parent_execution_id, workflow_id)
                
        except asyncio.TimeoutError:
            return ActionResult(success=False, error="Sub-workflow timed out")
        except Exception as e:
            logger.error(f"Sub-workflow failed: {e}")
            return ActionResult(success=False, error=str(e))
    
    def _detect_circular(self, exec_id: str, wf_id: str) -> bool:
        return exec_id and wf_id in _active_call_stacks.get(exec_id, set())
    
    def _add_to_stack(self, exec_id: str, wf_id: str):
        if exec_id:
            _active_call_stacks.setdefault(exec_id, set()).add(wf_id)
    
    def _remove_from_stack(self, exec_id: str, wf_id: str):
        if exec_id and exec_id in _active_call_stacks:
            _active_call_stacks[exec_id].discard(wf_id)
    
    async def _wait_completion(self, exec_id: str, timeout: int) -> Dict:
        start = datetime.utcnow()
        while True:
            execution = workflow_store.get_execution(exec_id)
            if not execution:
                return {"status": ExecutionStatus.FAILED, "error": "Not found"}
            if execution.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
                return {"status": execution.status, "output": execution.output, "error": execution.error}
            if (datetime.utcnow() - start).total_seconds() >= timeout:
                raise asyncio.TimeoutError()
            await asyncio.sleep(0.5)
```

---

## Task 7: Error Handling Actions

### 7.1 Try-Catch and Retry

**File: `backend/app/workflows/actions/error_handler.py`**

```python
"""
Error Handling Actions - Try-Catch, Retry, Fallback, Circuit Breaker
"""

from typing import Dict, Any, List
from datetime import datetime
import asyncio
import logging

from app.workflows.actions.base import ActionExecutor, ActionResult


logger = logging.getLogger(__name__)


class TryCatchAction(ActionExecutor):
    """Try-Catch block for error handling."""
    
    action_type = "try_catch"
    
    async def execute(self, config: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            try_steps = config.get("try_steps", [])
            catch_steps = config.get("catch_steps", [])
            finally_steps = config.get("finally_steps", [])
            rethrow = config.get("rethrow", False)
            
            if not try_steps:
                return ActionResult(success=False, error="try_steps required")
            
            from app.workflows.engine.executor import WorkflowExecutor
            executor = WorkflowExecutor()
            
            error_context = None
            try_success = True
            
            try:
                for step in try_steps:
                    result = await executor.execute_step(step, context)
                    if not result.success:
                        try_success = False
                        error_context = {"error": result.error, "step": step.get("name", step.get("type"))}
                        break
            except Exception as e:
                try_success = False
                error_context = {"error": str(e), "type": type(e).__name__}
            
            if not try_success and catch_steps:
                context["error"] = error_context
                for step in catch_steps:
                    await executor.execute_step(step, context)
            
            if finally_steps:
                for step in finally_steps:
                    await executor.execute_step(step, context)
            
            if try_success:
                return ActionResult(success=True, message="Try block completed")
            elif catch_steps and not rethrow:
                return ActionResult(success=True, data={"recovered": True, "error_context": error_context})
            else:
                return ActionResult(success=False, error=error_context.get("error"))
                
        except Exception as e:
            return ActionResult(success=False, error=str(e))


class RetryAction(ActionExecutor):
    """Retry action with configurable policy."""
    
    action_type = "retry"
    
    async def execute(self, config: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            action_config = config.get("action")
            max_retries = config.get("max_retries", 3)
            strategy = config.get("strategy", "exponential")
            initial_delay = config.get("initial_delay_seconds", 1)
            max_delay = config.get("max_delay_seconds", 60)
            
            if not action_config:
                return ActionResult(success=False, error="action required")
            
            from app.workflows.engine.executor import WorkflowExecutor
            executor = WorkflowExecutor()
            
            attempts = []
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    result = await executor.execute_step(action_config, context)
                    attempts.append({"attempt": attempt + 1, "success": result.success})
                    
                    if result.success:
                        return ActionResult(success=True, data={"attempts": len(attempts), **result.data})
                    last_error = result.error
                except Exception as e:
                    last_error = str(e)
                    attempts.append({"attempt": attempt + 1, "success": False, "error": last_error})
                
                if attempt < max_retries:
                    delay = self._calc_delay(attempt, strategy, initial_delay, max_delay)
                    await asyncio.sleep(delay)
            
            return ActionResult(success=False, error=f"Failed after {len(attempts)} attempts: {last_error}", data={"attempts": attempts})
            
        except Exception as e:
            return ActionResult(success=False, error=str(e))
    
    def _calc_delay(self, attempt: int, strategy: str, base: float, max_d: float) -> float:
        if strategy == "fixed":
            return min(base, max_d)
        elif strategy == "exponential":
            return min(base * (2 ** attempt), max_d)
        elif strategy == "linear":
            return min(base * (attempt + 1), max_d)
        return base


class FallbackAction(ActionExecutor):
    """Execute fallback if primary fails."""
    
    action_type = "fallback"
    
    async def execute(self, config: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            primary = config.get("primary")
            fallbacks = config.get("fallbacks", [])
            
            if not primary:
                return ActionResult(success=False, error="primary action required")
            
            from app.workflows.engine.executor import WorkflowExecutor
            executor = WorkflowExecutor()
            
            result = await executor.execute_step(primary, context)
            if result.success:
                return ActionResult(success=True, data={**result.data, "used_fallback": False})
            
            primary_error = result.error
            
            for i, fallback in enumerate(fallbacks):
                result = await executor.execute_step(fallback, context)
                if result.success:
                    return ActionResult(success=True, data={**result.data, "used_fallback": True, "fallback_index": i})
            
            return ActionResult(success=False, error=f"All actions failed. Primary: {primary_error}")
            
        except Exception as e:
            return ActionResult(success=False, error=str(e))


class CircuitBreakerAction(ActionExecutor):
    """Circuit breaker pattern."""
    
    action_type = "circuit_breaker"
    _circuits: Dict[str, Dict] = {}
    
    async def execute(self, config: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            circuit_id = config.get("circuit_id", "default")
            action_config = config.get("action")
            failure_threshold = config.get("failure_threshold", 5)
            reset_timeout = config.get("reset_timeout_seconds", 60)
            
            if not action_config:
                return ActionResult(success=False, error="action required")
            
            circuit = self._circuits.setdefault(circuit_id, {
                "state": "closed", "failures": 0, "last_failure": 0
            })
            
            if circuit["state"] == "open":
                if datetime.utcnow().timestamp() - circuit["last_failure"] > reset_timeout:
                    circuit["state"] = "half_open"
                else:
                    return ActionResult(success=False, error="Circuit breaker open", data={"circuit_state": "open"})
            
            from app.workflows.engine.executor import WorkflowExecutor
            result = await WorkflowExecutor().execute_step(action_config, context)
            
            if result.success:
                if circuit["state"] == "half_open":
                    circuit["state"] = "closed"
                circuit["failures"] = 0
                return ActionResult(success=True, data={**result.data, "circuit_state": circuit["state"]})
            
            circuit["failures"] += 1
            circuit["last_failure"] = datetime.utcnow().timestamp()
            if circuit["failures"] >= failure_threshold:
                circuit["state"] = "open"
            
            return ActionResult(success=False, error=result.error, data={"circuit_state": circuit["state"]})
            
        except Exception as e:
            return ActionResult(success=False, error=str(e))
```

---

## Task 8: Workflow Versioning

### 8.1 Version Service

**File: `backend/app/workflows/services/version_service.py`**

```python
"""
Workflow Version Control Service
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import uuid4
import logging

from app.workflows.models.workflow import Workflow
from app.workflows.models.store import workflow_store


logger = logging.getLogger(__name__)


class WorkflowVersionService:
    """Manages workflow versions with rollback capability."""
    
    def __init__(self):
        self._versions: Dict[str, List[Dict]] = {}
        self._max_versions = 50
    
    def save_version(self, workflow: Workflow, user_id: str, comment: str = None) -> Dict:
        """Save a new version snapshot."""
        wf_id = workflow.id
        versions = self._versions.setdefault(wf_id, [])
        version_number = len(versions) + 1
        
        version = {
            "id": str(uuid4()),
            "workflow_id": wf_id,
            "version": version_number,
            "snapshot": self._create_snapshot(workflow),
            "created_at": datetime.utcnow().isoformat(),
            "created_by": user_id,
            "comment": comment,
            "node_count": len(workflow.nodes),
        }
        
        versions.append(version)
        if len(versions) > self._max_versions:
            versions.pop(0)
        
        logger.info(f"Saved version {version_number} for workflow {wf_id}")
        return {"version": version_number, "id": version["id"]}
    
    def _create_snapshot(self, workflow: Workflow) -> Dict:
        return {
            "name": workflow.name,
            "description": workflow.description,
            "status": workflow.status.value if hasattr(workflow.status, 'value') else workflow.status,
            "trigger": workflow.trigger.dict() if hasattr(workflow.trigger, 'dict') else workflow.trigger,
            "nodes": [n.dict() if hasattr(n, 'dict') else n for n in workflow.nodes],
            "edges": workflow.edges,
            "settings": workflow.settings,
        }
    
    def list_versions(self, workflow_id: str, limit: int = 20) -> List[Dict]:
        versions = self._versions.get(workflow_id, [])
        return [
            {"id": v["id"], "version": v["version"], "created_at": v["created_at"], 
             "created_by": v["created_by"], "comment": v["comment"], "node_count": v["node_count"]}
            for v in reversed(versions[-limit:])
        ]
    
    def get_version(self, workflow_id: str, version: int = None, version_id: str = None) -> Optional[Dict]:
        versions = self._versions.get(workflow_id, [])
        for v in versions:
            if (version_id and v["id"] == version_id) or (version and v["version"] == version):
                return v
        return None
    
    def compare_versions(self, workflow_id: str, version_a: int, version_b: int) -> Dict:
        v_a = self.get_version(workflow_id, version=version_a)
        v_b = self.get_version(workflow_id, version=version_b)
        if not v_a or not v_b:
            return {"error": "Version not found"}
        
        snap_a, snap_b = v_a["snapshot"], v_b["snapshot"]
        nodes_a = {n.get("id"): n for n in snap_a.get("nodes", [])}
        nodes_b = {n.get("id"): n for n in snap_b.get("nodes", [])}
        
        return {
            "version_a": version_a, "version_b": version_b,
            "nodes_added": len(set(nodes_b) - set(nodes_a)),
            "nodes_removed": len(set(nodes_a) - set(nodes_b)),
            "nodes_modified": len([nid for nid in set(nodes_a) & set(nodes_b) if nodes_a[nid] != nodes_b[nid]]),
        }
    
    def rollback(self, workflow_id: str, version: int, user_id: str) -> Dict:
        target = self.get_version(workflow_id, version=version)
        if not target:
            raise ValueError(f"Version {version} not found")
        
        workflow = workflow_store.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found")
        
        snapshot = target["snapshot"]
        updates = {
            "name": snapshot["name"],
            "description": snapshot["description"],
            "nodes": snapshot["nodes"],
            "edges": snapshot.get("edges", []),
        }
        
        updated = workflow_store.update_workflow(workflow_id, updates)
        new_ver = self.save_version(updated, user_id, f"Rollback to v{version}")
        
        return {"success": True, "rolled_back_to": version, "new_version": new_ver["version"]}


version_service = WorkflowVersionService()
```

---

## Task 9: Version API Routes

**File: `backend/app/routes/workflows/versions.py`**

```python
"""
Workflow Version API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from pydantic import BaseModel

from app.utils.auth import get_current_user
from app.workflows.services.version_service import version_service
from app.workflows.models.store import workflow_store


router = APIRouter()


class SaveVersionRequest(BaseModel):
    comment: Optional[str] = None

class RollbackRequest(BaseModel):
    version: int


@router.get("/{workflow_id}/versions")
async def list_versions(workflow_id: str, limit: int = Query(20, ge=1, le=100), current_user: dict = Depends(get_current_user)):
    if not workflow_store.get_workflow(workflow_id):
        raise HTTPException(status_code=404, detail="Workflow not found")
    return version_service.list_versions(workflow_id, limit=limit)


@router.post("/{workflow_id}/versions")
async def save_version(workflow_id: str, data: SaveVersionRequest, current_user: dict = Depends(get_current_user)):
    workflow = workflow_store.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return version_service.save_version(workflow, user_id=current_user["id"], comment=data.comment)


@router.get("/{workflow_id}/versions/{version}")
async def get_version(workflow_id: str, version: int, current_user: dict = Depends(get_current_user)):
    ver = version_service.get_version(workflow_id, version=version)
    if not ver:
        raise HTTPException(status_code=404, detail="Version not found")
    return ver


@router.get("/{workflow_id}/versions/compare")
async def compare_versions(workflow_id: str, version_a: int = Query(...), version_b: int = Query(...), current_user: dict = Depends(get_current_user)):
    result = version_service.compare_versions(workflow_id, version_a, version_b)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/{workflow_id}/versions/rollback")
async def rollback_version(workflow_id: str, data: RollbackRequest, current_user: dict = Depends(get_current_user)):
    try:
        return version_service.rollback(workflow_id, data.version, current_user["id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## Task 10: Version History UI

**File: `frontend/src/features/workflows/components/VersionHistory.jsx`**

```jsx
import React, { useState, useEffect } from 'react';
import { History, GitCommit, GitCompare, RotateCcw, ChevronDown, ChevronUp, Check, X } from 'lucide-react';
import { workflowAPI } from '../../../services/api';

export default function VersionHistory({ workflowId, onRollback }) {
  const [versions, setVersions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedVersions, setSelectedVersions] = useState([]);
  const [comparison, setComparison] = useState(null);
  const [rollbackConfirm, setRollbackConfirm] = useState(null);

  useEffect(() => { workflowId && loadVersions(); }, [workflowId]);

  const loadVersions = async () => {
    try {
      setIsLoading(true);
      const res = await workflowAPI.listVersions(workflowId);
      setVersions(res.data || []);
    } catch (e) { console.error(e); }
    finally { setIsLoading(false); }
  };

  const handleSelect = (v) => {
    if (selectedVersions.includes(v)) setSelectedVersions(selectedVersions.filter(x => x !== v));
    else if (selectedVersions.length < 2) setSelectedVersions([...selectedVersions, v]);
    else setSelectedVersions([selectedVersions[1], v]);
  };

  const handleCompare = async () => {
    if (selectedVersions.length !== 2) return;
    const res = await workflowAPI.compareVersions(workflowId, Math.min(...selectedVersions), Math.max(...selectedVersions));
    setComparison(res.data);
  };

  const handleRollback = async (version) => {
    await workflowAPI.rollbackVersion(workflowId, version);
    setRollbackConfirm(null);
    loadVersions();
    onRollback?.();
  };

  return (
    <div className="version-history">
      <div className="header" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="left"><History size={16} /><span>Version History</span><span className="count">{versions.length}</span></div>
        {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </div>
      {isExpanded && (
        <div className="content">
          {selectedVersions.length === 2 && <button className="compare-btn" onClick={handleCompare}><GitCompare size={16} /> Compare</button>}
          <div className="list">
            {versions.map(v => (
              <div key={v.id} className={`item ${selectedVersions.includes(v.version) ? 'selected' : ''}`}>
                <div className="check" onClick={() => handleSelect(v.version)}>{selectedVersions.includes(v.version) ? <Check size={14} /> : <div className="empty" />}</div>
                <div className="info"><GitCommit size={14} /><span className="num">v{v.version}</span>{v.comment && <span className="comment">{v.comment}</span>}</div>
                <button className="rollback" onClick={() => setRollbackConfirm(v.version)}><RotateCcw size={14} /></button>
              </div>
            ))}
          </div>
          {comparison && (
            <div className="comparison">
              <h4>v{comparison.version_a} → v{comparison.version_b}</h4>
              <div className="stats"><span className="add">+{comparison.nodes_added}</span><span className="rem">-{comparison.nodes_removed}</span><span className="mod">~{comparison.nodes_modified}</span></div>
              <button onClick={() => setComparison(null)}><X size={14} /></button>
            </div>
          )}
          {rollbackConfirm && (
            <div className="confirm">
              <p>Rollback to v{rollbackConfirm}?</p>
              <div className="actions"><button onClick={() => setRollbackConfirm(null)}>Cancel</button><button className="primary" onClick={() => handleRollback(rollbackConfirm)}>Rollback</button></div>
            </div>
          )}
        </div>
      )}
      <style jsx>{`
        .version-history { background: var(--bg-primary); border: 1px solid var(--border-color); border-radius: 8px; }
        .header { display: flex; justify-content: space-between; padding: 12px 16px; cursor: pointer; }
        .header:hover { background: var(--bg-secondary); }
        .left { display: flex; align-items: center; gap: 8px; font-weight: 500; }
        .count { font-size: 12px; color: var(--text-muted); }
        .content { border-top: 1px solid var(--border-color); padding: 12px; }
        .compare-btn { display: flex; align-items: center; gap: 8px; padding: 8px 16px; background: var(--primary); color: white; border-radius: 6px; margin-bottom: 12px; }
        .list { display: flex; flex-direction: column; gap: 8px; max-height: 250px; overflow-y: auto; }
        .item { display: flex; align-items: center; gap: 12px; padding: 10px 12px; background: var(--bg-secondary); border-radius: 6px; border: 2px solid transparent; }
        .item.selected { border-color: var(--primary); }
        .check { cursor: pointer; color: var(--primary); }
        .empty { width: 14px; height: 14px; border: 2px solid var(--border-color); border-radius: 3px; }
        .info { flex: 1; display: flex; align-items: center; gap: 8px; }
        .num { font-weight: 600; }
        .comment { color: var(--text-muted); font-size: 13px; }
        .rollback { padding: 6px; border-radius: 4px; }
        .rollback:hover { background: var(--bg-primary); color: var(--primary); }
        .comparison { margin-top: 16px; padding: 12px; background: var(--bg-secondary); border-radius: 8px; display: flex; align-items: center; gap: 12px; }
        .comparison h4 { margin: 0; font-size: 14px; }
        .stats { display: flex; gap: 12px; font-size: 13px; }
        .add { color: #10b981; }
        .rem { color: #ef4444; }
        .mod { color: #f59e0b; }
        .confirm { margin-top: 16px; padding: 16px; background: rgba(245,158,11,0.1); border-radius: 8px; text-align: center; }
        .actions { display: flex; justify-content: center; gap: 12px; margin-top: 12px; }
        .actions button { padding: 8px 16px; border-radius: 6px; }
        .actions .primary { background: #f59e0b; color: white; }
      `}</style>
    </div>
  );
}
```

---

## Summary: Part 2 Complete

### Files Created:

| File | Lines | Purpose |
|------|-------|---------|
| `subworkflow_action.py` | ~120 | Sub-workflow executor |
| `error_handler.py` | ~200 | Try-Catch, Retry, Fallback, Circuit Breaker |
| `version_service.py` | ~120 | Version control service |
| `routes/workflows/versions.py` | ~60 | Version API routes |
| `VersionHistory.jsx` | ~80 | Frontend version panel |
| **Total** | **~580** | |

### Features Implemented:

| Feature | Status |
|---------|--------|
| Sub-workflow node | ✅ |
| Recursion prevention | ✅ |
| Try-Catch blocks | ✅ |
| Retry with strategies | ✅ |
| Fallback actions | ✅ |
| Circuit breaker | ✅ |
| Version history | ✅ |
| Version comparison | ✅ |
| Rollback capability | ✅ |

### Next: Part 3 - AI Features & Template Marketplace
