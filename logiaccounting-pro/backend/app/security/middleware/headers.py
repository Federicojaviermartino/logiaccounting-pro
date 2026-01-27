"""
Security Headers Middleware
Implements HTTP security headers for protection against common web vulnerabilities.
"""

from typing import Optional, List, Dict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all HTTP responses.

    Includes:
    - HSTS (HTTP Strict Transport Security)
    - CSP (Content Security Policy)
    - X-Frame-Options
    - X-Content-Type-Options
    - X-XSS-Protection
    - Referrer-Policy
    - Permissions-Policy
    """

    def __init__(
        self,
        app,
        hsts_enabled: bool = True,
        hsts_max_age: int = 31536000,
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = False,
        csp_enabled: bool = True,
        csp_directives: Optional[Dict[str, str]] = None,
        frame_options: str = "DENY",
        content_type_nosniff: bool = True,
        xss_protection: bool = True,
        referrer_policy: str = "strict-origin-when-cross-origin",
        permissions_policy: Optional[Dict[str, List[str]]] = None,
        excluded_paths: Optional[List[str]] = None,
    ):
        super().__init__(app)
        self.hsts_enabled = hsts_enabled
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload
        self.csp_enabled = csp_enabled
        self.csp_directives = csp_directives or self._default_csp_directives()
        self.frame_options = frame_options
        self.content_type_nosniff = content_type_nosniff
        self.xss_protection = xss_protection
        self.referrer_policy = referrer_policy
        self.permissions_policy = permissions_policy or self._default_permissions_policy()
        self.excluded_paths = excluded_paths or []

    def _default_csp_directives(self) -> Dict[str, str]:
        """Default Content Security Policy directives."""
        return {
            "default-src": "'self'",
            "script-src": "'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src": "'self' 'unsafe-inline'",
            "img-src": "'self' data: https:",
            "font-src": "'self' data:",
            "connect-src": "'self' https:",
            "frame-ancestors": "'none'",
            "base-uri": "'self'",
            "form-action": "'self'",
            "object-src": "'none'",
            "upgrade-insecure-requests": "",
        }

    def _default_permissions_policy(self) -> Dict[str, List[str]]:
        """Default Permissions Policy directives."""
        return {
            "accelerometer": [],
            "camera": [],
            "geolocation": [],
            "gyroscope": [],
            "magnetometer": [],
            "microphone": [],
            "payment": ["self"],
            "usb": [],
        }

    def _build_csp_header(self) -> str:
        """Build the Content-Security-Policy header value."""
        directives = []
        for directive, value in self.csp_directives.items():
            if value:
                directives.append(f"{directive} {value}")
            else:
                directives.append(directive)
        return "; ".join(directives)

    def _build_hsts_header(self) -> str:
        """Build the Strict-Transport-Security header value."""
        parts = [f"max-age={self.hsts_max_age}"]
        if self.hsts_include_subdomains:
            parts.append("includeSubDomains")
        if self.hsts_preload:
            parts.append("preload")
        return "; ".join(parts)

    def _build_permissions_policy_header(self) -> str:
        """Build the Permissions-Policy header value."""
        policies = []
        for feature, allowlist in self.permissions_policy.items():
            if not allowlist:
                policies.append(f"{feature}=()")
            else:
                allowed = " ".join(allowlist)
                policies.append(f"{feature}=({allowed})")
        return ", ".join(policies)

    def _should_apply_headers(self, path: str) -> bool:
        """Check if security headers should be applied to this path."""
        for excluded in self.excluded_paths:
            if path.startswith(excluded):
                return False
        return True

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request and add security headers to the response."""
        response = await call_next(request)

        if not self._should_apply_headers(request.url.path):
            return response

        if self.hsts_enabled:
            response.headers["Strict-Transport-Security"] = self._build_hsts_header()

        if self.csp_enabled:
            response.headers["Content-Security-Policy"] = self._build_csp_header()

        if self.frame_options:
            response.headers["X-Frame-Options"] = self.frame_options

        if self.content_type_nosniff:
            response.headers["X-Content-Type-Options"] = "nosniff"

        if self.xss_protection:
            response.headers["X-XSS-Protection"] = "1; mode=block"

        if self.referrer_policy:
            response.headers["Referrer-Policy"] = self.referrer_policy

        if self.permissions_policy:
            response.headers["Permissions-Policy"] = self._build_permissions_policy_header()

        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        return response


class SecurityHeadersConfig:
    """Configuration class for SecurityHeadersMiddleware."""

    def __init__(self):
        self.hsts_enabled = True
        self.hsts_max_age = 31536000
        self.hsts_include_subdomains = True
        self.hsts_preload = False
        self.csp_enabled = True
        self.csp_directives = {}
        self.frame_options = "DENY"
        self.content_type_nosniff = True
        self.xss_protection = True
        self.referrer_policy = "strict-origin-when-cross-origin"
        self.permissions_policy = {}
        self.excluded_paths = []

    def disable_hsts(self) -> "SecurityHeadersConfig":
        """Disable HSTS header."""
        self.hsts_enabled = False
        return self

    def enable_preload(self) -> "SecurityHeadersConfig":
        """Enable HSTS preload directive."""
        self.hsts_preload = True
        return self

    def set_csp_directive(self, directive: str, value: str) -> "SecurityHeadersConfig":
        """Set a CSP directive."""
        self.csp_directives[directive] = value
        return self

    def allow_frames_from(self, origin: str) -> "SecurityHeadersConfig":
        """Allow framing from a specific origin."""
        self.frame_options = f"ALLOW-FROM {origin}"
        return self

    def exclude_path(self, path: str) -> "SecurityHeadersConfig":
        """Exclude a path from security headers."""
        self.excluded_paths.append(path)
        return self

    def build(self):
        """Build the middleware configuration dictionary."""
        return {
            "hsts_enabled": self.hsts_enabled,
            "hsts_max_age": self.hsts_max_age,
            "hsts_include_subdomains": self.hsts_include_subdomains,
            "hsts_preload": self.hsts_preload,
            "csp_enabled": self.csp_enabled,
            "csp_directives": self.csp_directives if self.csp_directives else None,
            "frame_options": self.frame_options,
            "content_type_nosniff": self.content_type_nosniff,
            "xss_protection": self.xss_protection,
            "referrer_policy": self.referrer_policy,
            "permissions_policy": self.permissions_policy if self.permissions_policy else None,
            "excluded_paths": self.excluded_paths if self.excluded_paths else None,
        }
