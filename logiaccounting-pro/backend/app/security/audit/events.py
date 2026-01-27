"""
Audit event definitions for LogiAccounting Pro.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime
from uuid import uuid4


class AuditEventType(str, Enum):
    """Types of auditable events."""

    AUTH_LOGIN_SUCCESS = "auth.login_success"
    AUTH_LOGIN_FAILED = "auth.login_failed"
    AUTH_LOGOUT = "auth.logout"
    AUTH_PASSWORD_CHANGE = "auth.password_change"
    AUTH_PASSWORD_RESET = "auth.password_reset"
    AUTH_MFA_ENABLED = "auth.mfa_enabled"
    AUTH_MFA_DISABLED = "auth.mfa_disabled"
    AUTH_MFA_VERIFIED = "auth.mfa_verified"
    AUTH_MFA_FAILED = "auth.mfa_failed"
    AUTH_TOKEN_ISSUED = "auth.token_issued"
    AUTH_TOKEN_REVOKED = "auth.token_revoked"
    AUTH_SESSION_CREATED = "auth.session_created"
    AUTH_SESSION_TERMINATED = "auth.session_terminated"

    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_ACTIVATED = "user.activated"
    USER_DEACTIVATED = "user.deactivated"
    USER_LOCKED = "user.locked"
    USER_UNLOCKED = "user.unlocked"

    ROLE_ASSIGNED = "role.assigned"
    ROLE_REVOKED = "role.revoked"
    ROLE_CREATED = "role.created"
    ROLE_UPDATED = "role.updated"
    ROLE_DELETED = "role.deleted"

    PERMISSION_GRANTED = "permission.granted"
    PERMISSION_REVOKED = "permission.revoked"

    ENTITY_CREATED = "entity.created"
    ENTITY_READ = "entity.read"
    ENTITY_UPDATED = "entity.updated"
    ENTITY_DELETED = "entity.deleted"
    ENTITY_EXPORTED = "entity.exported"
    ENTITY_IMPORTED = "entity.imported"
    ENTITY_ARCHIVED = "entity.archived"
    ENTITY_RESTORED = "entity.restored"

    DATA_ACCESSED = "data.accessed"
    DATA_EXPORTED = "data.exported"
    DATA_ENCRYPTED = "data.encrypted"
    DATA_DECRYPTED = "data.decrypted"
    DATA_MODIFIED = "data.modified"

    SECURITY_ALERT = "security.alert"
    SECURITY_VIOLATION = "security.violation"
    SECURITY_CONFIG_CHANGE = "security.config_change"
    SECURITY_KEY_ROTATED = "security.key_rotated"

    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_CONFIG_CHANGE = "system.config_change"
    SYSTEM_ERROR = "system.error"
    SYSTEM_MAINTENANCE = "system.maintenance"

    API_REQUEST = "api.request"
    API_ERROR = "api.error"
    API_RATE_LIMITED = "api.rate_limited"

    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    WORKFLOW_STEP_EXECUTED = "workflow.step_executed"

    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_GRANTED = "approval.granted"
    APPROVAL_DENIED = "approval.denied"

    REPORT_GENERATED = "report.generated"
    REPORT_DOWNLOADED = "report.downloaded"


class AuditOutcome(str, Enum):
    """Outcome of an audited operation."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    DENIED = "denied"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class AuditSeverity(str, Enum):
    """Severity level of audit events."""

    DEBUG = "debug"
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    ALERT = "alert"
    EMERGENCY = "emergency"


class AuditCategory(str, Enum):
    """Category of audit events."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SECURITY = "security"
    SYSTEM = "system"
    COMPLIANCE = "compliance"
    USER_MANAGEMENT = "user_management"
    CONFIGURATION = "configuration"
    WORKFLOW = "workflow"


@dataclass
class AuditActor:
    """Information about the actor performing an action."""

    user_id: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    organization_id: Optional[str] = None
    tenant_id: Optional[str] = None
    is_system: bool = False
    impersonator_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "organization_id": self.organization_id,
            "tenant_id": self.tenant_id,
            "is_system": self.is_system,
            "impersonator_id": self.impersonator_id,
        }


@dataclass
class AuditTarget:
    """Information about the target of an action."""

    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    organization_id: Optional[str] = None
    parent_type: Optional[str] = None
    parent_id: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "organization_id": self.organization_id,
            "parent_type": self.parent_type,
            "parent_id": self.parent_id,
            "attributes": self.attributes,
        }


@dataclass
class AuditChanges:
    """Changes made during an operation."""

    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    fields_changed: List[str] = field(default_factory=list)
    diff: Optional[Dict[str, Any]] = None

    def compute_diff(self) -> Dict[str, Any]:
        """Compute differences between before and after states."""
        if not self.before and not self.after:
            return {}

        before = self.before or {}
        after = self.after or {}

        diff = {}
        all_keys = set(before.keys()) | set(after.keys())

        for key in all_keys:
            old_val = before.get(key)
            new_val = after.get(key)
            if old_val != new_val:
                diff[key] = {"old": old_val, "new": new_val}
                if key not in self.fields_changed:
                    self.fields_changed.append(key)

        self.diff = diff
        return diff

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        if self.diff is None and (self.before or self.after):
            self.compute_diff()

        return {
            "before": self.before,
            "after": self.after,
            "fields_changed": self.fields_changed,
            "diff": self.diff,
        }


@dataclass
class AuditEvent:
    """Complete audit event record."""

    event_type: AuditEventType
    outcome: AuditOutcome = AuditOutcome.SUCCESS
    severity: AuditSeverity = AuditSeverity.INFO
    category: AuditCategory = AuditCategory.SYSTEM
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    actor: Optional[AuditActor] = None
    target: Optional[AuditTarget] = None
    changes: Optional[AuditChanges] = None
    action: str = ""
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    duration_ms: Optional[int] = None
    compliance_tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization."""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "outcome": self.outcome.value,
            "severity": self.severity.value,
            "category": self.category.value,
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor.to_dict() if self.actor else None,
            "target": self.target.to_dict() if self.target else None,
            "changes": self.changes.to_dict() if self.changes else None,
            "action": self.action,
            "message": self.message,
            "details": self.details,
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "duration_ms": self.duration_ms,
            "compliance_tags": self.compliance_tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEvent":
        """Create from dictionary."""
        actor = None
        if data.get("actor"):
            actor = AuditActor(**data["actor"])

        target = None
        if data.get("target"):
            target = AuditTarget(**data["target"])

        changes = None
        if data.get("changes"):
            changes = AuditChanges(**data["changes"])

        return cls(
            id=data.get("id", str(uuid4())),
            event_type=AuditEventType(data["event_type"]),
            outcome=AuditOutcome(data.get("outcome", "success")),
            severity=AuditSeverity(data.get("severity", "info")),
            category=AuditCategory(data.get("category", "system")),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.utcnow(),
            actor=actor,
            target=target,
            changes=changes,
            action=data.get("action", ""),
            message=data.get("message", ""),
            details=data.get("details", {}),
            request_id=data.get("request_id"),
            correlation_id=data.get("correlation_id"),
            duration_ms=data.get("duration_ms"),
            compliance_tags=data.get("compliance_tags", []),
            metadata=data.get("metadata", {}),
        )


def create_auth_event(
    event_type: AuditEventType,
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    ip_address: Optional[str] = None,
    outcome: AuditOutcome = AuditOutcome.SUCCESS,
    details: Optional[Dict[str, Any]] = None,
) -> AuditEvent:
    """Create an authentication audit event."""
    actor = AuditActor(
        user_id=user_id,
        email=email,
        ip_address=ip_address,
    )

    severity = AuditSeverity.INFO
    if outcome == AuditOutcome.FAILURE:
        severity = AuditSeverity.WARNING
    if event_type in (AuditEventType.AUTH_PASSWORD_CHANGE, AuditEventType.AUTH_MFA_ENABLED):
        severity = AuditSeverity.NOTICE

    return AuditEvent(
        event_type=event_type,
        outcome=outcome,
        severity=severity,
        category=AuditCategory.AUTHENTICATION,
        actor=actor,
        action=event_type.value.split(".")[-1],
        details=details or {},
        compliance_tags=["soc2", "gdpr"],
    )


def create_data_event(
    event_type: AuditEventType,
    entity_type: str,
    entity_id: str,
    actor: AuditActor,
    changes: Optional[AuditChanges] = None,
    entity_name: Optional[str] = None,
) -> AuditEvent:
    """Create a data modification audit event."""
    target = AuditTarget(
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        organization_id=actor.organization_id,
    )

    return AuditEvent(
        event_type=event_type,
        category=AuditCategory.DATA_MODIFICATION,
        actor=actor,
        target=target,
        changes=changes,
        action=event_type.value.split(".")[-1],
        compliance_tags=["sox", "soc2"],
    )


def create_security_event(
    event_type: AuditEventType,
    message: str,
    severity: AuditSeverity = AuditSeverity.WARNING,
    actor: Optional[AuditActor] = None,
    details: Optional[Dict[str, Any]] = None,
) -> AuditEvent:
    """Create a security audit event."""
    return AuditEvent(
        event_type=event_type,
        severity=severity,
        category=AuditCategory.SECURITY,
        actor=actor,
        message=message,
        details=details or {},
        compliance_tags=["soc2", "pci"],
    )
