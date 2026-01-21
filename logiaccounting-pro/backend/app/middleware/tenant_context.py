"""
Tenant Context and Middleware
Phase 16 - Multi-tenant request handling and tenant resolution
"""

from contextvars import ContextVar
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import re


# Context variable for current tenant - thread-safe
_current_tenant: ContextVar[Optional[Dict[str, Any]]] = ContextVar("current_tenant", default=None)
_current_tenant_id: ContextVar[Optional[str]] = ContextVar("current_tenant_id", default=None)


@dataclass
class TenantContext:
    """Thread-local tenant context for the current request"""

    @staticmethod
    def get_current() -> Optional[Dict[str, Any]]:
        """Get current tenant data"""
        return _current_tenant.get()

    @staticmethod
    def get_tenant_id() -> Optional[str]:
        """Get current tenant ID"""
        return _current_tenant_id.get()

    @staticmethod
    def set_current(tenant: Dict[str, Any]) -> None:
        """Set current tenant for this context"""
        _current_tenant.set(tenant)
        _current_tenant_id.set(tenant.get("id") if tenant else None)

    @staticmethod
    def clear() -> None:
        """Clear tenant context"""
        _current_tenant.set(None)
        _current_tenant_id.set(None)

    @staticmethod
    def get_setting(key: str, default: Any = None) -> Any:
        """Get a tenant setting from context"""
        tenant = _current_tenant.get()
        if tenant and "settings" in tenant:
            return tenant["settings"].get(key, default)
        return default

    @staticmethod
    def is_feature_enabled(feature_name: str) -> bool:
        """Check if feature is enabled for current tenant"""
        tenant = _current_tenant.get()
        if not tenant:
            return False

        features = tenant.get("features", {})
        return features.get(feature_name, False)

    @staticmethod
    def check_quota(resource: str) -> Dict[str, Any]:
        """Check quota for current tenant"""
        tenant = _current_tenant.get()
        if not tenant:
            return {"allowed": False, "reason": "No tenant context"}

        quota = tenant.get("quota", {})
        return quota.get(resource, {"allowed": True})


class TenantResolver:
    """
    Resolves tenant from various request sources.
    Priority: Header > JWT > Subdomain > Custom Domain
    """

    HEADER_NAME = "X-Tenant-ID"
    SUBDOMAIN_PATTERN = re.compile(r'^([a-z0-9][a-z0-9-]*[a-z0-9])\.', re.IGNORECASE)

    def __init__(self):
        self._domain_cache: Dict[str, str] = {}  # domain -> tenant_id
        self._slug_cache: Dict[str, str] = {}    # slug -> tenant_id

    def resolve(self, request: Request) -> Optional[str]:
        """
        Resolve tenant ID from request.
        Returns tenant_id or None if not resolved.
        """
        # 1. Try header first (explicit tenant selection)
        tenant_id = self._resolve_from_header(request)
        if tenant_id:
            return tenant_id

        # 2. Try JWT claim
        tenant_id = self._resolve_from_jwt(request)
        if tenant_id:
            return tenant_id

        # 3. Try subdomain
        tenant_id = self._resolve_from_subdomain(request)
        if tenant_id:
            return tenant_id

        # 4. Try custom domain
        tenant_id = self._resolve_from_domain(request)
        if tenant_id:
            return tenant_id

        return None

    def _resolve_from_header(self, request: Request) -> Optional[str]:
        """Resolve tenant from X-Tenant-ID header"""
        return request.headers.get(self.HEADER_NAME)

    def _resolve_from_jwt(self, request: Request) -> Optional[str]:
        """Resolve tenant from JWT token claim"""
        # Check if user info is already attached to request state
        if hasattr(request.state, "user") and request.state.user:
            return request.state.user.get("tenant_id")
        return None

    def _resolve_from_subdomain(self, request: Request) -> Optional[str]:
        """Resolve tenant from subdomain"""
        host = request.headers.get("host", "")

        # Skip common non-tenant subdomains
        if host.startswith(("www.", "api.", "admin.", "static.")):
            return None

        match = self.SUBDOMAIN_PATTERN.match(host)
        if match:
            slug = match.group(1).lower()
            # Check cache first
            if slug in self._slug_cache:
                return self._slug_cache[slug]

            # Look up tenant by slug
            from app.models.tenant_store import tenant_db
            tenant = tenant_db.tenants.find_by_slug(slug)
            if tenant and tenant.get("status") == "active":
                self._slug_cache[slug] = tenant["id"]
                return tenant["id"]

        return None

    def _resolve_from_domain(self, request: Request) -> Optional[str]:
        """Resolve tenant from custom domain"""
        host = request.headers.get("host", "").lower()

        # Remove port if present
        if ":" in host:
            host = host.split(":")[0]

        # Check cache first
        if host in self._domain_cache:
            return self._domain_cache[host]

        # Look up tenant by custom domain
        from app.models.tenant_store import tenant_db
        domain = tenant_db.domains.find_by_domain(host)
        if domain and domain.get("is_verified"):
            tenant_id = domain.get("tenant_id")
            self._domain_cache[host] = tenant_id
            return tenant_id

        return None

    def invalidate_cache(self, domain: str = None, slug: str = None):
        """Invalidate resolver cache"""
        if domain and domain in self._domain_cache:
            del self._domain_cache[domain]
        if slug and slug in self._slug_cache:
            del self._slug_cache[slug]

    def clear_cache(self):
        """Clear all caches"""
        self._domain_cache.clear()
        self._slug_cache.clear()


# Global resolver instance
tenant_resolver = TenantResolver()


class TenantMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for tenant context management.
    Resolves tenant and sets context for each request.
    """

    # Paths that don't require tenant context
    EXCLUDED_PATHS = [
        "/health",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/forgot-password",
        "/api/auth/reset-password",
        "/api/public/",
        "/api/webhooks/",
        "/api/invitations/accept",
    ]

    def __init__(self, app, require_tenant: bool = False):
        super().__init__(app)
        self.require_tenant = require_tenant

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request with tenant context"""

        # Skip tenant resolution for excluded paths
        path = request.url.path
        if self._is_excluded(path):
            return await call_next(request)

        try:
            # Resolve tenant
            tenant_id = tenant_resolver.resolve(request)

            if tenant_id:
                # Load full tenant data
                tenant_data = await self._load_tenant(tenant_id)

                if tenant_data:
                    # Check tenant status
                    status = tenant_data.get("status")
                    if status == "suspended":
                        return JSONResponse(
                            status_code=403,
                            content={
                                "success": False,
                                "error": "tenant_suspended",
                                "message": "This account has been suspended"
                            }
                        )
                    elif status not in ("active", "trialing"):
                        return JSONResponse(
                            status_code=403,
                            content={
                                "success": False,
                                "error": "tenant_inactive",
                                "message": "This account is not active"
                            }
                        )

                    # Set tenant context
                    TenantContext.set_current(tenant_data)

                    # Attach to request state for easy access
                    request.state.tenant = tenant_data
                    request.state.tenant_id = tenant_id

            elif self.require_tenant and not self._is_excluded(path):
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": "tenant_required",
                        "message": "Tenant identification required"
                    }
                )

            # Process request
            response = await call_next(request)

            # Add tenant ID to response headers for debugging
            if tenant_id:
                response.headers["X-Tenant-ID"] = tenant_id

            return response

        except Exception as e:
            # Log error and continue without tenant context
            print(f"Tenant middleware error: {e}")
            return await call_next(request)

        finally:
            # Clear context after request
            TenantContext.clear()

    def _is_excluded(self, path: str) -> bool:
        """Check if path is excluded from tenant resolution"""
        for excluded in self.EXCLUDED_PATHS:
            if path.startswith(excluded) or path == excluded.rstrip("/"):
                return True
        return False

    async def _load_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Load complete tenant data with settings, quota, and features"""
        from app.models.tenant_store import tenant_db

        tenant = tenant_db.tenants.find_by_id(tenant_id)
        if not tenant:
            return None

        # Load related data
        settings = tenant_db.settings.find_by_tenant(tenant_id)
        quota = tenant_db.quotas.find_by_tenant(tenant_id)
        subscription = tenant_db.subscriptions.find_by_tenant(tenant_id)

        # Load features as dict
        features_list = tenant_db.features.find_by_tenant(tenant_id)
        features = {}
        for f in features_list:
            if f.get("is_enabled"):
                features[f["feature_name"]] = True

        return {
            **tenant,
            "settings": settings or {},
            "quota": quota or {},
            "subscription": subscription or {},
            "features": features
        }


def get_current_tenant() -> Optional[Dict[str, Any]]:
    """Get current tenant from context (for use in dependencies)"""
    return TenantContext.get_current()


def get_current_tenant_id() -> Optional[str]:
    """Get current tenant ID from context"""
    return TenantContext.get_tenant_id()


def require_tenant():
    """FastAPI dependency that requires a tenant context"""
    def dependency(request: Request) -> Dict[str, Any]:
        tenant = getattr(request.state, "tenant", None)
        if not tenant:
            raise HTTPException(
                status_code=400,
                detail="Tenant context required"
            )
        return tenant
    return dependency


def require_feature(feature_name: str):
    """FastAPI dependency that requires a specific feature to be enabled"""
    def dependency(request: Request) -> bool:
        tenant = getattr(request.state, "tenant", None)
        if not tenant:
            raise HTTPException(
                status_code=400,
                detail="Tenant context required"
            )

        features = tenant.get("features", {})
        if not features.get(feature_name):
            raise HTTPException(
                status_code=403,
                detail=f"Feature '{feature_name}' is not enabled for your plan"
            )
        return True
    return dependency


def check_quota(resource: str, increment: int = 1):
    """FastAPI dependency that checks quota before allowing operation"""
    def dependency(request: Request) -> Dict[str, Any]:
        tenant = getattr(request.state, "tenant", None)
        if not tenant:
            raise HTTPException(
                status_code=400,
                detail="Tenant context required"
            )

        tenant_id = tenant.get("id")
        if not tenant_id:
            raise HTTPException(
                status_code=400,
                detail="Invalid tenant context"
            )

        from app.models.tenant_store import tenant_db
        result = tenant_db.quotas.check_quota(tenant_id, resource, increment)

        if not result.get("allowed"):
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "quota_exceeded",
                    "message": result.get("reason", f"Quota exceeded for {resource}"),
                    "current": result.get("current"),
                    "limit": result.get("limit")
                }
            )

        return result
    return dependency


class TenantAwareQuery:
    """
    Helper for building tenant-aware queries.
    Automatically filters data by current tenant.
    """

    @staticmethod
    def filter_by_tenant(items: list, tenant_id: str = None) -> list:
        """Filter list of items by tenant_id"""
        if tenant_id is None:
            tenant_id = get_current_tenant_id()

        if not tenant_id:
            return items

        return [
            item for item in items
            if item.get("tenant_id") == tenant_id
        ]

    @staticmethod
    def add_tenant_id(data: dict, tenant_id: str = None) -> dict:
        """Add tenant_id to data dict"""
        if tenant_id is None:
            tenant_id = get_current_tenant_id()

        if tenant_id:
            data["tenant_id"] = tenant_id

        return data
