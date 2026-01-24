# Phase 30: Workflow Automation - Part 1: Workflow Engine Core

## Overview
This part covers the core workflow engine infrastructure including models, execution engine, state machine, and variable system.

---

## File 1: Workflow Models
**Path:** `backend/app/workflows/models.py`

```python
"""
Workflow Models
Data structures for workflow definitions and executions
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from uuid import uuid4
from dataclasses import dataclass, field


class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING = "waiting"
    RETRYING = "retrying"


class NodeType(str, Enum):
    TRIGGER = "trigger"
    ACTION = "action"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    DELAY = "delay"
    END = "end"


class TriggerType(str, Enum):
    EVENT = "event"
    SCHEDULE = "schedule"
    MANUAL = "manual"
    WEBHOOK = "webhook"


@dataclass
class WorkflowNode:
    """Represents a node in the workflow."""
    
    id: str
    type: NodeType
    name: str = ""
    description: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    position: Dict[str, int] = field(default_factory=lambda: {"x": 0, "y": 0})
    
    # For action nodes
    action: Optional[str] = None
    
    # For condition nodes
    condition: Optional[Dict] = None
    true_branch: List[str] = field(default_factory=list)
    false_branch: List[str] = field(default_factory=list)
    
    # For loop nodes
    collection: Optional[str] = None
    item_variable: Optional[str] = None
    body: List[str] = field(default_factory=list)
    
    # For parallel nodes
    branches: List[List[str]] = field(default_factory=list)
    
    # For delay nodes
    delay_seconds: int = 0
    delay_until: Optional[str] = None
    
    # Outputs
    outputs: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, NodeType) else self.type,
            "name": self.name,
            "description": self.description,
            "config": self.config,
            "position": self.position,
            "action": self.action,
            "condition": self.condition,
            "true_branch": self.true_branch,
            "false_branch": self.false_branch,
            "collection": self.collection,
            "item_variable": self.item_variable,
            "body": self.body,
            "branches": self.branches,
            "delay_seconds": self.delay_seconds,
            "delay_until": self.delay_until,
            "outputs": self.outputs,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "WorkflowNode":
        node_type = data.get("type")
        if isinstance(node_type, str):
            node_type = NodeType(node_type)
        
        return cls(
            id=data["id"],
            type=node_type,
            name=data.get("name", ""),
            description=data.get("description", ""),
            config=data.get("config", {}),
            position=data.get("position", {"x": 0, "y": 0}),
            action=data.get("action"),
            condition=data.get("condition"),
            true_branch=data.get("true_branch", []),
            false_branch=data.get("false_branch", []),
            collection=data.get("collection"),
            item_variable=data.get("item_variable"),
            body=data.get("body", []),
            branches=data.get("branches", []),
            delay_seconds=data.get("delay_seconds", 0),
            delay_until=data.get("delay_until"),
            outputs=data.get("outputs", []),
        )


@dataclass
class WorkflowEdge:
    """Represents a connection between nodes."""
    
    id: str
    source: str
    target: str
    label: Optional[str] = None
    condition: Optional[str] = None  # "true", "false", or None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "label": self.label,
            "condition": self.condition,
        }


@dataclass
class WorkflowTrigger:
    """Workflow trigger configuration."""
    
    type: TriggerType
    event: Optional[str] = None
    cron: Optional[str] = None
    interval_seconds: Optional[int] = None
    webhook_path: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type.value if isinstance(self.type, TriggerType) else self.type,
            "event": self.event,
            "cron": self.cron,
            "interval_seconds": self.interval_seconds,
            "webhook_path": self.webhook_path,
            "config": self.config,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "WorkflowTrigger":
        trigger_type = data.get("type")
        if isinstance(trigger_type, str):
            trigger_type = TriggerType(trigger_type)
        
        return cls(
            type=trigger_type,
            event=data.get("event"),
            cron=data.get("cron"),
            interval_seconds=data.get("interval_seconds"),
            webhook_path=data.get("webhook_path"),
            config=data.get("config", {}),
        )


@dataclass
class Workflow:
    """Complete workflow definition."""
    
    id: str
    name: str
    customer_id: str
    description: str = ""
    status: WorkflowStatus = WorkflowStatus.DRAFT
    version: int = 1
    trigger: Optional[WorkflowTrigger] = None
    nodes: List[WorkflowNode] = field(default_factory=list)
    edges: List[WorkflowEdge] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    
    # Runtime stats
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    last_run_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "customer_id": self.customer_id,
            "description": self.description,
            "status": self.status.value,
            "version": self.version,
            "trigger": self.trigger.to_dict() if self.trigger else None,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "variables": self.variables,
            "settings": self.settings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "run_count": self.run_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "success_rate": (self.success_count / self.run_count * 100) if self.run_count > 0 else 0,
        }
    
    def get_node(self, node_id: str) -> Optional[WorkflowNode]:
        """Get node by ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
    
    def get_start_nodes(self) -> List[str]:
        """Get nodes connected to trigger."""
        start_nodes = []
        for edge in self.edges:
            if edge.source == "trigger":
                start_nodes.append(edge.target)
        return start_nodes
    
    def get_next_nodes(self, node_id: str, condition: str = None) -> List[str]:
        """Get next nodes from current node."""
        next_nodes = []
        for edge in self.edges:
            if edge.source == node_id:
                if condition is None or edge.condition == condition:
                    next_nodes.append(edge.target)
        return next_nodes


@dataclass
class StepExecution:
    """Execution state of a single step/node."""
    
    id: str
    node_id: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "node_id": self.node_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error": self.error,
            "retry_count": self.retry_count,
            "duration_ms": self.duration_ms,
        }
    
    @property
    def duration_ms(self) -> Optional[int]:
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds() * 1000)
        return None


@dataclass
class WorkflowExecution:
    """Execution instance of a workflow."""
    
    id: str
    workflow_id: str
    workflow_version: int
    status: ExecutionStatus = ExecutionStatus.PENDING
    trigger_type: Optional[str] = None
    trigger_data: Dict[str, Any] = field(default_factory=dict)
    input_data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    steps: List[StepExecution] = field(default_factory=list)
    current_node_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "workflow_version": self.workflow_version,
            "status": self.status.value,
            "trigger_type": self.trigger_type,
            "trigger_data": self.trigger_data,
            "input_data": self.input_data,
            "context": self.context,
            "steps": [s.to_dict() for s in self.steps],
            "current_node_id": self.current_node_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "steps_completed": len([s for s in self.steps if s.status == ExecutionStatus.COMPLETED]),
            "steps_total": len(self.steps),
        }
    
    @property
    def duration_ms(self) -> Optional[int]:
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds() * 1000)
        return None
    
    def get_step(self, node_id: str) -> Optional[StepExecution]:
        """Get step execution by node ID."""
        for step in self.steps:
            if step.node_id == node_id:
                return step
        return None
    
    def add_step(self, node_id: str) -> StepExecution:
        """Add new step execution."""
        step = StepExecution(
            id=f"step_{uuid4().hex[:12]}",
            node_id=node_id,
        )
        self.steps.append(step)
        return step
```

---

## File 2: Variable System
**Path:** `backend/app/workflows/variables.py`

```python
"""
Variable System
Handles variable resolution and template rendering in workflows
"""

from typing import Dict, Any, List, Optional, Union
import re
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class VariableResolver:
    """Resolves variables in workflow configurations."""
    
    # Pattern to match {{variable}} or {{object.property}}
    VARIABLE_PATTERN = re.compile(r'\{\{([^}]+)\}\}')
    
    # Built-in functions
    FUNCTIONS = {
        "now": lambda: datetime.utcnow().isoformat(),
        "today": lambda: datetime.utcnow().strftime("%Y-%m-%d"),
        "timestamp": lambda: int(datetime.utcnow().timestamp()),
        "uuid": lambda: __import__('uuid').uuid4().hex,
    }
    
    def __init__(self, context: Dict[str, Any] = None):
        self.context = context or {}
    
    def set_context(self, context: Dict[str, Any]):
        """Set the variable context."""
        self.context = context
    
    def update_context(self, key: str, value: Any):
        """Update a single context variable."""
        self.context[key] = value
    
    def merge_context(self, data: Dict[str, Any]):
        """Merge data into context."""
        self.context.update(data)
    
    def resolve(self, template: Union[str, Dict, List, Any]) -> Any:
        """Resolve variables in a template."""
        if isinstance(template, str):
            return self._resolve_string(template)
        elif isinstance(template, dict):
            return self._resolve_dict(template)
        elif isinstance(template, list):
            return self._resolve_list(template)
        else:
            return template
    
    def _resolve_string(self, template: str) -> Any:
        """Resolve variables in a string template."""
        # Check if entire string is a single variable
        match = re.fullmatch(r'\{\{([^}]+)\}\}', template.strip())
        if match:
            # Return the actual value (not stringified)
            return self._get_value(match.group(1).strip())
        
        # Replace all variables in string
        def replace_var(match):
            var_name = match.group(1).strip()
            value = self._get_value(var_name)
            if value is None:
                return ""
            if isinstance(value, (dict, list)):
                return json.dumps(value)
            return str(value)
        
        return self.VARIABLE_PATTERN.sub(replace_var, template)
    
    def _resolve_dict(self, template: Dict) -> Dict:
        """Resolve variables in a dictionary."""
        result = {}
        for key, value in template.items():
            resolved_key = self._resolve_string(key) if isinstance(key, str) else key
            result[resolved_key] = self.resolve(value)
        return result
    
    def _resolve_list(self, template: List) -> List:
        """Resolve variables in a list."""
        return [self.resolve(item) for item in template]
    
    def _get_value(self, var_path: str) -> Any:
        """Get value from context using dot notation."""
        # Check for function call
        if var_path.endswith("()"):
            func_name = var_path[:-2]
            if func_name in self.FUNCTIONS:
                return self.FUNCTIONS[func_name]()
            return None
        
        # Check for pipe functions (e.g., {{name|upper}})
        if "|" in var_path:
            var_name, pipe_func = var_path.split("|", 1)
            value = self._get_value(var_name.strip())
            return self._apply_pipe(value, pipe_func.strip())
        
        # Navigate nested path
        parts = var_path.split(".")
        value = self.context
        
        for part in parts:
            if value is None:
                return None
            
            # Handle array indexing: items[0]
            array_match = re.match(r'(\w+)\[(\d+)\]', part)
            if array_match:
                key, index = array_match.groups()
                if isinstance(value, dict):
                    value = value.get(key)
                if isinstance(value, list) and len(value) > int(index):
                    value = value[int(index)]
                else:
                    return None
            elif isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        
        return value
    
    def _apply_pipe(self, value: Any, pipe_func: str) -> Any:
        """Apply a pipe function to a value."""
        if value is None:
            return None
        
        pipe_functions = {
            "upper": lambda v: str(v).upper(),
            "lower": lambda v: str(v).lower(),
            "title": lambda v: str(v).title(),
            "trim": lambda v: str(v).strip(),
            "length": lambda v: len(v) if hasattr(v, '__len__') else 0,
            "first": lambda v: v[0] if v else None,
            "last": lambda v: v[-1] if v else None,
            "sum": lambda v: sum(v) if isinstance(v, list) else v,
            "min": lambda v: min(v) if isinstance(v, list) else v,
            "max": lambda v: max(v) if isinstance(v, list) else v,
            "join": lambda v: ", ".join(str(x) for x in v) if isinstance(v, list) else str(v),
            "json": lambda v: json.dumps(v),
            "keys": lambda v: list(v.keys()) if isinstance(v, dict) else [],
            "values": lambda v: list(v.values()) if isinstance(v, dict) else [],
            "default": lambda v: v if v else "",
            "currency": lambda v: f"${float(v):,.2f}" if v else "$0.00",
            "date": lambda v: datetime.fromisoformat(str(v)).strftime("%Y-%m-%d") if v else "",
            "datetime": lambda v: datetime.fromisoformat(str(v)).strftime("%Y-%m-%d %H:%M") if v else "",
        }
        
        if pipe_func in pipe_functions:
            try:
                return pipe_functions[pipe_func](value)
            except Exception as e:
                logger.warning(f"Pipe function {pipe_func} failed: {e}")
                return value
        
        return value
    
    def extract_variables(self, template: Union[str, Dict, List]) -> List[str]:
        """Extract all variable names from a template."""
        variables = set()
        
        def extract(value):
            if isinstance(value, str):
                matches = self.VARIABLE_PATTERN.findall(value)
                for match in matches:
                    # Remove pipe functions
                    var_name = match.split("|")[0].strip()
                    # Remove function calls
                    if not var_name.endswith("()"):
                        variables.add(var_name)
            elif isinstance(value, dict):
                for v in value.values():
                    extract(v)
            elif isinstance(value, list):
                for item in value:
                    extract(item)
        
        extract(template)
        return list(variables)
    
    def validate_variables(self, template: Union[str, Dict, List]) -> List[str]:
        """Check which variables are missing from context."""
        required = self.extract_variables(template)
        missing = []
        
        for var in required:
            if self._get_value(var) is None:
                missing.append(var)
        
        return missing


class ExpressionEvaluator:
    """Evaluates expressions for conditions."""
    
    OPERATORS = {
        "equals": lambda a, b: a == b,
        "not_equals": lambda a, b: a != b,
        "greater_than": lambda a, b: float(a) > float(b) if a and b else False,
        "greater_than_or_equals": lambda a, b: float(a) >= float(b) if a and b else False,
        "less_than": lambda a, b: float(a) < float(b) if a and b else False,
        "less_than_or_equals": lambda a, b: float(a) <= float(b) if a and b else False,
        "contains": lambda a, b: str(b) in str(a) if a else False,
        "not_contains": lambda a, b: str(b) not in str(a) if a else True,
        "starts_with": lambda a, b: str(a).startswith(str(b)) if a else False,
        "ends_with": lambda a, b: str(a).endswith(str(b)) if a else False,
        "is_empty": lambda a, _: not a or (isinstance(a, (list, dict, str)) and len(a) == 0),
        "is_not_empty": lambda a, _: bool(a) and (not isinstance(a, (list, dict, str)) or len(a) > 0),
        "in": lambda a, b: a in b if isinstance(b, (list, tuple)) else False,
        "not_in": lambda a, b: a not in b if isinstance(b, (list, tuple)) else True,
        "matches": lambda a, b: bool(re.match(str(b), str(a))) if a and b else False,
    }
    
    def __init__(self, resolver: VariableResolver):
        self.resolver = resolver
    
    def evaluate(self, condition: Dict) -> bool:
        """Evaluate a condition."""
        condition_type = condition.get("type", "simple")
        
        if condition_type == "and":
            conditions = condition.get("conditions", [])
            return all(self.evaluate(c) for c in conditions)
        
        elif condition_type == "or":
            conditions = condition.get("conditions", [])
            return any(self.evaluate(c) for c in conditions)
        
        elif condition_type == "not":
            inner = condition.get("condition", {})
            return not self.evaluate(inner)
        
        else:
            # Simple condition
            field = condition.get("field")
            operator = condition.get("operator", "equals")
            value = condition.get("value")
            
            # Resolve variables
            field_value = self.resolver.resolve(field) if isinstance(field, str) and "{{" in field else self.resolver._get_value(field) if field else None
            compare_value = self.resolver.resolve(value) if isinstance(value, str) and "{{" in value else value
            
            # Get operator function
            op_func = self.OPERATORS.get(operator)
            if not op_func:
                logger.warning(f"Unknown operator: {operator}")
                return False
            
            try:
                return op_func(field_value, compare_value)
            except Exception as e:
                logger.warning(f"Condition evaluation failed: {e}")
                return False
```

---

## File 3: Workflow Engine
**Path:** `backend/app/workflows/engine.py`

```python
"""
Workflow Execution Engine
Core engine for running workflows
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from uuid import uuid4
import asyncio
import logging

from app.workflows.models import (
    Workflow, WorkflowNode, WorkflowExecution, StepExecution,
    ExecutionStatus, NodeType
)
from app.workflows.variables import VariableResolver, ExpressionEvaluator

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Executes workflows."""
    
    def __init__(self):
        self._action_handlers: Dict[str, Callable] = {}
        self._running_executions: Dict[str, WorkflowExecution] = {}
        self._execution_history: Dict[str, List[WorkflowExecution]] = {}
    
    def register_action(self, action_name: str, handler: Callable):
        """Register an action handler."""
        self._action_handlers[action_name] = handler
        logger.info(f"Registered action: {action_name}")
    
    async def execute(self, workflow: Workflow, input_data: Dict = None, trigger_data: Dict = None) -> WorkflowExecution:
        """Execute a workflow."""
        # Create execution instance
        execution = WorkflowExecution(
            id=f"exec_{uuid4().hex[:12]}",
            workflow_id=workflow.id,
            workflow_version=workflow.version,
            trigger_data=trigger_data or {},
            input_data=input_data or {},
            context={
                "workflow": {
                    "id": workflow.id,
                    "name": workflow.name,
                },
                "trigger": trigger_data or {},
                "input": input_data or {},
            },
        )
        
        # Track execution
        self._running_executions[execution.id] = execution
        if workflow.id not in self._execution_history:
            self._execution_history[workflow.id] = []
        self._execution_history[workflow.id].append(execution)
        
        # Initialize resolver
        resolver = VariableResolver(execution.context)
        evaluator = ExpressionEvaluator(resolver)
        
        try:
            execution.status = ExecutionStatus.RUNNING
            execution.started_at = datetime.utcnow()
            
            # Get starting nodes
            start_nodes = workflow.get_start_nodes()
            if not start_nodes:
                raise ValueError("No start nodes found in workflow")
            
            # Execute from start nodes
            for node_id in start_nodes:
                await self._execute_node(workflow, execution, node_id, resolver, evaluator)
            
            # Mark as completed
            execution.status = ExecutionStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            
            # Update workflow stats
            workflow.run_count += 1
            workflow.success_count += 1
            workflow.last_run_at = datetime.utcnow()
            
            logger.info(f"Workflow {workflow.id} completed successfully")
            
        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.utcnow()
            
            workflow.run_count += 1
            workflow.failure_count += 1
            workflow.last_run_at = datetime.utcnow()
            
            logger.error(f"Workflow {workflow.id} failed: {e}")
        
        finally:
            del self._running_executions[execution.id]
        
        return execution
    
    async def _execute_node(self, workflow: Workflow, execution: WorkflowExecution, node_id: str, resolver: VariableResolver, evaluator: ExpressionEvaluator):
        """Execute a single node."""
        node = workflow.get_node(node_id)
        if not node:
            logger.warning(f"Node not found: {node_id}")
            return
        
        # Create step execution
        step = execution.add_step(node_id)
        step.status = ExecutionStatus.RUNNING
        step.started_at = datetime.utcnow()
        execution.current_node_id = node_id
        
        try:
            logger.info(f"Executing node: {node_id} ({node.type})")
            
            if node.type == NodeType.ACTION:
                await self._execute_action(node, step, resolver)
            
            elif node.type == NodeType.CONDITION:
                branch = await self._execute_condition(node, evaluator)
                step.output_data["branch"] = branch
                
                # Execute appropriate branch
                next_nodes = node.true_branch if branch else node.false_branch
                for next_id in next_nodes:
                    await self._execute_node(workflow, execution, next_id, resolver, evaluator)
                
                step.status = ExecutionStatus.COMPLETED
                step.completed_at = datetime.utcnow()
                return  # Don't continue to normal next nodes
            
            elif node.type == NodeType.LOOP:
                await self._execute_loop(workflow, execution, node, resolver, evaluator)
            
            elif node.type == NodeType.PARALLEL:
                await self._execute_parallel(workflow, execution, node, resolver, evaluator)
            
            elif node.type == NodeType.DELAY:
                await self._execute_delay(node, step, resolver)
            
            elif node.type == NodeType.END:
                pass  # End node, nothing to do
            
            step.status = ExecutionStatus.COMPLETED
            step.completed_at = datetime.utcnow()
            
            # Store outputs in context
            for output_name in node.outputs:
                if output_name in step.output_data:
                    resolver.update_context(output_name, step.output_data[output_name])
            
            # Continue to next nodes
            next_nodes = workflow.get_next_nodes(node_id)
            for next_id in next_nodes:
                await self._execute_node(workflow, execution, next_id, resolver, evaluator)
            
        except Exception as e:
            step.status = ExecutionStatus.FAILED
            step.error = str(e)
            step.completed_at = datetime.utcnow()
            raise
    
    async def _execute_action(self, node: WorkflowNode, step: StepExecution, resolver: VariableResolver):
        """Execute an action node."""
        action_name = node.action
        if not action_name:
            raise ValueError(f"No action specified for node {node.id}")
        
        handler = self._action_handlers.get(action_name)
        if not handler:
            raise ValueError(f"Unknown action: {action_name}")
        
        # Resolve config variables
        config = resolver.resolve(node.config)
        step.input_data = config
        
        # Execute action
        if asyncio.iscoroutinefunction(handler):
            result = await handler(config, resolver.context)
        else:
            result = handler(config, resolver.context)
        
        step.output_data = result if isinstance(result, dict) else {"result": result}
    
    async def _execute_condition(self, node: WorkflowNode, evaluator: ExpressionEvaluator) -> bool:
        """Execute a condition node and return branch result."""
        if not node.condition:
            return True
        
        return evaluator.evaluate(node.condition)
    
    async def _execute_loop(self, workflow: Workflow, execution: WorkflowExecution, node: WorkflowNode, resolver: VariableResolver, evaluator: ExpressionEvaluator):
        """Execute a loop node."""
        collection = resolver.resolve(node.collection)
        
        if not isinstance(collection, list):
            logger.warning(f"Loop collection is not a list: {type(collection)}")
            return
        
        item_var = node.item_variable or "item"
        index_var = f"{item_var}_index"
        
        for index, item in enumerate(collection):
            # Set loop variables
            resolver.update_context(item_var, item)
            resolver.update_context(index_var, index)
            
            # Execute body nodes
            for body_node_id in node.body:
                await self._execute_node(workflow, execution, body_node_id, resolver, evaluator)
    
    async def _execute_parallel(self, workflow: Workflow, execution: WorkflowExecution, node: WorkflowNode, resolver: VariableResolver, evaluator: ExpressionEvaluator):
        """Execute parallel branches."""
        tasks = []
        
        for branch in node.branches:
            for branch_node_id in branch:
                # Create a copy of resolver for each branch
                branch_resolver = VariableResolver(dict(resolver.context))
                branch_evaluator = ExpressionEvaluator(branch_resolver)
                
                task = self._execute_node(workflow, execution, branch_node_id, branch_resolver, branch_evaluator)
                tasks.append(task)
        
        # Wait for all branches
        await asyncio.gather(*tasks)
    
    async def _execute_delay(self, node: WorkflowNode, step: StepExecution, resolver: VariableResolver):
        """Execute a delay node."""
        if node.delay_seconds > 0:
            step.output_data["delay_seconds"] = node.delay_seconds
            await asyncio.sleep(node.delay_seconds)
        elif node.delay_until:
            target_time = resolver.resolve(node.delay_until)
            if isinstance(target_time, str):
                target_time = datetime.fromisoformat(target_time)
            
            now = datetime.utcnow()
            if target_time > now:
                delay = (target_time - now).total_seconds()
                step.output_data["delay_until"] = target_time.isoformat()
                await asyncio.sleep(delay)
    
    # ==================== Management ====================
    
    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get execution by ID."""
        # Check running first
        if execution_id in self._running_executions:
            return self._running_executions[execution_id]
        
        # Check history
        for executions in self._execution_history.values():
            for execution in executions:
                if execution.id == execution_id:
                    return execution
        
        return None
    
    def get_workflow_executions(self, workflow_id: str, limit: int = 20) -> List[WorkflowExecution]:
        """Get executions for a workflow."""
        executions = self._execution_history.get(workflow_id, [])
        return sorted(executions, key=lambda e: e.started_at or datetime.min, reverse=True)[:limit]
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution."""
        execution = self._running_executions.get(execution_id)
        if execution:
            execution.status = ExecutionStatus.CANCELLED
            execution.completed_at = datetime.utcnow()
            return True
        return False
    
    def get_running_executions(self) -> List[WorkflowExecution]:
        """Get all running executions."""
        return list(self._running_executions.values())


# Global engine instance
workflow_engine = WorkflowEngine()
```

---

## File 4: Condition Evaluator
**Path:** `backend/app/workflows/conditions.py`

```python
"""
Condition Builder & Evaluator
Advanced condition handling for workflow decisions
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import re
import logging

logger = logging.getLogger(__name__)


class ConditionBuilder:
    """Builds condition objects for the workflow builder UI."""
    
    FIELD_TYPES = {
        "string": ["equals", "not_equals", "contains", "not_contains", "starts_with", "ends_with", "is_empty", "is_not_empty", "matches"],
        "number": ["equals", "not_equals", "greater_than", "greater_than_or_equals", "less_than", "less_than_or_equals", "is_empty", "is_not_empty"],
        "boolean": ["equals", "not_equals"],
        "date": ["equals", "not_equals", "before", "after", "between", "is_empty", "is_not_empty"],
        "array": ["contains", "not_contains", "is_empty", "is_not_empty", "length_equals", "length_greater_than", "length_less_than"],
    }
    
    OPERATOR_LABELS = {
        "equals": "equals",
        "not_equals": "does not equal",
        "greater_than": "is greater than",
        "greater_than_or_equals": "is greater than or equal to",
        "less_than": "is less than",
        "less_than_or_equals": "is less than or equal to",
        "contains": "contains",
        "not_contains": "does not contain",
        "starts_with": "starts with",
        "ends_with": "ends with",
        "is_empty": "is empty",
        "is_not_empty": "is not empty",
        "matches": "matches pattern",
        "before": "is before",
        "after": "is after",
        "between": "is between",
        "in": "is one of",
        "not_in": "is not one of",
    }
    
    @classmethod
    def get_operators_for_type(cls, field_type: str) -> List[Dict]:
        """Get available operators for a field type."""
        operators = cls.FIELD_TYPES.get(field_type, cls.FIELD_TYPES["string"])
        return [
            {"value": op, "label": cls.OPERATOR_LABELS.get(op, op)}
            for op in operators
        ]
    
    @classmethod
    def build_simple(cls, field: str, operator: str, value: Any) -> Dict:
        """Build a simple condition."""
        return {
            "type": "simple",
            "field": field,
            "operator": operator,
            "value": value,
        }
    
    @classmethod
    def build_and(cls, conditions: List[Dict]) -> Dict:
        """Build an AND condition."""
        return {
            "type": "and",
            "conditions": conditions,
        }
    
    @classmethod
    def build_or(cls, conditions: List[Dict]) -> Dict:
        """Build an OR condition."""
        return {
            "type": "or",
            "conditions": conditions,
        }
    
    @classmethod
    def build_not(cls, condition: Dict) -> Dict:
        """Build a NOT condition."""
        return {
            "type": "not",
            "condition": condition,
        }
    
    @classmethod
    def validate(cls, condition: Dict) -> List[str]:
        """Validate a condition structure."""
        errors = []
        
        condition_type = condition.get("type", "simple")
        
        if condition_type in ["and", "or"]:
            conditions = condition.get("conditions", [])
            if not conditions:
                errors.append(f"{condition_type.upper()} condition requires at least one sub-condition")
            for i, sub in enumerate(conditions):
                sub_errors = cls.validate(sub)
                errors.extend([f"[{i}] {e}" for e in sub_errors])
        
        elif condition_type == "not":
            inner = condition.get("condition")
            if not inner:
                errors.append("NOT condition requires an inner condition")
            else:
                errors.extend(cls.validate(inner))
        
        else:  # simple
            if not condition.get("field"):
                errors.append("Field is required")
            if not condition.get("operator"):
                errors.append("Operator is required")
            # Value can be empty for is_empty/is_not_empty operators
        
        return errors


class DateConditionHelper:
    """Helper for date-based conditions."""
    
    @staticmethod
    def days_ago(days: int) -> datetime:
        """Get datetime for N days ago."""
        return datetime.utcnow() - timedelta(days=days)
    
    @staticmethod
    def days_from_now(days: int) -> datetime:
        """Get datetime for N days from now."""
        return datetime.utcnow() + timedelta(days=days)
    
    @staticmethod
    def start_of_day(dt: datetime = None) -> datetime:
        """Get start of day."""
        dt = dt or datetime.utcnow()
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    
    @staticmethod
    def end_of_day(dt: datetime = None) -> datetime:
        """Get end of day."""
        dt = dt or datetime.utcnow()
        return dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    @staticmethod
    def start_of_week(dt: datetime = None) -> datetime:
        """Get start of week (Monday)."""
        dt = dt or datetime.utcnow()
        days_since_monday = dt.weekday()
        return DateConditionHelper.start_of_day(dt - timedelta(days=days_since_monday))
    
    @staticmethod
    def start_of_month(dt: datetime = None) -> datetime:
        """Get start of month."""
        dt = dt or datetime.utcnow()
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    @staticmethod
    def is_overdue(date_value: Union[str, datetime], reference: datetime = None) -> bool:
        """Check if a date is overdue."""
        if isinstance(date_value, str):
            date_value = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
        reference = reference or datetime.utcnow()
        return date_value < reference
    
    @staticmethod
    def days_until(date_value: Union[str, datetime]) -> int:
        """Get days until a date."""
        if isinstance(date_value, str):
            date_value = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
        delta = date_value - datetime.utcnow()
        return delta.days
    
    @staticmethod
    def days_since(date_value: Union[str, datetime]) -> int:
        """Get days since a date."""
        if isinstance(date_value, str):
            date_value = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
        delta = datetime.utcnow() - date_value
        return delta.days


class ConditionPresets:
    """Common condition presets for quick selection."""
    
    PRESETS = {
        "invoice_overdue": {
            "name": "Invoice is Overdue",
            "description": "Invoice due date has passed",
            "condition": {
                "type": "and",
                "conditions": [
                    {"field": "invoice.status", "operator": "not_equals", "value": "paid"},
                    {"field": "invoice.due_date", "operator": "before", "value": "{{now()}}"},
                ],
            },
        },
        "invoice_high_value": {
            "name": "High Value Invoice",
            "description": "Invoice amount exceeds threshold",
            "condition": {
                "field": "invoice.amount",
                "operator": "greater_than",
                "value": 10000,
            },
        },
        "customer_enterprise": {
            "name": "Enterprise Customer",
            "description": "Customer is enterprise tier",
            "condition": {
                "field": "customer.tier",
                "operator": "equals",
                "value": "enterprise",
            },
        },
        "ticket_urgent": {
            "name": "Urgent Ticket",
            "description": "Ticket priority is urgent or high",
            "condition": {
                "type": "or",
                "conditions": [
                    {"field": "ticket.priority", "operator": "equals", "value": "urgent"},
                    {"field": "ticket.priority", "operator": "equals", "value": "high"},
                ],
            },
        },
        "project_near_deadline": {
            "name": "Project Near Deadline",
            "description": "Project due within 7 days",
            "condition": {
                "type": "and",
                "conditions": [
                    {"field": "project.status", "operator": "not_equals", "value": "completed"},
                    {"field": "project.due_date", "operator": "before", "value": "{{days_from_now(7)}}"},
                ],
            },
        },
        "payment_failed": {
            "name": "Payment Failed",
            "description": "Payment status is failed",
            "condition": {
                "field": "payment.status",
                "operator": "equals",
                "value": "failed",
            },
        },
    }
    
    @classmethod
    def get_preset(cls, preset_id: str) -> Optional[Dict]:
        """Get a condition preset."""
        return cls.PRESETS.get(preset_id)
    
    @classmethod
    def list_presets(cls) -> List[Dict]:
        """List all available presets."""
        return [
            {
                "id": preset_id,
                "name": preset["name"],
                "description": preset["description"],
            }
            for preset_id, preset in cls.PRESETS.items()
        ]
```

---

## File 5: Error Handling
**Path:** `backend/app/workflows/errors.py`

```python
"""
Workflow Error Handling
Error types, retry logic, and recovery
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import logging
import asyncio

logger = logging.getLogger(__name__)


class WorkflowErrorType(str, Enum):
    VALIDATION_ERROR = "validation_error"
    EXECUTION_ERROR = "execution_error"
    ACTION_ERROR = "action_error"
    CONDITION_ERROR = "condition_error"
    TIMEOUT_ERROR = "timeout_error"
    RETRY_EXHAUSTED = "retry_exhausted"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class WorkflowError(Exception):
    """Base workflow exception."""
    
    def __init__(self, message: str, error_type: WorkflowErrorType = WorkflowErrorType.UNKNOWN, details: Dict = None, node_id: str = None, recoverable: bool = True):
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        self.node_id = node_id
        self.recoverable = recoverable
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)
    
    def to_dict(self) -> Dict:
        return {
            "message": self.message,
            "error_type": self.error_type.value,
            "details": self.details,
            "node_id": self.node_id,
            "recoverable": self.recoverable,
            "timestamp": self.timestamp.isoformat(),
        }


class ValidationError(WorkflowError):
    """Workflow validation error."""
    
    def __init__(self, message: str, errors: List[str] = None):
        super().__init__(
            message=message,
            error_type=WorkflowErrorType.VALIDATION_ERROR,
            details={"errors": errors or []},
            recoverable=False,
        )


class ActionError(WorkflowError):
    """Action execution error."""
    
    def __init__(self, message: str, action: str, node_id: str = None, original_error: Exception = None):
        super().__init__(
            message=message,
            error_type=WorkflowErrorType.ACTION_ERROR,
            details={
                "action": action,
                "original_error": str(original_error) if original_error else None,
            },
            node_id=node_id,
            recoverable=True,
        )


class TimeoutError(WorkflowError):
    """Workflow or action timeout."""
    
    def __init__(self, message: str, timeout_seconds: int, node_id: str = None):
        super().__init__(
            message=message,
            error_type=WorkflowErrorType.TIMEOUT_ERROR,
            details={"timeout_seconds": timeout_seconds},
            node_id=node_id,
            recoverable=True,
        )


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(self, max_retries: int = 3, initial_delay: float = 1.0, max_delay: float = 60.0, exponential_base: float = 2.0, retry_on: List[WorkflowErrorType] = None):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retry_on = retry_on or [
            WorkflowErrorType.EXECUTION_ERROR,
            WorkflowErrorType.ACTION_ERROR,
            WorkflowErrorType.TIMEOUT_ERROR,
        ]
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt."""
        delay = self.initial_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)
    
    def should_retry(self, error: WorkflowError, attempt: int) -> bool:
        """Check if should retry based on error and attempt count."""
        if attempt >= self.max_retries:
            return False
        if not error.recoverable:
            return False
        if error.error_type not in self.retry_on:
            return False
        return True


class RetryHandler:
    """Handles retry logic for workflow actions."""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
        self._retry_counts: Dict[str, int] = {}
    
    async def execute_with_retry(self, func: Callable, node_id: str, *args, **kwargs) -> Any:
        """Execute function with retry logic."""
        attempt = 0
        last_error = None
        
        while True:
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Success - reset retry count
                self._retry_counts[node_id] = 0
                return result
                
            except WorkflowError as e:
                last_error = e
                attempt += 1
                
                if self.config.should_retry(e, attempt):
                    delay = self.config.get_delay(attempt)
                    logger.warning(f"Retrying node {node_id} in {delay}s (attempt {attempt}/{self.config.max_retries})")
                    await asyncio.sleep(delay)
                else:
                    break
                    
            except Exception as e:
                # Wrap unknown exceptions
                last_error = WorkflowError(
                    message=str(e),
                    error_type=WorkflowErrorType.UNKNOWN,
                    node_id=node_id,
                )
                attempt += 1
                
                if attempt < self.config.max_retries:
                    delay = self.config.get_delay(attempt)
                    logger.warning(f"Retrying node {node_id} in {delay}s (attempt {attempt}/{self.config.max_retries})")
                    await asyncio.sleep(delay)
                else:
                    break
        
        # All retries exhausted
        self._retry_counts[node_id] = attempt
        raise WorkflowError(
            message=f"Retry exhausted after {attempt} attempts: {last_error.message}",
            error_type=WorkflowErrorType.RETRY_EXHAUSTED,
            details={"attempts": attempt, "last_error": last_error.to_dict()},
            node_id=node_id,
            recoverable=False,
        )
    
    def get_retry_count(self, node_id: str) -> int:
        """Get current retry count for a node."""
        return self._retry_counts.get(node_id, 0)


class ErrorRecovery:
    """Strategies for recovering from workflow errors."""
    
    @staticmethod
    async def skip_node(workflow, execution, node_id: str):
        """Skip the failed node and continue."""
        logger.info(f"Skipping failed node: {node_id}")
        step = execution.get_step(node_id)
        if step:
            step.output_data["skipped"] = True
        # Continue to next nodes
    
    @staticmethod
    async def use_fallback(workflow, execution, node_id: str, fallback_value: Any):
        """Use a fallback value for failed node."""
        logger.info(f"Using fallback for node: {node_id}")
        step = execution.get_step(node_id)
        if step:
            step.output_data = {"fallback": True, "value": fallback_value}
    
    @staticmethod
    async def retry_from_checkpoint(workflow, execution, checkpoint_node_id: str):
        """Retry workflow from a checkpoint node."""
        logger.info(f"Retrying from checkpoint: {checkpoint_node_id}")
        # Clear steps after checkpoint
        checkpoint_found = False
        steps_to_keep = []
        for step in execution.steps:
            if step.node_id == checkpoint_node_id:
                checkpoint_found = True
            if not checkpoint_found:
                steps_to_keep.append(step)
        execution.steps = steps_to_keep
    
    @staticmethod
    async def notify_and_pause(workflow, execution, error: WorkflowError):
        """Notify admin and pause workflow."""
        logger.warning(f"Pausing workflow due to error: {error.message}")
        execution.status = "waiting"
        # In production: send notification to admin


class WorkflowValidator:
    """Validates workflow definitions."""
    
    @staticmethod
    def validate(workflow: Dict) -> List[str]:
        """Validate a workflow definition."""
        errors = []
        
        # Check required fields
        if not workflow.get("name"):
            errors.append("Workflow name is required")
        
        if not workflow.get("trigger"):
            errors.append("Workflow trigger is required")
        
        nodes = workflow.get("nodes", [])
        edges = workflow.get("edges", [])
        
        if not nodes:
            errors.append("Workflow must have at least one node")
        
        # Validate nodes
        node_ids = set()
        for node in nodes:
            if not node.get("id"):
                errors.append("All nodes must have an ID")
                continue
            
            if node["id"] in node_ids:
                errors.append(f"Duplicate node ID: {node['id']}")
            node_ids.add(node["id"])
            
            node_type = node.get("type")
            if not node_type:
                errors.append(f"Node {node['id']} must have a type")
            
            # Validate action nodes
            if node_type == "action" and not node.get("action"):
                errors.append(f"Action node {node['id']} must specify an action")
            
            # Validate condition nodes
            if node_type == "condition" and not node.get("condition"):
                errors.append(f"Condition node {node['id']} must have a condition")
        
        # Validate edges
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            
            if source != "trigger" and source not in node_ids:
                errors.append(f"Edge source not found: {source}")
            
            if target not in node_ids:
                errors.append(f"Edge target not found: {target}")
        
        # Check for orphan nodes
        connected_nodes = set()
        for edge in edges:
            connected_nodes.add(edge.get("target"))
        
        for node_id in node_ids:
            if node_id not in connected_nodes:
                # Check if it's connected as source
                is_source = any(e.get("source") == node_id for e in edges)
                if not is_source:
                    errors.append(f"Orphan node detected: {node_id}")
        
        # Check trigger configuration
        trigger = workflow.get("trigger", {})
        trigger_type = trigger.get("type")
        
        if trigger_type == "event" and not trigger.get("event"):
            errors.append("Event trigger must specify an event")
        
        if trigger_type == "schedule" and not trigger.get("cron") and not trigger.get("interval_seconds"):
            errors.append("Schedule trigger must have cron or interval")
        
        return errors
```

---

## File 6: Workflows Init
**Path:** `backend/app/workflows/__init__.py`

```python
"""
Workflows Module
Workflow automation engine and components
"""

from app.workflows.models import (
    Workflow,
    WorkflowNode,
    WorkflowEdge,
    WorkflowTrigger,
    WorkflowExecution,
    StepExecution,
    WorkflowStatus,
    ExecutionStatus,
    NodeType,
    TriggerType,
)
from app.workflows.engine import workflow_engine, WorkflowEngine
from app.workflows.variables import VariableResolver, ExpressionEvaluator
from app.workflows.conditions import ConditionBuilder, ConditionPresets, DateConditionHelper
from app.workflows.errors import (
    WorkflowError,
    ValidationError,
    ActionError,
    TimeoutError,
    RetryConfig,
    RetryHandler,
    ErrorRecovery,
    WorkflowValidator,
)


__all__ = [
    # Models
    'Workflow',
    'WorkflowNode',
    'WorkflowEdge',
    'WorkflowTrigger',
    'WorkflowExecution',
    'StepExecution',
    'WorkflowStatus',
    'ExecutionStatus',
    'NodeType',
    'TriggerType',
    
    # Engine
    'workflow_engine',
    'WorkflowEngine',
    
    # Variables
    'VariableResolver',
    'ExpressionEvaluator',
    
    # Conditions
    'ConditionBuilder',
    'ConditionPresets',
    'DateConditionHelper',
    
    # Errors
    'WorkflowError',
    'ValidationError',
    'ActionError',
    'TimeoutError',
    'RetryConfig',
    'RetryHandler',
    'ErrorRecovery',
    'WorkflowValidator',
]


def init_workflows():
    """Initialize workflow system."""
    from app.workflows.actions import register_default_actions
    from app.workflows.triggers import init_trigger_handlers
    
    # Register default actions
    register_default_actions(workflow_engine)
    
    # Initialize trigger handlers
    init_trigger_handlers()
    
    print("[Workflows] Workflow engine initialized")
```

---

## Summary Part 1

| File | Description | Lines |
|------|-------------|-------|
| `models.py` | Workflow data models | ~350 |
| `variables.py` | Variable resolution system | ~280 |
| `engine.py` | Workflow execution engine | ~320 |
| `conditions.py` | Condition builder & presets | ~280 |
| `errors.py` | Error handling & retry | ~280 |
| `__init__.py` | Module initialization | ~80 |
| **Total** | | **~1,590 lines** |
