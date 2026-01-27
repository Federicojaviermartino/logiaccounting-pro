"""
RBAC (Role-Based Access Control) module for LogiAccounting Pro.
"""

from .roles import (
    SystemRole,
    RoleDefinition,
    RoleManager,
    role_manager,
    ROLE_HIERARCHY,
    DEFAULT_ROLE_DEFINITIONS,
)

from .permissions import (
    Action,
    Resource,
    Scope,
    Permission,
    PermissionGroup,
    PermissionRegistry,
    permission_registry,
)

from .policies import (
    PolicyEffect,
    PolicyPriority,
    ConditionOperator,
    PolicyCondition,
    TimeBasedCondition,
    IPBasedCondition,
    ResourceOwnershipCondition,
    Policy,
    PolicyEngine,
    policy_engine,
)

from .engine import (
    AccessDecision,
    AccessRequest,
    AccessResult,
    RBACEngine,
    rbac_engine,
    check_access,
    require_permission,
    require_role,
    require_any_role,
)

__all__ = [
    "SystemRole",
    "RoleDefinition",
    "RoleManager",
    "role_manager",
    "ROLE_HIERARCHY",
    "DEFAULT_ROLE_DEFINITIONS",
    "Action",
    "Resource",
    "Scope",
    "Permission",
    "PermissionGroup",
    "PermissionRegistry",
    "permission_registry",
    "PolicyEffect",
    "PolicyPriority",
    "ConditionOperator",
    "PolicyCondition",
    "TimeBasedCondition",
    "IPBasedCondition",
    "ResourceOwnershipCondition",
    "Policy",
    "PolicyEngine",
    "policy_engine",
    "AccessDecision",
    "AccessRequest",
    "AccessResult",
    "RBACEngine",
    "rbac_engine",
    "check_access",
    "require_permission",
    "require_role",
    "require_any_role",
]
