"""
Lead Management Service
Handles lead lifecycle, scoring, and conversion
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import uuid4

from app.models.crm_store import crm_store


class LeadService:
    """
    Service for managing sales leads
    """

    # Lead scoring weights
    SCORING_WEIGHTS = {
        "has_email": 10,
        "has_phone": 10,
        "has_company": 15,
        "has_job_title": 10,
        "source_website": 5,
        "source_referral": 20,
        "source_campaign": 15,
        "budget_mentioned": 15,
        "authority_confirmed": 15,
        "need_identified": 15,
        "timeline_defined": 10,
    }

    # Lead sources
    LEAD_SOURCES = [
        "website",
        "referral",
        "campaign",
        "cold_call",
        "trade_show",
        "social_media",
        "advertisement",
        "partner",
        "other",
    ]

    # Lead statuses
    LEAD_STATUSES = [
        "new",
        "contacted",
        "qualified",
        "unqualified",
        "converted",
        "lost",
    ]

    def create_lead(
        self,
        tenant_id: str,
        first_name: str,
        last_name: str = None,
        email: str = None,
        phone: str = None,
        company_name: str = None,
        job_title: str = None,
        source: str = "website",
        owner_id: str = None,
        notes: str = None,
        custom_fields: Dict[str, Any] = None,
        **kwargs
    ) -> dict:
        """Create a new lead with automatic scoring"""

        lead_data = {
            "tenant_id": tenant_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "company_name": company_name,
            "job_title": job_title,
            "source": source,
            "owner_id": owner_id,
            "notes": notes,
            "custom_fields": custom_fields or {},
            **kwargs,
        }

        lead = crm_store.create_lead(lead_data)

        # Calculate initial score
        score = self.calculate_lead_score(lead)
        crm_store.update_lead(lead["id"], {"score": score, "rating": self._get_rating(score)})
        lead["score"] = score
        lead["rating"] = self._get_rating(score)

        return lead

    def update_lead(self, lead_id: str, user_id: str, **updates) -> dict:
        """Update lead and recalculate score"""
        lead = crm_store.update_lead(lead_id, updates)

        if lead:
            # Recalculate score if relevant fields changed
            score_fields = ["email", "phone", "company_name", "job_title", "source", "bant_budget", "bant_authority", "bant_need", "bant_timeline"]
            if any(f in updates for f in score_fields):
                score = self.calculate_lead_score(lead)
                crm_store.update_lead(lead_id, {"score": score, "rating": self._get_rating(score)})
                lead["score"] = score
                lead["rating"] = self._get_rating(score)

        return lead

    def get_lead(self, lead_id: str) -> dict:
        """Get lead with related data"""
        lead = crm_store.get_lead(lead_id)
        if not lead:
            return None

        # Get activities
        activities, _ = crm_store.list_activities(lead_id=lead_id, limit=20)
        lead["activities"] = activities

        return lead

    def delete_lead(self, lead_id: str, user_id: str):
        """Delete a lead"""
        return crm_store.delete_lead(lead_id)

    def list_leads(
        self,
        tenant_id: str,
        status: str = None,
        source: str = None,
        owner_id: str = None,
        rating: str = None,
        search: str = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """List leads with pagination"""
        skip = (page - 1) * page_size
        leads, total = crm_store.list_leads(
            tenant_id=tenant_id,
            status=status,
            source=source,
            owner_id=owner_id,
            search=search,
            skip=skip,
            limit=page_size,
        )

        # Filter by rating if specified
        if rating:
            leads = [l for l in leads if l.get("rating") == rating]
            total = len(leads)

        return {
            "items": leads,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    def calculate_lead_score(self, lead: dict) -> int:
        """Calculate lead score based on completeness and BANT criteria"""
        score = 0

        # Basic info completeness
        if lead.get("email"):
            score += self.SCORING_WEIGHTS["has_email"]
        if lead.get("phone"):
            score += self.SCORING_WEIGHTS["has_phone"]
        if lead.get("company_name"):
            score += self.SCORING_WEIGHTS["has_company"]
        if lead.get("job_title"):
            score += self.SCORING_WEIGHTS["has_job_title"]

        # Source quality
        source = lead.get("source", "").lower()
        if source == "referral":
            score += self.SCORING_WEIGHTS["source_referral"]
        elif source == "campaign":
            score += self.SCORING_WEIGHTS["source_campaign"]
        elif source == "website":
            score += self.SCORING_WEIGHTS["source_website"]

        # BANT criteria
        if lead.get("bant_budget"):
            score += self.SCORING_WEIGHTS["budget_mentioned"]
        if lead.get("bant_authority"):
            score += self.SCORING_WEIGHTS["authority_confirmed"]
        if lead.get("bant_need"):
            score += self.SCORING_WEIGHTS["need_identified"]
        if lead.get("bant_timeline"):
            score += self.SCORING_WEIGHTS["timeline_defined"]

        return min(score, 100)

    def _get_rating(self, score: int) -> str:
        """Get lead rating from score"""
        if score >= 70:
            return "hot"
        elif score >= 40:
            return "warm"
        else:
            return "cold"

    def convert_lead(
        self,
        lead_id: str,
        user_id: str,
        create_contact: bool = True,
        create_opportunity: bool = True,
        opportunity_amount: float = None,
        opportunity_name: str = None,
    ) -> dict:
        """Convert lead to contact and/or opportunity"""
        lead = crm_store.get_lead(lead_id)
        if not lead:
            raise ValueError(f"Lead not found: {lead_id}")

        if lead.get("status") == "converted":
            raise ValueError("Lead already converted")

        opp_data = {}
        if opportunity_amount:
            opp_data["amount"] = opportunity_amount
        if opportunity_name:
            opp_data["name"] = opportunity_name

        result = crm_store.convert_lead(
            lead_id=lead_id,
            create_contact=create_contact,
            create_opportunity=create_opportunity,
            opportunity_data=opp_data if opp_data else None,
        )

        return result

    def change_status(self, lead_id: str, user_id: str, status: str) -> dict:
        """Change lead status"""
        if status not in self.LEAD_STATUSES:
            raise ValueError(f"Invalid status: {status}")

        return crm_store.update_lead(lead_id, {"status": status})

    def assign_lead(self, lead_id: str, owner_id: str, assigned_by: str) -> dict:
        """Assign lead to a user"""
        return crm_store.update_lead(lead_id, {
            "owner_id": owner_id,
            "assigned_at": datetime.utcnow().isoformat(),
            "assigned_by": assigned_by,
        })

    def bulk_assign(self, lead_ids: List[str], owner_id: str, assigned_by: str) -> int:
        """Bulk assign leads to a user"""
        count = 0
        for lead_id in lead_ids:
            if crm_store.update_lead(lead_id, {
                "owner_id": owner_id,
                "assigned_at": datetime.utcnow().isoformat(),
                "assigned_by": assigned_by,
            }):
                count += 1
        return count

    def get_lead_sources_stats(self, tenant_id: str) -> List[dict]:
        """Get lead statistics by source"""
        leads, _ = crm_store.list_leads(tenant_id=tenant_id, limit=10000)

        stats = {}
        for lead in leads:
            source = lead.get("source", "unknown")
            if source not in stats:
                stats[source] = {"source": source, "count": 0, "converted": 0}
            stats[source]["count"] += 1
            if lead.get("status") == "converted":
                stats[source]["converted"] += 1

        # Calculate conversion rates
        result = []
        for source, data in stats.items():
            data["conversion_rate"] = (data["converted"] / data["count"] * 100) if data["count"] > 0 else 0
            result.append(data)

        return sorted(result, key=lambda x: x["count"], reverse=True)

    def import_leads(self, tenant_id: str, user_id: str, leads_data: List[dict]) -> dict:
        """Bulk import leads from CSV/Excel"""
        created = 0
        errors = []

        for i, data in enumerate(leads_data):
            try:
                # Validate required fields
                if not data.get("first_name"):
                    raise ValueError("first_name is required")

                self.create_lead(
                    tenant_id=tenant_id,
                    first_name=data.get("first_name"),
                    last_name=data.get("last_name"),
                    email=data.get("email"),
                    phone=data.get("phone"),
                    company_name=data.get("company_name") or data.get("company"),
                    job_title=data.get("job_title") or data.get("title"),
                    source=data.get("source", "import"),
                    owner_id=user_id,
                    notes=data.get("notes"),
                )
                created += 1
            except Exception as e:
                errors.append({"row": i + 1, "error": str(e)})

        return {
            "total": len(leads_data),
            "created": created,
            "errors": errors,
        }


# Service instance
lead_service = LeadService()
