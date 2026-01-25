"""
Authentication and Authorization Middleware
Provides authentication verification and role-based access control.
"""

import time
from typing import Optional, List, Dict, Set, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from jose import jwt, JWTError


class AuthenticationMethod(str, Enum):
    """Supported authentication methods."""
    BEARER_TOKEN = "bearer"
    API_KEY = "api_key"
    SESSION = "session"
    BASIC = "basic"


@dataclass
class AuthConfig:
    """Authentication configuration."""
    secret_key: str
    algorithm: str = "HS256"
    token_header: str = "Authorization"
    token_prefix: str = "Bearer"
    api_key_header: str = "X-API-Key"
    session_cookie: str = "session_id"
    verify_exp: bool = True
    verify_iat: bool = True
    leeway: int = 0


@dataclass
class AuthenticatedUser:
    """Represents an authenticated user."""
    id: str
    email: Optional[str] = None
    role: str = "user"
    permissions: Set[str] = field(default_factory=set)
    organization_id: Optional[str] = None
    session_id: Optional[str] = None
    auth_method: AuthenticationMethod = AuthenticationMethod.BEARER_TOKEN
    metadata: Dict[str, Any] = field(default_factory=dict)

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return permission in self.permissions

    def has_any_permission(self, permissions: List[str]) -> bool:
        """Check if user has any of the specified permissions."""
        return bool(self.permissions & set(permissions))

    def has_all_permissions(self, permissions: List[str]) -> bool:
        """Check if user has all specified permissions."""
        return set(permissions).issubset(self.permissions)

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return self.role == role

    def has_any_role(self, roles: List[str]) -> bool:
        """Check if user has any of the specified roles."""
        return self.role in roles


@dataclass
class PathRule:
    """Access rule for a path pattern."""
    path_pattern: str
    methods: Optional[List[str]] = None
    roles: Optional[List[str]] = None
    permissions: Optional[List[str]] = None
    require_all_permissions: bool = False
    public: bool = False


class TokenValidator:
    """JWT token validation utilities."""

    def __init__(self, config: AuthConfig):
        self.config = config

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                options={
                    "verify_exp": self.config.verify_exp,
                    "verify_iat": self.config.verify_iat,
                    "leeway": self.config.leeway,
                },
            )
            return payload
        except JWTError:
            return None

    def extract_token(self, request: Request) -> Optional[str]:
        """Extract token from request headers."""
        auth_header = request.headers.get(self.config.token_header)
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2:
            return None

        if parts[0].lower() != self.config.token_prefix.lower():
            return None

        return parts[1]


class SessionStore:
    """In-memory session storage."""

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        session = self._sessions.get(session_id)
        if session:
            if session.get("expires_at", 0) > time.time():
                return session
            else:
                del self._sessions[session_id]
        return None

    def set(self, session_id: str, data: Dict[str, Any], ttl: int = 3600):
        """Store session data."""
        self._sessions[session_id] = {
            **data,
            "expires_at": time.time() + ttl,
        }

    def delete(self, session_id: str):
        """Delete session."""
        if session_id in self._sessions:
            del self._sessions[session_id]

    def cleanup(self):
        """Remove expired sessions."""
        current_time = time.time()
        expired = [
            sid for sid, data in self._sessions.items()
            if data.get("expires_at", 0) <= current_time
        ]
        for sid in expired:
            del self._sessions[sid]


class APIKeyStore:
    """In-memory API key storage."""

    def __init__(self):
        self._keys: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        key: str,
        user_id: str,
        permissions: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Register an API key."""
        self._keys[key] = {
            "user_id": user_id,
            "permissions": set(permissions or []),
            "metadata": metadata or {},
            "created_at": time.time(),
        }

    def validate(self, key: str) -> Optional[Dict[str, Any]]:
        """Validate an API key and return associated data."""
        return self._keys.get(key)

    def revoke(self, key: str):
        """Revoke an API key."""
        if key in self._keys:
            del self._keys[key]


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware for FastAPI applications.

    Features:
    - JWT token validation
    - API key authentication
    - Session-based authentication
    - Automatic token refresh
    - User context injection
    """

    def __init__(
        self,
        app,
        secret_key: str,
        algorithm: str = "HS256",
        public_paths: Optional[List[str]] = None,
        api_key_paths: Optional[List[str]] = None,
        session_store: Optional[SessionStore] = None,
        api_key_store: Optional[APIKeyStore] = None,
        user_loader: Optional[Callable[[str], Optional[Dict[str, Any]]]] = None,
        on_auth_failure: Optional[Callable[[Request, str], None]] = None,
    ):
        super().__init__(app)
        self.config = AuthConfig(secret_key=secret_key, algorithm=algorithm)
        self.public_paths = public_paths or [
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
        ]
        self.api_key_paths = api_key_paths or ["/api/v1/webhooks"]
        self.token_validator = TokenValidator(self.config)
        self.session_store = session_store or SessionStore()
        self.api_key_store = api_key_store or APIKeyStore()
        self.user_loader = user_loader
        self.on_auth_failure = on_auth_failure

    def _is_public_path(self, path: str) -> bool:
        """Check if path is public."""
        for public_path in self.public_paths:
            if path == public_path or path.startswith(f"{public_path}/"):
                return True
        return False

    def _is_api_key_path(self, path: str) -> bool:
        """Check if path accepts API key authentication."""
        for api_path in self.api_key_paths:
            if path.startswith(api_path):
                return True
        return False

    def _authenticate_bearer(self, request: Request) -> Optional[AuthenticatedUser]:
        """Authenticate using bearer token."""
        token = self.token_validator.extract_token(request)
        if not token:
            return None

        payload = self.token_validator.decode_token(token)
        if not payload:
            return None

        user_id = payload.get("user_id") or payload.get("sub")
        if not user_id:
            return None

        user_data = None
        if self.user_loader:
            user_data = self.user_loader(user_id)

        permissions = set(payload.get("permissions", []))
        if user_data:
            permissions.update(user_data.get("permissions", []))

        return AuthenticatedUser(
            id=user_id,
            email=payload.get("email") or (user_data.get("email") if user_data else None),
            role=payload.get("role") or (user_data.get("role") if user_data else "user"),
            permissions=permissions,
            organization_id=payload.get("organization_id") or (
                user_data.get("organization_id") if user_data else None
            ),
            session_id=payload.get("session_id"),
            auth_method=AuthenticationMethod.BEARER_TOKEN,
            metadata={"token_payload": payload},
        )

    def _authenticate_api_key(self, request: Request) -> Optional[AuthenticatedUser]:
        """Authenticate using API key."""
        api_key = request.headers.get(self.config.api_key_header)
        if not api_key:
            return None

        key_data = self.api_key_store.validate(api_key)
        if not key_data:
            return None

        user_id = key_data.get("user_id")

        user_data = None
        if self.user_loader:
            user_data = self.user_loader(user_id)

        return AuthenticatedUser(
            id=user_id,
            email=user_data.get("email") if user_data else None,
            role=user_data.get("role") if user_data else "api",
            permissions=key_data.get("permissions", set()),
            organization_id=user_data.get("organization_id") if user_data else None,
            auth_method=AuthenticationMethod.API_KEY,
            metadata={"api_key_metadata": key_data.get("metadata", {})},
        )

    def _authenticate_session(self, request: Request) -> Optional[AuthenticatedUser]:
        """Authenticate using session cookie."""
        session_id = request.cookies.get(self.config.session_cookie)
        if not session_id:
            return None

        session_data = self.session_store.get(session_id)
        if not session_data:
            return None

        user_id = session_data.get("user_id")

        user_data = None
        if self.user_loader:
            user_data = self.user_loader(user_id)

        return AuthenticatedUser(
            id=user_id,
            email=session_data.get("email") or (user_data.get("email") if user_data else None),
            role=session_data.get("role") or (user_data.get("role") if user_data else "user"),
            permissions=set(session_data.get("permissions", [])),
            organization_id=session_data.get("organization_id") or (
                user_data.get("organization_id") if user_data else None
            ),
            session_id=session_id,
            auth_method=AuthenticationMethod.SESSION,
            metadata={"session_data": session_data},
        )

    def _create_unauthorized_response(self, message: str = "Unauthorized") -> JSONResponse:
        """Create 401 Unauthorized response."""
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "error": "unauthorized",
                "message": message,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process authentication for the request."""
        if self._is_public_path(request.url.path):
            return await call_next(request)

        user: Optional[AuthenticatedUser] = None

        user = self._authenticate_bearer(request)

        if not user and self._is_api_key_path(request.url.path):
            user = self._authenticate_api_key(request)

        if not user:
            user = self._authenticate_session(request)

        if not user:
            if self.on_auth_failure:
                self.on_auth_failure(request, "No valid authentication provided")
            return self._create_unauthorized_response()

        request.state.user = {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "permissions": list(user.permissions),
            "organization_id": user.organization_id,
            "session_id": user.session_id,
            "auth_method": user.auth_method.value,
        }
        request.state.auth_user = user

        return await call_next(request)


class RBACMiddleware(BaseHTTPMiddleware):
    """
    Role-Based Access Control middleware.

    Features:
    - Path-based role requirements
    - Permission-based access control
    - Hierarchical role support
    - Custom access rules
    """

    def __init__(
        self,
        app,
        rules: Optional[List[PathRule]] = None,
        role_hierarchy: Optional[Dict[str, List[str]]] = None,
        default_deny: bool = True,
        on_access_denied: Optional[Callable[[Request, str], None]] = None,
    ):
        super().__init__(app)
        self.rules = rules or []
        self.role_hierarchy = role_hierarchy or {
            "admin": ["admin", "manager", "user", "viewer"],
            "manager": ["manager", "user", "viewer"],
            "user": ["user", "viewer"],
            "viewer": ["viewer"],
        }
        self.default_deny = default_deny
        self.on_access_denied = on_access_denied

    def _get_effective_roles(self, role: str) -> Set[str]:
        """Get all roles included in a role (including inherited)."""
        return set(self.role_hierarchy.get(role, [role]))

    def _path_matches(self, pattern: str, path: str) -> bool:
        """Check if path matches pattern."""
        if pattern.endswith("*"):
            return path.startswith(pattern[:-1])
        return path == pattern

    def _find_matching_rule(self, request: Request) -> Optional[PathRule]:
        """Find the first matching rule for the request."""
        path = request.url.path
        method = request.method

        for rule in self.rules:
            if not self._path_matches(rule.path_pattern, path):
                continue

            if rule.methods and method not in rule.methods:
                continue

            return rule

        return None

    def _check_access(self, user: AuthenticatedUser, rule: PathRule) -> bool:
        """Check if user has access based on rule."""
        if rule.public:
            return True

        if rule.roles:
            effective_roles = self._get_effective_roles(user.role)
            if not any(role in effective_roles for role in rule.roles):
                return False

        if rule.permissions:
            if rule.require_all_permissions:
                if not user.has_all_permissions(rule.permissions):
                    return False
            else:
                if not user.has_any_permission(rule.permissions):
                    return False

        return True

    def _create_forbidden_response(self, message: str = "Access denied") -> JSONResponse:
        """Create 403 Forbidden response."""
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "error": "forbidden",
                "message": message,
            },
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process authorization for the request."""
        rule = self._find_matching_rule(request)

        if not rule:
            if self.default_deny:
                return await call_next(request)
            else:
                return await call_next(request)

        if rule.public:
            return await call_next(request)

        user = getattr(request.state, "auth_user", None)
        if not user:
            user_dict = getattr(request.state, "user", None)
            if user_dict:
                user = AuthenticatedUser(
                    id=user_dict.get("id", ""),
                    email=user_dict.get("email"),
                    role=user_dict.get("role", "user"),
                    permissions=set(user_dict.get("permissions", [])),
                    organization_id=user_dict.get("organization_id"),
                )

        if not user:
            return self._create_forbidden_response("Authentication required")

        if not self._check_access(user, rule):
            if self.on_access_denied:
                self.on_access_denied(request, f"User {user.id} denied access to {request.url.path}")
            return self._create_forbidden_response("Insufficient permissions")

        return await call_next(request)


class RBACConfig:
    """Builder class for RBAC middleware configuration."""

    def __init__(self):
        self.rules: List[PathRule] = []
        self.role_hierarchy: Dict[str, List[str]] = {}
        self.default_deny = True

    def add_rule(self, rule: PathRule) -> "RBACConfig":
        """Add an access rule."""
        self.rules.append(rule)
        return self

    def add_public_path(self, path: str) -> "RBACConfig":
        """Add a public path that requires no authentication."""
        self.rules.append(PathRule(path_pattern=path, public=True))
        return self

    def add_role_rule(
        self,
        path: str,
        roles: List[str],
        methods: Optional[List[str]] = None,
    ) -> "RBACConfig":
        """Add a role-based access rule."""
        self.rules.append(PathRule(
            path_pattern=path,
            roles=roles,
            methods=methods,
        ))
        return self

    def add_permission_rule(
        self,
        path: str,
        permissions: List[str],
        require_all: bool = False,
        methods: Optional[List[str]] = None,
    ) -> "RBACConfig":
        """Add a permission-based access rule."""
        self.rules.append(PathRule(
            path_pattern=path,
            permissions=permissions,
            require_all_permissions=require_all,
            methods=methods,
        ))
        return self

    def set_role_hierarchy(self, hierarchy: Dict[str, List[str]]) -> "RBACConfig":
        """Set custom role hierarchy."""
        self.role_hierarchy = hierarchy
        return self

    def set_default_deny(self, deny: bool) -> "RBACConfig":
        """Set default deny behavior."""
        self.default_deny = deny
        return self

    def build(self) -> dict:
        """Build configuration dictionary."""
        return {
            "rules": self.rules,
            "role_hierarchy": self.role_hierarchy if self.role_hierarchy else None,
            "default_deny": self.default_deny,
        }
