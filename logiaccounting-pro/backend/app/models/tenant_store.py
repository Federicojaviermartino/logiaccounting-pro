"""
Multi-Tenancy Data Store
Phase 16 - Enterprise multi-tenant architecture with isolation
"""

import logging
from datetime import datetime, timedelta
from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)
from typing import Optional, List, Dict, Any
from uuid import uuid4
from enum import Enum
import secrets
import hashlib


class TenantStatus(str, Enum):
    """Tenant lifecycle status"""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    DELETED = "deleted"


class TenantTier(str, Enum):
    """Subscription tiers with different feature sets"""
    FREE = "free"
    STANDARD = "standard"
    PROFESSIONAL = "professional"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class IsolationLevel(str, Enum):
    """Data isolation strategies"""
    SHARED = "shared"           # Shared database, row-level isolation
    SCHEMA = "schema"           # Separate schema per tenant
    DATABASE = "database"       # Separate database per tenant


# Tier quota definitions
TIER_QUOTAS = {
    TenantTier.FREE: {
        "max_users": 3,
        "max_storage_mb": 500,
        "max_api_calls_daily": 1000,
        "max_invoices_monthly": 50,
        "max_products": 100,
        "max_projects": 5,
        "max_integrations": 1
    },
    TenantTier.STANDARD: {
        "max_users": 10,
        "max_storage_mb": 5000,
        "max_api_calls_daily": 10000,
        "max_invoices_monthly": 500,
        "max_products": 1000,
        "max_projects": 25,
        "max_integrations": 3
    },
    TenantTier.PROFESSIONAL: {
        "max_users": 25,
        "max_storage_mb": 25000,
        "max_api_calls_daily": 50000,
        "max_invoices_monthly": 2500,
        "max_products": 10000,
        "max_projects": 100,
        "max_integrations": 10
    },
    TenantTier.BUSINESS: {
        "max_users": 100,
        "max_storage_mb": 100000,
        "max_api_calls_daily": 200000,
        "max_invoices_monthly": 10000,
        "max_products": 50000,
        "max_projects": 500,
        "max_integrations": 25
    },
    TenantTier.ENTERPRISE: {
        "max_users": -1,           # Unlimited
        "max_storage_mb": -1,
        "max_api_calls_daily": -1,
        "max_invoices_monthly": -1,
        "max_products": -1,
        "max_projects": -1,
        "max_integrations": -1
    }
}

# Feature availability by tier
TIER_FEATURES = {
    TenantTier.FREE: [
        "basic_invoicing",
        "basic_reporting",
        "email_support"
    ],
    TenantTier.STANDARD: [
        "basic_invoicing",
        "basic_reporting",
        "email_support",
        "recurring_invoices",
        "multi_currency",
        "basic_integrations",
        "data_export"
    ],
    TenantTier.PROFESSIONAL: [
        "basic_invoicing",
        "basic_reporting",
        "email_support",
        "recurring_invoices",
        "multi_currency",
        "basic_integrations",
        "data_export",
        "advanced_reporting",
        "api_access",
        "custom_branding",
        "workflow_automation",
        "priority_support"
    ],
    TenantTier.BUSINESS: [
        "basic_invoicing",
        "basic_reporting",
        "email_support",
        "recurring_invoices",
        "multi_currency",
        "basic_integrations",
        "data_export",
        "advanced_reporting",
        "api_access",
        "custom_branding",
        "workflow_automation",
        "priority_support",
        "advanced_integrations",
        "audit_trail",
        "custom_fields",
        "bulk_operations",
        "dedicated_support"
    ],
    TenantTier.ENTERPRISE: [
        "basic_invoicing",
        "basic_reporting",
        "email_support",
        "recurring_invoices",
        "multi_currency",
        "basic_integrations",
        "data_export",
        "advanced_reporting",
        "api_access",
        "custom_branding",
        "workflow_automation",
        "priority_support",
        "advanced_integrations",
        "audit_trail",
        "custom_fields",
        "bulk_operations",
        "dedicated_support",
        "sso_saml",
        "sso_oidc",
        "custom_isolation",
        "sla_guarantee",
        "white_label",
        "dedicated_infrastructure"
    ]
}


class TenantStore:
    """Core tenant entity store"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []

    def create(self, data: Dict) -> Dict:
        """Create a new tenant"""
        now = utc_now().isoformat()
        tenant_id = data.get("id") or f"tenant-{uuid4().hex[:12]}"
        slug = data.get("slug") or self._generate_slug(data.get("name", "tenant"))

        tenant = {
            "id": tenant_id,
            "name": data.get("name"),
            "slug": slug,
            "display_name": data.get("display_name") or data.get("name"),
            "status": data.get("status", TenantStatus.PENDING.value),
            "tier": data.get("tier", TenantTier.FREE.value),
            "isolation_level": data.get("isolation_level", IsolationLevel.SHARED.value),
            "owner_id": data.get("owner_id"),
            "owner_email": data.get("owner_email"),
            "billing_email": data.get("billing_email") or data.get("owner_email"),
            "country": data.get("country"),
            "timezone": data.get("timezone", "UTC"),
            "locale": data.get("locale", "en"),
            "metadata": data.get("metadata", {}),
            "created_at": now,
            "updated_at": now,
            "activated_at": None,
            "suspended_at": None,
            "deleted_at": None
        }

        self._data.append(tenant)
        return tenant

    def _generate_slug(self, name: str) -> str:
        """Generate URL-safe slug from name"""
        import re
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')

        # Ensure uniqueness
        base_slug = slug
        counter = 1
        while self.find_by_slug(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug

    def find_by_id(self, tenant_id: str) -> Optional[Dict]:
        """Find tenant by ID"""
        return next((t for t in self._data if t["id"] == tenant_id), None)

    def find_by_slug(self, slug: str) -> Optional[Dict]:
        """Find tenant by slug"""
        return next((t for t in self._data if t.get("slug") == slug), None)

    def find_by_owner(self, owner_id: str) -> List[Dict]:
        """Find tenants by owner"""
        return [t for t in self._data if t.get("owner_id") == owner_id]

    def find_all(self, filters: Optional[Dict] = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Find all tenants with filters"""
        results = [t for t in self._data if t.get("status") != TenantStatus.DELETED.value]

        if filters:
            if filters.get("status"):
                results = [t for t in results if t.get("status") == filters["status"]]
            if filters.get("tier"):
                results = [t for t in results if t.get("tier") == filters["tier"]]
            if filters.get("search"):
                search = filters["search"].lower()
                results = [
                    t for t in results
                    if search in t.get("name", "").lower() or
                       search in t.get("slug", "").lower() or
                       search in t.get("owner_email", "").lower()
                ]

        results = sorted(results, key=lambda x: x.get("created_at", ""), reverse=True)
        return results[offset:offset + limit]

    def count(self, filters: Optional[Dict] = None) -> int:
        """Count tenants matching filters"""
        return len(self.find_all(filters, limit=100000))

    def update(self, tenant_id: str, data: Dict) -> Optional[Dict]:
        """Update a tenant"""
        for i, tenant in enumerate(self._data):
            if tenant["id"] == tenant_id:
                self._data[i] = {
                    **tenant,
                    **data,
                    "updated_at": utc_now().isoformat()
                }
                return self._data[i]
        return None

    def activate(self, tenant_id: str) -> Optional[Dict]:
        """Activate a tenant"""
        return self.update(tenant_id, {
            "status": TenantStatus.ACTIVE.value,
            "activated_at": utc_now().isoformat()
        })

    def suspend(self, tenant_id: str, reason: str = None) -> Optional[Dict]:
        """Suspend a tenant"""
        data = {
            "status": TenantStatus.SUSPENDED.value,
            "suspended_at": utc_now().isoformat()
        }
        if reason:
            data["suspension_reason"] = reason
        return self.update(tenant_id, data)

    def delete(self, tenant_id: str) -> Optional[Dict]:
        """Soft delete a tenant"""
        return self.update(tenant_id, {
            "status": TenantStatus.DELETED.value,
            "deleted_at": utc_now().isoformat()
        })


class TenantDomainStore:
    """Custom domain management for tenants"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []

    def create(self, data: Dict) -> Dict:
        """Create a domain mapping"""
        now = utc_now().isoformat()
        domain = {
            "id": str(uuid4()),
            "tenant_id": data.get("tenant_id"),
            "domain": data.get("domain"),
            "domain_type": data.get("domain_type", "subdomain"),  # custom, subdomain
            "is_primary": data.get("is_primary", False),
            "is_verified": data.get("is_verified", False),
            "verification_token": secrets.token_urlsafe(32),
            "verification_method": data.get("verification_method", "dns_txt"),
            "ssl_status": data.get("ssl_status", "pending"),
            "ssl_certificate_id": data.get("ssl_certificate_id"),
            "created_at": now,
            "updated_at": now,
            "verified_at": None
        }
        self._data.append(domain)
        return domain

    def find_by_id(self, domain_id: str) -> Optional[Dict]:
        return next((d for d in self._data if d["id"] == domain_id), None)

    def find_by_domain(self, domain: str) -> Optional[Dict]:
        """Find domain mapping by domain name"""
        return next((d for d in self._data if d.get("domain") == domain), None)

    def find_by_tenant(self, tenant_id: str) -> List[Dict]:
        """Find all domains for a tenant"""
        return [d for d in self._data if d.get("tenant_id") == tenant_id]

    def get_primary_domain(self, tenant_id: str) -> Optional[Dict]:
        """Get primary domain for tenant"""
        return next(
            (d for d in self._data if d.get("tenant_id") == tenant_id and d.get("is_primary")),
            None
        )

    def update(self, domain_id: str, data: Dict) -> Optional[Dict]:
        for i, domain in enumerate(self._data):
            if domain["id"] == domain_id:
                self._data[i] = {
                    **domain,
                    **data,
                    "updated_at": utc_now().isoformat()
                }
                return self._data[i]
        return None

    def verify(self, domain_id: str) -> Optional[Dict]:
        """Mark domain as verified"""
        return self.update(domain_id, {
            "is_verified": True,
            "verified_at": utc_now().isoformat()
        })

    def delete(self, domain_id: str) -> bool:
        for i, domain in enumerate(self._data):
            if domain["id"] == domain_id:
                self._data.pop(i)
                return True
        return False


class TenantSettingsStore:
    """Tenant-specific settings and configuration"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []

    def create(self, data: Dict) -> Dict:
        """Create or initialize settings for a tenant"""
        now = utc_now().isoformat()
        settings = {
            "id": str(uuid4()),
            "tenant_id": data.get("tenant_id"),
            # Branding
            "logo_url": data.get("logo_url"),
            "favicon_url": data.get("favicon_url"),
            "primary_color": data.get("primary_color", "#3B82F6"),
            "secondary_color": data.get("secondary_color", "#10B981"),
            "custom_css": data.get("custom_css"),
            # Email
            "email_from_name": data.get("email_from_name"),
            "email_from_address": data.get("email_from_address"),
            "email_reply_to": data.get("email_reply_to"),
            "email_footer": data.get("email_footer"),
            # Invoice
            "invoice_prefix": data.get("invoice_prefix", "INV"),
            "invoice_starting_number": data.get("invoice_starting_number", 1001),
            "invoice_footer": data.get("invoice_footer"),
            "default_payment_terms": data.get("default_payment_terms", 30),
            "default_tax_rate": data.get("default_tax_rate", 0),
            "default_currency": data.get("default_currency", "USD"),
            # Security
            "require_2fa": data.get("require_2fa", False),
            "allowed_ip_ranges": data.get("allowed_ip_ranges", []),
            "session_timeout_minutes": data.get("session_timeout_minutes", 480),
            "password_min_length": data.get("password_min_length", 8),
            "password_require_special": data.get("password_require_special", True),
            # Integrations
            "webhook_secret": secrets.token_urlsafe(32),
            "api_rate_limit": data.get("api_rate_limit", 1000),
            # Timestamps
            "created_at": now,
            "updated_at": now
        }
        self._data.append(settings)
        return settings

    def find_by_tenant(self, tenant_id: str) -> Optional[Dict]:
        """Find settings for a tenant"""
        return next((s for s in self._data if s.get("tenant_id") == tenant_id), None)

    def update(self, tenant_id: str, data: Dict) -> Optional[Dict]:
        """Update tenant settings"""
        for i, settings in enumerate(self._data):
            if settings.get("tenant_id") == tenant_id:
                self._data[i] = {
                    **settings,
                    **data,
                    "updated_at": utc_now().isoformat()
                }
                return self._data[i]
        return None

    def delete(self, tenant_id: str) -> bool:
        for i, settings in enumerate(self._data):
            if settings.get("tenant_id") == tenant_id:
                self._data.pop(i)
                return True
        return False


class TenantSubscriptionStore:
    """Billing and subscription management"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []

    def create(self, data: Dict) -> Dict:
        """Create a subscription"""
        now = utc_now().isoformat()
        subscription = {
            "id": str(uuid4()),
            "tenant_id": data.get("tenant_id"),
            "tier": data.get("tier", TenantTier.FREE.value),
            "status": data.get("status", "active"),
            "billing_cycle": data.get("billing_cycle", "monthly"),
            "price_cents": data.get("price_cents", 0),
            "currency": data.get("currency", "USD"),
            "payment_method_id": data.get("payment_method_id"),
            "stripe_subscription_id": data.get("stripe_subscription_id"),
            "stripe_customer_id": data.get("stripe_customer_id"),
            "current_period_start": data.get("current_period_start", now),
            "current_period_end": data.get("current_period_end"),
            "trial_ends_at": data.get("trial_ends_at"),
            "cancelled_at": data.get("cancelled_at"),
            "cancel_at_period_end": data.get("cancel_at_period_end", False),
            "created_at": now,
            "updated_at": now
        }
        self._data.append(subscription)
        return subscription

    def find_by_id(self, sub_id: str) -> Optional[Dict]:
        return next((s for s in self._data if s["id"] == sub_id), None)

    def find_by_tenant(self, tenant_id: str) -> Optional[Dict]:
        """Get active subscription for tenant"""
        return next(
            (s for s in self._data
             if s.get("tenant_id") == tenant_id and s.get("status") in ["active", "trialing"]),
            None
        )

    def find_all_by_tenant(self, tenant_id: str) -> List[Dict]:
        """Get all subscriptions for tenant"""
        return [s for s in self._data if s.get("tenant_id") == tenant_id]

    def update(self, sub_id: str, data: Dict) -> Optional[Dict]:
        for i, sub in enumerate(self._data):
            if sub["id"] == sub_id:
                self._data[i] = {
                    **sub,
                    **data,
                    "updated_at": utc_now().isoformat()
                }
                return self._data[i]
        return None

    def cancel(self, sub_id: str, at_period_end: bool = True) -> Optional[Dict]:
        """Cancel a subscription"""
        data = {
            "cancelled_at": utc_now().isoformat(),
            "cancel_at_period_end": at_period_end
        }
        if not at_period_end:
            data["status"] = "cancelled"
        return self.update(sub_id, data)


class TenantQuotaStore:
    """Resource quota tracking and enforcement"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []

    def create(self, data: Dict) -> Dict:
        """Create quota record for tenant"""
        now = utc_now().isoformat()
        tier = data.get("tier", TenantTier.FREE.value)
        limits = TIER_QUOTAS.get(TenantTier(tier), TIER_QUOTAS[TenantTier.FREE])

        quota = {
            "id": str(uuid4()),
            "tenant_id": data.get("tenant_id"),
            "tier": tier,
            # Limits from tier
            "max_users": limits["max_users"],
            "max_storage_mb": limits["max_storage_mb"],
            "max_api_calls_daily": limits["max_api_calls_daily"],
            "max_invoices_monthly": limits["max_invoices_monthly"],
            "max_products": limits["max_products"],
            "max_projects": limits["max_projects"],
            "max_integrations": limits["max_integrations"],
            # Current usage
            "current_users": data.get("current_users", 0),
            "current_storage_mb": data.get("current_storage_mb", 0),
            "current_api_calls_today": data.get("current_api_calls_today", 0),
            "current_invoices_month": data.get("current_invoices_month", 0),
            "current_products": data.get("current_products", 0),
            "current_projects": data.get("current_projects", 0),
            "current_integrations": data.get("current_integrations", 0),
            # Reset tracking
            "api_calls_reset_at": now,
            "invoices_reset_at": now,
            "created_at": now,
            "updated_at": now
        }
        self._data.append(quota)
        return quota

    def find_by_tenant(self, tenant_id: str) -> Optional[Dict]:
        return next((q for q in self._data if q.get("tenant_id") == tenant_id), None)

    def update(self, tenant_id: str, data: Dict) -> Optional[Dict]:
        for i, quota in enumerate(self._data):
            if quota.get("tenant_id") == tenant_id:
                self._data[i] = {
                    **quota,
                    **data,
                    "updated_at": utc_now().isoformat()
                }
                return self._data[i]
        return None

    def check_quota(self, tenant_id: str, resource: str, increment: int = 1) -> Dict:
        """Check if quota allows the operation"""
        quota = self.find_by_tenant(tenant_id)
        if not quota:
            return {"allowed": False, "reason": "No quota record found"}

        resource_map = {
            "users": ("current_users", "max_users"),
            "storage": ("current_storage_mb", "max_storage_mb"),
            "api_calls": ("current_api_calls_today", "max_api_calls_daily"),
            "invoices": ("current_invoices_month", "max_invoices_monthly"),
            "products": ("current_products", "max_products"),
            "projects": ("current_projects", "max_projects"),
            "integrations": ("current_integrations", "max_integrations")
        }

        if resource not in resource_map:
            return {"allowed": True}

        current_key, max_key = resource_map[resource]
        current = quota.get(current_key, 0)
        maximum = quota.get(max_key, 0)

        # -1 means unlimited
        if maximum == -1:
            return {"allowed": True, "current": current, "limit": "unlimited"}

        if current + increment > maximum:
            return {
                "allowed": False,
                "reason": f"Quota exceeded for {resource}",
                "current": current,
                "limit": maximum,
                "requested": increment
            }

        return {"allowed": True, "current": current, "limit": maximum}

    def increment_usage(self, tenant_id: str, resource: str, amount: int = 1) -> Optional[Dict]:
        """Increment resource usage"""
        quota = self.find_by_tenant(tenant_id)
        if not quota:
            return None

        resource_keys = {
            "users": "current_users",
            "storage": "current_storage_mb",
            "api_calls": "current_api_calls_today",
            "invoices": "current_invoices_month",
            "products": "current_products",
            "projects": "current_projects",
            "integrations": "current_integrations"
        }

        if resource not in resource_keys:
            return quota

        key = resource_keys[resource]
        new_value = quota.get(key, 0) + amount

        return self.update(tenant_id, {key: new_value})

    def decrement_usage(self, tenant_id: str, resource: str, amount: int = 1) -> Optional[Dict]:
        """Decrement resource usage"""
        return self.increment_usage(tenant_id, resource, -amount)

    def reset_daily_counters(self, tenant_id: str) -> Optional[Dict]:
        """Reset daily counters (API calls)"""
        return self.update(tenant_id, {
            "current_api_calls_today": 0,
            "api_calls_reset_at": utc_now().isoformat()
        })

    def reset_monthly_counters(self, tenant_id: str) -> Optional[Dict]:
        """Reset monthly counters (invoices)"""
        return self.update(tenant_id, {
            "current_invoices_month": 0,
            "invoices_reset_at": utc_now().isoformat()
        })

    def update_tier_limits(self, tenant_id: str, tier: str) -> Optional[Dict]:
        """Update quota limits when tier changes"""
        limits = TIER_QUOTAS.get(TenantTier(tier), TIER_QUOTAS[TenantTier.FREE])
        return self.update(tenant_id, {
            "tier": tier,
            "max_users": limits["max_users"],
            "max_storage_mb": limits["max_storage_mb"],
            "max_api_calls_daily": limits["max_api_calls_daily"],
            "max_invoices_monthly": limits["max_invoices_monthly"],
            "max_products": limits["max_products"],
            "max_projects": limits["max_projects"],
            "max_integrations": limits["max_integrations"]
        })


class TenantFeatureStore:
    """Feature flag management per tenant"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []

    def create(self, data: Dict) -> Dict:
        """Create feature flag for tenant"""
        now = utc_now().isoformat()
        feature = {
            "id": str(uuid4()),
            "tenant_id": data.get("tenant_id"),
            "feature_name": data.get("feature_name"),
            "is_enabled": data.get("is_enabled", True),
            "config": data.get("config", {}),
            "expires_at": data.get("expires_at"),
            "created_at": now,
            "updated_at": now
        }
        self._data.append(feature)
        return feature

    def find_by_tenant(self, tenant_id: str) -> List[Dict]:
        """Get all features for tenant"""
        return [f for f in self._data if f.get("tenant_id") == tenant_id]

    def find_feature(self, tenant_id: str, feature_name: str) -> Optional[Dict]:
        """Find specific feature for tenant"""
        return next(
            (f for f in self._data
             if f.get("tenant_id") == tenant_id and f.get("feature_name") == feature_name),
            None
        )

    def is_enabled(self, tenant_id: str, feature_name: str, tier: str = None) -> bool:
        """Check if feature is enabled for tenant"""
        # First check explicit feature flag
        feature = self.find_feature(tenant_id, feature_name)

        if feature:
            # Check expiration
            if feature.get("expires_at"):
                try:
                    expires = datetime.fromisoformat(feature["expires_at"])
                    if utc_now() > expires:
                        return False
                except (ValueError, TypeError):
                    pass
            return feature.get("is_enabled", False)

        # Fall back to tier-based features
        if tier:
            try:
                tier_enum = TenantTier(tier)
                tier_features = TIER_FEATURES.get(tier_enum, [])
                return feature_name in tier_features
            except ValueError:
                pass

        return False

    def enable_feature(self, tenant_id: str, feature_name: str, config: Dict = None, expires_at: str = None) -> Dict:
        """Enable a feature for tenant"""
        existing = self.find_feature(tenant_id, feature_name)

        if existing:
            return self.update(existing["id"], {
                "is_enabled": True,
                "config": config or existing.get("config", {}),
                "expires_at": expires_at
            })

        return self.create({
            "tenant_id": tenant_id,
            "feature_name": feature_name,
            "is_enabled": True,
            "config": config or {},
            "expires_at": expires_at
        })

    def disable_feature(self, tenant_id: str, feature_name: str) -> Optional[Dict]:
        """Disable a feature for tenant"""
        existing = self.find_feature(tenant_id, feature_name)
        if existing:
            return self.update(existing["id"], {"is_enabled": False})
        return None

    def update(self, feature_id: str, data: Dict) -> Optional[Dict]:
        for i, feature in enumerate(self._data):
            if feature["id"] == feature_id:
                self._data[i] = {
                    **feature,
                    **data,
                    "updated_at": utc_now().isoformat()
                }
                return self._data[i]
        return None

    def initialize_tier_features(self, tenant_id: str, tier: str) -> List[Dict]:
        """Initialize features based on tier"""
        try:
            tier_enum = TenantTier(tier)
            features = TIER_FEATURES.get(tier_enum, [])

            created = []
            for feature_name in features:
                if not self.find_feature(tenant_id, feature_name):
                    created.append(self.create({
                        "tenant_id": tenant_id,
                        "feature_name": feature_name,
                        "is_enabled": True
                    }))

            return created
        except ValueError:
            return []


class TenantInvitationStore:
    """Team member invitation management"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []

    def create(self, data: Dict) -> Dict:
        """Create invitation"""
        now = utc_now().isoformat()
        expires_at = data.get("expires_at")
        if not expires_at:
            expires_at = (utc_now() + timedelta(days=7)).isoformat()

        invitation = {
            "id": str(uuid4()),
            "tenant_id": data.get("tenant_id"),
            "email": data.get("email"),
            "role": data.get("role", "member"),
            "invited_by": data.get("invited_by"),
            "token": secrets.token_urlsafe(32),
            "status": data.get("status", "pending"),
            "expires_at": expires_at,
            "accepted_at": None,
            "accepted_by_user_id": None,
            "created_at": now,
            "updated_at": now
        }
        self._data.append(invitation)
        return invitation

    def find_by_id(self, invitation_id: str) -> Optional[Dict]:
        return next((i for i in self._data if i["id"] == invitation_id), None)

    def find_by_token(self, token: str) -> Optional[Dict]:
        """Find invitation by token"""
        return next((i for i in self._data if i.get("token") == token), None)

    def find_by_email(self, tenant_id: str, email: str) -> Optional[Dict]:
        """Find pending invitation by email"""
        return next(
            (i for i in self._data
             if i.get("tenant_id") == tenant_id and
                i.get("email") == email and
                i.get("status") == "pending"),
            None
        )

    def find_by_tenant(self, tenant_id: str, status: str = None) -> List[Dict]:
        """Get all invitations for tenant"""
        results = [i for i in self._data if i.get("tenant_id") == tenant_id]
        if status:
            results = [i for i in results if i.get("status") == status]
        return sorted(results, key=lambda x: x.get("created_at", ""), reverse=True)

    def update(self, invitation_id: str, data: Dict) -> Optional[Dict]:
        for i, inv in enumerate(self._data):
            if inv["id"] == invitation_id:
                self._data[i] = {
                    **inv,
                    **data,
                    "updated_at": utc_now().isoformat()
                }
                return self._data[i]
        return None

    def accept(self, invitation_id: str, user_id: str) -> Optional[Dict]:
        """Mark invitation as accepted"""
        return self.update(invitation_id, {
            "status": "accepted",
            "accepted_at": utc_now().isoformat(),
            "accepted_by_user_id": user_id
        })

    def revoke(self, invitation_id: str) -> Optional[Dict]:
        """Revoke an invitation"""
        return self.update(invitation_id, {"status": "revoked"})

    def is_valid(self, invitation: Dict) -> bool:
        """Check if invitation is valid"""
        if invitation.get("status") != "pending":
            return False

        expires_at = invitation.get("expires_at")
        if expires_at:
            try:
                expires = datetime.fromisoformat(expires_at)
                if utc_now() > expires:
                    return False
            except (ValueError, TypeError):
                pass

        return True

    def delete(self, invitation_id: str) -> bool:
        for i, inv in enumerate(self._data):
            if inv["id"] == invitation_id:
                self._data.pop(i)
                return True
        return False


class TenantMemberStore:
    """Tenant membership management"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []

    def create(self, data: Dict) -> Dict:
        """Add user to tenant"""
        now = utc_now().isoformat()
        member = {
            "id": str(uuid4()),
            "tenant_id": data.get("tenant_id"),
            "user_id": data.get("user_id"),
            "role": data.get("role", "member"),
            "is_owner": data.get("is_owner", False),
            "permissions": data.get("permissions", []),
            "joined_at": now,
            "invited_by": data.get("invited_by"),
            "created_at": now,
            "updated_at": now
        }
        self._data.append(member)
        return member

    def find_by_id(self, member_id: str) -> Optional[Dict]:
        return next((m for m in self._data if m["id"] == member_id), None)

    def find_membership(self, tenant_id: str, user_id: str) -> Optional[Dict]:
        """Find user's membership in tenant"""
        return next(
            (m for m in self._data
             if m.get("tenant_id") == tenant_id and m.get("user_id") == user_id),
            None
        )

    def find_by_tenant(self, tenant_id: str) -> List[Dict]:
        """Get all members of a tenant"""
        return [m for m in self._data if m.get("tenant_id") == tenant_id]

    def find_by_user(self, user_id: str) -> List[Dict]:
        """Get all tenant memberships for a user"""
        return [m for m in self._data if m.get("user_id") == user_id]

    def count_by_tenant(self, tenant_id: str) -> int:
        """Count members in tenant"""
        return len(self.find_by_tenant(tenant_id))

    def update(self, member_id: str, data: Dict) -> Optional[Dict]:
        for i, member in enumerate(self._data):
            if member["id"] == member_id:
                self._data[i] = {
                    **member,
                    **data,
                    "updated_at": utc_now().isoformat()
                }
                return self._data[i]
        return None

    def remove(self, tenant_id: str, user_id: str) -> bool:
        """Remove user from tenant"""
        for i, member in enumerate(self._data):
            if member.get("tenant_id") == tenant_id and member.get("user_id") == user_id:
                self._data.pop(i)
                return True
        return False


class TenantDatabase:
    """Container for all tenant-related stores"""

    def __init__(self):
        self.tenants = TenantStore()
        self.domains = TenantDomainStore()
        self.settings = TenantSettingsStore()
        self.subscriptions = TenantSubscriptionStore()
        self.quotas = TenantQuotaStore()
        self.features = TenantFeatureStore()
        self.invitations = TenantInvitationStore()
        self.members = TenantMemberStore()


# Global instance
tenant_db = TenantDatabase()


def init_tenant_database():
    """Initialize tenant database with demo data"""
    # Create demo tenant
    demo_tenant = tenant_db.tenants.create({
        "id": "tenant-demo-001",
        "name": "LogiAccounting Demo",
        "slug": "demo",
        "display_name": "LogiAccounting Demo Company",
        "status": TenantStatus.ACTIVE.value,
        "tier": TenantTier.PROFESSIONAL.value,
        "isolation_level": IsolationLevel.SHARED.value,
        "owner_id": "user-admin-001",
        "owner_email": "admin@logiaccounting.demo",
        "billing_email": "billing@logiaccounting.demo",
        "country": "US",
        "timezone": "America/New_York"
    })
    demo_tenant = tenant_db.tenants.activate(demo_tenant["id"])

    # Create demo domain
    tenant_db.domains.create({
        "tenant_id": demo_tenant["id"],
        "domain": "demo.logiaccounting.local",
        "domain_type": "subdomain",
        "is_primary": True,
        "is_verified": True,
        "ssl_status": "active"
    })

    # Create demo settings
    tenant_db.settings.create({
        "tenant_id": demo_tenant["id"],
        "logo_url": "/assets/demo-logo.png",
        "primary_color": "#3B82F6",
        "secondary_color": "#10B981",
        "email_from_name": "LogiAccounting Demo",
        "email_from_address": "noreply@logiaccounting.demo",
        "invoice_prefix": "DEMO",
        "default_currency": "USD"
    })

    # Create demo subscription
    tenant_db.subscriptions.create({
        "tenant_id": demo_tenant["id"],
        "tier": TenantTier.PROFESSIONAL.value,
        "status": "active",
        "billing_cycle": "monthly",
        "price_cents": 7900,
        "currency": "USD"
    })

    # Create demo quota
    tenant_db.quotas.create({
        "tenant_id": demo_tenant["id"],
        "tier": TenantTier.PROFESSIONAL.value,
        "current_users": 3,
        "current_storage_mb": 1250,
        "current_products": 150,
        "current_projects": 12
    })

    # Initialize features for tier
    tenant_db.features.initialize_tier_features(demo_tenant["id"], TenantTier.PROFESSIONAL.value)

    # Add owner as member
    tenant_db.members.create({
        "tenant_id": demo_tenant["id"],
        "user_id": "user-admin-001",
        "role": "admin",
        "is_owner": True
    })

    # Create enterprise tenant for showcase
    enterprise_tenant = tenant_db.tenants.create({
        "id": "tenant-enterprise-001",
        "name": "Enterprise Corp",
        "slug": "enterprise",
        "status": TenantStatus.ACTIVE.value,
        "tier": TenantTier.ENTERPRISE.value,
        "isolation_level": IsolationLevel.SCHEMA.value,
        "owner_id": "user-enterprise-001",
        "owner_email": "admin@enterprise.example",
        "country": "US"
    })
    tenant_db.tenants.activate(enterprise_tenant["id"])
    tenant_db.quotas.create({
        "tenant_id": enterprise_tenant["id"],
        "tier": TenantTier.ENTERPRISE.value
    })
    tenant_db.features.initialize_tier_features(enterprise_tenant["id"], TenantTier.ENTERPRISE.value)

    logger.info("Tenant database initialized with demo data")
