"""
Opportunity/Deal Management Service
Handles sales pipeline and deal lifecycle
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import uuid4

from app.models.crm_store import crm_store
from app.utils.datetime_utils import utc_now


class OpportunityService:
    """
    Service for managing sales opportunities/deals
    """

    def create_opportunity(
        self,
        tenant_id: str,
        name: str,
        pipeline_id: str = None,
        stage_id: str = None,
        amount: float = 0,
        currency: str = "USD",
        probability: int = None,
        expected_close_date: str = None,
        contact_id: str = None,
        company_id: str = None,
        owner_id: str = None,
        description: str = None,
        **kwargs
    ) -> dict:
        """Create a new opportunity"""
        opp_data = {
            "tenant_id": tenant_id,
            "name": name,
            "pipeline_id": pipeline_id or "default_pipeline",
            "stage_id": stage_id,
            "amount": amount,
            "currency": currency,
            "probability": probability,
            "expected_close_date": expected_close_date,
            "contact_id": contact_id,
            "company_id": company_id,
            "owner_id": owner_id,
            "description": description,
            **kwargs,
        }

        return crm_store.create_opportunity(opp_data)

    def update_opportunity(self, opp_id: str, user_id: str, **updates) -> dict:
        """Update opportunity"""
        return crm_store.update_opportunity(opp_id, updates)

    def get_opportunity(self, opp_id: str) -> dict:
        """Get opportunity with related data"""
        opp = crm_store.get_opportunity(opp_id)
        if not opp:
            return None

        # Get related entities
        if opp.get("contact_id"):
            opp["contact"] = crm_store.get_contact(opp["contact_id"])
        if opp.get("company_id"):
            opp["company"] = crm_store.get_company(opp["company_id"])

        # Get activities
        activities, _ = crm_store.list_activities(opportunity_id=opp_id, limit=20)
        opp["activities"] = activities

        # Get stage info
        if opp.get("stage_id"):
            stage = crm_store._stages.get(opp["stage_id"])
            opp["stage"] = stage

        return opp

    def delete_opportunity(self, opp_id: str, user_id: str):
        """Delete opportunity"""
        return crm_store.delete_opportunity(opp_id)

    def list_opportunities(
        self,
        tenant_id: str,
        pipeline_id: str = None,
        stage_id: str = None,
        status: str = None,
        owner_id: str = None,
        company_id: str = None,
        search: str = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """List opportunities with pagination"""
        skip = (page - 1) * page_size
        opps, total = crm_store.list_opportunities(
            tenant_id=tenant_id,
            pipeline_id=pipeline_id,
            stage_id=stage_id,
            status=status,
            owner_id=owner_id,
            company_id=company_id,
            search=search,
            skip=skip,
            limit=page_size,
        )

        return {
            "items": opps,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    def move_stage(self, opp_id: str, stage_id: str, user_id: str) -> dict:
        """Move opportunity to a new stage"""
        return crm_store.update_opportunity(opp_id, {"stage_id": stage_id})

    def win_opportunity(
        self,
        opp_id: str,
        user_id: str,
        actual_amount: float = None,
        notes: str = None,
    ) -> dict:
        """Mark opportunity as won"""
        opp = crm_store.get_opportunity(opp_id)
        if not opp:
            raise ValueError(f"Opportunity not found: {opp_id}")

        # Find won stage
        pipeline = crm_store.get_pipeline(opp["pipeline_id"])
        won_stage = next(
            (s for s in pipeline.get("stages", []) if s.get("is_won")),
            None
        )

        updates = {
            "status": "won",
            "actual_close_date": utc_now().isoformat(),
            "win_notes": notes,
        }

        if won_stage:
            updates["stage_id"] = won_stage["id"]
            updates["probability"] = 100

        if actual_amount is not None:
            updates["amount"] = actual_amount

        return crm_store.update_opportunity(opp_id, updates)

    def lose_opportunity(
        self,
        opp_id: str,
        user_id: str,
        lost_reason: str = None,
        competitor: str = None,
        notes: str = None,
    ) -> dict:
        """Mark opportunity as lost"""
        opp = crm_store.get_opportunity(opp_id)
        if not opp:
            raise ValueError(f"Opportunity not found: {opp_id}")

        # Find lost stage
        pipeline = crm_store.get_pipeline(opp["pipeline_id"])
        lost_stage = next(
            (s for s in pipeline.get("stages", []) if s.get("is_lost")),
            None
        )

        updates = {
            "status": "lost",
            "actual_close_date": utc_now().isoformat(),
            "lost_reason": lost_reason,
            "competitor": competitor,
            "loss_notes": notes,
        }

        if lost_stage:
            updates["stage_id"] = lost_stage["id"]
            updates["probability"] = 0

        return crm_store.update_opportunity(opp_id, updates)

    def reopen_opportunity(self, opp_id: str, user_id: str) -> dict:
        """Reopen a closed opportunity"""
        opp = crm_store.get_opportunity(opp_id)
        if not opp:
            raise ValueError(f"Opportunity not found: {opp_id}")

        # Move to first stage
        pipeline = crm_store.get_pipeline(opp["pipeline_id"])
        first_stage = next(
            (s for s in pipeline.get("stages", []) if s.get("position") == 1),
            None
        )

        updates = {
            "status": "open",
            "actual_close_date": None,
            "lost_reason": None,
            "competitor": None,
        }

        if first_stage:
            updates["stage_id"] = first_stage["id"]
            updates["probability"] = first_stage.get("probability", 10)

        return crm_store.update_opportunity(opp_id, updates)

    def get_pipeline_board(self, tenant_id: str, pipeline_id: str = None) -> dict:
        """Get Kanban board data for pipeline"""
        if not pipeline_id:
            pipeline_id = "default_pipeline"

        pipeline = crm_store.get_pipeline(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline not found: {pipeline_id}")

        opps, _ = crm_store.list_opportunities(
            tenant_id=tenant_id,
            pipeline_id=pipeline_id,
            status="open",
            limit=1000,
        )

        # Group by stage
        board = {
            "pipeline": {
                "id": pipeline["id"],
                "name": pipeline["name"],
            },
            "stages": [],
            "totals": {
                "count": len(opps),
                "value": sum(o.get("amount", 0) for o in opps),
                "weighted_value": sum(
                    o.get("amount", 0) * (o.get("probability", 0) / 100)
                    for o in opps
                ),
            }
        }

        for stage in pipeline.get("stages", []):
            if stage.get("is_lost"):
                continue  # Don't show lost stage in board

            stage_opps = [o for o in opps if o.get("stage_id") == stage["id"]]

            # Enrich opportunities with contact/company names
            for opp in stage_opps:
                if opp.get("contact_id"):
                    contact = crm_store.get_contact(opp["contact_id"])
                    if contact:
                        opp["contact_name"] = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
                if opp.get("company_id"):
                    company = crm_store.get_company(opp["company_id"])
                    if company:
                        opp["company_name"] = company.get("name")

            board["stages"].append({
                "id": stage["id"],
                "name": stage["name"],
                "color": stage.get("color"),
                "probability": stage.get("probability"),
                "is_won": stage.get("is_won", False),
                "opportunities": sorted(
                    stage_opps,
                    key=lambda x: x.get("expected_close_date") or "9999",
                ),
                "count": len(stage_opps),
                "value": sum(o.get("amount", 0) for o in stage_opps),
            })

        return board

    def get_forecast(
        self,
        tenant_id: str,
        pipeline_id: str = None,
        days: int = 90,
    ) -> dict:
        """Get sales forecast for next N days"""
        opps, _ = crm_store.list_opportunities(
            tenant_id=tenant_id,
            pipeline_id=pipeline_id,
            status="open",
            limit=1000,
        )

        today = utc_now().date()
        end_date = today + timedelta(days=days)

        # Filter by expected close date
        forecast_opps = [
            o for o in opps
            if o.get("expected_close_date") and
            today.isoformat() <= o["expected_close_date"] <= end_date.isoformat()
        ]

        # Group by period (monthly)
        periods = {}
        for opp in forecast_opps:
            close_date = datetime.fromisoformat(opp["expected_close_date"])
            period_key = close_date.strftime("%Y-%m")

            if period_key not in periods:
                periods[period_key] = {
                    "period": period_key,
                    "label": close_date.strftime("%B %Y"),
                    "count": 0,
                    "value": 0,
                    "weighted_value": 0,
                }

            periods[period_key]["count"] += 1
            periods[period_key]["value"] += opp.get("amount", 0)
            periods[period_key]["weighted_value"] += (
                opp.get("amount", 0) * (opp.get("probability", 0) / 100)
            )

        return {
            "total_pipeline": sum(o.get("amount", 0) for o in forecast_opps),
            "weighted_forecast": sum(
                o.get("amount", 0) * (o.get("probability", 0) / 100)
                for o in forecast_opps
            ),
            "deal_count": len(forecast_opps),
            "periods": sorted(periods.values(), key=lambda x: x["period"]),
        }

    def get_win_loss_analysis(self, tenant_id: str, days: int = 90) -> dict:
        """Analyze win/loss rates"""
        opps, _ = crm_store.list_opportunities(tenant_id=tenant_id, limit=1000)

        cutoff = (utc_now() - timedelta(days=days)).isoformat()
        recent_opps = [
            o for o in opps
            if o.get("actual_close_date") and o["actual_close_date"] >= cutoff
        ]

        won = [o for o in recent_opps if o.get("status") == "won"]
        lost = [o for o in recent_opps if o.get("status") == "lost"]

        # Lost reasons analysis
        lost_reasons = {}
        for opp in lost:
            reason = opp.get("lost_reason", "Unknown")
            if reason not in lost_reasons:
                lost_reasons[reason] = {"reason": reason, "count": 0, "value": 0}
            lost_reasons[reason]["count"] += 1
            lost_reasons[reason]["value"] += opp.get("amount", 0)

        # Competitor analysis
        competitors = {}
        for opp in lost:
            comp = opp.get("competitor")
            if comp:
                if comp not in competitors:
                    competitors[comp] = {"competitor": comp, "count": 0, "value": 0}
                competitors[comp]["count"] += 1
                competitors[comp]["value"] += opp.get("amount", 0)

        total_closed = len(won) + len(lost)

        return {
            "period_days": days,
            "total_closed": total_closed,
            "won_count": len(won),
            "lost_count": len(lost),
            "won_value": sum(o.get("amount", 0) for o in won),
            "lost_value": sum(o.get("amount", 0) for o in lost),
            "win_rate": (len(won) / total_closed * 100) if total_closed > 0 else 0,
            "lost_reasons": sorted(
                lost_reasons.values(),
                key=lambda x: x["count"],
                reverse=True
            ),
            "competitors": sorted(
                competitors.values(),
                key=lambda x: x["count"],
                reverse=True
            ),
        }


# Service instance
opportunity_service = OpportunityService()
