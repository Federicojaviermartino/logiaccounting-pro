"""
Enhanced API Key Management Service
Phase 17 - API Gateway with scopes, rate limits, IP restrictions
"""

import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from app.utils.datetime_utils import utc_now

from app.models.gateway_store import gateway_db
from app.middleware.tenant_context import TenantContext


class APIKeyService:
    """Enhanced API Key management service"""

    _instance = None

    # Available scopes for API keys
    SCOPES = {
        "invoices:read": "View invoices",
        "invoices:write": "Create and update invoices",
        "inventory:read": "View products and inventory",
        "inventory:write": "Manage products and inventory",
        "customers:read": "View customers",
        "customers:write": "Manage customers",
        "suppliers:read": "View suppliers",
        "suppliers:write": "Manage suppliers",
        "projects:read": "View projects",
        "projects:write": "Manage projects",
        "payments:read": "View payments",
        "payments:write": "Process payments",
        "reports:read": "Generate reports",
        "documents:read": "View documents",
        "documents:write": "Upload and manage documents",
        "webhooks:manage": "Manage webhooks",
        "*": "Full access to all resources"
    }

    # Default rate limits by tier
    RATE_LIMITS = {
        "free": {"minute": 30, "hour": 500, "day": 5000},
        "standard": {"minute": 100, "hour": 2000, "day": 20000},
        "professional": {"minute": 300, "hour": 10000, "day": 100000},
        "business": {"minute": 1000, "hour": 50000, "day": 500000},
        "enterprise": {"minute": 5000, "hour": 200000, "day": 2000000}
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def create_api_key(
        self,
        name: str,
        scopes: List[str] = None,
        description: str = None,
        environment: str = "production",
        expires_days: int = None,
        allowed_ips: List[str] = None,
        rate_limit_per_minute: int = None,
        rate_limit_per_hour: int = None,
        rate_limit_per_day: int = None,
        created_by: str = None,
        tenant_id: str = None
    ) -> Dict[str, Any]:
        """
        Create a new API key

        Returns dict with api_key data and raw_key (shown only once)
        """
        if tenant_id is None:
            tenant_id = TenantContext.get_tenant_id()

        # Validate scopes
        if scopes:
            invalid_scopes = [s for s in scopes if s not in self.SCOPES]
            if invalid_scopes:
                raise ValueError(f"Invalid scopes: {invalid_scopes}")
        else:
            scopes = ["invoices:read", "customers:read", "inventory:read"]

        # Calculate expiration
        expires_at = None
        if expires_days:
            expires_at = (utc_now() + timedelta(days=expires_days)).isoformat()

        # Create key
        result = gateway_db.api_keys.create({
            "tenant_id": tenant_id,
            "name": name,
            "description": description,
            "scopes": scopes,
            "environment": environment,
            "allowed_ips": allowed_ips or [],
            "rate_limit_per_minute": rate_limit_per_minute,
            "rate_limit_per_hour": rate_limit_per_hour,
            "rate_limit_per_day": rate_limit_per_day,
            "expires_at": expires_at,
            "created_by": created_by
        })

        return {
            "api_key": self._format_key(result),
            "key": result["raw_key"]  # Only shown once!
        }

    def validate_key(self, raw_key: str) -> Optional[Dict]:
        """
        Validate an API key and return its data

        Returns None if key is invalid, expired, or inactive
        """
        key = gateway_db.api_keys.find_by_raw_key(raw_key)

        if not key:
            return None

        if not key.get("is_active"):
            return None

        # Check expiration
        if key.get("expires_at"):
            if datetime.fromisoformat(key["expires_at"]) < utc_now():
                return None

        return key

    def check_scope(self, key_data: Dict, required_scope: str) -> bool:
        """Check if API key has the required scope"""
        scopes = key_data.get("scopes", [])

        # Full access
        if "*" in scopes:
            return True

        # Direct match
        if required_scope in scopes:
            return True

        # Wildcard match (e.g., "invoices:*" for "invoices:read")
        scope_base = required_scope.split(":")[0] if ":" in required_scope else required_scope
        if f"{scope_base}:*" in scopes:
            return True

        return False

    def check_ip(self, key_data: Dict, client_ip: str) -> bool:
        """Check if IP is allowed for this key"""
        allowed_ips = key_data.get("allowed_ips", [])

        if not allowed_ips:
            return True  # No restrictions

        return client_ip in allowed_ips

    def get_rate_limits(self, key_data: Dict, tier: str = "standard") -> Dict[str, int]:
        """Get effective rate limits for a key"""
        # Key-specific limits take precedence
        limits = {
            "minute": key_data.get("rate_limit_per_minute"),
            "hour": key_data.get("rate_limit_per_hour"),
            "day": key_data.get("rate_limit_per_day")
        }

        # Fall back to tier defaults
        tier_limits = self.RATE_LIMITS.get(tier, self.RATE_LIMITS["standard"])

        return {
            "minute": limits["minute"] or tier_limits["minute"],
            "hour": limits["hour"] or tier_limits["hour"],
            "day": limits["day"] or tier_limits["day"]
        }

    def record_usage(self, key_id: str):
        """Record API key usage"""
        gateway_db.api_keys.record_usage(key_id)

    def get_key(self, key_id: str, tenant_id: str = None) -> Optional[Dict]:
        """Get API key by ID"""
        if tenant_id is None:
            tenant_id = TenantContext.get_tenant_id()

        key = gateway_db.api_keys.find_by_id(key_id)

        if key and key.get("tenant_id") == tenant_id:
            return self._format_key(key)

        return None

    def list_keys(
        self,
        tenant_id: str = None,
        is_active: bool = None,
        environment: str = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """List API keys for tenant"""
        if tenant_id is None:
            tenant_id = TenantContext.get_tenant_id()

        filters = {"tenant_id": tenant_id}
        if is_active is not None:
            filters["is_active"] = is_active
        if environment:
            filters["environment"] = environment

        keys = gateway_db.api_keys.find_all(filters)

        # Pagination
        total = len(keys)
        start = (page - 1) * per_page
        end = start + per_page
        keys = keys[start:end]

        return {
            "keys": [self._format_key(k) for k in keys],
            "total": total,
            "page": page,
            "per_page": per_page
        }

    def update_key(
        self,
        key_id: str,
        name: str = None,
        description: str = None,
        scopes: List[str] = None,
        allowed_ips: List[str] = None,
        rate_limit_per_minute: int = None,
        is_active: bool = None,
        tenant_id: str = None
    ) -> Optional[Dict]:
        """Update an API key"""
        if tenant_id is None:
            tenant_id = TenantContext.get_tenant_id()

        # Verify ownership
        key = gateway_db.api_keys.find_by_id(key_id)
        if not key or key.get("tenant_id") != tenant_id:
            return None

        # Validate scopes
        if scopes:
            invalid_scopes = [s for s in scopes if s not in self.SCOPES]
            if invalid_scopes:
                raise ValueError(f"Invalid scopes: {invalid_scopes}")

        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if scopes is not None:
            update_data["scopes"] = scopes
        if allowed_ips is not None:
            update_data["allowed_ips"] = allowed_ips
        if rate_limit_per_minute is not None:
            update_data["rate_limit_per_minute"] = rate_limit_per_minute
        if is_active is not None:
            update_data["is_active"] = is_active

        result = gateway_db.api_keys.update(key_id, update_data)
        return self._format_key(result) if result else None

    def regenerate_key(self, key_id: str, tenant_id: str = None) -> Optional[Dict]:
        """Regenerate API key (new key value, same settings)"""
        if tenant_id is None:
            tenant_id = TenantContext.get_tenant_id()

        # Verify ownership
        key = gateway_db.api_keys.find_by_id(key_id)
        if not key or key.get("tenant_id") != tenant_id:
            return None

        result = gateway_db.api_keys.regenerate(key_id)

        if result:
            return {
                "api_key": self._format_key(result),
                "key": result["raw_key"]
            }

        return None

    def revoke_key(self, key_id: str, tenant_id: str = None) -> bool:
        """Revoke (deactivate) an API key"""
        if tenant_id is None:
            tenant_id = TenantContext.get_tenant_id()

        # Verify ownership
        key = gateway_db.api_keys.find_by_id(key_id)
        if not key or key.get("tenant_id") != tenant_id:
            return False

        return gateway_db.api_keys.revoke(key_id)

    def delete_key(self, key_id: str, tenant_id: str = None) -> bool:
        """Permanently delete an API key"""
        if tenant_id is None:
            tenant_id = TenantContext.get_tenant_id()

        # Verify ownership
        key = gateway_db.api_keys.find_by_id(key_id)
        if not key or key.get("tenant_id") != tenant_id:
            return False

        return gateway_db.api_keys.delete(key_id)

    def get_usage_stats(self, key_id: str, days: int = 30, tenant_id: str = None) -> Optional[Dict]:
        """Get usage statistics for an API key"""
        if tenant_id is None:
            tenant_id = TenantContext.get_tenant_id()

        # Verify ownership
        key = gateway_db.api_keys.find_by_id(key_id)
        if not key or key.get("tenant_id") != tenant_id:
            return None

        stats = gateway_db.request_logs.get_stats(
            tenant_id=tenant_id,
            api_key_id=key_id,
            days=days
        )

        return {
            "api_key_id": key_id,
            "period_days": days,
            "total_requests": key.get("total_requests", 0),
            "last_used_at": key.get("last_used_at"),
            **stats
        }

    def get_available_scopes(self) -> List[Dict]:
        """Get list of available scopes with descriptions"""
        return [
            {"scope": k, "description": v}
            for k, v in self.SCOPES.items()
        ]

    def _format_key(self, key: Dict) -> Dict:
        """Format API key for response (exclude sensitive data)"""
        return {
            "id": key.get("id"),
            "name": key.get("name"),
            "description": key.get("description"),
            "key_prefix": f"{key.get('key_prefix', '')[:12]}...",
            "scopes": key.get("scopes", []),
            "environment": key.get("environment"),
            "rate_limits": {
                "per_minute": key.get("rate_limit_per_minute"),
                "per_hour": key.get("rate_limit_per_hour"),
                "per_day": key.get("rate_limit_per_day")
            },
            "allowed_ips": key.get("allowed_ips", []),
            "is_active": key.get("is_active", True),
            "is_expired": self._is_expired(key),
            "last_used_at": key.get("last_used_at"),
            "total_requests": key.get("total_requests", 0),
            "expires_at": key.get("expires_at"),
            "created_at": key.get("created_at")
        }

    def _is_expired(self, key: Dict) -> bool:
        """Check if key has expired"""
        expires_at = key.get("expires_at")
        if not expires_at:
            return False
        return datetime.fromisoformat(expires_at) < utc_now()


# Global service instance
api_key_service = APIKeyService()
