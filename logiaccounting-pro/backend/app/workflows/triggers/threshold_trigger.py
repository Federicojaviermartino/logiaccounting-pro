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
