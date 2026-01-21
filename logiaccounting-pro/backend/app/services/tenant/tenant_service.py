"""
Tenant Service
Core tenant management operations
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from app.models.tenant_store import (
    tenant_db, TenantStatus, TenantTier, IsolationLevel,
    TIER_QUOTAS, TIER_FEATURES
)


class TenantService:
    """Service for tenant lifecycle management"""

    def __init__(self, tenant_id: str = None):
        self.tenant_id = tenant_id

    def create_tenant(
        self,
        name: str,
        owner_email: str,
        owner_id: str = None,
        tier: str = TenantTier.FREE.value,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new tenant with all related resources.
        """
        # Create the tenant
        tenant = tenant_db.tenants.create({
            "name": name,
            "owner_email": owner_email,
            "owner_id": owner_id,
            "tier": tier,
            "status": TenantStatus.PENDING.value,
            "isolation_level": IsolationLevel.SHARED.value,
            **kwargs
        })

        tenant_id = tenant["id"]

        # Create default settings
        tenant_db.settings.create({
            "tenant_id": tenant_id,
            "email_from_name": name,
            "email_from_address": f"noreply@{tenant['slug']}.logiaccounting.io"
        })

        # Create subscription
        tenant_db.subscriptions.create({
            "tenant_id": tenant_id,
            "tier": tier,
            "status": "active",
            "billing_cycle": "monthly",
            "price_cents": self._get_tier_price(tier)
        })

        # Create quota with tier limits
        tenant_db.quotas.create({
            "tenant_id": tenant_id,
            "tier": tier
        })

        # Initialize features based on tier
        tenant_db.features.initialize_tier_features(tenant_id, tier)

        # Add owner as member if owner_id provided
        if owner_id:
            tenant_db.members.create({
                "tenant_id": tenant_id,
                "user_id": owner_id,
                "role": "admin",
                "is_owner": True
            })

        return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant by ID with related data"""
        tenant = tenant_db.tenants.find_by_id(tenant_id)
        if not tenant:
            return None

        return self._enrich_tenant(tenant)

    def get_tenant_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get tenant by slug"""
        tenant = tenant_db.tenants.find_by_slug(slug)
        if not tenant:
            return None

        return self._enrich_tenant(tenant)

    def _enrich_tenant(self, tenant: Dict) -> Dict[str, Any]:
        """Add related data to tenant"""
        tenant_id = tenant["id"]
        return {
            **tenant,
            "settings": tenant_db.settings.find_by_tenant(tenant_id),
            "subscription": tenant_db.subscriptions.find_by_tenant(tenant_id),
            "quota": tenant_db.quotas.find_by_tenant(tenant_id),
            "domains": tenant_db.domains.find_by_tenant(tenant_id),
            "member_count": tenant_db.members.count_by_tenant(tenant_id)
        }

    def list_tenants(
        self,
        status: str = None,
        tier: str = None,
        search: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List tenants with filters"""
        filters = {}
        if status:
            filters["status"] = status
        if tier:
            filters["tier"] = tier
        if search:
            filters["search"] = search

        tenants = tenant_db.tenants.find_all(filters, limit=limit, offset=offset)
        total = tenant_db.tenants.count(filters)

        return {
            "tenants": tenants,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total
            }
        }

    def update_tenant(self, tenant_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update tenant information"""
        # Filter allowed fields
        allowed_fields = [
            "name", "display_name", "billing_email",
            "country", "timezone", "locale", "metadata"
        ]
        update_data = {k: v for k, v in data.items() if k in allowed_fields and v is not None}

        if not update_data:
            return tenant_db.tenants.find_by_id(tenant_id)

        return tenant_db.tenants.update(tenant_id, update_data)

    def activate_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Activate a pending or suspended tenant"""
        tenant = tenant_db.tenants.find_by_id(tenant_id)
        if not tenant:
            return None

        if tenant.get("status") in [TenantStatus.DELETED.value, TenantStatus.CANCELLED.value]:
            raise ValueError("Cannot activate deleted or cancelled tenant")

        return tenant_db.tenants.activate(tenant_id)

    def suspend_tenant(self, tenant_id: str, reason: str = None) -> Optional[Dict[str, Any]]:
        """Suspend a tenant"""
        tenant = tenant_db.tenants.find_by_id(tenant_id)
        if not tenant:
            return None

        if tenant.get("status") == TenantStatus.DELETED.value:
            raise ValueError("Cannot suspend deleted tenant")

        return tenant_db.tenants.suspend(tenant_id, reason)

    def cancel_tenant(self, tenant_id: str, reason: str = None) -> Optional[Dict[str, Any]]:
        """Cancel a tenant subscription"""
        tenant = tenant_db.tenants.find_by_id(tenant_id)
        if not tenant:
            return None

        # Cancel subscription
        subscription = tenant_db.subscriptions.find_by_tenant(tenant_id)
        if subscription:
            tenant_db.subscriptions.cancel(subscription["id"], at_period_end=True)

        return tenant_db.tenants.update(tenant_id, {
            "status": TenantStatus.CANCELLED.value,
            "cancellation_reason": reason
        })

    def delete_tenant(self, tenant_id: str, hard_delete: bool = False) -> bool:
        """
        Delete a tenant.
        Soft delete by default, hard delete removes all data.
        """
        tenant = tenant_db.tenants.find_by_id(tenant_id)
        if not tenant:
            return False

        if hard_delete:
            # Remove all related data
            tenant_db.settings.delete(tenant_id)
            for inv in tenant_db.invitations.find_by_tenant(tenant_id):
                tenant_db.invitations.delete(inv["id"])
            for domain in tenant_db.domains.find_by_tenant(tenant_id):
                tenant_db.domains.delete(domain["id"])
            # Remove tenant from store
            for i, t in enumerate(tenant_db.tenants._data):
                if t["id"] == tenant_id:
                    tenant_db.tenants._data.pop(i)
                    break
            return True
        else:
            # Soft delete
            tenant_db.tenants.delete(tenant_id)
            return True

    def change_tier(self, tenant_id: str, new_tier: str) -> Dict[str, Any]:
        """
        Change tenant subscription tier.
        Updates quotas and features accordingly.
        """
        tenant = tenant_db.tenants.find_by_id(tenant_id)
        if not tenant:
            raise ValueError("Tenant not found")

        old_tier = tenant.get("tier")
        if old_tier == new_tier:
            return tenant

        # Update tenant tier
        tenant_db.tenants.update(tenant_id, {"tier": new_tier})

        # Update quota limits
        tenant_db.quotas.update_tier_limits(tenant_id, new_tier)

        # Update subscription
        subscription = tenant_db.subscriptions.find_by_tenant(tenant_id)
        if subscription:
            tenant_db.subscriptions.update(subscription["id"], {
                "tier": new_tier,
                "price_cents": self._get_tier_price(new_tier)
            })

        # Update features
        tenant_db.features.initialize_tier_features(tenant_id, new_tier)

        return self.get_tenant(tenant_id)

    def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant statistics"""
        tenant = tenant_db.tenants.find_by_id(tenant_id)
        if not tenant:
            return {}

        quota = tenant_db.quotas.find_by_tenant(tenant_id)
        members = tenant_db.members.find_by_tenant(tenant_id)

        return {
            "tenant_id": tenant_id,
            "members_count": len(members),
            "storage_used_mb": quota.get("current_storage_mb", 0) if quota else 0,
            "api_calls_today": quota.get("current_api_calls_today", 0) if quota else 0,
            "invoices_this_month": quota.get("current_invoices_month", 0) if quota else 0,
            "active_projects": quota.get("current_projects", 0) if quota else 0,
            "active_integrations": quota.get("current_integrations", 0) if quota else 0,
            "last_activity_at": tenant.get("updated_at")
        }

    def _get_tier_price(self, tier: str) -> int:
        """Get monthly price in cents for tier"""
        prices = {
            TenantTier.FREE.value: 0,
            TenantTier.STANDARD.value: 2900,
            TenantTier.PROFESSIONAL.value: 7900,
            TenantTier.BUSINESS.value: 19900,
            TenantTier.ENTERPRISE.value: 0  # Custom pricing
        }
        return prices.get(tier, 0)

    # Domain Management

    def add_domain(self, tenant_id: str, domain: str, domain_type: str = "custom", is_primary: bool = False) -> Dict[str, Any]:
        """Add a custom domain to tenant"""
        # Check if domain already exists
        existing = tenant_db.domains.find_by_domain(domain)
        if existing:
            raise ValueError("Domain already registered")

        # If setting as primary, unset other primary domains
        if is_primary:
            for d in tenant_db.domains.find_by_tenant(tenant_id):
                if d.get("is_primary"):
                    tenant_db.domains.update(d["id"], {"is_primary": False})

        return tenant_db.domains.create({
            "tenant_id": tenant_id,
            "domain": domain.lower(),
            "domain_type": domain_type,
            "is_primary": is_primary
        })

    def verify_domain(self, domain_id: str) -> Dict[str, Any]:
        """Verify domain ownership"""
        domain = tenant_db.domains.find_by_id(domain_id)
        if not domain:
            raise ValueError("Domain not found")

        # In production, would verify DNS TXT record or file verification
        # For demo, mark as verified
        return tenant_db.domains.verify(domain_id)

    def remove_domain(self, domain_id: str) -> bool:
        """Remove a domain from tenant"""
        domain = tenant_db.domains.find_by_id(domain_id)
        if not domain:
            return False

        if domain.get("is_primary"):
            raise ValueError("Cannot remove primary domain")

        return tenant_db.domains.delete(domain_id)

    # Settings Management

    def get_settings(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant settings"""
        return tenant_db.settings.find_by_tenant(tenant_id)

    def update_settings(self, tenant_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update tenant settings"""
        settings = tenant_db.settings.find_by_tenant(tenant_id)
        if not settings:
            # Create settings if not exists
            return tenant_db.settings.create({"tenant_id": tenant_id, **data})

        return tenant_db.settings.update(tenant_id, data)

    # Member Management

    def get_members(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get all members of a tenant"""
        return tenant_db.members.find_by_tenant(tenant_id)

    def add_member(self, tenant_id: str, user_id: str, role: str = "member", invited_by: str = None) -> Dict[str, Any]:
        """Add a user as tenant member"""
        # Check if already a member
        existing = tenant_db.members.find_membership(tenant_id, user_id)
        if existing:
            raise ValueError("User is already a member")

        # Check user quota
        from app.services.tenant.quota_service import QuotaService
        quota_service = QuotaService(tenant_id)
        if not quota_service.check_quota("users")["allowed"]:
            raise ValueError("User quota exceeded")

        member = tenant_db.members.create({
            "tenant_id": tenant_id,
            "user_id": user_id,
            "role": role,
            "invited_by": invited_by
        })

        # Increment user count
        quota_service.increment_usage("users")

        return member

    def update_member_role(self, tenant_id: str, user_id: str, role: str) -> Optional[Dict[str, Any]]:
        """Update member role"""
        membership = tenant_db.members.find_membership(tenant_id, user_id)
        if not membership:
            return None

        if membership.get("is_owner"):
            raise ValueError("Cannot change owner role")

        return tenant_db.members.update(membership["id"], {"role": role})

    def remove_member(self, tenant_id: str, user_id: str) -> bool:
        """Remove a member from tenant"""
        membership = tenant_db.members.find_membership(tenant_id, user_id)
        if not membership:
            return False

        if membership.get("is_owner"):
            raise ValueError("Cannot remove tenant owner")

        result = tenant_db.members.remove(tenant_id, user_id)

        if result:
            # Decrement user count
            from app.services.tenant.quota_service import QuotaService
            QuotaService(tenant_id).decrement_usage("users")

        return result

    # Invitation Management

    def create_invitation(self, tenant_id: str, email: str, role: str = "member", invited_by: str = None) -> Dict[str, Any]:
        """Create invitation for new member"""
        # Check if already invited
        existing = tenant_db.invitations.find_by_email(tenant_id, email)
        if existing:
            raise ValueError("User already invited")

        # Check user quota
        from app.services.tenant.quota_service import QuotaService
        if not QuotaService(tenant_id).check_quota("users")["allowed"]:
            raise ValueError("User quota exceeded")

        return tenant_db.invitations.create({
            "tenant_id": tenant_id,
            "email": email.lower(),
            "role": role,
            "invited_by": invited_by
        })

    def accept_invitation(self, token: str, user_id: str) -> Dict[str, Any]:
        """Accept an invitation"""
        invitation = tenant_db.invitations.find_by_token(token)
        if not invitation:
            raise ValueError("Invalid invitation token")

        if not tenant_db.invitations.is_valid(invitation):
            raise ValueError("Invitation has expired or been revoked")

        # Mark invitation as accepted
        tenant_db.invitations.accept(invitation["id"], user_id)

        # Add user as member
        return self.add_member(
            invitation["tenant_id"],
            user_id,
            invitation.get("role", "member"),
            invitation.get("invited_by")
        )

    def revoke_invitation(self, invitation_id: str) -> Optional[Dict[str, Any]]:
        """Revoke an invitation"""
        return tenant_db.invitations.revoke(invitation_id)

    def get_invitations(self, tenant_id: str, status: str = None) -> List[Dict[str, Any]]:
        """Get invitations for tenant"""
        return tenant_db.invitations.find_by_tenant(tenant_id, status)
