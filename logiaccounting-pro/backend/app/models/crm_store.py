"""
CRM Data Store
In-memory storage for CRM entities
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import uuid4
from app.utils.datetime_utils import utc_now


class CRMStore:
    """
    Central data store for CRM module.
    Manages leads, contacts, companies, opportunities, activities.
    """

    def __init__(self):
        self._leads = {}
        self._contacts = {}
        self._companies = {}
        self._opportunities = {}
        self._activities = {}
        self._pipelines = {}
        self._stages = {}
        self._quotes = {}
        self._quote_items = {}
        self._email_templates = {}
        self._workflows = {}

        self._init_default_pipeline()

    def _init_default_pipeline(self):
        """Create default sales pipeline"""
        pipeline_id = "default_pipeline"
        self._pipelines[pipeline_id] = {
            "id": pipeline_id,
            "name": "Sales Pipeline",
            "is_default": True,
            "created_at": utc_now().isoformat(),
        }

        default_stages = [
            {"name": "Qualification", "probability": 10, "position": 1, "color": "#667eea"},
            {"name": "Meeting", "probability": 25, "position": 2, "color": "#06b6d4"},
            {"name": "Proposal", "probability": 50, "position": 3, "color": "#f59e0b"},
            {"name": "Negotiation", "probability": 75, "position": 4, "color": "#8b5cf6"},
            {"name": "Closed Won", "probability": 100, "position": 5, "color": "#10b981", "is_won": True},
            {"name": "Closed Lost", "probability": 0, "position": 6, "color": "#ef4444", "is_lost": True},
        ]

        for stage_data in default_stages:
            stage_id = str(uuid4())
            self._stages[stage_id] = {
                "id": stage_id,
                "pipeline_id": pipeline_id,
                **stage_data,
                "is_won": stage_data.get("is_won", False),
                "is_lost": stage_data.get("is_lost", False),
            }

    # ==========================================
    # LEADS
    # ==========================================

    def create_lead(self, data: dict) -> dict:
        """Create a new lead"""
        lead_id = str(uuid4())
        lead = {
            "id": lead_id,
            "status": "new",
            "score": 0,
            "rating": "cold",
            "created_at": utc_now().isoformat(),
            "updated_at": utc_now().isoformat(),
            **data,
        }
        self._leads[lead_id] = lead
        return lead

    def get_lead(self, lead_id: str) -> Optional[dict]:
        """Get lead by ID"""
        return self._leads.get(lead_id)

    def update_lead(self, lead_id: str, updates: dict) -> Optional[dict]:
        """Update lead"""
        if lead_id not in self._leads:
            return None
        updates["updated_at"] = utc_now().isoformat()
        self._leads[lead_id].update(updates)
        return self._leads[lead_id]

    def delete_lead(self, lead_id: str) -> bool:
        """Delete lead"""
        if lead_id in self._leads:
            del self._leads[lead_id]
            return True
        return False

    def list_leads(
        self,
        tenant_id: str = None,
        status: str = None,
        source: str = None,
        owner_id: str = None,
        search: str = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple:
        """List leads with filters"""
        leads = list(self._leads.values())

        if tenant_id:
            leads = [l for l in leads if l.get("tenant_id") == tenant_id]
        if status:
            leads = [l for l in leads if l.get("status") == status]
        if source:
            leads = [l for l in leads if l.get("source") == source]
        if owner_id:
            leads = [l for l in leads if l.get("owner_id") == owner_id]
        if search:
            search_lower = search.lower()
            leads = [
                l for l in leads
                if search_lower in l.get("first_name", "").lower()
                or search_lower in l.get("last_name", "").lower()
                or search_lower in l.get("email", "").lower()
                or search_lower in l.get("company_name", "").lower()
            ]

        total = len(leads)
        leads = sorted(leads, key=lambda x: x.get("created_at", ""), reverse=True)
        leads = leads[skip:skip + limit]

        return leads, total

    def convert_lead(
        self,
        lead_id: str,
        create_contact: bool = True,
        create_opportunity: bool = True,
        opportunity_data: dict = None,
    ) -> dict:
        """Convert lead to contact and/or opportunity"""
        lead = self.get_lead(lead_id)
        if not lead:
            raise ValueError(f"Lead not found: {lead_id}")

        result = {"lead_id": lead_id}

        if create_contact:
            contact = self.create_contact({
                "tenant_id": lead.get("tenant_id"),
                "first_name": lead.get("first_name"),
                "last_name": lead.get("last_name"),
                "email": lead.get("email"),
                "phone": lead.get("phone"),
                "job_title": lead.get("job_title"),
                "owner_id": lead.get("owner_id"),
                "lead_source": lead.get("source"),
            })
            result["contact_id"] = contact["id"]

            if lead.get("company_name"):
                company = self.create_company({
                    "tenant_id": lead.get("tenant_id"),
                    "name": lead.get("company_name"),
                    "owner_id": lead.get("owner_id"),
                })
                result["company_id"] = company["id"]

                self.update_contact(contact["id"], {"company_id": company["id"]})

        if create_opportunity:
            opp_data = {
                "tenant_id": lead.get("tenant_id"),
                "name": f"Deal with {lead.get('company_name') or lead.get('first_name')}",
                "contact_id": result.get("contact_id"),
                "company_id": result.get("company_id"),
                "owner_id": lead.get("owner_id"),
                **(opportunity_data or {}),
            }
            opportunity = self.create_opportunity(opp_data)
            result["opportunity_id"] = opportunity["id"]

        self.update_lead(lead_id, {
            "status": "converted",
            "converted_at": utc_now().isoformat(),
            "converted_contact_id": result.get("contact_id"),
            "converted_opportunity_id": result.get("opportunity_id"),
        })

        return result

    # ==========================================
    # CONTACTS
    # ==========================================

    def create_contact(self, data: dict) -> dict:
        """Create a new contact"""
        contact_id = str(uuid4())
        contact = {
            "id": contact_id,
            "do_not_call": False,
            "do_not_email": False,
            "created_at": utc_now().isoformat(),
            "updated_at": utc_now().isoformat(),
            **data,
        }
        self._contacts[contact_id] = contact
        return contact

    def get_contact(self, contact_id: str) -> Optional[dict]:
        """Get contact by ID"""
        return self._contacts.get(contact_id)

    def update_contact(self, contact_id: str, updates: dict) -> Optional[dict]:
        """Update contact"""
        if contact_id not in self._contacts:
            return None
        updates["updated_at"] = utc_now().isoformat()
        self._contacts[contact_id].update(updates)
        return self._contacts[contact_id]

    def delete_contact(self, contact_id: str) -> bool:
        """Delete contact"""
        if contact_id in self._contacts:
            del self._contacts[contact_id]
            return True
        return False

    def list_contacts(
        self,
        tenant_id: str = None,
        company_id: str = None,
        owner_id: str = None,
        search: str = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple:
        """List contacts with filters"""
        contacts = list(self._contacts.values())

        if tenant_id:
            contacts = [c for c in contacts if c.get("tenant_id") == tenant_id]
        if company_id:
            contacts = [c for c in contacts if c.get("company_id") == company_id]
        if owner_id:
            contacts = [c for c in contacts if c.get("owner_id") == owner_id]
        if search:
            search_lower = search.lower()
            contacts = [
                c for c in contacts
                if search_lower in c.get("first_name", "").lower()
                or search_lower in c.get("last_name", "").lower()
                or search_lower in c.get("email", "").lower()
            ]

        total = len(contacts)
        contacts = sorted(contacts, key=lambda x: x.get("created_at", ""), reverse=True)
        contacts = contacts[skip:skip + limit]

        return contacts, total

    def get_contact_360(self, contact_id: str) -> dict:
        """Get 360-degree view of contact"""
        contact = self.get_contact(contact_id)
        if not contact:
            return None

        company = self.get_company(contact.get("company_id")) if contact.get("company_id") else None

        activities, _ = self.list_activities(contact_id=contact_id, limit=10)

        opps = [
            o for o in self._opportunities.values()
            if o.get("contact_id") == contact_id
        ]

        total_deals = sum(o.get("amount", 0) for o in opps if o.get("status") == "won")
        open_deals = sum(o.get("amount", 0) for o in opps if o.get("status") == "open")

        return {
            "contact": contact,
            "company": company,
            "activities": activities,
            "opportunities": opps,
            "metrics": {
                "total_deals_won": total_deals,
                "open_pipeline": open_deals,
                "total_activities": len(activities),
            }
        }

    # ==========================================
    # COMPANIES
    # ==========================================

    def create_company(self, data: dict) -> dict:
        """Create a new company"""
        company_id = str(uuid4())
        company = {
            "id": company_id,
            "type": "prospect",
            "health_score": 50,
            "created_at": utc_now().isoformat(),
            "updated_at": utc_now().isoformat(),
            **data,
        }
        self._companies[company_id] = company
        return company

    def get_company(self, company_id: str) -> Optional[dict]:
        """Get company by ID"""
        return self._companies.get(company_id)

    def update_company(self, company_id: str, updates: dict) -> Optional[dict]:
        """Update company"""
        if company_id not in self._companies:
            return None
        updates["updated_at"] = utc_now().isoformat()
        self._companies[company_id].update(updates)
        return self._companies[company_id]

    def delete_company(self, company_id: str) -> bool:
        """Delete company"""
        if company_id in self._companies:
            del self._companies[company_id]
            return True
        return False

    def list_companies(
        self,
        tenant_id: str = None,
        type: str = None,
        industry: str = None,
        owner_id: str = None,
        search: str = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple:
        """List companies with filters"""
        companies = list(self._companies.values())

        if tenant_id:
            companies = [c for c in companies if c.get("tenant_id") == tenant_id]
        if type:
            companies = [c for c in companies if c.get("type") == type]
        if industry:
            companies = [c for c in companies if c.get("industry") == industry]
        if owner_id:
            companies = [c for c in companies if c.get("owner_id") == owner_id]
        if search:
            search_lower = search.lower()
            companies = [
                c for c in companies
                if search_lower in c.get("name", "").lower()
                or search_lower in c.get("website", "").lower()
            ]

        total = len(companies)
        companies = sorted(companies, key=lambda x: x.get("created_at", ""), reverse=True)
        companies = companies[skip:skip + limit]

        return companies, total

    def get_company_summary(self, company_id: str) -> dict:
        """Get company summary with related data"""
        company = self.get_company(company_id)
        if not company:
            return None

        contacts = [
            c for c in self._contacts.values()
            if c.get("company_id") == company_id
        ]

        opps = [
            o for o in self._opportunities.values()
            if o.get("company_id") == company_id
        ]

        activities, _ = self.list_activities(company_id=company_id, limit=10)

        total_revenue = sum(o.get("amount", 0) for o in opps if o.get("status") == "won")
        open_pipeline = sum(o.get("amount", 0) for o in opps if o.get("status") == "open")
        won_deals = len([o for o in opps if o.get("status") == "won"])
        lost_deals = len([o for o in opps if o.get("status") == "lost"])

        return {
            "company": company,
            "contacts": contacts,
            "opportunities": opps[:5],
            "activities": activities,
            "metrics": {
                "total_revenue": total_revenue,
                "open_pipeline": open_pipeline,
                "contacts_count": len(contacts),
                "won_deals": won_deals,
                "lost_deals": lost_deals,
                "win_rate": (won_deals / (won_deals + lost_deals) * 100) if (won_deals + lost_deals) > 0 else 0,
            }
        }

    # ==========================================
    # OPPORTUNITIES
    # ==========================================

    def create_opportunity(self, data: dict) -> dict:
        """Create a new opportunity"""
        opp_id = str(uuid4())

        if "pipeline_id" not in data:
            data["pipeline_id"] = "default_pipeline"

        if "stage_id" not in data:
            first_stage = next(
                (s for s in self._stages.values()
                 if s.get("pipeline_id") == data["pipeline_id"] and s.get("position") == 1),
                None
            )
            if first_stage:
                data["stage_id"] = first_stage["id"]
                data["probability"] = first_stage.get("probability", 0)

        opportunity = {
            "id": opp_id,
            "status": "open",
            "amount": 0,
            "currency": "USD",
            "stage_history": [{
                "stage_id": data.get("stage_id"),
                "entered_at": utc_now().isoformat(),
            }],
            "created_at": utc_now().isoformat(),
            "updated_at": utc_now().isoformat(),
            **data,
        }
        self._opportunities[opp_id] = opportunity
        return opportunity

    def get_opportunity(self, opp_id: str) -> Optional[dict]:
        """Get opportunity by ID"""
        return self._opportunities.get(opp_id)

    def update_opportunity(self, opp_id: str, updates: dict) -> Optional[dict]:
        """Update opportunity"""
        if opp_id not in self._opportunities:
            return None

        opp = self._opportunities[opp_id]

        if "stage_id" in updates and updates["stage_id"] != opp.get("stage_id"):
            stage_history = opp.get("stage_history", [])
            stage_history.append({
                "stage_id": updates["stage_id"],
                "entered_at": utc_now().isoformat(),
            })
            updates["stage_history"] = stage_history

            stage = self._stages.get(updates["stage_id"])
            if stage:
                updates["probability"] = stage.get("probability", 0)
                if stage.get("is_won"):
                    updates["status"] = "won"
                    updates["actual_close_date"] = utc_now().isoformat()
                elif stage.get("is_lost"):
                    updates["status"] = "lost"
                    updates["actual_close_date"] = utc_now().isoformat()

        updates["updated_at"] = utc_now().isoformat()
        self._opportunities[opp_id].update(updates)
        return self._opportunities[opp_id]

    def delete_opportunity(self, opp_id: str) -> bool:
        """Delete opportunity"""
        if opp_id in self._opportunities:
            del self._opportunities[opp_id]
            return True
        return False

    def list_opportunities(
        self,
        tenant_id: str = None,
        pipeline_id: str = None,
        stage_id: str = None,
        status: str = None,
        owner_id: str = None,
        company_id: str = None,
        search: str = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple:
        """List opportunities with filters"""
        opps = list(self._opportunities.values())

        if tenant_id:
            opps = [o for o in opps if o.get("tenant_id") == tenant_id]
        if pipeline_id:
            opps = [o for o in opps if o.get("pipeline_id") == pipeline_id]
        if stage_id:
            opps = [o for o in opps if o.get("stage_id") == stage_id]
        if status:
            opps = [o for o in opps if o.get("status") == status]
        if owner_id:
            opps = [o for o in opps if o.get("owner_id") == owner_id]
        if company_id:
            opps = [o for o in opps if o.get("company_id") == company_id]
        if search:
            search_lower = search.lower()
            opps = [o for o in opps if search_lower in o.get("name", "").lower()]

        total = len(opps)
        opps = sorted(opps, key=lambda x: x.get("created_at", ""), reverse=True)
        opps = opps[skip:skip + limit]

        return opps, total

    # ==========================================
    # ACTIVITIES
    # ==========================================

    def create_activity(self, data: dict) -> dict:
        """Create a new activity"""
        activity_id = str(uuid4())
        activity = {
            "id": activity_id,
            "status": "scheduled",
            "created_at": utc_now().isoformat(),
            "updated_at": utc_now().isoformat(),
            **data,
        }
        self._activities[activity_id] = activity
        return activity

    def get_activity(self, activity_id: str) -> Optional[dict]:
        """Get activity by ID"""
        return self._activities.get(activity_id)

    def update_activity(self, activity_id: str, updates: dict) -> Optional[dict]:
        """Update activity"""
        if activity_id not in self._activities:
            return None
        updates["updated_at"] = utc_now().isoformat()
        self._activities[activity_id].update(updates)
        return self._activities[activity_id]

    def delete_activity(self, activity_id: str) -> bool:
        """Delete activity"""
        if activity_id in self._activities:
            del self._activities[activity_id]
            return True
        return False

    def list_activities(
        self,
        tenant_id: str = None,
        type: str = None,
        lead_id: str = None,
        contact_id: str = None,
        company_id: str = None,
        opportunity_id: str = None,
        owner_id: str = None,
        status: str = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple:
        """List activities with filters"""
        activities = list(self._activities.values())

        if tenant_id:
            activities = [a for a in activities if a.get("tenant_id") == tenant_id]
        if type:
            activities = [a for a in activities if a.get("type") == type]
        if lead_id:
            activities = [a for a in activities if a.get("lead_id") == lead_id]
        if contact_id:
            activities = [a for a in activities if a.get("contact_id") == contact_id]
        if company_id:
            activities = [a for a in activities if a.get("company_id") == company_id]
        if opportunity_id:
            activities = [a for a in activities if a.get("opportunity_id") == opportunity_id]
        if owner_id:
            activities = [a for a in activities if a.get("owner_id") == owner_id]
        if status:
            activities = [a for a in activities if a.get("status") == status]

        total = len(activities)
        activities = sorted(activities, key=lambda x: x.get("created_at", ""), reverse=True)
        activities = activities[skip:skip + limit]

        return activities, total

    def complete_activity(self, activity_id: str, outcome: str = None) -> dict:
        """Mark activity as completed"""
        return self.update_activity(activity_id, {
            "status": "completed",
            "completed_at": utc_now().isoformat(),
            "outcome": outcome,
        })

    # ==========================================
    # PIPELINES & STAGES
    # ==========================================

    def get_pipeline(self, pipeline_id: str) -> Optional[dict]:
        """Get pipeline with stages"""
        pipeline = self._pipelines.get(pipeline_id)
        if not pipeline:
            return None

        stages = sorted(
            [s for s in self._stages.values() if s.get("pipeline_id") == pipeline_id],
            key=lambda x: x.get("position", 0)
        )

        return {**pipeline, "stages": stages}

    def list_pipelines(self, tenant_id: str = None) -> List[dict]:
        """List all pipelines"""
        pipelines = list(self._pipelines.values())
        if tenant_id:
            pipelines = [p for p in pipelines if p.get("tenant_id") == tenant_id or not p.get("tenant_id")]
        return pipelines

    def create_pipeline(self, data: dict) -> dict:
        """Create new pipeline"""
        pipeline_id = str(uuid4())
        pipeline = {
            "id": pipeline_id,
            "is_default": False,
            "created_at": utc_now().isoformat(),
            **data,
        }
        self._pipelines[pipeline_id] = pipeline
        return pipeline

    def create_stage(self, data: dict) -> dict:
        """Create pipeline stage"""
        stage_id = str(uuid4())
        stage = {
            "id": stage_id,
            "is_won": False,
            "is_lost": False,
            **data,
        }
        self._stages[stage_id] = stage
        return stage

    def get_pipeline_stats(self, pipeline_id: str, tenant_id: str = None) -> dict:
        """Get pipeline statistics"""
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            return None

        opps, _ = self.list_opportunities(pipeline_id=pipeline_id, tenant_id=tenant_id, limit=1000)

        stats = {
            "pipeline_id": pipeline_id,
            "pipeline_name": pipeline["name"],
            "stages": [],
            "totals": {
                "count": len(opps),
                "value": sum(o.get("amount", 0) for o in opps),
                "weighted_value": sum(o.get("amount", 0) * (o.get("probability", 0) / 100) for o in opps),
            }
        }

        for stage in pipeline.get("stages", []):
            stage_opps = [o for o in opps if o.get("stage_id") == stage["id"]]
            stats["stages"].append({
                "stage_id": stage["id"],
                "stage_name": stage["name"],
                "count": len(stage_opps),
                "value": sum(o.get("amount", 0) for o in stage_opps),
                "color": stage.get("color"),
            })

        return stats


# Global instance
crm_store = CRMStore()
