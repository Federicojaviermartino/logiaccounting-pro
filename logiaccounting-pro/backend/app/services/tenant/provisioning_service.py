"""
Provisioning Service
Tenant resource provisioning and deprovisioning
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from app.models.tenant_store import (
    tenant_db, TenantStatus, TenantTier, IsolationLevel
)


class ProvisioningService:
    """
    Service for provisioning and deprovisioning tenant resources.
    Handles initial setup and teardown of tenant infrastructure.
    """

    def __init__(self, tenant_id: str = None):
        self.tenant_id = tenant_id

    def provision_tenant(
        self,
        name: str,
        owner_email: str,
        owner_id: str = None,
        tier: str = TenantTier.FREE.value,
        isolation_level: str = IsolationLevel.SHARED.value,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fully provision a new tenant with all resources.
        """
        # Create tenant record
        tenant = tenant_db.tenants.create({
            "name": name,
            "owner_email": owner_email,
            "owner_id": owner_id,
            "tier": tier,
            "isolation_level": isolation_level,
            "status": TenantStatus.PENDING.value,
            **kwargs
        })

        tenant_id = tenant["id"]
        slug = tenant["slug"]

        try:
            # Provision settings
            self._provision_settings(tenant_id, name, slug)

            # Provision subscription
            self._provision_subscription(tenant_id, tier)

            # Provision quotas
            self._provision_quotas(tenant_id, tier)

            # Provision features
            self._provision_features(tenant_id, tier)

            # Provision default domain
            self._provision_domain(tenant_id, slug)

            # Add owner as admin member
            if owner_id:
                self._provision_owner(tenant_id, owner_id)

            # Provision isolation resources if needed
            if isolation_level != IsolationLevel.SHARED.value:
                self._provision_isolation(tenant_id, isolation_level)

            # Activate tenant
            tenant = tenant_db.tenants.activate(tenant_id)

            return {
                "success": True,
                "tenant": tenant,
                "message": "Tenant provisioned successfully"
            }

        except Exception as e:
            # Rollback on failure
            self._rollback_provisioning(tenant_id)
            raise ValueError(f"Provisioning failed: {str(e)}")

    def _provision_settings(self, tenant_id: str, name: str, slug: str) -> Dict:
        """Provision default tenant settings"""
        return tenant_db.settings.create({
            "tenant_id": tenant_id,
            "email_from_name": name,
            "email_from_address": f"noreply@{slug}.logiaccounting.io",
            "invoice_prefix": slug.upper()[:4],
            "default_currency": "USD"
        })

    def _provision_subscription(self, tenant_id: str, tier: str) -> Dict:
        """Provision subscription"""
        prices = {
            TenantTier.FREE.value: 0,
            TenantTier.STANDARD.value: 2900,
            TenantTier.PROFESSIONAL.value: 7900,
            TenantTier.BUSINESS.value: 19900,
            TenantTier.ENTERPRISE.value: 0
        }

        return tenant_db.subscriptions.create({
            "tenant_id": tenant_id,
            "tier": tier,
            "status": "active",
            "billing_cycle": "monthly",
            "price_cents": prices.get(tier, 0),
            "currency": "USD"
        })

    def _provision_quotas(self, tenant_id: str, tier: str) -> Dict:
        """Provision quota with tier limits"""
        return tenant_db.quotas.create({
            "tenant_id": tenant_id,
            "tier": tier
        })

    def _provision_features(self, tenant_id: str, tier: str) -> List[Dict]:
        """Provision tier features"""
        return tenant_db.features.initialize_tier_features(tenant_id, tier)

    def _provision_domain(self, tenant_id: str, slug: str) -> Dict:
        """Provision default subdomain"""
        return tenant_db.domains.create({
            "tenant_id": tenant_id,
            "domain": f"{slug}.logiaccounting.local",
            "domain_type": "subdomain",
            "is_primary": True,
            "is_verified": True,
            "ssl_status": "active"
        })

    def _provision_owner(self, tenant_id: str, owner_id: str) -> Dict:
        """Add owner as admin member"""
        return tenant_db.members.create({
            "tenant_id": tenant_id,
            "user_id": owner_id,
            "role": "admin",
            "is_owner": True
        })

    def _provision_isolation(self, tenant_id: str, isolation_level: str):
        """
        Provision isolation resources (schema or database).
        In production, this would create actual database resources.
        """
        if isolation_level == IsolationLevel.SCHEMA.value:
            # Create dedicated schema
            pass
        elif isolation_level == IsolationLevel.DATABASE.value:
            # Create dedicated database
            pass

    def _rollback_provisioning(self, tenant_id: str):
        """Rollback partial provisioning on failure"""
        try:
            # Delete settings
            tenant_db.settings.delete(tenant_id)

            # Delete subscriptions
            for sub in tenant_db.subscriptions.find_all_by_tenant(tenant_id):
                # Remove from store
                for i, s in enumerate(tenant_db.subscriptions._data):
                    if s["id"] == sub["id"]:
                        tenant_db.subscriptions._data.pop(i)
                        break

            # Delete quota
            for i, q in enumerate(tenant_db.quotas._data):
                if q.get("tenant_id") == tenant_id:
                    tenant_db.quotas._data.pop(i)
                    break

            # Delete features
            features = tenant_db.features.find_by_tenant(tenant_id)
            for f in features:
                for i, feat in enumerate(tenant_db.features._data):
                    if feat["id"] == f["id"]:
                        tenant_db.features._data.pop(i)
                        break

            # Delete domains
            for domain in tenant_db.domains.find_by_tenant(tenant_id):
                tenant_db.domains.delete(domain["id"])

            # Delete members
            for member in tenant_db.members.find_by_tenant(tenant_id):
                for i, m in enumerate(tenant_db.members._data):
                    if m["id"] == member["id"]:
                        tenant_db.members._data.pop(i)
                        break

            # Delete tenant
            for i, t in enumerate(tenant_db.tenants._data):
                if t["id"] == tenant_id:
                    tenant_db.tenants._data.pop(i)
                    break

        except Exception as e:
            print(f"Rollback error: {e}")

    def deprovision_tenant(self, tenant_id: str, hard_delete: bool = False) -> Dict[str, Any]:
        """
        Deprovision a tenant and clean up resources.
        """
        tenant = tenant_db.tenants.find_by_id(tenant_id)
        if not tenant:
            return {"success": False, "message": "Tenant not found"}

        try:
            if hard_delete:
                # Full data deletion
                self._hard_delete_tenant_data(tenant_id)
            else:
                # Soft delete - mark as deleted
                tenant_db.tenants.delete(tenant_id)

                # Cancel subscription
                subscription = tenant_db.subscriptions.find_by_tenant(tenant_id)
                if subscription:
                    tenant_db.subscriptions.cancel(subscription["id"], at_period_end=False)

            return {
                "success": True,
                "message": "Tenant deprovisioned successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Deprovisioning failed: {str(e)}"
            }

    def _hard_delete_tenant_data(self, tenant_id: str):
        """Permanently delete all tenant data"""
        # Delete invitations
        for inv in tenant_db.invitations.find_by_tenant(tenant_id):
            tenant_db.invitations.delete(inv["id"])

        # Delete domains
        for domain in tenant_db.domains.find_by_tenant(tenant_id):
            tenant_db.domains.delete(domain["id"])

        # Delete settings
        tenant_db.settings.delete(tenant_id)

        # Delete subscription records
        for sub in tenant_db.subscriptions.find_all_by_tenant(tenant_id):
            for i, s in enumerate(tenant_db.subscriptions._data):
                if s["id"] == sub["id"]:
                    tenant_db.subscriptions._data.pop(i)
                    break

        # Delete quota
        for i, q in enumerate(tenant_db.quotas._data):
            if q.get("tenant_id") == tenant_id:
                tenant_db.quotas._data.pop(i)
                break

        # Delete features
        features = tenant_db.features.find_by_tenant(tenant_id)
        for f in features:
            for i, feat in enumerate(tenant_db.features._data):
                if feat["id"] == f["id"]:
                    tenant_db.features._data.pop(i)
                    break

        # Delete members
        for member in tenant_db.members.find_by_tenant(tenant_id):
            for i, m in enumerate(tenant_db.members._data):
                if m["id"] == member["id"]:
                    tenant_db.members._data.pop(i)
                    break

        # Delete tenant record
        for i, t in enumerate(tenant_db.tenants._data):
            if t["id"] == tenant_id:
                tenant_db.tenants._data.pop(i)
                break

    def upgrade_isolation(self, tenant_id: str, new_level: str) -> Dict[str, Any]:
        """
        Upgrade tenant isolation level.
        Migrates data to new isolation strategy.
        """
        tenant = tenant_db.tenants.find_by_id(tenant_id)
        if not tenant:
            return {"success": False, "message": "Tenant not found"}

        current_level = tenant.get("isolation_level")
        if current_level == new_level:
            return {"success": True, "message": "Already at this isolation level"}

        # Validate upgrade path
        levels = [IsolationLevel.SHARED.value, IsolationLevel.SCHEMA.value, IsolationLevel.DATABASE.value]
        current_idx = levels.index(current_level) if current_level in levels else 0
        new_idx = levels.index(new_level) if new_level in levels else 0

        if new_idx < current_idx:
            return {"success": False, "message": "Cannot downgrade isolation level"}

        try:
            # In production, would migrate data to new isolation
            # For now, just update the level
            tenant_db.tenants.update(tenant_id, {"isolation_level": new_level})

            return {
                "success": True,
                "message": f"Upgraded from {current_level} to {new_level}"
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Upgrade failed: {str(e)}"
            }

    def get_provisioning_status(self, tenant_id: str) -> Dict[str, Any]:
        """Get detailed provisioning status"""
        tenant = tenant_db.tenants.find_by_id(tenant_id)
        if not tenant:
            return {"exists": False}

        return {
            "exists": True,
            "tenant_id": tenant_id,
            "status": tenant.get("status"),
            "resources": {
                "settings": tenant_db.settings.find_by_tenant(tenant_id) is not None,
                "subscription": tenant_db.subscriptions.find_by_tenant(tenant_id) is not None,
                "quota": tenant_db.quotas.find_by_tenant(tenant_id) is not None,
                "domains": len(tenant_db.domains.find_by_tenant(tenant_id)),
                "members": tenant_db.members.count_by_tenant(tenant_id),
                "features": len(tenant_db.features.find_by_tenant(tenant_id))
            },
            "isolation_level": tenant.get("isolation_level"),
            "created_at": tenant.get("created_at"),
            "activated_at": tenant.get("activated_at")
        }
