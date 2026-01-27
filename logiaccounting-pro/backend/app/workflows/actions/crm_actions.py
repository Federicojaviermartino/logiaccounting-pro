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
