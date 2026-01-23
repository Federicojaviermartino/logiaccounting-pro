"""
Contact Management Service
Handles contact CRUD and 360-degree views
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from app.models.crm_store import crm_store


class ContactService:
    """
    Service for managing contacts
    """

    # Contact roles
    CONTACT_ROLES = [
        "decision_maker",
        "influencer",
        "economic_buyer",
        "technical_buyer",
        "champion",
        "blocker",
        "end_user",
        "other",
    ]

    def create_contact(
        self,
        tenant_id: str,
        first_name: str,
        last_name: str = None,
        email: str = None,
        phone: str = None,
        mobile: str = None,
        job_title: str = None,
        department: str = None,
        company_id: str = None,
        owner_id: str = None,
        **kwargs
    ) -> dict:
        """Create a new contact"""
        contact_data = {
            "tenant_id": tenant_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "mobile": mobile,
            "job_title": job_title,
            "department": department,
            "company_id": company_id,
            "owner_id": owner_id,
            **kwargs,
        }

        return crm_store.create_contact(contact_data)

    def update_contact(self, contact_id: str, user_id: str, **updates) -> dict:
        """Update contact"""
        return crm_store.update_contact(contact_id, updates)

    def get_contact(self, contact_id: str) -> dict:
        """Get contact by ID"""
        return crm_store.get_contact(contact_id)

    def get_contact_360(self, contact_id: str) -> dict:
        """Get 360-degree view of contact"""
        return crm_store.get_contact_360(contact_id)

    def delete_contact(self, contact_id: str, user_id: str):
        """Delete contact"""
        return crm_store.delete_contact(contact_id)

    def list_contacts(
        self,
        tenant_id: str,
        company_id: str = None,
        owner_id: str = None,
        search: str = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """List contacts with pagination"""
        skip = (page - 1) * page_size
        contacts, total = crm_store.list_contacts(
            tenant_id=tenant_id,
            company_id=company_id,
            owner_id=owner_id,
            search=search,
            skip=skip,
            limit=page_size,
        )

        return {
            "items": contacts,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    def search_contacts(
        self,
        tenant_id: str,
        query: str,
        limit: int = 10,
    ) -> List[dict]:
        """Quick search for contacts"""
        contacts, _ = crm_store.list_contacts(
            tenant_id=tenant_id,
            search=query,
            limit=limit,
        )
        return contacts

    def merge_contacts(
        self,
        primary_id: str,
        secondary_id: str,
        user_id: str,
    ) -> dict:
        """Merge two contacts into one"""
        primary = crm_store.get_contact(primary_id)
        secondary = crm_store.get_contact(secondary_id)

        if not primary or not secondary:
            raise ValueError("One or both contacts not found")

        # Merge data - prefer primary, fill gaps from secondary
        merged_data = {}
        for key, value in secondary.items():
            if key in ["id", "created_at", "updated_at"]:
                continue
            if not primary.get(key) and value:
                merged_data[key] = value

        # Update primary with merged data
        if merged_data:
            crm_store.update_contact(primary_id, merged_data)

        # Move all activities from secondary to primary
        activities, _ = crm_store.list_activities(contact_id=secondary_id, limit=1000)
        for activity in activities:
            crm_store.update_activity(activity["id"], {"contact_id": primary_id})

        # Move all opportunities from secondary to primary
        opps, _ = crm_store.list_opportunities(tenant_id=primary.get("tenant_id"), limit=1000)
        for opp in opps:
            if opp.get("contact_id") == secondary_id:
                crm_store.update_opportunity(opp["id"], {"contact_id": primary_id})

        # Delete secondary
        crm_store.delete_contact(secondary_id)

        # Return merged contact
        return crm_store.get_contact(primary_id)

    def set_preferences(
        self,
        contact_id: str,
        do_not_call: bool = None,
        do_not_email: bool = None,
        preferred_contact_method: str = None,
    ) -> dict:
        """Update contact communication preferences"""
        updates = {}
        if do_not_call is not None:
            updates["do_not_call"] = do_not_call
        if do_not_email is not None:
            updates["do_not_email"] = do_not_email
        if preferred_contact_method:
            updates["preferred_contact_method"] = preferred_contact_method

        return crm_store.update_contact(contact_id, updates)

    def import_contacts(self, tenant_id: str, user_id: str, contacts_data: List[dict]) -> dict:
        """Bulk import contacts"""
        created = 0
        errors = []

        for i, data in enumerate(contacts_data):
            try:
                if not data.get("first_name"):
                    raise ValueError("first_name is required")

                self.create_contact(
                    tenant_id=tenant_id,
                    first_name=data.get("first_name"),
                    last_name=data.get("last_name"),
                    email=data.get("email"),
                    phone=data.get("phone"),
                    mobile=data.get("mobile"),
                    job_title=data.get("job_title") or data.get("title"),
                    department=data.get("department"),
                    owner_id=user_id,
                )
                created += 1
            except Exception as e:
                errors.append({"row": i + 1, "error": str(e)})

        return {
            "total": len(contacts_data),
            "created": created,
            "errors": errors,
        }

    def export_contacts(self, tenant_id: str, format: str = "csv") -> bytes:
        """Export contacts to CSV"""
        contacts, _ = crm_store.list_contacts(tenant_id=tenant_id, limit=10000)

        if format == "csv":
            import io
            import csv

            output = io.StringIO()
            fieldnames = ["first_name", "last_name", "email", "phone", "mobile", "job_title", "department"]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()

            for contact in contacts:
                writer.writerow({k: contact.get(k, "") for k in fieldnames})

            return output.getvalue().encode()

        raise ValueError(f"Unsupported format: {format}")


# Service instance
contact_service = ContactService()
