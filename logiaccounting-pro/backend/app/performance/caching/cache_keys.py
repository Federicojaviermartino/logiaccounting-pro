"""
Cache key generation and pattern management.
"""
import hashlib
import json
from typing import Any, Optional, List, Dict
from enum import Enum


class CacheNamespace(str, Enum):
    """Cache key namespaces."""
    SESSION = "session"
    USER = "user"
    TENANT = "tenant"
    API = "api"
    QUERY = "query"
    DASHBOARD = "dashboard"
    REPORT = "report"
    ENTITY = "entity"
    PERMISSION = "permission"
    RATE_LIMIT = "ratelimit"
    FEATURE_FLAG = "feature"
    LOCK = "lock"


class CacheTTL:
    """Standard TTL values in seconds."""
    MICRO = 10
    SHORT = 60
    MEDIUM = 300
    LONG = 3600
    EXTENDED = 86400
    SESSION = 86400
    PERMANENT = 604800


class CacheKeyBuilder:
    """
    Builder for consistent cache key generation.

    Key Format: {namespace}:{version}:{tenant}:{entity}:{identifier}:{hash}

    Examples:
    - api:v1:tenant123:invoices:list:abc123
    - user:v1:tenant123:user456:permissions
    - dashboard:v1:tenant123:financial:daily:hash789
    """

    VERSION = "v1"
    SEPARATOR = ":"

    def __init__(self):
        self._prefix = "logiaccounting"

    def _hash_params(self, params: Dict[str, Any]) -> str:
        """Generate consistent hash from parameters."""
        sorted_params = json.dumps(params, sort_keys=True, default=str)
        return hashlib.md5(sorted_params.encode()).hexdigest()[:12]

    def build(
        self,
        namespace: CacheNamespace,
        tenant_id: str,
        *parts: str,
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build cache key.

        Args:
            namespace: Cache namespace
            tenant_id: Tenant identifier
            *parts: Additional key parts
            params: Optional parameters to hash

        Returns:
            Cache key string
        """
        key_parts = [
            self._prefix,
            namespace.value,
            self.VERSION,
            str(tenant_id)
        ]

        key_parts.extend([str(p) for p in parts if p])

        if params:
            key_parts.append(self._hash_params(params))

        return self.SEPARATOR.join(key_parts)

    def entity_key(
        self,
        tenant_id: str,
        entity_type: str,
        entity_id: str
    ) -> str:
        """Key for single entity."""
        return self.build(
            CacheNamespace.ENTITY,
            tenant_id,
            entity_type,
            entity_id
        )

    def entity_list_key(
        self,
        tenant_id: str,
        entity_type: str,
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """Key for entity list."""
        return self.build(
            CacheNamespace.ENTITY,
            tenant_id,
            entity_type,
            "list",
            params=params or {}
        )

    def api_response_key(
        self,
        tenant_id: str,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """Key for API response cache."""
        return self.build(
            CacheNamespace.API,
            tenant_id,
            endpoint.replace("/", "_"),
            method.lower(),
            params=params
        )

    def user_session_key(self, user_id: str) -> str:
        """Key for user session."""
        return f"{self._prefix}:{CacheNamespace.SESSION.value}:{user_id}"

    def user_permissions_key(self, tenant_id: str, user_id: str) -> str:
        """Key for user permissions."""
        return self.build(
            CacheNamespace.PERMISSION,
            tenant_id,
            user_id
        )

    def user_profile_key(self, tenant_id: str, user_id: str) -> str:
        """Key for user profile."""
        return self.build(
            CacheNamespace.USER,
            tenant_id,
            user_id,
            "profile"
        )

    def dashboard_key(
        self,
        tenant_id: str,
        dashboard_type: str,
        user_id: Optional[str] = None,
        date_range: Optional[str] = None
    ) -> str:
        """Key for dashboard data."""
        parts = [dashboard_type]
        if user_id:
            parts.append(user_id)
        if date_range:
            parts.append(date_range)

        return self.build(
            CacheNamespace.DASHBOARD,
            tenant_id,
            *parts
        )

    def report_key(
        self,
        tenant_id: str,
        report_type: str,
        params: Dict[str, Any]
    ) -> str:
        """Key for generated reports."""
        return self.build(
            CacheNamespace.REPORT,
            tenant_id,
            report_type,
            params=params
        )

    def rate_limit_key(
        self,
        identifier: str,
        endpoint: str
    ) -> str:
        """Key for rate limiting."""
        return f"{self._prefix}:{CacheNamespace.RATE_LIMIT.value}:{identifier}:{endpoint}"

    def lock_key(
        self,
        resource_type: str,
        resource_id: str
    ) -> str:
        """Key for distributed locks."""
        return f"{self._prefix}:{CacheNamespace.LOCK.value}:{resource_type}:{resource_id}"

    def tenant_pattern(self, tenant_id: str) -> str:
        """Pattern to match all keys for a tenant."""
        return f"{self._prefix}:*:{self.VERSION}:{tenant_id}:*"

    def entity_pattern(
        self,
        tenant_id: str,
        entity_type: str
    ) -> str:
        """Pattern to match all keys for an entity type."""
        return f"{self._prefix}:{CacheNamespace.ENTITY.value}:{self.VERSION}:{tenant_id}:{entity_type}:*"

    def user_pattern(self, user_id: str) -> str:
        """Pattern to match all keys for a user."""
        return f"{self._prefix}:*:*:*:{user_id}:*"


cache_keys = CacheKeyBuilder()


class CacheTags:
    """
    Predefined cache tags for invalidation.

    Usage:
        await cache_manager.set(key, value, tags=[CacheTags.invoices(tenant_id)])
        await cache_manager.invalidate_by_tag(CacheTags.invoices(tenant_id))
    """

    @staticmethod
    def tenant(tenant_id: str) -> str:
        return f"tenant:{tenant_id}"

    @staticmethod
    def user(user_id: str) -> str:
        return f"user:{user_id}"

    @staticmethod
    def invoices(tenant_id: str) -> str:
        return f"invoices:{tenant_id}"

    @staticmethod
    def invoice(invoice_id: str) -> str:
        return f"invoice:{invoice_id}"

    @staticmethod
    def clients(tenant_id: str) -> str:
        return f"clients:{tenant_id}"

    @staticmethod
    def client(client_id: str) -> str:
        return f"client:{client_id}"

    @staticmethod
    def projects(tenant_id: str) -> str:
        return f"projects:{tenant_id}"

    @staticmethod
    def project(project_id: str) -> str:
        return f"project:{project_id}"

    @staticmethod
    def transactions(tenant_id: str) -> str:
        return f"transactions:{tenant_id}"

    @staticmethod
    def dashboard(tenant_id: str) -> str:
        return f"dashboard:{tenant_id}"

    @staticmethod
    def reports(tenant_id: str) -> str:
        return f"reports:{tenant_id}"

    @staticmethod
    def permissions(tenant_id: str) -> str:
        return f"permissions:{tenant_id}"
