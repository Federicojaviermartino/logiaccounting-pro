"""
Permission definitions and registry for LogiAccounting Pro RBAC system.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Set, Dict, List, Any, Callable
from datetime import datetime
import re


class Action(str, Enum):
    """Standard CRUD and additional actions."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    EXPORT = "export"
    IMPORT = "import"
    APPROVE = "approve"
    REJECT = "reject"
    SUBMIT = "submit"
    CANCEL = "cancel"
    ARCHIVE = "archive"
    RESTORE = "restore"
    ASSIGN = "assign"
    UNASSIGN = "unassign"
    EXECUTE = "execute"
    MANAGE = "manage"
    CONFIGURE = "configure"
    ADMIN = "admin"
    ALL = "*"


class Resource(str, Enum):
    """System resources that can be protected."""

    SYSTEM = "system"
    TENANT = "tenant"
    ORGANIZATION = "organization"
    USER = "user"
    ROLE = "role"
    PERMISSION = "permission"
    SETTINGS = "settings"
    AUDIT = "audit"
    SECURITY = "security"
    INVOICE = "invoice"
    PAYMENT = "payment"
    TRANSACTION = "transaction"
    MATERIAL = "material"
    INVENTORY = "inventory"
    PROJECT = "project"
    CLIENT = "client"
    SUPPLIER = "supplier"
    REPORT = "report"
    DOCUMENT = "document"
    WORKFLOW = "workflow"
    NOTIFICATION = "notification"
    INTEGRATION = "integration"
    API_KEY = "api_key"
    WEBHOOK = "webhook"
    DASHBOARD = "dashboard"
    ANALYTICS = "analytics"
    PUBLIC = "public"


class Scope(str, Enum):
    """Permission scope modifiers."""

    ALL = "all"
    OWN = "own"
    TEAM = "team"
    DEPARTMENT = "department"
    ORGANIZATION = "organization"
    ASSIGNED = "assigned"


@dataclass
class Permission:
    """Complete permission definition."""

    resource: str
    action: str
    scope: Optional[str] = None
    conditions: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    is_sensitive: bool = False
    requires_mfa: bool = False
    audit_level: str = "standard"

    @property
    def name(self) -> str:
        """Generate permission name in format resource:action[:scope]."""
        parts = [self.resource, self.action]
        if self.scope:
            parts.append(self.scope)
        return ":".join(parts)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, Permission):
            return self.name == other.name
        if isinstance(other, str):
            return self.name == other
        return False


@dataclass
class PermissionGroup:
    """Group of related permissions for easier management."""

    name: str
    display_name: str
    description: str
    permissions: Set[str]
    is_system_group: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class PermissionRegistry:
    """Central registry for all system permissions."""

    def __init__(self):
        self._permissions: Dict[str, Permission] = {}
        self._groups: Dict[str, PermissionGroup] = {}
        self._validators: Dict[str, Callable] = {}
        self._initialize_default_permissions()
        self._initialize_default_groups()

    def _initialize_default_permissions(self) -> None:
        """Initialize all default system permissions."""
        standard_resources = [
            (Resource.USER, ["create", "read", "update", "delete", "list", "assign"]),
            (Resource.ROLE, ["create", "read", "update", "delete", "list", "assign"]),
            (Resource.INVOICE, ["create", "read", "update", "delete", "list", "export", "approve", "submit"]),
            (Resource.PAYMENT, ["create", "read", "update", "delete", "list", "approve", "execute"]),
            (Resource.MATERIAL, ["create", "read", "update", "delete", "list", "export", "import"]),
            (Resource.PROJECT, ["create", "read", "update", "delete", "list", "archive", "assign"]),
            (Resource.CLIENT, ["create", "read", "update", "delete", "list", "export"]),
            (Resource.SUPPLIER, ["create", "read", "update", "delete", "list", "export"]),
            (Resource.REPORT, ["create", "read", "delete", "list", "export"]),
            (Resource.DOCUMENT, ["create", "read", "update", "delete", "list", "export"]),
            (Resource.WORKFLOW, ["create", "read", "update", "delete", "list", "execute"]),
            (Resource.NOTIFICATION, ["create", "read", "update", "delete", "list"]),
            (Resource.INTEGRATION, ["create", "read", "update", "delete", "list", "configure"]),
            (Resource.DASHBOARD, ["read", "update", "configure"]),
            (Resource.ANALYTICS, ["read", "export"]),
        ]

        for resource, actions in standard_resources:
            for action in actions:
                self.register_permission(Permission(
                    resource=resource.value,
                    action=action,
                    description=f"{action.capitalize()} {resource.value}",
                ))
                for scope in [Scope.OWN, Scope.TEAM, Scope.ASSIGNED]:
                    self.register_permission(Permission(
                        resource=resource.value,
                        action=action,
                        scope=scope.value,
                        description=f"{action.capitalize()} {scope.value} {resource.value}",
                    ))

        sensitive_permissions = [
            Permission(
                resource=Resource.SYSTEM.value,
                action=Action.ALL.value,
                description="Full system access",
                is_sensitive=True,
                requires_mfa=True,
                audit_level="critical",
            ),
            Permission(
                resource=Resource.TENANT.value,
                action=Action.ALL.value,
                description="Full tenant management",
                is_sensitive=True,
                requires_mfa=True,
                audit_level="critical",
            ),
            Permission(
                resource=Resource.SECURITY.value,
                action=Action.ALL.value,
                description="Security settings management",
                is_sensitive=True,
                requires_mfa=True,
                audit_level="critical",
            ),
            Permission(
                resource=Resource.AUDIT.value,
                action=Action.READ.value,
                description="View audit logs",
                is_sensitive=True,
                audit_level="high",
            ),
            Permission(
                resource=Resource.AUDIT.value,
                action=Action.ALL.value,
                description="Full audit management",
                is_sensitive=True,
                requires_mfa=True,
                audit_level="critical",
            ),
            Permission(
                resource=Resource.SETTINGS.value,
                action=Action.ALL.value,
                description="Full settings management",
                is_sensitive=True,
                audit_level="high",
            ),
            Permission(
                resource=Resource.API_KEY.value,
                action=Action.CREATE.value,
                description="Create API keys",
                is_sensitive=True,
                requires_mfa=True,
                audit_level="high",
            ),
            Permission(
                resource=Resource.USER.value,
                action=Action.DELETE.value,
                description="Delete users",
                is_sensitive=True,
                audit_level="high",
            ),
        ]

        for perm in sensitive_permissions:
            self.register_permission(perm)

    def _initialize_default_groups(self) -> None:
        """Initialize default permission groups."""
        groups = [
            PermissionGroup(
                name="financial_full",
                display_name="Financial Full Access",
                description="Complete access to financial operations",
                permissions={
                    "invoice:*", "payment:*", "transaction:*",
                    "report:read", "report:create", "report:export",
                },
            ),
            PermissionGroup(
                name="financial_view",
                display_name="Financial View Only",
                description="View-only access to financial data",
                permissions={
                    "invoice:read", "invoice:list",
                    "payment:read", "payment:list",
                    "transaction:read", "transaction:list",
                    "report:read",
                },
            ),
            PermissionGroup(
                name="inventory_full",
                display_name="Inventory Full Access",
                description="Complete access to inventory management",
                permissions={
                    "material:*", "inventory:*",
                },
            ),
            PermissionGroup(
                name="project_management",
                display_name="Project Management",
                description="Project planning and execution",
                permissions={
                    "project:*",
                    "material:read", "material:update",
                    "client:read",
                },
            ),
            PermissionGroup(
                name="user_management",
                display_name="User Management",
                description="User and role administration",
                permissions={
                    "user:read", "user:create", "user:update", "user:list",
                    "role:read", "role:list", "role:assign",
                },
            ),
            PermissionGroup(
                name="system_admin",
                display_name="System Administration",
                description="System-level administrative access",
                permissions={
                    "system:*", "settings:*", "security:*",
                    "audit:read", "integration:*",
                },
            ),
        ]

        for group in groups:
            self._groups[group.name] = group

    def register_permission(self, permission: Permission) -> None:
        """Register a new permission."""
        self._permissions[permission.name] = permission

    def get_permission(self, name: str) -> Optional[Permission]:
        """Get a permission by name."""
        return self._permissions.get(name)

    def get_all_permissions(self) -> List[Permission]:
        """Get all registered permissions."""
        return list(self._permissions.values())

    def get_permissions_for_resource(self, resource: str) -> List[Permission]:
        """Get all permissions for a specific resource."""
        return [
            p for p in self._permissions.values()
            if p.resource == resource
        ]

    def get_group(self, name: str) -> Optional[PermissionGroup]:
        """Get a permission group by name."""
        return self._groups.get(name)

    def get_all_groups(self) -> List[PermissionGroup]:
        """Get all permission groups."""
        return list(self._groups.values())

    def create_group(
        self,
        name: str,
        display_name: str,
        description: str,
        permissions: Set[str],
    ) -> PermissionGroup:
        """Create a new permission group."""
        if name in self._groups:
            raise ValueError(f"Group '{name}' already exists")

        group = PermissionGroup(
            name=name,
            display_name=display_name,
            description=description,
            permissions=permissions,
            is_system_group=False,
        )
        self._groups[name] = group
        return group

    def expand_group(self, group_name: str) -> Set[str]:
        """Expand a permission group to its individual permissions."""
        group = self._groups.get(group_name)
        if not group:
            return set()
        return group.permissions.copy()

    def matches_permission(
        self,
        required: str,
        granted: str,
    ) -> bool:
        """Check if a granted permission matches a required permission."""
        if granted == required:
            return True

        if granted.endswith(":*"):
            prefix = granted[:-1]
            if required.startswith(prefix):
                return True

        req_parts = required.split(":")
        grant_parts = granted.split(":")

        if len(grant_parts) > len(req_parts):
            return False

        for i, grant_part in enumerate(grant_parts):
            if grant_part == "*":
                continue
            if i >= len(req_parts) or grant_part != req_parts[i]:
                return False

        return True

    def has_permission(
        self,
        required: str,
        granted_permissions: Set[str],
    ) -> bool:
        """Check if required permission is satisfied by granted permissions."""
        for granted in granted_permissions:
            if self.matches_permission(required, granted):
                return True
        return False

    def register_validator(
        self,
        permission_pattern: str,
        validator: Callable[[Dict[str, Any]], bool],
    ) -> None:
        """Register a custom validator for a permission pattern."""
        self._validators[permission_pattern] = validator

    def validate_permission(
        self,
        permission: str,
        context: Dict[str, Any],
    ) -> bool:
        """Run custom validators for a permission."""
        for pattern, validator in self._validators.items():
            if re.match(pattern, permission):
                if not validator(context):
                    return False
        return True

    def get_sensitive_permissions(self) -> List[Permission]:
        """Get all sensitive permissions."""
        return [p for p in self._permissions.values() if p.is_sensitive]

    def get_mfa_required_permissions(self) -> List[Permission]:
        """Get permissions that require MFA."""
        return [p for p in self._permissions.values() if p.requires_mfa]

    def format_permission_name(
        self,
        resource: str,
        action: str,
        scope: Optional[str] = None,
    ) -> str:
        """Format a permission name from components."""
        parts = [resource, action]
        if scope:
            parts.append(scope)
        return ":".join(parts)

    def parse_permission_name(self, name: str) -> Dict[str, Optional[str]]:
        """Parse a permission name into components."""
        parts = name.split(":")
        return {
            "resource": parts[0] if len(parts) > 0 else None,
            "action": parts[1] if len(parts) > 1 else None,
            "scope": parts[2] if len(parts) > 2 else None,
        }


permission_registry = PermissionRegistry()
