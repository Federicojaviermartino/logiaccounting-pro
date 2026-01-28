"""
Feature Service
Feature flag management for tenants
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from app.models.tenant_store import tenant_db, TenantTier, TIER_FEATURES
from app.utils.datetime_utils import utc_now


class FeatureService:
    """
    Service for managing tenant feature flags.
    Controls feature availability based on tier and custom flags.
    """

    # All available features in the system
    ALL_FEATURES = {
        # Basic Features
        "basic_invoicing": {
            "name": "Basic Invoicing",
            "description": "Create and manage invoices",
            "category": "invoicing"
        },
        "basic_reporting": {
            "name": "Basic Reports",
            "description": "Access standard financial reports",
            "category": "reporting"
        },
        "email_support": {
            "name": "Email Support",
            "description": "Access to email support",
            "category": "support"
        },

        # Standard Features
        "recurring_invoices": {
            "name": "Recurring Invoices",
            "description": "Automated recurring invoice generation",
            "category": "invoicing"
        },
        "multi_currency": {
            "name": "Multi-Currency",
            "description": "Support for multiple currencies",
            "category": "finance"
        },
        "basic_integrations": {
            "name": "Basic Integrations",
            "description": "Connect with basic third-party services",
            "category": "integrations"
        },
        "data_export": {
            "name": "Data Export",
            "description": "Export data to CSV/Excel",
            "category": "data"
        },

        # Professional Features
        "advanced_reporting": {
            "name": "Advanced Reports",
            "description": "Custom reports and dashboards",
            "category": "reporting"
        },
        "api_access": {
            "name": "API Access",
            "description": "Full REST API access",
            "category": "developer"
        },
        "custom_branding": {
            "name": "Custom Branding",
            "description": "White-label with custom logo and colors",
            "category": "branding"
        },
        "workflow_automation": {
            "name": "Workflow Automation",
            "description": "Automated workflows and triggers",
            "category": "automation"
        },
        "priority_support": {
            "name": "Priority Support",
            "description": "Priority email and chat support",
            "category": "support"
        },

        # Business Features
        "advanced_integrations": {
            "name": "Advanced Integrations",
            "description": "Enterprise-grade integrations",
            "category": "integrations"
        },
        "audit_trail": {
            "name": "Audit Trail",
            "description": "Complete audit logging",
            "category": "compliance"
        },
        "custom_fields": {
            "name": "Custom Fields",
            "description": "Add custom data fields",
            "category": "customization"
        },
        "bulk_operations": {
            "name": "Bulk Operations",
            "description": "Bulk import, export, and actions",
            "category": "data"
        },
        "dedicated_support": {
            "name": "Dedicated Support",
            "description": "Dedicated account manager",
            "category": "support"
        },

        # Enterprise Features
        "sso_saml": {
            "name": "SAML SSO",
            "description": "SAML-based single sign-on",
            "category": "security"
        },
        "sso_oidc": {
            "name": "OIDC SSO",
            "description": "OpenID Connect single sign-on",
            "category": "security"
        },
        "custom_isolation": {
            "name": "Custom Isolation",
            "description": "Dedicated schema/database isolation",
            "category": "infrastructure"
        },
        "sla_guarantee": {
            "name": "SLA Guarantee",
            "description": "99.99% uptime SLA",
            "category": "support"
        },
        "white_label": {
            "name": "White Label",
            "description": "Complete white-label solution",
            "category": "branding"
        },
        "dedicated_infrastructure": {
            "name": "Dedicated Infrastructure",
            "description": "Dedicated server resources",
            "category": "infrastructure"
        }
    }

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

    def is_enabled(self, feature_name: str) -> bool:
        """Check if feature is enabled for tenant"""
        tenant = tenant_db.tenants.find_by_id(self.tenant_id)
        if not tenant:
            return False

        tier = tenant.get("tier")
        return tenant_db.features.is_enabled(self.tenant_id, feature_name, tier)

    def get_all_features(self) -> List[Dict[str, Any]]:
        """Get all features with their status for tenant"""
        tenant = tenant_db.tenants.find_by_id(self.tenant_id)
        if not tenant:
            return []

        tier = tenant.get("tier")
        custom_features = tenant_db.features.find_by_tenant(self.tenant_id)

        # Build feature map from custom features
        custom_map = {f["feature_name"]: f for f in custom_features}

        features = []
        for feature_name, info in self.ALL_FEATURES.items():
            # Check if enabled
            is_enabled = tenant_db.features.is_enabled(self.tenant_id, feature_name, tier)

            # Get custom config if any
            custom = custom_map.get(feature_name)

            features.append({
                "name": feature_name,
                "display_name": info["name"],
                "description": info["description"],
                "category": info["category"],
                "is_enabled": is_enabled,
                "is_custom": feature_name in custom_map,
                "config": custom.get("config", {}) if custom else {},
                "expires_at": custom.get("expires_at") if custom else None
            })

        return features

    def get_enabled_features(self) -> List[str]:
        """Get list of enabled feature names"""
        features = self.get_all_features()
        return [f["name"] for f in features if f["is_enabled"]]

    def get_feature(self, feature_name: str) -> Optional[Dict[str, Any]]:
        """Get specific feature details"""
        if feature_name not in self.ALL_FEATURES:
            return None

        tenant = tenant_db.tenants.find_by_id(self.tenant_id)
        if not tenant:
            return None

        tier = tenant.get("tier")
        info = self.ALL_FEATURES[feature_name]
        custom = tenant_db.features.find_feature(self.tenant_id, feature_name)

        return {
            "name": feature_name,
            "display_name": info["name"],
            "description": info["description"],
            "category": info["category"],
            "is_enabled": tenant_db.features.is_enabled(self.tenant_id, feature_name, tier),
            "is_custom": custom is not None,
            "config": custom.get("config", {}) if custom else {},
            "expires_at": custom.get("expires_at") if custom else None,
            "included_in_tier": feature_name in TIER_FEATURES.get(TenantTier(tier), [])
        }

    def enable_feature(
        self,
        feature_name: str,
        config: Dict[str, Any] = None,
        expires_at: str = None
    ) -> Dict[str, Any]:
        """
        Enable a feature for tenant.
        Can be used to grant features outside of tier.
        """
        if feature_name not in self.ALL_FEATURES:
            raise ValueError(f"Unknown feature: {feature_name}")

        return tenant_db.features.enable_feature(
            self.tenant_id,
            feature_name,
            config=config,
            expires_at=expires_at
        )

    def disable_feature(self, feature_name: str) -> Optional[Dict[str, Any]]:
        """Disable a custom feature flag"""
        return tenant_db.features.disable_feature(self.tenant_id, feature_name)

    def update_feature_config(self, feature_name: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update feature configuration"""
        feature = tenant_db.features.find_feature(self.tenant_id, feature_name)
        if not feature:
            return None

        return tenant_db.features.update(feature["id"], {"config": config})

    def get_features_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get features grouped by category"""
        all_features = self.get_all_features()
        return [f for f in all_features if f["category"] == category]

    def get_available_categories(self) -> List[str]:
        """Get list of feature categories"""
        categories = set()
        for info in self.ALL_FEATURES.values():
            categories.add(info["category"])
        return sorted(list(categories))

    def initialize_tier_features(self, tier: str) -> List[Dict[str, Any]]:
        """Initialize features based on tier"""
        return tenant_db.features.initialize_tier_features(self.tenant_id, tier)

    def grant_trial_feature(self, feature_name: str, days: int = 14) -> Dict[str, Any]:
        """Grant a feature for a trial period"""
        if feature_name not in self.ALL_FEATURES:
            raise ValueError(f"Unknown feature: {feature_name}")

        expires_at = (utc_now() + timedelta(days=days)).isoformat()

        return self.enable_feature(
            feature_name,
            config={"trial": True},
            expires_at=expires_at
        )

    def get_upgrade_suggestions(self) -> Dict[str, Any]:
        """
        Get suggestions for tier upgrade based on usage.
        Returns features that would be unlocked.
        """
        tenant = tenant_db.tenants.find_by_id(self.tenant_id)
        if not tenant:
            return {}

        current_tier = tenant.get("tier")
        tiers_order = [
            TenantTier.FREE.value,
            TenantTier.STANDARD.value,
            TenantTier.PROFESSIONAL.value,
            TenantTier.BUSINESS.value,
            TenantTier.ENTERPRISE.value
        ]

        current_idx = tiers_order.index(current_tier) if current_tier in tiers_order else 0

        # Get next tier
        if current_idx >= len(tiers_order) - 1:
            return {"message": "Already at highest tier"}

        next_tier = tiers_order[current_idx + 1]
        current_features = set(TIER_FEATURES.get(TenantTier(current_tier), []))
        next_features = set(TIER_FEATURES.get(TenantTier(next_tier), []))

        # Features unlocked in next tier
        new_features = next_features - current_features

        return {
            "current_tier": current_tier,
            "suggested_tier": next_tier,
            "new_features": [
                {
                    "name": f,
                    "display_name": self.ALL_FEATURES.get(f, {}).get("name", f),
                    "description": self.ALL_FEATURES.get(f, {}).get("description", "")
                }
                for f in new_features
            ]
        }

    def compare_tiers(self) -> Dict[str, Any]:
        """Get comparison of all tiers with features"""
        comparison = {}

        for tier in TenantTier:
            tier_features = TIER_FEATURES.get(tier, [])
            comparison[tier.value] = {
                "features": tier_features,
                "feature_count": len(tier_features),
                "details": [
                    {
                        "name": f,
                        "display_name": self.ALL_FEATURES.get(f, {}).get("name", f),
                        "category": self.ALL_FEATURES.get(f, {}).get("category", "")
                    }
                    for f in tier_features
                ]
            }

        return comparison


def require_feature(tenant_id: str, feature_name: str) -> bool:
    """
    Helper function to check feature availability.
    Raises exception if feature not enabled.
    """
    service = FeatureService(tenant_id)
    if not service.is_enabled(feature_name):
        info = FeatureService.ALL_FEATURES.get(feature_name, {})
        raise PermissionError(
            f"Feature '{info.get('name', feature_name)}' is not enabled. "
            f"Please upgrade your plan to access this feature."
        )
    return True
