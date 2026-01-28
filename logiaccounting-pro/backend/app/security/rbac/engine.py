"""
RBAC Engine combining roles, permissions, and policies for LogiAccounting Pro.
"""

from dataclasses import dataclass, field
from typing import Optional, Set, Dict, List, Any, Tuple
from datetime import datetime
from enum import Enum

from app.utils.datetime_utils import utc_now
from .roles import RoleManager, role_manager, SystemRole
from .permissions import PermissionRegistry, permission_registry, Scope
from .policies import PolicyEngine, policy_engine, PolicyEffect


class AccessDecision(str, Enum):
    """Final access decision."""

    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_MFA = "require_mfa"
    REQUIRE_APPROVAL = "require_approval"


@dataclass
class AccessRequest:
    """Request for access evaluation."""

    user_id: str
    resource: str
    action: str
    organization_id: Optional[str] = None
    resource_id: Optional[str] = None
    resource_data: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    mfa_verified: bool = False
    session_id: Optional[str] = None
    additional_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessResult:
    """Result of access evaluation."""

    decision: AccessDecision
    allowed: bool
    reason: str
    evaluated_permissions: List[str] = field(default_factory=list)
    matched_permission: Optional[str] = None
    policy_effect: Optional[str] = None
    deciding_policy: Optional[str] = None
    required_actions: List[str] = field(default_factory=list)
    audit_data: Dict[str, Any] = field(default_factory=dict)


class RBACEngine:
    """Central RBAC engine combining roles, permissions, and policies."""

    def __init__(
        self,
        role_manager: Optional[RoleManager] = None,
        permission_registry: Optional[PermissionRegistry] = None,
        policy_engine: Optional[PolicyEngine] = None,
    ):
        self._role_manager = role_manager or RoleManager()
        self._permission_registry = permission_registry or PermissionRegistry()
        self._policy_engine = policy_engine or PolicyEngine()
        self._user_permissions_cache: Dict[str, Tuple[Set[str], datetime]] = {}
        self._cache_ttl_seconds: int = 300

    def check_access(self, request: AccessRequest) -> AccessResult:
        """Evaluate access request and return decision."""
        context = self._build_context(request)
        user_permissions = self._get_user_permissions(
            request.user_id,
            request.organization_id,
        )

        required_permission = self._permission_registry.format_permission_name(
            request.resource,
            request.action,
        )

        permission_obj = self._permission_registry.get_permission(required_permission)
        if permission_obj and permission_obj.requires_mfa and not request.mfa_verified:
            return AccessResult(
                decision=AccessDecision.REQUIRE_MFA,
                allowed=False,
                reason="MFA verification required for this action",
                evaluated_permissions=[required_permission],
                required_actions=["mfa_verification"],
                audit_data=self._create_audit_data(request, "mfa_required"),
            )

        has_permission, matched = self._check_permission(
            required_permission,
            user_permissions,
        )

        if not has_permission:
            scoped_permission = f"{required_permission}:own"
            has_scoped, scoped_matched = self._check_permission(
                scoped_permission,
                user_permissions,
            )
            if has_scoped:
                if self._check_ownership(request, context):
                    has_permission = True
                    matched = scoped_matched

        if not has_permission:
            return AccessResult(
                decision=AccessDecision.DENY,
                allowed=False,
                reason=f"Permission '{required_permission}' not granted",
                evaluated_permissions=[required_permission],
                audit_data=self._create_audit_data(request, "permission_denied"),
            )

        user_roles = self._role_manager.get_user_roles(
            request.user_id,
            request.organization_id,
        )
        primary_role = list(user_roles)[0] if user_roles else None

        policy_result = self._policy_engine.evaluate_with_details(
            request.resource,
            request.action,
            context,
            primary_role,
        )

        if policy_result["effect"] == PolicyEffect.DENY.value:
            return AccessResult(
                decision=AccessDecision.DENY,
                allowed=False,
                reason="Access denied by policy",
                evaluated_permissions=[required_permission],
                matched_permission=matched,
                policy_effect=policy_result["effect"],
                deciding_policy=policy_result["deciding_policy"],
                audit_data=self._create_audit_data(request, "policy_denied"),
            )

        return AccessResult(
            decision=AccessDecision.ALLOW,
            allowed=True,
            reason="Access granted",
            evaluated_permissions=[required_permission],
            matched_permission=matched,
            policy_effect=policy_result["effect"],
            deciding_policy=policy_result.get("deciding_policy"),
            audit_data=self._create_audit_data(request, "granted"),
        )

    def _build_context(self, request: AccessRequest) -> Dict[str, Any]:
        """Build evaluation context from request."""
        return {
            "user_id": request.user_id,
            "organization_id": request.organization_id,
            "resource": request.resource_data,
            "resource_id": request.resource_id,
            "ip_address": request.ip_address,
            "user_agent": request.user_agent,
            "mfa_verified": request.mfa_verified,
            "session_id": request.session_id,
            "current_time": utc_now(),
            **request.additional_context,
        }

    def _get_user_permissions(
        self,
        user_id: str,
        organization_id: Optional[str] = None,
    ) -> Set[str]:
        """Get user permissions with caching."""
        cache_key = f"{user_id}:{organization_id}"
        cached = self._user_permissions_cache.get(cache_key)

        if cached:
            permissions, cached_at = cached
            elapsed = (utc_now() - cached_at).total_seconds()
            if elapsed < self._cache_ttl_seconds:
                return permissions

        permissions = self._role_manager.get_effective_permissions(
            user_id,
            organization_id,
        )

        self._user_permissions_cache[cache_key] = (permissions, utc_now())
        return permissions

    def _check_permission(
        self,
        required: str,
        granted: Set[str],
    ) -> Tuple[bool, Optional[str]]:
        """Check if required permission is granted."""
        for perm in granted:
            if self._permission_registry.matches_permission(required, perm):
                return True, perm
        return False, None

    def _check_ownership(
        self,
        request: AccessRequest,
        context: Dict[str, Any],
    ) -> bool:
        """Check resource ownership for scoped permissions."""
        resource = request.resource_data
        if not resource:
            return False

        owner_id = resource.get("user_id") or resource.get("owner_id")
        if owner_id and owner_id == request.user_id:
            return True

        creator_id = resource.get("created_by")
        if creator_id and creator_id == request.user_id:
            return True

        return False

    def _create_audit_data(
        self,
        request: AccessRequest,
        result: str,
    ) -> Dict[str, Any]:
        """Create audit data for the access check."""
        return {
            "user_id": request.user_id,
            "organization_id": request.organization_id,
            "resource": request.resource,
            "action": request.action,
            "resource_id": request.resource_id,
            "result": result,
            "ip_address": request.ip_address,
            "timestamp": utc_now().isoformat(),
        }

    def invalidate_user_cache(
        self,
        user_id: str,
        organization_id: Optional[str] = None,
    ) -> None:
        """Invalidate cached permissions for a user."""
        cache_key = f"{user_id}:{organization_id}"
        if cache_key in self._user_permissions_cache:
            del self._user_permissions_cache[cache_key]

    def invalidate_all_cache(self) -> None:
        """Clear all cached permissions."""
        self._user_permissions_cache.clear()

    def assign_role(
        self,
        user_id: str,
        role: str,
        assigner_id: str,
        assigner_role: str,
        organization_id: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Assign a role to a user with authorization check."""
        if not self._role_manager.can_assign_role(assigner_role, role):
            return False, f"Role '{assigner_role}' cannot assign role '{role}'"

        success = self._role_manager.assign_role_to_user(
            user_id,
            role,
            organization_id,
        )

        if success:
            self.invalidate_user_cache(user_id, organization_id)
            return True, f"Role '{role}' assigned successfully"

        return False, "Failed to assign role"

    def revoke_role(
        self,
        user_id: str,
        role: str,
        revoker_id: str,
        revoker_role: str,
        organization_id: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Revoke a role from a user with authorization check."""
        if not self._role_manager.is_role_superior(revoker_role, role):
            return False, f"Role '{revoker_role}' cannot revoke role '{role}'"

        success = self._role_manager.revoke_role_from_user(
            user_id,
            role,
            organization_id,
        )

        if success:
            self.invalidate_user_cache(user_id, organization_id)
            return True, f"Role '{role}' revoked successfully"

        return False, "Failed to revoke role"

    def get_user_roles(
        self,
        user_id: str,
        organization_id: Optional[str] = None,
    ) -> Set[str]:
        """Get roles assigned to a user."""
        return self._role_manager.get_user_roles(user_id, organization_id)

    def get_user_permissions(
        self,
        user_id: str,
        organization_id: Optional[str] = None,
    ) -> Set[str]:
        """Get all effective permissions for a user."""
        return self._get_user_permissions(user_id, organization_id)

    def has_permission(
        self,
        user_id: str,
        permission: str,
        organization_id: Optional[str] = None,
    ) -> bool:
        """Quick check if user has a specific permission."""
        permissions = self._get_user_permissions(user_id, organization_id)
        has_it, _ = self._check_permission(permission, permissions)
        return has_it

    def has_any_permission(
        self,
        user_id: str,
        permissions: List[str],
        organization_id: Optional[str] = None,
    ) -> bool:
        """Check if user has any of the specified permissions."""
        user_permissions = self._get_user_permissions(user_id, organization_id)
        for perm in permissions:
            has_it, _ = self._check_permission(perm, user_permissions)
            if has_it:
                return True
        return False

    def has_all_permissions(
        self,
        user_id: str,
        permissions: List[str],
        organization_id: Optional[str] = None,
    ) -> bool:
        """Check if user has all of the specified permissions."""
        user_permissions = self._get_user_permissions(user_id, organization_id)
        for perm in permissions:
            has_it, _ = self._check_permission(perm, user_permissions)
            if not has_it:
                return False
        return True

    def has_role(
        self,
        user_id: str,
        role: str,
        organization_id: Optional[str] = None,
    ) -> bool:
        """Check if user has a specific role."""
        roles = self._role_manager.get_user_roles(user_id, organization_id)
        return role in roles

    def has_any_role(
        self,
        user_id: str,
        roles: List[str],
        organization_id: Optional[str] = None,
    ) -> bool:
        """Check if user has any of the specified roles."""
        user_roles = self._role_manager.get_user_roles(user_id, organization_id)
        return bool(user_roles.intersection(set(roles)))

    def get_accessible_resources(
        self,
        user_id: str,
        action: str,
        organization_id: Optional[str] = None,
    ) -> List[str]:
        """Get list of resources user can access with given action."""
        permissions = self._get_user_permissions(user_id, organization_id)
        accessible = []

        for perm in permissions:
            parts = perm.split(":")
            if len(parts) >= 2:
                resource, perm_action = parts[0], parts[1]
                if perm_action == action or perm_action == "*":
                    if resource not in accessible:
                        accessible.append(resource)

        return accessible

    def get_role_manager(self) -> RoleManager:
        """Get the role manager instance."""
        return self._role_manager

    def get_permission_registry(self) -> PermissionRegistry:
        """Get the permission registry instance."""
        return self._permission_registry

    def get_policy_engine(self) -> PolicyEngine:
        """Get the policy engine instance."""
        return self._policy_engine


rbac_engine = RBACEngine(
    role_manager=role_manager,
    permission_registry=permission_registry,
    policy_engine=policy_engine,
)


def check_access(
    user_id: str,
    resource: str,
    action: str,
    organization_id: Optional[str] = None,
    resource_data: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    mfa_verified: bool = False,
) -> AccessResult:
    """Convenience function for access checking."""
    request = AccessRequest(
        user_id=user_id,
        resource=resource,
        action=action,
        organization_id=organization_id,
        resource_data=resource_data or {},
        ip_address=ip_address,
        mfa_verified=mfa_verified,
    )
    return rbac_engine.check_access(request)


def require_permission(permission: str):
    """Decorator for requiring a permission on a function."""
    def decorator(func):
        func._required_permission = permission
        return func
    return decorator


def require_role(role: str):
    """Decorator for requiring a role on a function."""
    def decorator(func):
        func._required_role = role
        return func
    return decorator


def require_any_role(*roles: str):
    """Decorator for requiring any of the specified roles."""
    def decorator(func):
        func._required_any_role = list(roles)
        return func
    return decorator
