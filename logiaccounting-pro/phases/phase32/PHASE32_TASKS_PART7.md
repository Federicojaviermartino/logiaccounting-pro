# Phase 32: Advanced Security - Part 7: Security Middleware

## Overview
This part covers FastAPI middleware for security headers, CSRF protection, and request validation.

---

## File 1: Security Headers Middleware
**Path:** `backend/app/security/middleware/headers.py`

```python
"""
Security Headers Middleware
Add security headers to all responses
"""

from typing import Dict, Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import logging

from app.security.config import get_security_config

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses."""
    
    def __init__(self, app, config=None):
        super().__init__(app)
        self.config = config or get_security_config()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        self._add_security_headers(response)
        
        return response
    
    def _add_security_headers(self, response: Response):
        """Add all security headers."""
        
        # Strict Transport Security (HTTPS only)
        if self.config.enable_hsts:
            response.headers["Strict-Transport-Security"] = (
                f"max-age={self.config.hsts_max_age}; includeSubDomains; preload"
            )
        
        # Content Security Policy
        if self.config.enable_csp:
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net",
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
                "font-src 'self' https://fonts.gstatic.com",
                "img-src 'self' data: https:",
                "connect-src 'self' https://api.anthropic.com",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'",
            ]
            response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS Protection (legacy, but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy (formerly Feature Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=()"
        )
        
        # Cache control for sensitive pages
        if self._is_sensitive_endpoint(response):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        # Remove server header
        if "Server" in response.headers:
            del response.headers["Server"]
    
    def _is_sensitive_endpoint(self, response: Response) -> bool:
        """Check if response is from a sensitive endpoint."""
        # Add logic to identify sensitive endpoints
        return True  # Default to secure caching


def get_security_headers_middleware(app):
    """Factory function for security headers middleware."""
    return SecurityHeadersMiddleware(app)
```

---

## File 2: Rate Limit Middleware
**Path:** `backend/app/security/middleware/rate_limit.py`

```python
"""
Rate Limit Middleware
Apply rate limiting to requests
"""

from typing import Callable, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
import logging

from app.security.protection.rate_limiter import rate_limiter, RateLimitResult

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply rate limiting to requests."""
    
    # Endpoint-specific rate limit rules
    ENDPOINT_RULES = {
        "/api/auth/login": "login",
        "/api/auth/register": "login",
        "/api/auth/password/reset": "password_reset",
        "/api/auth/password/forgot": "password_reset",
        "/api/reports/export": "export",
        "/api/invoices/export": "export",
    }
    
    # Skip rate limiting for these paths
    SKIP_PATHS = [
        "/health",
        "/metrics",
        "/docs",
        "/openapi.json",
    ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip for certain paths
        if self._should_skip(request.url.path):
            return await call_next(request)
        
        # Get client IP
        ip = self._get_client_ip(request)
        
        # Get user ID if authenticated
        user_id = getattr(request.state, "user_id", None)
        
        # Determine rule to apply
        rule_name = self._get_rule_for_endpoint(request.url.path)
        
        # Check rate limit
        result = rate_limiter.check_and_increment(
            ip=ip,
            user_id=user_id,
            endpoint=request.url.path,
            rule_name=rule_name,
        )
        
        if not result.allowed:
            logger.warning(f"Rate limit exceeded: {ip} on {request.url.path}")
            return self._rate_limit_response(result)
        
        # Continue with request
        response = await call_next(request)
        
        # Add rate limit headers
        for header, value in result.to_headers().items():
            response.headers[header] = value
        
        return response
    
    def _should_skip(self, path: str) -> bool:
        """Check if path should skip rate limiting."""
        return any(path.startswith(skip) for skip in self.SKIP_PATHS)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for proxy headers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct connection
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _get_rule_for_endpoint(self, path: str) -> str:
        """Get rate limit rule for endpoint."""
        for endpoint_prefix, rule in self.ENDPOINT_RULES.items():
            if path.startswith(endpoint_prefix):
                return rule
        return "default"
    
    def _rate_limit_response(self, result: RateLimitResult) -> Response:
        """Generate rate limit exceeded response."""
        return JSONResponse(
            status_code=429,
            content={
                "error": "rate_limit_exceeded",
                "message": "Too many requests. Please try again later.",
                "retry_after": result.retry_after,
            },
            headers=result.to_headers(),
        )


def get_rate_limit_middleware(app):
    """Factory function for rate limit middleware."""
    return RateLimitMiddleware(app)
```

---

## File 3: Request Validation Middleware
**Path:** `backend/app/security/middleware/validation.py`

```python
"""
Request Validation Middleware
Validate and sanitize incoming requests
"""

from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
import logging

from app.security.protection.sanitizer import input_sanitizer
from app.security.protection.ip_filter import ip_filter

logger = logging.getLogger(__name__)


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate incoming requests for security issues."""
    
    # Maximum request body size (10MB)
    MAX_BODY_SIZE = 10 * 1024 * 1024
    
    # Allowed content types
    ALLOWED_CONTENT_TYPES = [
        "application/json",
        "application/x-www-form-urlencoded",
        "multipart/form-data",
        "text/plain",
    ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client IP
        ip = self._get_client_ip(request)
        
        # Check IP filter
        ip_result = ip_filter.check_ip(ip)
        if not ip_result.allowed:
            logger.warning(f"IP blocked: {ip} - {ip_result.reason}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": "access_denied",
                    "message": "Access denied from your location",
                },
            )
        
        # Validate content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_BODY_SIZE:
            return JSONResponse(
                status_code=413,
                content={
                    "error": "payload_too_large",
                    "message": f"Request body too large. Maximum size: {self.MAX_BODY_SIZE} bytes",
                },
            )
        
        # Validate content type for POST/PUT/PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "").split(";")[0].strip()
            if content_type and content_type not in self.ALLOWED_CONTENT_TYPES:
                return JSONResponse(
                    status_code=415,
                    content={
                        "error": "unsupported_media_type",
                        "message": f"Content type '{content_type}' is not supported",
                    },
                )
        
        # Check query parameters for injection
        query_validation = self._validate_query_params(request)
        if not query_validation["safe"]:
            logger.warning(f"Suspicious query params from {ip}: {query_validation['issues']}")
            return JSONResponse(
                status_code=400,
                content={
                    "error": "invalid_request",
                    "message": "Invalid characters in request",
                },
            )
        
        # Store validated IP in request state
        request.state.client_ip = ip
        
        # Continue with request
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _validate_query_params(self, request: Request) -> dict:
        """Validate query parameters."""
        issues = []
        
        for key, value in request.query_params.items():
            validation = input_sanitizer.validate_input(value)
            if not validation["safe"]:
                issues.extend(validation["issues"])
        
        return {
            "safe": len(issues) == 0,
            "issues": issues,
        }


def get_request_validation_middleware(app):
    """Factory function for request validation middleware."""
    return RequestValidationMiddleware(app)
```

---

## File 4: Auth Middleware
**Path:** `backend/app/security/middleware/auth.py`

```python
"""
Auth Middleware
JWT authentication and session validation
"""

from typing import Callable, Optional, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
import logging

from app.security.auth.tokens import token_manager, TokenType, TokenExpiredError, TokenInvalidError
from app.security.auth.sessions import session_manager
from app.security.rbac.engine import rbac_engine

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """JWT authentication middleware."""
    
    # Paths that don't require authentication
    PUBLIC_PATHS = [
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/password/forgot",
        "/api/auth/password/reset",
        "/api/auth/oauth",
    ]
    
    # Paths with optional authentication
    OPTIONAL_AUTH_PATHS = [
        "/api/public",
    ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        
        # Skip auth for public paths
        if self._is_public_path(path):
            return await call_next(request)
        
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        
        # Check if authentication is optional
        is_optional = self._is_optional_auth_path(path)
        
        if not auth_header:
            if is_optional:
                return await call_next(request)
            return self._unauthorized_response("Missing authorization header")
        
        # Parse token
        try:
            scheme, token = auth_header.split(" ", 1)
            if scheme.lower() != "bearer":
                return self._unauthorized_response("Invalid authentication scheme")
        except ValueError:
            return self._unauthorized_response("Invalid authorization header format")
        
        # Validate token
        try:
            payload = token_manager.verify_token(token, TokenType.ACCESS)
            
            # Check for MFA pending
            if payload.get("mfa_pending"):
                return self._unauthorized_response("MFA verification required")
            
            # Set user info in request state
            request.state.user_id = payload.get("sub")
            request.state.customer_id = payload.get("customer_id")
            request.state.roles = payload.get("roles", [])
            request.state.token_payload = payload
            
        except TokenExpiredError:
            return self._unauthorized_response("Token has expired", code="token_expired")
        except TokenInvalidError as e:
            return self._unauthorized_response(str(e))
        
        # Continue with request
        return await call_next(request)
    
    def _is_public_path(self, path: str) -> bool:
        """Check if path is public."""
        for public_path in self.PUBLIC_PATHS:
            if path == public_path or path.startswith(public_path + "/"):
                return True
        return False
    
    def _is_optional_auth_path(self, path: str) -> bool:
        """Check if authentication is optional for path."""
        for optional_path in self.OPTIONAL_AUTH_PATHS:
            if path.startswith(optional_path):
                return True
        return False
    
    def _unauthorized_response(self, message: str, code: str = "unauthorized") -> Response:
        """Generate 401 response."""
        return JSONResponse(
            status_code=401,
            content={
                "error": code,
                "message": message,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )


class RBACMiddleware(BaseHTTPMiddleware):
    """Role-based access control middleware."""
    
    # Permission mappings for endpoints
    PERMISSION_MAP = {
        ("GET", "/api/customers"): "customers:read",
        ("POST", "/api/customers"): "customers:create",
        ("PUT", "/api/customers"): "customers:update",
        ("DELETE", "/api/customers"): "customers:delete",
        ("GET", "/api/invoices"): "invoices:read",
        ("POST", "/api/invoices"): "invoices:create",
        ("PUT", "/api/invoices"): "invoices:update",
        ("DELETE", "/api/invoices"): "invoices:delete",
        ("GET", "/api/projects"): "projects:read",
        ("POST", "/api/projects"): "projects:create",
        ("GET", "/api/reports"): "reports:read",
        ("GET", "/api/audit"): "audit:read",
        ("GET", "/api/settings"): "settings:read",
        ("PUT", "/api/settings"): "settings:update",
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip if no user (public endpoint)
        user_id = getattr(request.state, "user_id", None)
        if not user_id:
            return await call_next(request)
        
        # Get required permission
        permission = self._get_required_permission(request)
        if not permission:
            return await call_next(request)
        
        # Check permission
        customer_id = getattr(request.state, "customer_id", None)
        result = rbac_engine.check_permission(
            user_id=user_id,
            permission=permission,
            customer_id=customer_id,
        )
        
        if not result.allowed:
            logger.warning(
                f"Permission denied: user={user_id}, permission={permission}, "
                f"reason={result.reason}"
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error": "forbidden",
                    "message": "You don't have permission to perform this action",
                    "required_permission": permission,
                },
            )
        
        # Continue with request
        return await call_next(request)
    
    def _get_required_permission(self, request: Request) -> Optional[str]:
        """Get required permission for request."""
        path = request.url.path
        method = request.method
        
        # Check exact match first
        key = (method, path)
        if key in self.PERMISSION_MAP:
            return self.PERMISSION_MAP[key]
        
        # Check prefix matches
        for (rule_method, rule_path), permission in self.PERMISSION_MAP.items():
            if method == rule_method and path.startswith(rule_path):
                return permission
        
        return None


def get_auth_middleware(app):
    """Factory function for auth middleware."""
    return AuthMiddleware(app)


def get_rbac_middleware(app):
    """Factory function for RBAC middleware."""
    return RBACMiddleware(app)
```

---

## File 5: Middleware Module Init
**Path:** `backend/app/security/middleware/__init__.py`

```python
"""
Security Middleware Module
All security-related middleware
"""

from app.security.middleware.headers import (
    SecurityHeadersMiddleware,
    get_security_headers_middleware,
)

from app.security.middleware.rate_limit import (
    RateLimitMiddleware,
    get_rate_limit_middleware,
)

from app.security.middleware.validation import (
    RequestValidationMiddleware,
    get_request_validation_middleware,
)

from app.security.middleware.auth import (
    AuthMiddleware,
    RBACMiddleware,
    get_auth_middleware,
    get_rbac_middleware,
)


__all__ = [
    'SecurityHeadersMiddleware',
    'get_security_headers_middleware',
    'RateLimitMiddleware',
    'get_rate_limit_middleware',
    'RequestValidationMiddleware',
    'get_request_validation_middleware',
    'AuthMiddleware',
    'RBACMiddleware',
    'get_auth_middleware',
    'get_rbac_middleware',
]


def setup_security_middleware(app):
    """Setup all security middleware."""
    # Order matters! Applied in reverse order
    
    # 1. Security headers (outermost - applied last)
    app.add_middleware(SecurityHeadersMiddleware)
    
    # 2. RBAC
    app.add_middleware(RBACMiddleware)
    
    # 3. Authentication
    app.add_middleware(AuthMiddleware)
    
    # 4. Rate limiting
    app.add_middleware(RateLimitMiddleware)
    
    # 5. Request validation (innermost - applied first)
    app.add_middleware(RequestValidationMiddleware)
    
    return app
```

---

## Summary Part 7

| File | Description | Lines |
|------|-------------|-------|
| `middleware/headers.py` | Security headers | ~120 |
| `middleware/rate_limit.py` | Rate limiting middleware | ~130 |
| `middleware/validation.py` | Request validation | ~150 |
| `middleware/auth.py` | Auth & RBAC middleware | ~200 |
| `middleware/__init__.py` | Middleware setup | ~60 |
| **Total** | | **~660 lines** |
