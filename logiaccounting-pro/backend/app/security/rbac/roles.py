"""
Role definitions and management for LogiAccounting Pro RBAC system.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Set, Dict, List, Any
from datetime import datetime


class SystemRole(str, Enum):
    """System-defined roles with hierarchical permissions."""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    ACCOUNTANT = "accountant"
    PROJECT_MANAGER = "project_manager"
    CLIENT = "client"
    SUPPLIER = "supplier"
    READ_ONLY = "read_only"
    GUEST = "guest"


ROLE_HIERARCHY: Dict[SystemRole, int] = {
    SystemRole.SUPER_ADMIN: 100,
    SystemRole.ADMIN: 90,
    SystemRole.MANAGER: 70,
    SystemRole.ACCOUNTANT: 60,
    SystemRole.PROJECT_MANAGER: 60,
    SystemRole.CLIENT: 30,
    SystemRole.SUPPLIER: 30,
    SystemRole.READ_ONLY: 10,
    SystemRole.GUEST: 0,
}


@dataclass
class RoleDefinition:
    """Complete role definition with metadata and permissions."""

    name: str
    display_name: str
    description: str
    hierarchy_level: int
    is_system_role: bool = True
    is_assignable: bool = True
    permissions: Set[str] = field(default_factory=set)
    inherits_from: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


DEFAULT_ROLE_DEFINITIONS: Dict[str, RoleDefinition] = {
    SystemRole.SUPER_ADMIN.value: RoleDefinition(
        name=SystemRole.SUPER_ADMIN.value,
        display_name="Super Administrator",
        description="Full system access with tenant management capabilities",
        hierarchy_level=ROLE_HIERARCHY[SystemRole.SUPER_ADMIN],
        is_assignable=False,
        permissions={
            "system:*",
            "tenant:*",
            "user:*",
            "role:*",
            "audit:*",
            "security:*",
        },
    ),
    SystemRole.ADMIN.value: RoleDefinition(
        name=SystemRole.ADMIN.value,
        display_name="Administrator",
        description="Organization-level administrative access",
        hierarchy_level=ROLE_HIERARCHY[SystemRole.ADMIN],
        inherits_from=None,
        permissions={
            "user:read", "user:create", "user:update", "user:delete",
            "role:read", "role:assign",
            "settings:*",
            "audit:read",
            "invoice:*",
            "material:*",
            "project:*",
            "payment:*",
            "report:*",
            "client:*",
            "supplier:*",
        },
    ),
    SystemRole.MANAGER.value: RoleDefinition(
        name=SystemRole.MANAGER.value,
        display_name="Manager",
        description="Department or team management capabilities",
        hierarchy_level=ROLE_HIERARCHY[SystemRole.MANAGER],
        inherits_from=None,
        permissions={
            "user:read",
            "invoice:*",
            "material:*",
            "project:*",
            "payment:read", "payment:create", "payment:update",
            "report:read", "report:create",
            "client:read", "client:update",
            "supplier:read", "supplier:update",
        },
    ),
    SystemRole.ACCOUNTANT.value: RoleDefinition(
        name=SystemRole.ACCOUNTANT.value,
        display_name="Accountant",
        description="Financial and accounting operations access",
        hierarchy_level=ROLE_HIERARCHY[SystemRole.ACCOUNTANT],
        permissions={
            "invoice:*",
            "payment:*",
            "transaction:*",
            "report:read", "report:create",
            "client:read",
            "supplier:read",
            "material:read",
        },
    ),
    SystemRole.PROJECT_MANAGER.value: RoleDefinition(
        name=SystemRole.PROJECT_MANAGER.value,
        display_name="Project Manager",
        description="Project planning and execution management",
        hierarchy_level=ROLE_HIERARCHY[SystemRole.PROJECT_MANAGER],
        permissions={
            "project:*",
            "material:read", "material:update",
            "invoice:read", "invoice:create",
            "client:read",
            "supplier:read",
            "report:read",
        },
    ),
    SystemRole.CLIENT.value: RoleDefinition(
        name=SystemRole.CLIENT.value,
        display_name="Client",
        description="External client with limited portal access",
        hierarchy_level=ROLE_HIERARCHY[SystemRole.CLIENT],
        permissions={
            "invoice:read:own",
            "payment:read:own",
            "project:read:own",
            "document:read:own",
        },
    ),
    SystemRole.SUPPLIER.value: RoleDefinition(
        name=SystemRole.SUPPLIER.value,
        display_name="Supplier",
        description="External supplier with limited portal access",
        hierarchy_level=ROLE_HIERARCHY[SystemRole.SUPPLIER],
        permissions={
            "invoice:read:own",
            "payment:read:own",
            "material:read:assigned",
            "order:read:own",
        },
    ),
    SystemRole.READ_ONLY.value: RoleDefinition(
        name=SystemRole.READ_ONLY.value,
        display_name="Read Only",
        description="View-only access to assigned resources",
        hierarchy_level=ROLE_HIERARCHY[SystemRole.READ_ONLY],
        permissions={
            "invoice:read",
            "material:read",
            "project:read",
            "payment:read",
            "report:read",
        },
    ),
    SystemRole.GUEST.value: RoleDefinition(
        name=SystemRole.GUEST.value,
        display_name="Guest",
        description="Minimal access for unauthenticated or temporary users",
        hierarchy_level=ROLE_HIERARCHY[SystemRole.GUEST],
        permissions={
            "public:read",
        },
    ),
}


class RoleManager:
    """Manages role definitions, assignments, and hierarchy operations."""

    def __init__(self):
        self._roles: Dict[str, RoleDefinition] = {}
        self._custom_roles: Dict[str, RoleDefinition] = {}
        self._role_assignments: Dict[str, Set[str]] = {}
        self._load_default_roles()

    def _load_default_roles(self) -> None:
        """Load system-defined roles."""
        for role_name, role_def in DEFAULT_ROLE_DEFINITIONS.items():
            self._roles[role_name] = role_def

    def get_role(self, role_name: str) -> Optional[RoleDefinition]:
        """Get role definition by name."""
        if role_name in self._roles:
            return self._roles[role_name]
        return self._custom_roles.get(role_name)

    def get_all_roles(self, include_custom: bool = True) -> List[RoleDefinition]:
        """Get all role definitions."""
        roles = list(self._roles.values())
        if include_custom:
            roles.extend(self._custom_roles.values())
        return sorted(roles, key=lambda r: r.hierarchy_level, reverse=True)

    def get_assignable_roles(self, assigner_role: str) -> List[RoleDefinition]:
        """Get roles that can be assigned by the given role."""
        assigner = self.get_role(assigner_role)
        if not assigner:
            return []

        all_roles = self.get_all_roles()
        return [
            role for role in all_roles
            if role.is_assignable and role.hierarchy_level < assigner.hierarchy_level
        ]

    def create_custom_role(
        self,
        name: str,
        display_name: str,
        description: str,
        permissions: Set[str],
        base_role: Optional[str] = None,
        hierarchy_level: Optional[int] = None,
    ) -> RoleDefinition:
        """Create a new custom role."""
        if name in self._roles or name in self._custom_roles:
            raise ValueError(f"Role '{name}' already exists")

        if base_role:
            base = self.get_role(base_role)
            if base:
                permissions = permissions.union(base.permissions)
                if hierarchy_level is None:
                    hierarchy_level = base.hierarchy_level - 1

        if hierarchy_level is None:
            hierarchy_level = 50

        role = RoleDefinition(
            name=name,
            display_name=display_name,
            description=description,
            hierarchy_level=hierarchy_level,
            is_system_role=False,
            permissions=permissions,
            inherits_from=base_role,
        )

        self._custom_roles[name] = role
        return role

    def update_custom_role(
        self,
        name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        permissions: Optional[Set[str]] = None,
    ) -> Optional[RoleDefinition]:
        """Update a custom role."""
        if name not in self._custom_roles:
            return None

        role = self._custom_roles[name]
        if display_name:
            role.display_name = display_name
        if description:
            role.description = description
        if permissions is not None:
            role.permissions = permissions
        role.updated_at = datetime.utcnow()

        return role

    def delete_custom_role(self, name: str) -> bool:
        """Delete a custom role."""
        if name in self._custom_roles:
            del self._custom_roles[name]
            return True
        return False

    def get_role_permissions(self, role_name: str, resolve_inheritance: bool = True) -> Set[str]:
        """Get all permissions for a role, optionally resolving inheritance."""
        role = self.get_role(role_name)
        if not role:
            return set()

        permissions = role.permissions.copy()

        if resolve_inheritance and role.inherits_from:
            parent_permissions = self.get_role_permissions(role.inherits_from, True)
            permissions = permissions.union(parent_permissions)

        return permissions

    def is_role_superior(self, role_a: str, role_b: str) -> bool:
        """Check if role_a is superior to role_b in hierarchy."""
        role_a_def = self.get_role(role_a)
        role_b_def = self.get_role(role_b)

        if not role_a_def or not role_b_def:
            return False

        return role_a_def.hierarchy_level > role_b_def.hierarchy_level

    def can_assign_role(self, assigner_role: str, target_role: str) -> bool:
        """Check if assigner_role can assign target_role."""
        target = self.get_role(target_role)
        if not target or not target.is_assignable:
            return False

        return self.is_role_superior(assigner_role, target_role)

    def assign_role_to_user(
        self,
        user_id: str,
        role_name: str,
        organization_id: Optional[str] = None,
    ) -> bool:
        """Assign a role to a user."""
        if not self.get_role(role_name):
            return False

        key = f"{user_id}:{organization_id}" if organization_id else user_id
        if key not in self._role_assignments:
            self._role_assignments[key] = set()

        self._role_assignments[key].add(role_name)
        return True

    def revoke_role_from_user(
        self,
        user_id: str,
        role_name: str,
        organization_id: Optional[str] = None,
    ) -> bool:
        """Revoke a role from a user."""
        key = f"{user_id}:{organization_id}" if organization_id else user_id
        if key in self._role_assignments:
            self._role_assignments[key].discard(role_name)
            return True
        return False

    def get_user_roles(
        self,
        user_id: str,
        organization_id: Optional[str] = None,
    ) -> Set[str]:
        """Get all roles assigned to a user."""
        key = f"{user_id}:{organization_id}" if organization_id else user_id
        return self._role_assignments.get(key, set()).copy()

    def get_effective_permissions(
        self,
        user_id: str,
        organization_id: Optional[str] = None,
    ) -> Set[str]:
        """Get all effective permissions for a user based on their roles."""
        roles = self.get_user_roles(user_id, organization_id)
        permissions: Set[str] = set()

        for role_name in roles:
            role_permissions = self.get_role_permissions(role_name)
            permissions = permissions.union(role_permissions)

        return permissions


role_manager = RoleManager()
