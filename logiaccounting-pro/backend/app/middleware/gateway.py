"""
API Gateway Middleware
Phase 17 - API Key authentication, rate limiting, request logging
"""

import time
from datetime import datetime
from typing import Optional, Callable, Tuple, Dict, Any
from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.api_key_service import api_key_service
from app.models.gateway_store import gateway_db
from app.middleware.tenant_context import TenantContext


class APIKeyAuth:
    """API Key authentication handler"""

    HEADER_NAME = "X-API-Key"
    BEARER_PREFIX = "Bearer "

    @classmethod
    def extract_api_key(cls, request: Request) -> Optional[str]:
        """Extract API key from request"""
        # Check header
        api_key = request.headers.get(cls.HEADER_NAME)
        if api_key:
            return api_key

        # Check Authorization header with Bearer prefix
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith(cls.BEARER_PREFIX):
            return auth_header[len(cls.BEARER_PREFIX):]

        # Check query parameter (for webhooks, etc.)
        api_key = request.query_params.get("api_key")
        if api_key:
            return api_key

        return None

    @classmethod
    def authenticate(cls, request: Request) -> Tuple[Optional[Dict], Optional[Dict], Optional[Dict]]:
        """
        Authenticate request using API key

        Returns:
            Tuple of (api_key, tenant, error_response)
        """
        raw_key = cls.extract_api_key(request)

        if not raw_key:
            return None, None, {
                "success": False,
                "error": "API key required",
                "code": "API_KEY_MISSING"
            }

        # Validate key
        api_key = api_key_service.validate_key(raw_key)

        if not api_key:
            return None, None, {
                "success": False,
                "error": "Invalid API key",
                "code": "API_KEY_INVALID"
            }

        # Check IP restriction
        client_ip = cls.get_client_ip(request)
        if not api_key_service.check_ip(api_key, client_ip):
            return None, None, {
                "success": False,
                "error": "IP address not allowed",
                "code": "IP_NOT_ALLOWED"
            }

        # Get tenant
        tenant_id = api_key.get("tenant_id")
        if tenant_id:
            from app.models.tenant_store import tenant_db
            tenant = tenant_db.tenants.find_by_id(tenant_id)

            if not tenant or tenant.get("status") != "active":
                return None, None, {
                    "success": False,
                    "error": "Tenant not found or inactive",
                    "code": "TENANT_INACTIVE"
                }

            return api_key, tenant, None

        return api_key, None, None

    @staticmethod
    def get_client_ip(request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded IP (behind proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "0.0.0.0"


def require_api_key():
    """FastAPI dependency to require API key authentication"""
    async def dependency(request: Request) -> Dict:
        api_key, tenant, error = APIKeyAuth.authenticate(request)

        if error:
            raise HTTPException(status_code=401, detail=error)

        # Set context
        if tenant:
            TenantContext.set_current(tenant)
            request.state.tenant = tenant
            request.state.tenant_id = tenant.get("id")

        request.state.api_key = api_key

        # Record usage
        api_key_service.record_usage(api_key.get("id"))

        return api_key

    return Depends(dependency)


def require_scope(scope: str):
    """FastAPI dependency to require specific API key scope"""
    async def dependency(request: Request) -> bool:
        api_key = getattr(request.state, "api_key", None)

        if not api_key:
            raise HTTPException(
                status_code=401,
                detail={
                    "success": False,
                    "error": "API key required",
                    "code": "API_KEY_MISSING"
                }
            )

        if not api_key_service.check_scope(api_key, scope):
            raise HTTPException(
                status_code=403,
                detail={
                    "success": False,
                    "error": f"Missing required scope: {scope}",
                    "code": "INSUFFICIENT_SCOPE"
                }
            )

        return True

    return Depends(dependency)


def check_rate_limit():
    """FastAPI dependency to check rate limits"""
    async def dependency(request: Request) -> Dict:
        api_key = getattr(request.state, "api_key", None)

        if not api_key:
            # Rate limit by IP for unauthenticated requests
            identifier = f"ip:{APIKeyAuth.get_client_ip(request)}"
            limits = {"minute": 30, "hour": 500, "day": 5000}
        else:
            identifier = f"key:{api_key.get('id')}"
            # Get tenant tier for rate limits
            tenant = getattr(request.state, "tenant", None)
            tier = tenant.get("tier", "standard") if tenant else "standard"
            limits = api_key_service.get_rate_limits(api_key, tier)

        # Check limits
        result = gateway_db.rate_limits.check_limit(identifier, limits)

        if not result["allowed"]:
            raise HTTPException(
                status_code=429,
                detail={
                    "success": False,
                    "error": "Rate limit exceeded",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "limit": result["limit"],
                    "window": result["window"],
                    "retry_after": result["retry_after"]
                },
                headers={
                    "X-RateLimit-Limit": str(result["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(result["reset"]),
                    "Retry-After": str(result["retry_after"])
                }
            )

        # Record request
        gateway_db.rate_limits.record_request(identifier)

        return result

    return Depends(dependency)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """Middleware for logging API requests"""

    EXCLUDED_PATHS = [
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico",
        "/static"
    ]

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request and log details"""
        start_time = time.time()

        # Skip logging for excluded paths
        if self._should_skip(request.url.path):
            return await call_next(request)

        # Process request
        response = await call_next(request)

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # Log request if it's an API call
        if request.url.path.startswith("/api/"):
            try:
                self._log_request(request, response, response_time_ms)
            except Exception:
                pass  # Don't fail request on logging error

        # Add rate limit headers if available
        if hasattr(request.state, "rate_limit_info"):
            info = request.state.rate_limit_info
            if info.get("all_limits", {}).get("minute"):
                minute_info = info["all_limits"]["minute"]
                response.headers["X-RateLimit-Limit"] = str(minute_info.get("limit", 0))
                response.headers["X-RateLimit-Remaining"] = str(minute_info.get("remaining", 0))
                response.headers["X-RateLimit-Reset"] = str(minute_info.get("reset", 0))

        return response

    def _should_skip(self, path: str) -> bool:
        """Check if path should be skipped"""
        for excluded in self.EXCLUDED_PATHS:
            if path.startswith(excluded):
                return True
        return False

    def _log_request(self, request: Request, response, response_time_ms: int):
        """Log request details"""
        tenant_id = getattr(request.state, "tenant_id", None)

        if not tenant_id:
            return  # Skip logging without tenant context

        api_key = getattr(request.state, "api_key", None)

        # Determine error info
        error_code = None
        error_message = None

        if response.status_code >= 400:
            error_code = f"HTTP_{response.status_code}"

        gateway_db.request_logs.create({
            "tenant_id": tenant_id,
            "api_key_id": api_key.get("id") if api_key else None,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "user_agent": request.headers.get("User-Agent"),
            "content_type": request.headers.get("Content-Type"),
            "client_ip": APIKeyAuth.get_client_ip(request),
            "status_code": response.status_code,
            "response_time_ms": response_time_ms,
            "request_size": int(request.headers.get("Content-Length", 0)),
            "error_code": error_code,
            "error_message": error_message,
            "api_version": self._extract_api_version(request.url.path)
        })

    def _extract_api_version(self, path: str) -> str:
        """Extract API version from path"""
        if "/api/v" in path:
            parts = path.split("/")
            for part in parts:
                if part.startswith("v") and len(part) <= 3:
                    return part
        return "v1"


class GatewayMiddleware(BaseHTTPMiddleware):
    """Combined gateway middleware for API authentication and rate limiting"""

    # Paths that require API key authentication
    API_KEY_PATHS = [
        "/api/v1/external/",
        "/api/external/"
    ]

    # Paths excluded from middleware
    EXCLUDED_PATHS = [
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/",
        "/api/v1/public/"
    ]

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request through gateway"""
        path = request.url.path

        # Skip excluded paths
        if self._is_excluded(path):
            return await call_next(request)

        # Check if API key authentication is required
        if self._requires_api_key(path):
            api_key, tenant, error = APIKeyAuth.authenticate(request)

            if error:
                return JSONResponse(
                    status_code=401,
                    content=error
                )

            # Set context
            if tenant:
                TenantContext.set_current(tenant)
                request.state.tenant = tenant
                request.state.tenant_id = tenant.get("id")

            request.state.api_key = api_key

            # Check rate limits
            identifier = f"key:{api_key.get('id')}"
            tier = tenant.get("tier", "standard") if tenant else "standard"
            limits = api_key_service.get_rate_limits(api_key, tier)

            result = gateway_db.rate_limits.check_limit(identifier, limits)

            if not result["allowed"]:
                return JSONResponse(
                    status_code=429,
                    content={
                        "success": False,
                        "error": "Rate limit exceeded",
                        "code": "RATE_LIMIT_EXCEEDED",
                        "limit": result["limit"],
                        "window": result["window"],
                        "retry_after": result["retry_after"]
                    },
                    headers={
                        "X-RateLimit-Limit": str(result["limit"]),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(result["reset"]),
                        "Retry-After": str(result["retry_after"])
                    }
                )

            # Record request
            gateway_db.rate_limits.record_request(identifier)
            request.state.rate_limit_info = result

            # Record usage
            api_key_service.record_usage(api_key.get("id"))

        return await call_next(request)

    def _is_excluded(self, path: str) -> bool:
        """Check if path is excluded"""
        for excluded in self.EXCLUDED_PATHS:
            if path.startswith(excluded):
                return True
        return False

    def _requires_api_key(self, path: str) -> bool:
        """Check if path requires API key"""
        for api_path in self.API_KEY_PATHS:
            if path.startswith(api_path):
                return True
        return False
