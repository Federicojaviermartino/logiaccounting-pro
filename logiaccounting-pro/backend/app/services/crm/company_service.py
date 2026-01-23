"""
Company/Account Management Service
Handles company profiles and account health
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from app.models.crm_store import crm_store


class CompanyService:
    """
    Service for managing companies/accounts
    """

    # Company types
    COMPANY_TYPES = [
        "prospect",
        "customer",
        "former_customer",
        "partner",
        "competitor",
        "vendor",
        "other",
    ]

    # Industries
    INDUSTRIES = [
        "technology",
        "healthcare",
        "finance",
        "manufacturing",
        "retail",
        "education",
        "government",
        "non_profit",
        "professional_services",
        "real_estate",
        "transportation",
        "energy",
        "agriculture",
        "hospitality",
        "media",
        "telecommunications",
        "other",
    ]

    def create_company(
        self,
        tenant_id: str,
        name: str,
        website: str = None,
        industry: str = None,
        employees_count: int = None,
        annual_revenue: float = None,
        type: str = "prospect",
        owner_id: str = None,
        **kwargs
    ) -> dict:
        """Create a new company"""
        company_data = {
            "tenant_id": tenant_id,
            "name": name,
            "website": website,
            "industry": industry,
            "employees_count": employees_count,
            "annual_revenue": annual_revenue,
            "type": type,
            "owner_id": owner_id,
            **kwargs,
        }

        company = crm_store.create_company(company_data)

        # Calculate initial health score
        health = self.calculate_health_score(company["id"])
        crm_store.update_company(company["id"], {"health_score": health})
        company["health_score"] = health

        return company

    def update_company(self, company_id: str, user_id: str, **updates) -> dict:
        """Update company"""
        company = crm_store.update_company(company_id, updates)

        # Recalculate health score
        if company:
            health = self.calculate_health_score(company_id)
            crm_store.update_company(company_id, {"health_score": health})
            company["health_score"] = health

        return company

    def get_company(self, company_id: str) -> dict:
        """Get company by ID"""
        return crm_store.get_company(company_id)

    def get_company_summary(self, company_id: str) -> dict:
        """Get company with full summary"""
        return crm_store.get_company_summary(company_id)

    def delete_company(self, company_id: str, user_id: str):
        """Delete company"""
        return crm_store.delete_company(company_id)

    def list_companies(
        self,
        tenant_id: str,
        type: str = None,
        industry: str = None,
        owner_id: str = None,
        search: str = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """List companies with pagination"""
        skip = (page - 1) * page_size
        companies, total = crm_store.list_companies(
            tenant_id=tenant_id,
            type=type,
            industry=industry,
            owner_id=owner_id,
            search=search,
            skip=skip,
            limit=page_size,
        )

        return {
            "items": companies,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    def calculate_health_score(self, company_id: str) -> int:
        """Calculate account health score (0-100)"""
        company = crm_store.get_company(company_id)
        if not company:
            return 0

        score = 50  # Base score

        # Get related data
        contacts, _ = crm_store.list_contacts(company_id=company_id, limit=100)
        opps, _ = crm_store.list_opportunities(company_id=company_id, limit=100)
        activities, _ = crm_store.list_activities(company_id=company_id, limit=100)

        # Engagement factors
        if contacts:
            score += min(len(contacts) * 2, 10)  # Up to +10 for contacts

        # Recent activity
        recent_activities = [
            a for a in activities
            if a.get("created_at", "") > (datetime.utcnow().replace(day=1)).isoformat()
        ]
        if recent_activities:
            score += min(len(recent_activities) * 2, 15)  # Up to +15 for recent activity

        # Deal history
        won_deals = [o for o in opps if o.get("status") == "won"]
        lost_deals = [o for o in opps if o.get("status") == "lost"]
        open_deals = [o for o in opps if o.get("status") == "open"]

        if won_deals:
            score += min(len(won_deals) * 5, 20)  # Up to +20 for won deals

        if open_deals:
            score += 5  # +5 for having open pipeline

        if lost_deals and not won_deals:
            score -= 15  # -15 if only lost deals

        # Company type bonus
        if company.get("type") == "customer":
            score += 10
        elif company.get("type") == "partner":
            score += 5

        return max(0, min(100, score))

    def set_parent_company(self, company_id: str, parent_id: str, user_id: str) -> dict:
        """Set company hierarchy"""
        if company_id == parent_id:
            raise ValueError("Company cannot be its own parent")

        return crm_store.update_company(company_id, {"parent_company_id": parent_id})

    def get_subsidiaries(self, parent_id: str) -> List[dict]:
        """Get all subsidiary companies"""
        companies, _ = crm_store.list_companies(limit=1000)
        return [c for c in companies if c.get("parent_company_id") == parent_id]

    def link_to_client(self, company_id: str, client_id: str, user_id: str) -> dict:
        """Link CRM company to existing client record"""
        return crm_store.update_company(company_id, {
            "linked_client_id": client_id,
            "type": "customer",
        })

    def get_top_accounts(self, tenant_id: str, limit: int = 10) -> List[dict]:
        """Get top accounts by revenue"""
        companies, _ = crm_store.list_companies(tenant_id=tenant_id, limit=1000)

        # Calculate total revenue for each company
        accounts_with_revenue = []
        for company in companies:
            summary = crm_store.get_company_summary(company["id"])
            if summary:
                accounts_with_revenue.append({
                    **company,
                    "total_revenue": summary["metrics"]["total_revenue"],
                    "open_pipeline": summary["metrics"]["open_pipeline"],
                })

        # Sort by total revenue
        accounts_with_revenue.sort(key=lambda x: x["total_revenue"], reverse=True)

        return accounts_with_revenue[:limit]

    def get_at_risk_accounts(self, tenant_id: str) -> List[dict]:
        """Get accounts with low health scores"""
        companies, _ = crm_store.list_companies(tenant_id=tenant_id, type="customer", limit=1000)

        at_risk = [c for c in companies if c.get("health_score", 50) < 40]
        return sorted(at_risk, key=lambda x: x.get("health_score", 0))


# Service instance
company_service = CompanyService()
