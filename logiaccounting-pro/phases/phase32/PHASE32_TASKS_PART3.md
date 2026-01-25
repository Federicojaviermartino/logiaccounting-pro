# Phase 32: Advanced Security - Part 3: RBAC Engine

## Overview
This part covers Role-Based Access Control (RBAC) with roles, permissions, and policy engine.

---

## File 1: Role Definitions
**Path:** `backend/app/security/rbac/roles.py`

```python
"""
Role Definitions
System and custom role management
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)


class SystemRole(str, Enum):
    """Built-in system roles."""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    ACCOUNTANT = "accountant"
    PROJECT_MANAGER = "project_manager"
    CLIENT = "client"
    SUPPLIER = "supplier"
    READ_ONLY = "read_only"
    GUEST = "guest"


@dataclass
class Role:
    """Role definition."""
    id: str
    name: str
    display_name: str
    description: str = ""
    is_system: bool = False
    permissions: Set[str] = field(default_factory=set)
    inherits_from: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "is_system": self.is_system,
            "permissions": list(self.permissions),
            "inherits_from": self.inherits_from,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class RoleManager:
    """Manages roles and role assignments."""
    
    def __init__(self):
        self._roles: Dict[str, Role] = {}
        self._role_hierarchy: Dict[str, Set[str]] = {}
        self._init_system_roles()
    
    def _init_system_roles(self):
        """Initialize built-in system roles."""
        
        # Super Admin - full access
        self.create_role(Role(
            id="role_super_admin",
            name=SystemRole.SUPER_ADMIN.value,
            display_name="Super Administrator",
            description="Full system access with all permissions",
            is_system=True,
            permissions={"*"},  # Wildcard for all permissions
        ))
        
        # Admin - organization-level admin
        self.create_role(Role(
            id="role_admin",
            name=SystemRole.ADMIN.value,
            display_name="Administrator",
            description="Organization administrator with broad access",
            is_system=True,
            permissions={
                "users:*",
                "customers:*",
                "invoices:*",
                "projects:*",
                "reports:*",
                "settings:read",
                "settings:update",
                "audit:read",
            },
        ))
        
        # Manager
        self.create_role(Role(
            id="role_manager",
            name=SystemRole.MANAGER.value,
            display_name="Manager",
            description="Department or team manager",
            is_system=True,
            permissions={
                "customers:read",
                "customers:create",
                "customers:update",
                "invoices:*",
                "projects:*",
                "reports:read",
                "reports:create",
            },
        ))
        
        # Accountant
        self.create_role(Role(
            id="role_accountant",
            name=SystemRole.ACCOUNTANT.value,
            display_name="Accountant",
            description="Financial operations access",
            is_system=True,
            permissions={
                "invoices:*",
                "payments:*",
                "expenses:*",
                "reports:read",
                "reports:create",
                "customers:read",
                "projects:read",
                "transactions:*",
            },
        ))
        
        # Project Manager
        self.create_role(Role(
            id="role_project_manager",
            name=SystemRole.PROJECT_MANAGER.value,
            display_name="Project Manager",
            description="Project management access",
            is_system=True,
            permissions={
                "projects:*",
                "tasks:*",
                "customers:read",
                "invoices:read",
                "invoices:create",
                "reports:read",
            },
        ))
        
        # Client
        self.create_role(Role(
            id="role_client",
            name=SystemRole.CLIENT.value,
            display_name="Client",
            description="External client access",
            is_system=True,
            permissions={
                "invoices:read:own",
                "projects:read:own",
                "payments:create:own",
                "documents:read:own",
                "profile:*",
            },
        ))
        
        # Supplier
        self.create_role(Role(
            id="role_supplier",
            name=SystemRole.SUPPLIER.value,
            display_name="Supplier",
            description="External supplier access",
            is_system=True,
            permissions={
                "invoices:read:own",
                "invoices:create:own",
                "payments:read:own",
                "documents:read:own",
                "profile:*",
            },
        ))
        
        # Read Only
        self.create_role(Role(
            id="role_read_only",
            name=SystemRole.READ_ONLY.value,
            display_name="Read Only",
            description="View-only access",
            is_system=True,
            permissions={
                "customers:read",
                "invoices:read",
                "projects:read",
                "reports:read",
            },
        ))
        
        # Guest
        self.create_role(Role(
            id="role_guest",
            name=SystemRole.GUEST.value,
            display_name="Guest",
            description="Limited guest access",
            is_system=True,
            permissions={
                "public:read",
            },
        ))
        
        # Build hierarchy
        self._build_hierarchy()
    
    def _build_hierarchy(self):
        """Build role inheritance hierarchy."""
        self._role_hierarchy = {
            SystemRole.SUPER_ADMIN.value: {
                SystemRole.ADMIN.value,
            },
            SystemRole.ADMIN.value: {
                SystemRole.MANAGER.value,
            },
            SystemRole.MANAGER.value: {
                SystemRole.READ_ONLY.value,
            },
            SystemRole.ACCOUNTANT.value: {
                SystemRole.READ_ONLY.value,
            },
            SystemRole.PROJECT_MANAGER.value: {
                SystemRole.READ_ONLY.value,
            },
        }
    
    def create_role(self, role: Role) -> Role:
        """Create or update a role."""
        self._roles[role.name] = role
        logger.info(f"Role created/updated: {role.name}")
        return role
    
    def get_role(self, name: str) -> Optional[Role]:
        """Get role by name."""
        return self._roles.get(name)
    
    def get_all_roles(self, include_system: bool = True) -> List[Role]:
        """Get all roles."""
        roles = list(self._roles.values())
        if not include_system:
            roles = [r for r in roles if not r.is_system]
        return roles
    
    def delete_role(self, name: str) -> bool:
        """Delete a custom role."""
        role = self._roles.get(name)
        if not role:
            return False
        
        if role.is_system:
            raise ValueError("Cannot delete system roles")
        
        del self._roles[name]
        logger.info(f"Role deleted: {name}")
        return True
    
    def get_role_permissions(self, role_name: str, include_inherited: bool = True) -> Set[str]:
        """Get all permissions for a role."""
        role = self._roles.get(role_name)
        if not role:
            return set()
        
        permissions = role.permissions.copy()
        
        if include_inherited:
            # Get inherited roles
            inherited_roles = self._get_inherited_roles(role_name)
            for inherited_name in inherited_roles:
                inherited_role = self._roles.get(inherited_name)
                if inherited_role:
                    permissions.update(inherited_role.permissions)
        
        return permissions
    
    def _get_inherited_roles(self, role_name: str, visited: Set[str] = None) -> Set[str]:
        """Get all roles inherited by a role."""
        if visited is None:
            visited = set()
        
        if role_name in visited:
            return set()
        
        visited.add(role_name)
        inherited = self._role_hierarchy.get(role_name, set()).copy()
        
        for child_role in inherited.copy():
            inherited.update(self._get_inherited_roles(child_role, visited))
        
        return inherited
    
    def add_permission_to_role(self, role_name: str, permission: str):
        """Add permission to a role."""
        role = self._roles.get(role_name)
        if not role:
            raise ValueError(f"Role not found: {role_name}")
        
        role.permissions.add(permission)
        role.updated_at = datetime.utcnow()
    
    def remove_permission_from_role(self, role_name: str, permission: str):
        """Remove permission from a role."""
        role = self._roles.get(role_name)
        if not role:
            raise ValueError(f"Role not found: {role_name}")
        
        role.permissions.discard(permission)
        role.updated_at = datetime.utcnow()


# Global role manager
role_manager = RoleManager()


def get_role_manager() -> RoleManager:
    """Get role manager instance."""
    return role_manager
```

---

## File 2: Permission Definitions
**Path:** `backend/app/security/rbac/permissions.py`

```python
"""
Permission Definitions
Resource and action-based permissions
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class Action(str, Enum):
    """Standard CRUD actions."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    EXPORT = "export"
    IMPORT = "import"
    APPROVE = "approve"
    REJECT = "reject"
    EXECUTE = "execute"


class Resource(str, Enum):
    """System resources."""
    USERS = "users"
    CUSTOMERS = "customers"
    SUPPLIERS = "suppliers"
    INVOICES = "invoices"
    PROJECTS = "projects"
    TASKS = "tasks"
    PAYMENTS = "payments"
    EXPENSES = "expenses"
    TRANSACTIONS = "transactions"
    REPORTS = "reports"
    DOCUMENTS = "documents"
    SETTINGS = "settings"
    AUDIT = "audit"
    ROLES = "roles"
    PROFILE = "profile"
    PUBLIC = "public"


@dataclass
class Permission:
    """Permission definition."""
    resource: str
    action: str
    scope: str = "*"  # *, own, team, customer
    description: str = ""
    
    def __str__(self) -> str:
        if self.scope and self.scope != "*":
            return f"{self.resource}:{self.action}:{self.scope}"
        return f"{self.resource}:{self.action}"
    
    def __hash__(self):
        return hash(str(self))
    
    def __eq__(self, other):
        if isinstance(other, str):
            return str(self) == other
        return str(self) == str(other)


class PermissionRegistry:
    """Registry of all available permissions."""
    
    def __init__(self):
        self._permissions: Dict[str, Permission] = {}
        self._init_permissions()
    
    def _init_permissions(self):
        """Initialize all system permissions."""
        
        # Define permissions for each resource
        resources_actions = {
            Resource.USERS: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.LIST],
            Resource.CUSTOMERS: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.LIST, Action.EXPORT],
            Resource.SUPPLIERS: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.LIST],
            Resource.INVOICES: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.LIST, Action.EXPORT, Action.APPROVE],
            Resource.PROJECTS: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.LIST, Action.EXPORT],
            Resource.TASKS: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.LIST],
            Resource.PAYMENTS: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.LIST, Action.APPROVE],
            Resource.EXPENSES: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.LIST, Action.APPROVE],
            Resource.TRANSACTIONS: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.LIST, Action.EXPORT],
            Resource.REPORTS: [Action.CREATE, Action.READ, Action.LIST, Action.EXPORT],
            Resource.DOCUMENTS: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.LIST],
            Resource.SETTINGS: [Action.READ, Action.UPDATE],
            Resource.AUDIT: [Action.READ, Action.LIST, Action.EXPORT],
            Resource.ROLES: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.LIST],
            Resource.PROFILE: [Action.READ, Action.UPDATE],
            Resource.PUBLIC: [Action.READ],
        }
        
        for resource, actions in resources_actions.items():
            for action in actions:
                # Standard permission
                perm = Permission(
                    resource=resource.value,
                    action=action.value,
                    description=f"{action.value.title()} {resource.value}",
                )
                self._permissions[str(perm)] = perm
                
                # Scoped permissions for certain resources
                if resource in [Resource.INVOICES, Resource.PROJECTS, Resource.DOCUMENTS, Resource.PAYMENTS]:
                    for scope in ["own", "team", "customer"]:
                        scoped_perm = Permission(
                            resource=resource.value,
                            action=action.value,
                            scope=scope,
                            description=f"{action.value.title()} {scope} {resource.value}",
                        )
                        self._permissions[str(scoped_perm)] = scoped_perm
    
    def get_permission(self, permission_str: str) -> Optional[Permission]:
        """Get permission by string."""
        return self._permissions.get(permission_str)
    
    def get_all_permissions(self) -> List[Permission]:
        """Get all registered permissions."""
        return list(self._permissions.values())
    
    def get_permissions_for_resource(self, resource: str) -> List[Permission]:
        """Get all permissions for a resource."""
        return [
            p for p in self._permissions.values()
            if p.resource == resource
        ]
    
    def is_valid_permission(self, permission_str: str) -> bool:
        """Check if permission string is valid."""
        if permission_str == "*":
            return True
        
        if permission_str.endswith(":*"):
            resource = permission_str[:-2]
            return any(p.resource == resource for p in self._permissions.values())
        
        return permission_str in self._permissions


class PermissionMatcher:
    """Matches permission requests against granted permissions."""
    
    @staticmethod
    def matches(granted: Set[str], required: str) -> bool:
        """Check if granted permissions satisfy the required permission."""
        
        # Wildcard matches everything
        if "*" in granted:
            return True
        
        # Direct match
        if required in granted:
            return True
        
        # Parse required permission
        parts = required.split(":")
        resource = parts[0]
        action = parts[1] if len(parts) > 1 else None
        scope = parts[2] if len(parts) > 2 else None
        
        # Check resource wildcard (e.g., "invoices:*")
        if f"{resource}:*" in granted:
            return True
        
        # Check if granted has broader scope
        if scope:
            # If granted has same action without scope restriction, it matches
            if f"{resource}:{action}" in granted:
                return True
            
            # Scope hierarchy: * > customer > team > own
            scope_hierarchy = ["own", "team", "customer", "*"]
            required_scope_idx = scope_hierarchy.index(scope) if scope in scope_hierarchy else -1
            
            for granted_perm in granted:
                if granted_perm.startswith(f"{resource}:{action}:"):
                    granted_scope = granted_perm.split(":")[2]
                    granted_scope_idx = scope_hierarchy.index(granted_scope) if granted_scope in scope_hierarchy else -1
                    
                    if granted_scope_idx >= required_scope_idx:
                        return True
        
        return False


# Global permission registry
permission_registry = PermissionRegistry()


def get_permission_registry() -> PermissionRegistry:
    """Get permission registry instance."""
    return permission_registry
```

---

## File 3: Access Policies
**Path:** `backend/app/security/rbac/policies.py`

```python
"""
Access Policies
Attribute-based and conditional access policies
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class PolicyEffect(str, Enum):
    """Policy effect."""
    ALLOW = "allow"
    DENY = "deny"


class PolicyConditionType(str, Enum):
    """Types of policy conditions."""
    TIME_RANGE = "time_range"
    IP_RANGE = "ip_range"
    RESOURCE_OWNER = "resource_owner"
    ATTRIBUTE_MATCH = "attribute_match"
    CUSTOM = "custom"


@dataclass
class PolicyCondition:
    """A single policy condition."""
    type: PolicyConditionType
    params: Dict[str, Any] = field(default_factory=dict)
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate the condition against context."""
        if self.type == PolicyConditionType.TIME_RANGE:
            return self._eval_time_range(context)
        elif self.type == PolicyConditionType.IP_RANGE:
            return self._eval_ip_range(context)
        elif self.type == PolicyConditionType.RESOURCE_OWNER:
            return self._eval_resource_owner(context)
        elif self.type == PolicyConditionType.ATTRIBUTE_MATCH:
            return self._eval_attribute_match(context)
        elif self.type == PolicyConditionType.CUSTOM:
            return self._eval_custom(context)
        return False
    
    def _eval_time_range(self, context: Dict) -> bool:
        """Check if current time is within allowed range."""
        start_time = self.params.get("start_time")
        end_time = self.params.get("end_time")
        allowed_days = self.params.get("days", [0, 1, 2, 3, 4])  # Mon-Fri default
        timezone = self.params.get("timezone", "UTC")
        
        now = datetime.utcnow()
        current_day = now.weekday()
        current_time = now.time()
        
        # Check day
        if current_day not in allowed_days:
            return False
        
        # Check time
        if start_time and end_time:
            start = time.fromisoformat(start_time)
            end = time.fromisoformat(end_time)
            
            if start <= end:
                return start <= current_time <= end
            else:
                # Time range crosses midnight
                return current_time >= start or current_time <= end
        
        return True
    
    def _eval_ip_range(self, context: Dict) -> bool:
        """Check if IP is in allowed range."""
        import ipaddress
        
        allowed_ranges = self.params.get("ranges", [])
        client_ip = context.get("ip_address")
        
        if not client_ip:
            return False
        
        try:
            client = ipaddress.ip_address(client_ip)
            
            for range_str in allowed_ranges:
                if "/" in range_str:
                    network = ipaddress.ip_network(range_str, strict=False)
                    if client in network:
                        return True
                else:
                    if client == ipaddress.ip_address(range_str):
                        return True
        except ValueError:
            return False
        
        return False
    
    def _eval_resource_owner(self, context: Dict) -> bool:
        """Check if user owns the resource."""
        user_id = context.get("user_id")
        resource_owner_id = context.get("resource", {}).get("owner_id")
        
        if not user_id or not resource_owner_id:
            return False
        
        return user_id == resource_owner_id
    
    def _eval_attribute_match(self, context: Dict) -> bool:
        """Check if attribute matches expected value."""
        attribute = self.params.get("attribute")
        expected = self.params.get("expected")
        operator = self.params.get("operator", "eq")
        
        actual = context.get(attribute)
        
        if operator == "eq":
            return actual == expected
        elif operator == "neq":
            return actual != expected
        elif operator == "in":
            return actual in expected
        elif operator == "not_in":
            return actual not in expected
        elif operator == "gt":
            return actual > expected
        elif operator == "gte":
            return actual >= expected
        elif operator == "lt":
            return actual < expected
        elif operator == "lte":
            return actual <= expected
        elif operator == "contains":
            return expected in actual if actual else False
        
        return False
    
    def _eval_custom(self, context: Dict) -> bool:
        """Evaluate custom condition."""
        evaluator = self.params.get("evaluator")
        if callable(evaluator):
            return evaluator(context)
        return False


@dataclass
class Policy:
    """Access policy definition."""
    id: str
    name: str
    description: str = ""
    effect: PolicyEffect = PolicyEffect.ALLOW
    resources: List[str] = field(default_factory=list)  # Resource patterns
    actions: List[str] = field(default_factory=list)  # Action patterns
    conditions: List[PolicyCondition] = field(default_factory=list)
    principals: List[str] = field(default_factory=list)  # User/role patterns
    priority: int = 0  # Higher = evaluated first
    is_active: bool = True
    
    def matches_request(
        self,
        resource: str,
        action: str,
        principal: str,
    ) -> bool:
        """Check if policy matches the request."""
        # Check resource
        if not self._matches_pattern(resource, self.resources):
            return False
        
        # Check action
        if not self._matches_pattern(action, self.actions):
            return False
        
        # Check principal
        if self.principals and not self._matches_pattern(principal, self.principals):
            return False
        
        return True
    
    def evaluate_conditions(self, context: Dict[str, Any]) -> bool:
        """Evaluate all policy conditions."""
        if not self.conditions:
            return True
        
        # All conditions must pass
        return all(cond.evaluate(context) for cond in self.conditions)
    
    def _matches_pattern(self, value: str, patterns: List[str]) -> bool:
        """Check if value matches any pattern."""
        if not patterns:
            return True
        
        for pattern in patterns:
            if pattern == "*":
                return True
            if pattern == value:
                return True
            if pattern.endswith("*"):
                if value.startswith(pattern[:-1]):
                    return True
        
        return False
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "effect": self.effect.value,
            "resources": self.resources,
            "actions": self.actions,
            "priority": self.priority,
            "is_active": self.is_active,
        }


class PolicyEngine:
    """Evaluates access policies."""
    
    def __init__(self):
        self._policies: List[Policy] = []
        self._init_default_policies()
    
    def _init_default_policies(self):
        """Initialize default security policies."""
        
        # Deny access outside business hours for sensitive operations
        self.add_policy(Policy(
            id="policy_business_hours",
            name="Business Hours Only",
            description="Restrict sensitive operations to business hours",
            effect=PolicyEffect.DENY,
            resources=["payments:*", "invoices:approve"],
            actions=["*"],
            conditions=[
                PolicyCondition(
                    type=PolicyConditionType.TIME_RANGE,
                    params={
                        "start_time": "08:00",
                        "end_time": "18:00",
                        "days": [0, 1, 2, 3, 4],  # Mon-Fri
                    },
                ),
            ],
            priority=10,
            is_active=False,  # Disabled by default
        ))
        
        # Require resource ownership for own-scoped permissions
        self.add_policy(Policy(
            id="policy_ownership",
            name="Resource Ownership",
            description="Users can only access their own resources",
            effect=PolicyEffect.DENY,
            resources=["*:own"],
            actions=["*"],
            conditions=[
                PolicyCondition(
                    type=PolicyConditionType.RESOURCE_OWNER,
                ),
            ],
            priority=100,
            is_active=True,
        ))
    
    def add_policy(self, policy: Policy):
        """Add a policy."""
        self._policies.append(policy)
        self._policies.sort(key=lambda p: -p.priority)
    
    def remove_policy(self, policy_id: str):
        """Remove a policy."""
        self._policies = [p for p in self._policies if p.id != policy_id]
    
    def get_policy(self, policy_id: str) -> Optional[Policy]:
        """Get policy by ID."""
        for policy in self._policies:
            if policy.id == policy_id:
                return policy
        return None
    
    def get_all_policies(self) -> List[Policy]:
        """Get all policies."""
        return self._policies.copy()
    
    def evaluate(
        self,
        resource: str,
        action: str,
        principal: str,
        context: Dict[str, Any] = None,
    ) -> tuple[bool, Optional[Policy]]:
        """
        Evaluate policies for an access request.
        Returns (allowed, matching_policy).
        """
        context = context or {}
        
        for policy in self._policies:
            if not policy.is_active:
                continue
            
            if not policy.matches_request(resource, action, principal):
                continue
            
            if not policy.evaluate_conditions(context):
                continue
            
            # Policy matches
            is_allowed = policy.effect == PolicyEffect.ALLOW
            return is_allowed, policy
        
        # No matching policy - default allow
        return True, None


# Global policy engine
policy_engine = PolicyEngine()


def get_policy_engine() -> PolicyEngine:
    """Get policy engine instance."""
    return policy_engine
```

---

## File 4: RBAC Engine
**Path:** `backend/app/security/rbac/engine.py`

```python
"""
RBAC Engine
Main authorization engine combining roles, permissions, and policies
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import logging

from app.security.rbac.roles import RoleManager, role_manager, Role
from app.security.rbac.permissions import PermissionMatcher, permission_registry
from app.security.rbac.policies import PolicyEngine, policy_engine, PolicyEffect

logger = logging.getLogger(__name__)


@dataclass
class AuthorizationResult:
    """Result of an authorization check."""
    allowed: bool
    reason: str = ""
    matched_permission: Optional[str] = None
    matched_policy: Optional[str] = None
    context: Dict = None


@dataclass
class UserRoleAssignment:
    """Role assignment for a user."""
    user_id: str
    role_name: str
    customer_id: Optional[str] = None
    granted_by: Optional[str] = None
    granted_at: datetime = None
    expires_at: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at


class RBACEngine:
    """Main RBAC authorization engine."""
    
    def __init__(self):
        self.role_manager = role_manager
        self.policy_engine = policy_engine
        
        # In-memory storage (use database in production)
        self._user_roles: Dict[str, List[UserRoleAssignment]] = {}
        self._authorization_cache: Dict[str, AuthorizationResult] = {}
        self._cache_ttl_seconds = 60
    
    def assign_role(
        self,
        user_id: str,
        role_name: str,
        customer_id: str = None,
        granted_by: str = None,
        expires_at: datetime = None,
    ) -> UserRoleAssignment:
        """Assign a role to a user."""
        # Validate role exists
        role = self.role_manager.get_role(role_name)
        if not role:
            raise ValueError(f"Role not found: {role_name}")
        
        assignment = UserRoleAssignment(
            user_id=user_id,
            role_name=role_name,
            customer_id=customer_id,
            granted_by=granted_by,
            granted_at=datetime.utcnow(),
            expires_at=expires_at,
        )
        
        if user_id not in self._user_roles:
            self._user_roles[user_id] = []
        
        # Check for duplicate
        existing = [a for a in self._user_roles[user_id]
                   if a.role_name == role_name and a.customer_id == customer_id]
        
        if existing:
            # Update existing assignment
            existing[0].expires_at = expires_at
            existing[0].granted_at = datetime.utcnow()
            existing[0].granted_by = granted_by
            assignment = existing[0]
        else:
            self._user_roles[user_id].append(assignment)
        
        # Clear cache for user
        self._clear_user_cache(user_id)
        
        logger.info(f"Role {role_name} assigned to user {user_id}")
        return assignment
    
    def revoke_role(
        self,
        user_id: str,
        role_name: str,
        customer_id: str = None,
    ) -> bool:
        """Revoke a role from a user."""
        if user_id not in self._user_roles:
            return False
        
        original_count = len(self._user_roles[user_id])
        
        self._user_roles[user_id] = [
            a for a in self._user_roles[user_id]
            if not (a.role_name == role_name and
                   (customer_id is None or a.customer_id == customer_id))
        ]
        
        revoked = len(self._user_roles[user_id]) < original_count
        
        if revoked:
            self._clear_user_cache(user_id)
            logger.info(f"Role {role_name} revoked from user {user_id}")
        
        return revoked
    
    def get_user_roles(self, user_id: str, customer_id: str = None) -> List[Role]:
        """Get all roles for a user."""
        assignments = self._user_roles.get(user_id, [])
        
        # Filter by customer if specified
        if customer_id:
            assignments = [a for a in assignments
                         if a.customer_id is None or a.customer_id == customer_id]
        
        # Filter expired
        assignments = [a for a in assignments if not a.is_expired()]
        
        # Get role objects
        roles = []
        for assignment in assignments:
            role = self.role_manager.get_role(assignment.role_name)
            if role:
                roles.append(role)
        
        return roles
    
    def get_user_permissions(
        self,
        user_id: str,
        customer_id: str = None,
    ) -> Set[str]:
        """Get all permissions for a user (including inherited)."""
        roles = self.get_user_roles(user_id, customer_id)
        
        permissions = set()
        for role in roles:
            role_permissions = self.role_manager.get_role_permissions(
                role.name,
                include_inherited=True,
            )
            permissions.update(role_permissions)
        
        return permissions
    
    def check_permission(
        self,
        user_id: str,
        permission: str,
        customer_id: str = None,
        context: Dict[str, Any] = None,
    ) -> AuthorizationResult:
        """Check if user has a specific permission."""
        context = context or {}
        
        # Check cache
        cache_key = f"{user_id}:{permission}:{customer_id}"
        cached = self._authorization_cache.get(cache_key)
        if cached:
            return cached
        
        # Get user permissions
        user_permissions = self.get_user_permissions(user_id, customer_id)
        
        # Check permission match
        has_permission = PermissionMatcher.matches(user_permissions, permission)
        
        if not has_permission:
            result = AuthorizationResult(
                allowed=False,
                reason="Permission not granted",
                context=context,
            )
        else:
            # Check policies
            resource = permission.split(":")[0]
            action = permission.split(":")[1] if ":" in permission else "*"
            
            context["user_id"] = user_id
            context["customer_id"] = customer_id
            
            policy_allowed, matched_policy = self.policy_engine.evaluate(
                resource=permission,
                action=action,
                principal=user_id,
                context=context,
            )
            
            if not policy_allowed:
                result = AuthorizationResult(
                    allowed=False,
                    reason=f"Denied by policy: {matched_policy.name}" if matched_policy else "Policy denied",
                    matched_permission=permission,
                    matched_policy=matched_policy.id if matched_policy else None,
                    context=context,
                )
            else:
                result = AuthorizationResult(
                    allowed=True,
                    reason="Permission granted",
                    matched_permission=permission,
                    context=context,
                )
        
        # Cache result
        self._authorization_cache[cache_key] = result
        
        return result
    
    def authorize(
        self,
        user_id: str,
        resource: str,
        action: str,
        customer_id: str = None,
        resource_data: Dict = None,
    ) -> AuthorizationResult:
        """Authorize an action on a resource."""
        permission = f"{resource}:{action}"
        
        context = {
            "resource": resource_data or {},
            "ip_address": resource_data.get("_ip_address") if resource_data else None,
        }
        
        return self.check_permission(
            user_id=user_id,
            permission=permission,
            customer_id=customer_id,
            context=context,
        )
    
    def has_role(self, user_id: str, role_name: str, customer_id: str = None) -> bool:
        """Check if user has a specific role."""
        roles = self.get_user_roles(user_id, customer_id)
        return any(r.name == role_name for r in roles)
    
    def is_admin(self, user_id: str) -> bool:
        """Check if user is an admin."""
        return self.has_role(user_id, "admin") or self.has_role(user_id, "super_admin")
    
    def _clear_user_cache(self, user_id: str):
        """Clear authorization cache for a user."""
        keys_to_remove = [k for k in self._authorization_cache if k.startswith(f"{user_id}:")]
        for key in keys_to_remove:
            del self._authorization_cache[key]


# Global RBAC engine
rbac_engine = RBACEngine()


def get_rbac_engine() -> RBACEngine:
    """Get RBAC engine instance."""
    return rbac_engine
```

---

## File 5: RBAC Module Init
**Path:** `backend/app/security/rbac/__init__.py`

```python
"""
RBAC Module
Role-Based Access Control
"""

from app.security.rbac.roles import (
    RoleManager,
    Role,
    SystemRole,
    role_manager,
    get_role_manager,
)

from app.security.rbac.permissions import (
    Permission,
    Action,
    Resource,
    PermissionRegistry,
    PermissionMatcher,
    permission_registry,
    get_permission_registry,
)

from app.security.rbac.policies import (
    Policy,
    PolicyCondition,
    PolicyConditionType,
    PolicyEffect,
    PolicyEngine,
    policy_engine,
    get_policy_engine,
)

from app.security.rbac.engine import (
    RBACEngine,
    AuthorizationResult,
    UserRoleAssignment,
    rbac_engine,
    get_rbac_engine,
)


__all__ = [
    # Roles
    'RoleManager',
    'Role',
    'SystemRole',
    'role_manager',
    'get_role_manager',
    
    # Permissions
    'Permission',
    'Action',
    'Resource',
    'PermissionRegistry',
    'PermissionMatcher',
    'permission_registry',
    'get_permission_registry',
    
    # Policies
    'Policy',
    'PolicyCondition',
    'PolicyConditionType',
    'PolicyEffect',
    'PolicyEngine',
    'policy_engine',
    'get_policy_engine',
    
    # Engine
    'RBACEngine',
    'AuthorizationResult',
    'UserRoleAssignment',
    'rbac_engine',
    'get_rbac_engine',
]
```

---

## Summary Part 3

| File | Description | Lines |
|------|-------------|-------|
| `rbac/roles.py` | Role definitions and management | ~280 |
| `rbac/permissions.py` | Permission definitions | ~240 |
| `rbac/policies.py` | Access policies | ~320 |
| `rbac/engine.py` | Main RBAC engine | ~280 |
| `rbac/__init__.py` | RBAC module exports | ~70 |
| **Total** | | **~1,190 lines** |
