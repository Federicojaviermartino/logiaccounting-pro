"""
Main Security API Routes
Comprehensive security management endpoints including MFA, OAuth, Sessions, RBAC,
Audit, IP/Rate limits, and Security Configuration.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request, Query, status
from pydantic import BaseModel, Field, EmailStr

from app.utils.auth import get_current_user, require_roles
from app.routes.security import router as security_sub_router


router = APIRouter()

router.include_router(security_sub_router)


class OAuthProvider(BaseModel):
    """OAuth provider configuration."""
    id: str
    name: str
    enabled: bool = False
    client_id: Optional[str] = None
    scopes: List[str] = []
    authorization_url: Optional[str] = None
    token_url: Optional[str] = None


class OAuthProviderListResponse(BaseModel):
    """Response for OAuth provider list."""
    success: bool = True
    providers: List[OAuthProvider]


class OAuthConnectRequest(BaseModel):
    """Request to connect OAuth provider."""
    provider: str
    redirect_uri: str


class OAuthConnectResponse(BaseModel):
    """Response for OAuth connect initiation."""
    success: bool = True
    authorization_url: str
    state: str


class OAuthCallbackRequest(BaseModel):
    """Request for OAuth callback."""
    provider: str
    code: str
    state: str


class OAuthConnectionResponse(BaseModel):
    """Response for OAuth connection status."""
    success: bool = True
    connected: bool
    provider: str
    connected_at: Optional[str] = None
    email: Optional[str] = None


class RoleDefinition(BaseModel):
    """Role definition with permissions."""
    id: str
    name: str
    description: Optional[str] = None
    permissions: List[str]
    is_system: bool = False
    created_at: str
    updated_at: str


class RoleListResponse(BaseModel):
    """Response for role list."""
    success: bool = True
    roles: List[RoleDefinition]


class RoleCreateRequest(BaseModel):
    """Request to create a role."""
    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None
    permissions: List[str]


class RoleUpdateRequest(BaseModel):
    """Request to update a role."""
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None


class UserRoleAssignment(BaseModel):
    """User role assignment."""
    user_id: str
    roles: List[str]


class PermissionListResponse(BaseModel):
    """Response for permission list."""
    success: bool = True
    permissions: List[Dict[str, Any]]


class IPRule(BaseModel):
    """IP access rule."""
    id: str
    type: str  # allow, deny
    ip_address: Optional[str] = None
    ip_range: Optional[str] = None
    description: Optional[str] = None
    enabled: bool = True
    created_at: str


class IPRuleListResponse(BaseModel):
    """Response for IP rule list."""
    success: bool = True
    rules: List[IPRule]


class IPRuleCreateRequest(BaseModel):
    """Request to create IP rule."""
    type: str = Field(..., pattern="^(allow|deny)$")
    ip_address: Optional[str] = None
    ip_range: Optional[str] = None
    description: Optional[str] = None


class RateLimitConfig(BaseModel):
    """Rate limit configuration."""
    endpoint_pattern: str
    requests_per_minute: int = Field(..., ge=1, le=10000)
    requests_per_hour: Optional[int] = None
    burst_limit: Optional[int] = None
    enabled: bool = True


class RateLimitListResponse(BaseModel):
    """Response for rate limit list."""
    success: bool = True
    limits: List[RateLimitConfig]


class SecurityConfigResponse(BaseModel):
    """Response for security configuration."""
    success: bool = True
    config: Dict[str, Any]


class SecurityConfigUpdateRequest(BaseModel):
    """Request to update security configuration."""
    password_min_length: Optional[int] = Field(None, ge=8, le=128)
    password_require_uppercase: Optional[bool] = None
    password_require_lowercase: Optional[bool] = None
    password_require_numbers: Optional[bool] = None
    password_require_special: Optional[bool] = None
    password_expiry_days: Optional[int] = Field(None, ge=0, le=365)
    session_timeout_minutes: Optional[int] = Field(None, ge=5, le=1440)
    max_failed_login_attempts: Optional[int] = Field(None, ge=3, le=20)
    lockout_duration_minutes: Optional[int] = Field(None, ge=5, le=1440)
    mfa_required: Optional[bool] = None
    mfa_required_for_roles: Optional[List[str]] = None


class SecurityStore:
    """In-memory security data storage."""

    _instance = None
    _oauth_providers: Dict[str, Dict[str, Any]] = {}
    _oauth_connections: Dict[str, Dict[str, Dict[str, Any]]] = {}
    _roles: Dict[str, Dict[str, Any]] = {}
    _user_roles: Dict[str, List[str]] = {}
    _ip_rules: List[Dict[str, Any]] = []
    _rate_limits: List[Dict[str, Any]] = []
    _config: Dict[str, Any] = {}
    _counter = 0

    SYSTEM_PERMISSIONS = [
        "users.read", "users.write", "users.delete",
        "roles.read", "roles.write", "roles.delete",
        "transactions.read", "transactions.write", "transactions.delete",
        "reports.read", "reports.generate", "reports.export",
        "settings.read", "settings.write",
        "audit.read", "audit.export",
        "security.manage",
    ]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._initialize()
        return cls._instance

    @classmethod
    def _initialize(cls):
        """Initialize default data."""
        cls._oauth_providers = {
            "google": {
                "id": "google",
                "name": "Google",
                "enabled": True,
                "scopes": ["openid", "email", "profile"],
                "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
            },
            "microsoft": {
                "id": "microsoft",
                "name": "Microsoft",
                "enabled": True,
                "scopes": ["openid", "email", "profile"],
                "authorization_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            },
            "github": {
                "id": "github",
                "name": "GitHub",
                "enabled": False,
                "scopes": ["read:user", "user:email"],
                "authorization_url": "https://github.com/login/oauth/authorize",
                "token_url": "https://github.com/login/oauth/access_token",
            },
        }

        now = datetime.utcnow().isoformat()
        cls._roles = {
            "admin": {
                "id": "admin",
                "name": "Administrator",
                "description": "Full system access",
                "permissions": cls.SYSTEM_PERMISSIONS,
                "is_system": True,
                "created_at": now,
                "updated_at": now,
            },
            "manager": {
                "id": "manager",
                "name": "Manager",
                "description": "Management access",
                "permissions": [
                    "users.read", "transactions.read", "transactions.write",
                    "reports.read", "reports.generate", "settings.read",
                ],
                "is_system": True,
                "created_at": now,
                "updated_at": now,
            },
            "user": {
                "id": "user",
                "name": "User",
                "description": "Standard user access",
                "permissions": [
                    "transactions.read", "transactions.write",
                    "reports.read",
                ],
                "is_system": True,
                "created_at": now,
                "updated_at": now,
            },
            "auditor": {
                "id": "auditor",
                "name": "Auditor",
                "description": "Audit and compliance access",
                "permissions": [
                    "transactions.read", "reports.read", "reports.export",
                    "audit.read", "audit.export",
                ],
                "is_system": True,
                "created_at": now,
                "updated_at": now,
            },
        }

        cls._config = {
            "password_min_length": 8,
            "password_require_uppercase": True,
            "password_require_lowercase": True,
            "password_require_numbers": True,
            "password_require_special": False,
            "password_expiry_days": 90,
            "session_timeout_minutes": 60,
            "max_failed_login_attempts": 5,
            "lockout_duration_minutes": 30,
            "mfa_required": False,
            "mfa_required_for_roles": ["admin"],
        }

        cls._oauth_connections = {}
        cls._user_roles = {}
        cls._ip_rules = []
        cls._rate_limits = []
        cls._counter = 0

    def get_oauth_providers(self) -> List[Dict[str, Any]]:
        """Get all OAuth providers."""
        return list(self._oauth_providers.values())

    def get_oauth_provider(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific OAuth provider."""
        return self._oauth_providers.get(provider_id)

    def get_user_oauth_connections(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        """Get OAuth connections for a user."""
        return self._oauth_connections.get(user_id, {})

    def connect_oauth(
        self,
        user_id: str,
        provider: str,
        email: str,
        access_token: str,
    ) -> Dict[str, Any]:
        """Store OAuth connection for a user."""
        if user_id not in self._oauth_connections:
            self._oauth_connections[user_id] = {}

        connection = {
            "provider": provider,
            "email": email,
            "connected_at": datetime.utcnow().isoformat(),
            "access_token": access_token,
        }
        self._oauth_connections[user_id][provider] = connection

        return connection

    def disconnect_oauth(self, user_id: str, provider: str) -> bool:
        """Remove OAuth connection for a user."""
        if user_id in self._oauth_connections:
            if provider in self._oauth_connections[user_id]:
                del self._oauth_connections[user_id][provider]
                return True
        return False

    def get_roles(self) -> List[Dict[str, Any]]:
        """Get all roles."""
        return list(self._roles.values())

    def get_role(self, role_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific role."""
        return self._roles.get(role_id)

    def create_role(self, role_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new role."""
        self._counter += 1
        role_id = f"role_{self._counter}"
        now = datetime.utcnow().isoformat()

        role = {
            "id": role_id,
            "name": role_data["name"],
            "description": role_data.get("description"),
            "permissions": role_data.get("permissions", []),
            "is_system": False,
            "created_at": now,
            "updated_at": now,
        }

        self._roles[role_id] = role
        return role

    def update_role(self, role_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a role."""
        role = self._roles.get(role_id)
        if not role:
            return None

        if role.get("is_system"):
            raise ValueError("Cannot modify system roles")

        for key, value in updates.items():
            if value is not None:
                role[key] = value

        role["updated_at"] = datetime.utcnow().isoformat()
        return role

    def delete_role(self, role_id: str) -> bool:
        """Delete a role."""
        role = self._roles.get(role_id)
        if not role:
            return False

        if role.get("is_system"):
            raise ValueError("Cannot delete system roles")

        del self._roles[role_id]
        return True

    def get_user_roles(self, user_id: str) -> List[str]:
        """Get roles for a user."""
        return self._user_roles.get(user_id, ["user"])

    def assign_roles(self, user_id: str, roles: List[str]) -> List[str]:
        """Assign roles to a user."""
        valid_roles = [r for r in roles if r in self._roles]
        self._user_roles[user_id] = valid_roles
        return valid_roles

    def get_permissions(self) -> List[Dict[str, str]]:
        """Get all available permissions."""
        return [
            {"id": p, "name": p.replace(".", " ").replace("_", " ").title()}
            for p in self.SYSTEM_PERMISSIONS
        ]

    def get_ip_rules(self) -> List[Dict[str, Any]]:
        """Get all IP rules."""
        return self._ip_rules

    def create_ip_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an IP rule."""
        self._counter += 1

        rule = {
            "id": f"ip_{self._counter}",
            "type": rule_data["type"],
            "ip_address": rule_data.get("ip_address"),
            "ip_range": rule_data.get("ip_range"),
            "description": rule_data.get("description"),
            "enabled": True,
            "created_at": datetime.utcnow().isoformat(),
        }

        self._ip_rules.append(rule)
        return rule

    def delete_ip_rule(self, rule_id: str) -> bool:
        """Delete an IP rule."""
        for i, rule in enumerate(self._ip_rules):
            if rule["id"] == rule_id:
                del self._ip_rules[i]
                return True
        return False

    def get_rate_limits(self) -> List[Dict[str, Any]]:
        """Get all rate limit configurations."""
        return self._rate_limits

    def set_rate_limit(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Set a rate limit configuration."""
        for i, limit in enumerate(self._rate_limits):
            if limit["endpoint_pattern"] == config["endpoint_pattern"]:
                self._rate_limits[i] = config
                return config

        self._rate_limits.append(config)
        return config

    def delete_rate_limit(self, endpoint_pattern: str) -> bool:
        """Delete a rate limit configuration."""
        for i, limit in enumerate(self._rate_limits):
            if limit["endpoint_pattern"] == endpoint_pattern:
                del self._rate_limits[i]
                return True
        return False

    def get_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        return self._config.copy()

    def update_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update security configuration."""
        for key, value in updates.items():
            if value is not None:
                self._config[key] = value
        return self._config.copy()


security_store = SecurityStore()


@router.get("/oauth/providers", response_model=OAuthProviderListResponse)
async def list_oauth_providers(current_user: dict = Depends(get_current_user)):
    """List available OAuth providers."""
    providers = security_store.get_oauth_providers()
    return OAuthProviderListResponse(
        providers=[OAuthProvider(**p) for p in providers],
    )


@router.post("/oauth/connect", response_model=OAuthConnectResponse)
async def initiate_oauth_connect(
    request: OAuthConnectRequest,
    current_user: dict = Depends(get_current_user),
):
    """Initiate OAuth connection flow."""
    provider = security_store.get_oauth_provider(request.provider)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown OAuth provider: {request.provider}",
        )

    if not provider.get("enabled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth provider {request.provider} is not enabled",
        )

    import secrets
    state = secrets.token_urlsafe(32)

    scopes = " ".join(provider.get("scopes", []))
    auth_url = (
        f"{provider['authorization_url']}?"
        f"client_id={provider.get('client_id', 'CLIENT_ID')}"
        f"&redirect_uri={request.redirect_uri}"
        f"&response_type=code"
        f"&scope={scopes}"
        f"&state={state}"
    )

    return OAuthConnectResponse(
        authorization_url=auth_url,
        state=state,
    )


@router.post("/oauth/callback")
async def handle_oauth_callback(
    request: OAuthCallbackRequest,
    current_user: dict = Depends(get_current_user),
):
    """Handle OAuth callback and complete connection."""
    provider = security_store.get_oauth_provider(request.provider)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown OAuth provider",
        )

    connection = security_store.connect_oauth(
        user_id=current_user["id"],
        provider=request.provider,
        email=current_user.get("email", ""),
        access_token="mock_access_token",
    )

    return {
        "success": True,
        "message": f"Successfully connected to {request.provider}",
        "connection": connection,
    }


@router.get("/oauth/connections")
async def get_oauth_connections(current_user: dict = Depends(get_current_user)):
    """Get user's OAuth connections."""
    connections = security_store.get_user_oauth_connections(current_user["id"])

    return {
        "success": True,
        "connections": [
            OAuthConnectionResponse(
                connected=True,
                provider=provider,
                connected_at=conn.get("connected_at"),
                email=conn.get("email"),
            )
            for provider, conn in connections.items()
        ],
    }


@router.delete("/oauth/connections/{provider}")
async def disconnect_oauth(
    provider: str,
    current_user: dict = Depends(get_current_user),
):
    """Disconnect an OAuth provider."""
    if not security_store.disconnect_oauth(current_user["id"], provider):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No connection found for provider: {provider}",
        )

    return {
        "success": True,
        "message": f"Disconnected from {provider}",
    }


@router.get("/rbac/roles", response_model=RoleListResponse)
async def list_roles(current_user: dict = Depends(require_roles("admin"))):
    """List all roles."""
    roles = security_store.get_roles()
    return RoleListResponse(
        roles=[RoleDefinition(**r) for r in roles],
    )


@router.post("/rbac/roles")
async def create_role(
    request: RoleCreateRequest,
    current_user: dict = Depends(require_roles("admin")),
):
    """Create a new role."""
    role = security_store.create_role(request.model_dump())
    return {
        "success": True,
        "role": RoleDefinition(**role),
    }


@router.get("/rbac/roles/{role_id}")
async def get_role(
    role_id: str,
    current_user: dict = Depends(require_roles("admin")),
):
    """Get a specific role."""
    role = security_store.get_role(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    return {
        "success": True,
        "role": RoleDefinition(**role),
    }


@router.put("/rbac/roles/{role_id}")
async def update_role(
    role_id: str,
    request: RoleUpdateRequest,
    current_user: dict = Depends(require_roles("admin")),
):
    """Update a role."""
    try:
        role = security_store.update_role(role_id, request.model_dump(exclude_unset=True))
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )
        return {
            "success": True,
            "role": RoleDefinition(**role),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/rbac/roles/{role_id}")
async def delete_role(
    role_id: str,
    current_user: dict = Depends(require_roles("admin")),
):
    """Delete a role."""
    try:
        if not security_store.delete_role(role_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )
        return {
            "success": True,
            "message": "Role deleted",
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/rbac/permissions", response_model=PermissionListResponse)
async def list_permissions(current_user: dict = Depends(require_roles("admin"))):
    """List all available permissions."""
    permissions = security_store.get_permissions()
    return PermissionListResponse(permissions=permissions)


@router.get("/rbac/users/{user_id}/roles")
async def get_user_roles(
    user_id: str,
    current_user: dict = Depends(require_roles("admin")),
):
    """Get roles for a specific user."""
    roles = security_store.get_user_roles(user_id)
    return {
        "success": True,
        "user_id": user_id,
        "roles": roles,
    }


@router.put("/rbac/users/{user_id}/roles")
async def assign_user_roles(
    user_id: str,
    request: UserRoleAssignment,
    current_user: dict = Depends(require_roles("admin")),
):
    """Assign roles to a user."""
    roles = security_store.assign_roles(user_id, request.roles)
    return {
        "success": True,
        "user_id": user_id,
        "roles": roles,
    }


@router.get("/ip-rules", response_model=IPRuleListResponse)
async def list_ip_rules(current_user: dict = Depends(require_roles("admin"))):
    """List all IP access rules."""
    rules = security_store.get_ip_rules()
    return IPRuleListResponse(
        rules=[IPRule(**r) for r in rules],
    )


@router.post("/ip-rules")
async def create_ip_rule(
    request: IPRuleCreateRequest,
    current_user: dict = Depends(require_roles("admin")),
):
    """Create an IP access rule."""
    if not request.ip_address and not request.ip_range:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either ip_address or ip_range is required",
        )

    rule = security_store.create_ip_rule(request.model_dump())
    return {
        "success": True,
        "rule": IPRule(**rule),
    }


@router.delete("/ip-rules/{rule_id}")
async def delete_ip_rule(
    rule_id: str,
    current_user: dict = Depends(require_roles("admin")),
):
    """Delete an IP access rule."""
    if not security_store.delete_ip_rule(rule_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IP rule not found",
        )
    return {
        "success": True,
        "message": "IP rule deleted",
    }


@router.get("/rate-limits", response_model=RateLimitListResponse)
async def list_rate_limits(current_user: dict = Depends(require_roles("admin"))):
    """List all rate limit configurations."""
    limits = security_store.get_rate_limits()
    return RateLimitListResponse(
        limits=[RateLimitConfig(**l) for l in limits],
    )


@router.post("/rate-limits")
async def set_rate_limit(
    request: RateLimitConfig,
    current_user: dict = Depends(require_roles("admin")),
):
    """Set a rate limit configuration."""
    config = security_store.set_rate_limit(request.model_dump())
    return {
        "success": True,
        "config": RateLimitConfig(**config),
    }


@router.delete("/rate-limits/{endpoint_pattern:path}")
async def delete_rate_limit(
    endpoint_pattern: str,
    current_user: dict = Depends(require_roles("admin")),
):
    """Delete a rate limit configuration."""
    if not security_store.delete_rate_limit(endpoint_pattern):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rate limit configuration not found",
        )
    return {
        "success": True,
        "message": "Rate limit configuration deleted",
    }


@router.get("/config", response_model=SecurityConfigResponse)
async def get_security_config(current_user: dict = Depends(require_roles("admin"))):
    """Get security configuration."""
    config = security_store.get_config()
    return SecurityConfigResponse(config=config)


@router.put("/config", response_model=SecurityConfigResponse)
async def update_security_config(
    request: SecurityConfigUpdateRequest,
    current_user: dict = Depends(require_roles("admin")),
):
    """Update security configuration."""
    updates = request.model_dump(exclude_unset=True)
    config = security_store.update_config(updates)
    return SecurityConfigResponse(config=config)


@router.get("/overview")
async def get_security_overview(current_user: dict = Depends(require_roles("admin"))):
    """Get security overview dashboard data."""
    config = security_store.get_config()
    ip_rules = security_store.get_ip_rules()
    rate_limits = security_store.get_rate_limits()
    oauth_providers = [p for p in security_store.get_oauth_providers() if p.get("enabled")]

    return {
        "success": True,
        "overview": {
            "mfa_required": config.get("mfa_required", False),
            "password_policy": {
                "min_length": config.get("password_min_length"),
                "complexity_required": any([
                    config.get("password_require_uppercase"),
                    config.get("password_require_numbers"),
                    config.get("password_require_special"),
                ]),
            },
            "session_timeout_minutes": config.get("session_timeout_minutes"),
            "lockout_after_attempts": config.get("max_failed_login_attempts"),
            "ip_rules_count": len(ip_rules),
            "rate_limits_count": len(rate_limits),
            "oauth_providers_enabled": len(oauth_providers),
        },
    }
