"""
Quota Service
Resource usage tracking and quota enforcement
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from app.models.tenant_store import tenant_db, TenantTier, TIER_QUOTAS


class QuotaService:
    """
    Service for managing tenant resource quotas.
    Tracks usage and enforces limits.
    """

    RESOURCE_TYPES = [
        "users",
        "storage",
        "api_calls",
        "invoices",
        "products",
        "projects",
        "integrations"
    ]

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

    def get_quota(self) -> Optional[Dict[str, Any]]:
        """Get current quota for tenant"""
        return tenant_db.quotas.find_by_tenant(self.tenant_id)

    def check_quota(self, resource: str, increment: int = 1) -> Dict[str, Any]:
        """
        Check if a resource operation is allowed within quota.
        Returns dict with allowed status and details.
        """
        quota = self.get_quota()
        if not quota:
            return {
                "allowed": False,
                "reason": "No quota record found"
            }

        return tenant_db.quotas.check_quota(self.tenant_id, resource, increment)

    def increment_usage(self, resource: str, amount: int = 1) -> Optional[Dict[str, Any]]:
        """Increment resource usage counter"""
        return tenant_db.quotas.increment_usage(self.tenant_id, resource, amount)

    def decrement_usage(self, resource: str, amount: int = 1) -> Optional[Dict[str, Any]]:
        """Decrement resource usage counter"""
        return tenant_db.quotas.decrement_usage(self.tenant_id, resource, amount)

    def get_usage_summary(self) -> Dict[str, Any]:
        """Get complete usage summary with percentages"""
        quota = self.get_quota()
        if not quota:
            return {"error": "No quota found"}

        summary = []
        resources = [
            ("users", "current_users", "max_users"),
            ("storage", "current_storage_mb", "max_storage_mb"),
            ("api_calls", "current_api_calls_today", "max_api_calls_daily"),
            ("invoices", "current_invoices_month", "max_invoices_monthly"),
            ("products", "current_products", "max_products"),
            ("projects", "current_projects", "max_projects"),
            ("integrations", "current_integrations", "max_integrations")
        ]

        for name, current_key, max_key in resources:
            current = quota.get(current_key, 0)
            maximum = quota.get(max_key, 0)
            unlimited = maximum == -1

            if unlimited:
                percentage = 0
            elif maximum > 0:
                percentage = round((current / maximum) * 100, 1)
            else:
                percentage = 0

            summary.append({
                "resource": name,
                "current": current,
                "limit": maximum if not unlimited else -1,
                "percentage": percentage,
                "unlimited": unlimited
            })

        return {
            "tenant_id": self.tenant_id,
            "tier": quota.get("tier"),
            "usage": summary
        }

    def set_usage(self, resource: str, value: int) -> Optional[Dict[str, Any]]:
        """Set absolute usage value for a resource"""
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
            return None

        return tenant_db.quotas.update(self.tenant_id, {
            resource_keys[resource]: max(0, value)
        })

    def reset_daily_counters(self) -> Optional[Dict[str, Any]]:
        """Reset daily usage counters (e.g., API calls)"""
        return tenant_db.quotas.reset_daily_counters(self.tenant_id)

    def reset_monthly_counters(self) -> Optional[Dict[str, Any]]:
        """Reset monthly usage counters (e.g., invoices)"""
        return tenant_db.quotas.reset_monthly_counters(self.tenant_id)

    def update_tier_limits(self, new_tier: str) -> Optional[Dict[str, Any]]:
        """Update quota limits when tier changes"""
        return tenant_db.quotas.update_tier_limits(self.tenant_id, new_tier)

    def get_overage(self) -> Dict[str, Any]:
        """Get resources that are over quota"""
        quota = self.get_quota()
        if not quota:
            return {"overages": []}

        overages = []
        checks = [
            ("users", "current_users", "max_users"),
            ("storage", "current_storage_mb", "max_storage_mb"),
            ("api_calls", "current_api_calls_today", "max_api_calls_daily"),
            ("invoices", "current_invoices_month", "max_invoices_monthly"),
            ("products", "current_products", "max_products"),
            ("projects", "current_projects", "max_projects"),
            ("integrations", "current_integrations", "max_integrations")
        ]

        for name, current_key, max_key in checks:
            current = quota.get(current_key, 0)
            maximum = quota.get(max_key, 0)

            if maximum != -1 and current > maximum:
                overages.append({
                    "resource": name,
                    "current": current,
                    "limit": maximum,
                    "overage": current - maximum
                })

        return {"overages": overages}

    def is_within_quota(self) -> bool:
        """Check if tenant is within all quotas"""
        overage = self.get_overage()
        return len(overage.get("overages", [])) == 0

    def get_quota_alerts(self, threshold: int = 80) -> List[Dict[str, Any]]:
        """
        Get alerts for resources approaching quota limit.
        Default threshold is 80% usage.
        """
        summary = self.get_usage_summary()
        if "error" in summary:
            return []

        alerts = []
        for usage in summary.get("usage", []):
            if usage["unlimited"]:
                continue

            if usage["percentage"] >= threshold:
                alerts.append({
                    "resource": usage["resource"],
                    "current": usage["current"],
                    "limit": usage["limit"],
                    "percentage": usage["percentage"],
                    "severity": "critical" if usage["percentage"] >= 100 else "warning"
                })

        return alerts

    def forecast_usage(self, resource: str, days: int = 30) -> Dict[str, Any]:
        """
        Forecast when a resource will hit its limit.
        Based on current usage rate.
        """
        quota = self.get_quota()
        if not quota:
            return {"error": "No quota found"}

        resource_map = {
            "users": ("current_users", "max_users"),
            "storage": ("current_storage_mb", "max_storage_mb"),
            "products": ("current_products", "max_products"),
            "projects": ("current_projects", "max_projects")
        }

        if resource not in resource_map:
            return {"error": f"Cannot forecast {resource}"}

        current_key, max_key = resource_map[resource]
        current = quota.get(current_key, 0)
        maximum = quota.get(max_key, 0)

        if maximum == -1:
            return {
                "resource": resource,
                "unlimited": True,
                "days_until_limit": None
            }

        remaining = maximum - current
        if remaining <= 0:
            return {
                "resource": resource,
                "unlimited": False,
                "days_until_limit": 0,
                "message": "Quota already exceeded"
            }

        # Simple linear forecast - in production would use historical data
        # Assume average growth rate
        daily_rate = current / max(days, 1) if current > 0 else 0

        if daily_rate <= 0:
            days_remaining = None
        else:
            days_remaining = int(remaining / daily_rate)

        return {
            "resource": resource,
            "current": current,
            "limit": maximum,
            "unlimited": False,
            "daily_rate": round(daily_rate, 2),
            "days_until_limit": days_remaining
        }


class QuotaEnforcer:
    """
    Decorator/helper for enforcing quotas on operations.
    """

    @staticmethod
    def check_and_increment(tenant_id: str, resource: str, amount: int = 1) -> Dict[str, Any]:
        """
        Check quota and increment if allowed.
        Returns result with allowed status.
        """
        service = QuotaService(tenant_id)

        # Check quota
        result = service.check_quota(resource, amount)
        if not result.get("allowed"):
            return result

        # Increment usage
        service.increment_usage(resource, amount)

        return {
            "allowed": True,
            "resource": resource,
            "incremented": amount
        }

    @staticmethod
    def decrement(tenant_id: str, resource: str, amount: int = 1) -> Dict[str, Any]:
        """
        Decrement quota usage (e.g., when resource is deleted).
        """
        service = QuotaService(tenant_id)
        service.decrement_usage(resource, amount)

        return {
            "resource": resource,
            "decremented": amount
        }
