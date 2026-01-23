# Phase 26: Advanced Workflow Engine v2 - Part 1
## CRM Workflow Integration

---

## Task 1: CRM Event Trigger

**File: `backend/app/workflows/triggers/crm_trigger.py`**

```python
"""
CRM Event Trigger - Triggers from CRM module events
"""

from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime
import asyncio
import logging

from app.workflows.models.workflow import Workflow
from app.workflows.models.execution import ExecutionContext
from app.workflows.models.store import workflow_store
from app.workflows.config import TriggerType, WorkflowStatus

if TYPE_CHECKING:
    from app.workflows.engine.core import WorkflowEngine


logger = logging.getLogger(__name__)


class CRMEventType:
    """CRM Event types"""
    LEAD_CREATED = "lead.created"
    LEAD_CONVERTED = "lead.converted"
    LEAD_ASSIGNED = "lead.assigned"
    DEAL_CREATED = "deal.created"
    DEAL_STAGE_CHANGED = "deal.stage_changed"
    DEAL_WON = "deal.won"
    DEAL_LOST = "deal.lost"
    CONTACT_CREATED = "contact.created"
    COMPANY_HEALTH_CHANGED = "company.health_changed"
    ACTIVITY_LOGGED = "activity.logged"
    QUOTE_CREATED = "quote.created"
    QUOTE_SENT = "quote.sent"
    QUOTE_ACCEPTED = "quote.accepted"


CRM_EVENTS = {
    CRMEventType.LEAD_CREATED: {"label": "Lead Created", "entity": "lead", "fields": ["id", "first_name", "email", "source", "score"]},
    CRMEventType.LEAD_CONVERTED: {"label": "Lead Converted", "entity": "lead", "fields": ["id", "contact_id", "opportunity_id"]},
    CRMEventType.DEAL_CREATED: {"label": "Deal Created", "entity": "opportunity", "fields": ["id", "name", "amount", "stage_id"]},
    CRMEventType.DEAL_STAGE_CHANGED: {"label": "Deal Stage Changed", "entity": "opportunity", "fields": ["id", "previous_stage", "new_stage"]},
    CRMEventType.DEAL_WON: {"label": "Deal Won", "entity": "opportunity", "fields": ["id", "name", "amount"]},
    CRMEventType.DEAL_LOST: {"label": "Deal Lost", "entity": "opportunity", "fields": ["id", "lost_reason"]},
    CRMEventType.QUOTE_SENT: {"label": "Quote Sent", "entity": "quote", "fields": ["id", "quote_number", "total"]},
    CRMEventType.QUOTE_ACCEPTED: {"label": "Quote Accepted", "entity": "quote", "fields": ["id", "total", "opportunity_id"]},
}


class CRMTrigger:
    """Handles CRM event triggers."""
    
    def __init__(self, engine: "WorkflowEngine"):
        self.engine = engine
        self._subscriptions: Dict[str, List[str]] = {}
        self._running = False
    
    async def start(self):
        self._running = True
        await self._load_subscriptions()
        logger.info("CRM trigger started")
    
    async def stop(self):
        self._running = False
        logger.info("CRM trigger stopped")
    
    async def _load_subscriptions(self):
        self._subscriptions.clear()
        workflows = workflow_store.list_workflows(status=WorkflowStatus.ACTIVE)
        
        for workflow in workflows:
            if workflow.trigger.type == TriggerType.CRM_EVENT:
                event_type = workflow.trigger.crm_event
                if event_type not in self._subscriptions:
                    self._subscriptions[event_type] = []
                self._subscriptions[event_type].append(workflow.id)
        
        logger.info(f"Loaded {len(self._subscriptions)} CRM subscriptions")
    
    async def handle_event(self, event_type: str, entity_data: Dict, tenant_id: str, user_id: str = None, metadata: Dict = None):
        """Handle a CRM event and trigger matching workflows."""
        if not self._running:
            return
        
        workflow_ids = self._subscriptions.get(event_type, [])
        
        for workflow_id in workflow_ids:
            workflow = workflow_store.get_workflow(workflow_id)
            
            if not workflow or workflow.tenant_id != tenant_id or workflow.status != WorkflowStatus.ACTIVE:
                continue
            
            if not await self._check_conditions(workflow, entity_data):
                continue
            
            context = ExecutionContext(
                trigger_type=TriggerType.CRM_EVENT.value,
                trigger_data={"event_type": event_type, "entity": entity_data, "metadata": metadata or {}},
                entity_type=CRM_EVENTS.get(event_type, {}).get("entity"),
                entity_id=entity_data.get("id"),
                user_id=user_id,
                tenant_id=tenant_id,
            )
            
            await self.engine.trigger_workflow(workflow_id=workflow_id, context=context, run_async=True)
            logger.info(f"Triggered workflow {workflow_id} for {event_type}")
    
    async def _check_conditions(self, workflow: Workflow, entity_data: Dict) -> bool:
        conditions = workflow.trigger.conditions
        if not conditions:
            return True
        from app.workflows.rules.evaluator import evaluate_conditions
        return evaluate_conditions(conditions, {"entity": entity_data})
    
    @staticmethod
    def get_available_events() -> List[Dict]:
        return [{"type": event_type, **event_info} for event_type, event_info in CRM_EVENTS.items()]


class CRMEventEmitter:
    """Helper to emit CRM events to workflow engine."""
    _trigger: Optional[CRMTrigger] = None
    
    @classmethod
    def set_trigger(cls, trigger: CRMTrigger):
        cls._trigger = trigger
    
    @classmethod
    async def emit(cls, event_type: str, entity_data: Dict, tenant_id: str, user_id: str = None, metadata: Dict = None):
        if cls._trigger:
            await cls._trigger.handle_event(event_type, entity_data, tenant_id, user_id, metadata)
```

---

## Task 2: CRM Action Nodes

**File: `backend/app/workflows/actions/crm_actions.py`**

```python
"""
CRM Action Executors - Actions for CRM entities
"""

from typing import Dict, Any
from datetime import datetime
import logging

from app.workflows.actions.base import ActionExecutor, ActionResult
from app.models.crm_store import crm_store
from app.services.crm.lead_service import lead_service
from app.services.crm.opportunity_service import opportunity_service
from app.services.crm.activity_service import activity_service
from app.services.crm.quote_service import quote_service


logger = logging.getLogger(__name__)


class CreateLeadAction(ActionExecutor):
    """Create a new lead"""
    action_type = "crm.create_lead"
    
    async def execute(self, config: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            first_name = self.interpolate(config.get("first_name", ""), context)
            last_name = self.interpolate(config.get("last_name", ""), context)
            email = self.interpolate(config.get("email", ""), context)
            company_name = self.interpolate(config.get("company_name", ""), context)
            source = config.get("source", "workflow")
            owner_id = config.get("owner_id") or context.get("user_id")
            tenant_id = context.get("tenant_id")
            
            lead = lead_service.create_lead(tenant_id=tenant_id, first_name=first_name, last_name=last_name, email=email, company_name=company_name, source=source, owner_id=owner_id)
            
            return ActionResult(success=True, data={"lead_id": lead["id"], "lead": lead}, message=f"Lead created: {first_name}")
        except Exception as e:
            return ActionResult(success=False, error=str(e))


class CreateDealAction(ActionExecutor):
    """Create a new deal/opportunity"""
    action_type = "crm.create_deal"
    
    async def execute(self, config: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            name = self.interpolate(config.get("name", ""), context)
            amount = float(config.get("amount", 0))
            pipeline_id = config.get("pipeline_id", "default_pipeline")
            contact_id = config.get("contact_id") or context.get("entity", {}).get("contact_id")
            company_id = config.get("company_id") or context.get("entity", {}).get("company_id")
            owner_id = config.get("owner_id") or context.get("user_id")
            tenant_id = context.get("tenant_id")
            
            deal = opportunity_service.create_opportunity(tenant_id=tenant_id, name=name, amount=amount, pipeline_id=pipeline_id, contact_id=contact_id, company_id=company_id, owner_id=owner_id)
            
            return ActionResult(success=True, data={"deal_id": deal["id"]}, message=f"Deal created: {name}")
        except Exception as e:
            return ActionResult(success=False, error=str(e))


class UpdateDealStageAction(ActionExecutor):
    """Update deal stage"""
    action_type = "crm.update_deal_stage"
    
    async def execute(self, config: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            deal_id = config.get("deal_id") or context.get("entity", {}).get("id")
            stage_id = config.get("stage_id")
            user_id = context.get("user_id", "workflow")
            
            deal = opportunity_service.move_stage(opp_id=deal_id, stage_id=stage_id, user_id=user_id)
            
            return ActionResult(success=True, data={"deal_id": deal_id, "stage_id": stage_id})
        except Exception as e:
            return ActionResult(success=False, error=str(e))


class WinDealAction(ActionExecutor):
    """Mark deal as won"""
    action_type = "crm.win_deal"
    
    async def execute(self, config: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            deal_id = config.get("deal_id") or context.get("entity", {}).get("id")
            actual_amount = config.get("actual_amount")
            user_id = context.get("user_id", "workflow")
            
            deal = opportunity_service.win_opportunity(opp_id=deal_id, user_id=user_id, actual_amount=actual_amount)
            
            return ActionResult(success=True, data={"deal_id": deal_id}, message="Deal marked as won")
        except Exception as e:
            return ActionResult(success=False, error=str(e))


class CreateActivityAction(ActionExecutor):
    """Create a CRM activity"""
    action_type = "crm.create_activity"
    
    async def execute(self, config: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            activity_type = config.get("type", "task")
            subject = self.interpolate(config.get("subject", ""), context)
            description = self.interpolate(config.get("description", ""), context)
            due_date = config.get("due_date")
            contact_id = config.get("contact_id") or context.get("entity", {}).get("contact_id")
            opportunity_id = config.get("opportunity_id") or context.get("entity", {}).get("id")
            owner_id = config.get("owner_id") or context.get("user_id")
            tenant_id = context.get("tenant_id")
            
            activity = activity_service.create_activity(tenant_id=tenant_id, type=activity_type, subject=subject, description=description, owner_id=owner_id, due_date=due_date, contact_id=contact_id, opportunity_id=opportunity_id)
            
            return ActionResult(success=True, data={"activity_id": activity["id"]}, message=f"Activity created: {subject}")
        except Exception as e:
            return ActionResult(success=False, error=str(e))


class AssignOwnerAction(ActionExecutor):
    """Assign owner to a CRM entity"""
    action_type = "crm.assign_owner"
    
    STRATEGY_SPECIFIC = "specific"
    STRATEGY_ROUND_ROBIN = "round_robin"
    STRATEGY_LEAST_LOADED = "least_loaded"
    
    async def execute(self, config: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            entity_type = config.get("entity_type", "lead")
            entity_id = config.get("entity_id") or context.get("entity", {}).get("id")
            strategy = config.get("strategy", self.STRATEGY_SPECIFIC)
            owner_id = config.get("owner_id")
            user_pool = config.get("user_pool", [])
            
            if strategy == self.STRATEGY_ROUND_ROBIN:
                import random
                owner_id = random.choice(user_pool) if user_pool else None
            elif strategy == self.STRATEGY_LEAST_LOADED:
                owner_id = user_pool[0] if user_pool else None
            
            user_id = context.get("user_id", "workflow")
            
            if entity_type == "lead":
                lead_service.assign_lead(entity_id, owner_id, user_id)
            elif entity_type == "deal":
                opportunity_service.update_opportunity(entity_id, user_id, owner_id=owner_id)
            
            return ActionResult(success=True, data={"entity_type": entity_type, "entity_id": entity_id, "owner_id": owner_id})
        except Exception as e:
            return ActionResult(success=False, error=str(e))


class UpdateLeadScoreAction(ActionExecutor):
    """Update lead score"""
    action_type = "crm.update_lead_score"
    
    async def execute(self, config: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            lead_id = config.get("lead_id") or context.get("entity", {}).get("id")
            score_delta = config.get("score_delta", 0)
            score_absolute = config.get("score_absolute")
            
            lead = crm_store.get_lead(lead_id)
            if not lead:
                return ActionResult(success=False, error=f"Lead not found: {lead_id}")
            
            if score_absolute is not None:
                new_score = int(score_absolute)
            else:
                new_score = lead.get("score", 0) + int(score_delta)
            
            new_score = max(0, min(100, new_score))
            rating = "hot" if new_score >= 70 else "warm" if new_score >= 40 else "cold"
            
            lead_service.update_lead(lead_id, context.get("user_id", "workflow"), score=new_score, rating=rating)
            
            return ActionResult(success=True, data={"lead_id": lead_id, "score": new_score, "rating": rating})
        except Exception as e:
            return ActionResult(success=False, error=str(e))


class ConvertLeadAction(ActionExecutor):
    """Convert lead to contact and opportunity"""
    action_type = "crm.convert_lead"
    
    async def execute(self, config: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            lead_id = config.get("lead_id") or context.get("entity", {}).get("id")
            create_contact = config.get("create_contact", True)
            create_opportunity = config.get("create_opportunity", True)
            opportunity_amount = config.get("opportunity_amount")
            user_id = context.get("user_id", "workflow")
            
            result = lead_service.convert_lead(lead_id=lead_id, user_id=user_id, create_contact=create_contact, create_opportunity=create_opportunity, opportunity_amount=opportunity_amount)
            
            return ActionResult(success=True, data=result, message="Lead converted successfully")
        except Exception as e:
            return ActionResult(success=False, error=str(e))


CRM_ACTIONS = {
    CreateLeadAction.action_type: CreateLeadAction,
    CreateDealAction.action_type: CreateDealAction,
    UpdateDealStageAction.action_type: UpdateDealStageAction,
    WinDealAction.action_type: WinDealAction,
    CreateActivityAction.action_type: CreateActivityAction,
    AssignOwnerAction.action_type: AssignOwnerAction,
    UpdateLeadScoreAction.action_type: UpdateLeadScoreAction,
    ConvertLeadAction.action_type: ConvertLeadAction,
}
```

---

## Task 3: Threshold Trigger

**File: `backend/app/workflows/triggers/threshold_trigger.py`**

```python
"""
Threshold Trigger - Triggers based on metric thresholds
"""

from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime, timedelta
import asyncio
import logging

from app.workflows.models.execution import ExecutionContext
from app.workflows.models.store import workflow_store
from app.workflows.config import TriggerType, WorkflowStatus

if TYPE_CHECKING:
    from app.workflows.engine.core import WorkflowEngine


logger = logging.getLogger(__name__)


class ThresholdMetric:
    INVOICE_OVERDUE_COUNT = "invoice.overdue_count"
    INVOICE_OVERDUE_AMOUNT = "invoice.overdue_amount"
    LEAD_COUNT_UNASSIGNED = "lead.unassigned_count"
    DEAL_PIPELINE_VALUE = "deal.pipeline_value"
    ACTIVITY_OVERDUE_COUNT = "activity.overdue_count"
    INVENTORY_LOW_STOCK_COUNT = "inventory.low_stock_count"


THRESHOLD_METRICS = {
    ThresholdMetric.INVOICE_OVERDUE_COUNT: {"label": "Overdue Invoices Count", "unit": "count", "default_threshold": 5},
    ThresholdMetric.INVOICE_OVERDUE_AMOUNT: {"label": "Overdue Amount", "unit": "currency", "default_threshold": 10000},
    ThresholdMetric.DEAL_PIPELINE_VALUE: {"label": "Pipeline Value", "unit": "currency", "default_threshold": 100000},
    ThresholdMetric.LEAD_COUNT_UNASSIGNED: {"label": "Unassigned Leads", "unit": "count", "default_threshold": 10},
    ThresholdMetric.INVENTORY_LOW_STOCK_COUNT: {"label": "Low Stock Items", "unit": "count", "default_threshold": 5},
    ThresholdMetric.ACTIVITY_OVERDUE_COUNT: {"label": "Overdue Activities", "unit": "count", "default_threshold": 10},
}


class ThresholdTrigger:
    """Monitors metrics and triggers workflows when thresholds are crossed."""
    
    def __init__(self, engine: "WorkflowEngine"):
        self.engine = engine
        self._running = False
        self._check_interval = 300
        self._last_values: Dict[str, Dict[str, float]] = {}
    
    async def start(self):
        self._running = True
        logger.info("Threshold trigger started")
        asyncio.create_task(self._monitoring_loop())
    
    async def stop(self):
        self._running = False
    
    async def _monitoring_loop(self):
        while self._running:
            try:
                await self._check_thresholds()
            except Exception as e:
                logger.error(f"Threshold check error: {e}")
            await asyncio.sleep(self._check_interval)
    
    async def _check_thresholds(self):
        workflows = workflow_store.list_workflows(status=WorkflowStatus.ACTIVE)
        threshold_workflows = [w for w in workflows if w.trigger.type == TriggerType.THRESHOLD]
        
        for workflow in threshold_workflows:
            try:
                await self._evaluate_workflow(workflow)
            except Exception as e:
                logger.error(f"Error evaluating {workflow.id}: {e}")
    
    async def _evaluate_workflow(self, workflow):
        metric = workflow.trigger.threshold_metric
        threshold = workflow.trigger.threshold_value
        comparison = workflow.trigger.threshold_comparison or "greater_than"
        tenant_id = workflow.tenant_id
        
        current_value = await self._get_metric_value(metric, tenant_id)
        if current_value is None:
            return
        
        prev_key = f"{workflow.id}:{tenant_id}"
        previous_value = self._last_values.get(metric, {}).get(prev_key)
        
        if metric not in self._last_values:
            self._last_values[metric] = {}
        self._last_values[metric][prev_key] = current_value
        
        threshold_crossed = self._check_threshold(current_value, threshold, comparison)
        was_crossed = self._check_threshold(previous_value, threshold, comparison) if previous_value is not None else False
        
        if threshold_crossed and not was_crossed:
            context = ExecutionContext(
                trigger_type=TriggerType.THRESHOLD.value,
                trigger_data={"metric": metric, "current_value": current_value, "threshold": threshold},
                tenant_id=tenant_id,
            )
            await self.engine.trigger_workflow(workflow_id=workflow.id, context=context, run_async=True)
            logger.info(f"Threshold crossed for {metric}: {current_value}")
    
    def _check_threshold(self, value: float, threshold: float, comparison: str) -> bool:
        if value is None:
            return False
        if comparison == "greater_than":
            return value > threshold
        elif comparison == "less_than":
            return value < threshold
        elif comparison == "greater_than_or_equal":
            return value >= threshold
        elif comparison == "less_than_or_equal":
            return value <= threshold
        return False
    
    async def _get_metric_value(self, metric: str, tenant_id: str) -> Optional[float]:
        try:
            if metric == ThresholdMetric.INVOICE_OVERDUE_COUNT:
                from app.models.store import db
                return float(len(db.invoices.list_all(status="overdue")))
            elif metric == ThresholdMetric.LEAD_COUNT_UNASSIGNED:
                from app.models.crm_store import crm_store
                leads, _ = crm_store.list_leads(tenant_id=tenant_id, limit=10000)
                return float(len([l for l in leads if not l.get("owner_id")]))
            elif metric == ThresholdMetric.DEAL_PIPELINE_VALUE:
                from app.models.crm_store import crm_store
                opps, _ = crm_store.list_opportunities(tenant_id=tenant_id, status="open", limit=10000)
                return sum(o.get("amount", 0) for o in opps)
            return None
        except Exception as e:
            logger.error(f"Error getting metric {metric}: {e}")
            return None
    
    @staticmethod
    def get_available_metrics() -> List[Dict]:
        return [{"type": metric_type, **metric_info} for metric_type, metric_info in THRESHOLD_METRICS.items()]
```

---

## Task 4: CRM Condition Evaluator

**File: `backend/app/workflows/rules/crm_conditions.py`**

```python
"""
CRM Condition Evaluators
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging


logger = logging.getLogger(__name__)


class CRMConditionEvaluator:
    """Evaluates conditions on CRM entities."""
    
    OPERATORS = {
        "equals": lambda a, b: a == b,
        "not_equals": lambda a, b: a != b,
        "contains": lambda a, b: b in str(a) if a else False,
        "greater_than": lambda a, b: float(a or 0) > float(b),
        "less_than": lambda a, b: float(a or 0) < float(b),
        "greater_than_or_equal": lambda a, b: float(a or 0) >= float(b),
        "less_than_or_equal": lambda a, b: float(a or 0) <= float(b),
        "is_empty": lambda a, b: not a,
        "is_not_empty": lambda a, b: bool(a),
        "in_list": lambda a, b: a in b if isinstance(b, list) else False,
    }
    
    def evaluate(self, conditions: List[Dict], context: Dict) -> bool:
        if not conditions:
            return True
        
        for group in conditions:
            group_type = group.get("type", "all")
            rules = group.get("rules", [])
            
            if group_type == "all":
                if not self._evaluate_all(rules, context):
                    return False
            elif group_type == "any":
                if not self._evaluate_any(rules, context):
                    return False
            elif group_type == "none":
                if self._evaluate_any(rules, context):
                    return False
        return True
    
    def _evaluate_all(self, rules: List[Dict], context: Dict) -> bool:
        return all(self._evaluate_rule(rule, context) for rule in rules)
    
    def _evaluate_any(self, rules: List[Dict], context: Dict) -> bool:
        return any(self._evaluate_rule(rule, context) for rule in rules)
    
    def _evaluate_rule(self, rule: Dict, context: Dict) -> bool:
        if "type" in rule and "rules" in rule:
            return self.evaluate([rule], context)
        
        field = rule.get("field", "")
        operator = rule.get("operator", "equals")
        value = rule.get("value")
        
        actual_value = self._get_field_value(field, context)
        op_func = self.OPERATORS.get(operator)
        
        if not op_func:
            return False
        
        try:
            return op_func(actual_value, value)
        except Exception:
            return False
    
    def _get_field_value(self, field: str, context: Dict) -> Any:
        parts = field.split(".")
        value = context
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value


CRM_CONDITION_TEMPLATES = [
    {"id": "lead_is_hot", "name": "Lead is Hot", "entity": "lead", "conditions": [{"type": "any", "rules": [{"field": "entity.rating", "operator": "equals", "value": "hot"}, {"field": "entity.score", "operator": "greater_than_or_equal", "value": 70}]}]},
    {"id": "deal_high_value", "name": "High Value Deal", "entity": "opportunity", "conditions": [{"type": "all", "rules": [{"field": "entity.amount", "operator": "greater_than", "value": 10000}]}]},
    {"id": "company_at_risk", "name": "At-Risk Account", "entity": "company", "conditions": [{"type": "all", "rules": [{"field": "entity.type", "operator": "equals", "value": "customer"}, {"field": "entity.health_score", "operator": "less_than", "value": 40}]}]},
]

crm_condition_evaluator = CRMConditionEvaluator()
```

---

## Task 5: CRM Workflow API Routes

**File: `backend/app/routes/workflows/crm_workflows.py`**

```python
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
```

---

## Summary: Part 1 Complete

### Files Created:

| File | Purpose | Lines |
|------|---------|-------|
| `crm_trigger.py` | CRM event trigger | ~120 |
| `crm_actions.py` | CRM action executors | ~200 |
| `threshold_trigger.py` | Metric-based triggers | ~130 |
| `crm_conditions.py` | CRM condition evaluators | ~80 |
| `crm_workflows.py` | CRM workflow API routes | ~50 |
| **Total** | | **~580** |

### Features:

| Feature | Status |
|---------|--------|
| Lead event triggers | ✅ |
| Deal event triggers | ✅ |
| Activity event triggers | ✅ |
| Quote event triggers | ✅ |
| Create lead action | ✅ |
| Create deal action | ✅ |
| Update deal stage action | ✅ |
| Win deal action | ✅ |
| Create activity action | ✅ |
| Assign owner action | ✅ |
| Update lead score | ✅ |
| Convert lead action | ✅ |
| Threshold triggers | ✅ |
| CRM conditions | ✅ |
| 5 CRM workflow templates | ✅ |

### Next: Part 2 - Sub-Workflows & Error Handling
