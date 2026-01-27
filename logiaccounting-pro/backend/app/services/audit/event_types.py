"""
Audit Event Types
Standardized event type definitions for audit logging
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional


class EventCategory(str, Enum):
    """Event categories"""
    DATA_CHANGE = 'data_change'
    AUTHENTICATION = 'authentication'
    AUTHORIZATION = 'authorization'
    SYSTEM = 'system'
    COMPLIANCE = 'compliance'
    SECURITY = 'security'


class Severity(str, Enum):
    """Event severity levels"""
    DEBUG = 'debug'
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'


class Action(str, Enum):
    """CRUD + additional actions"""
    CREATE = 'create'
    READ = 'read'
    UPDATE = 'update'
    DELETE = 'delete'
    EXECUTE = 'execute'
    EXPORT = 'export'
    IMPORT = 'import'
    APPROVE = 'approve'
    REJECT = 'reject'
    ARCHIVE = 'archive'
    RESTORE = 'restore'


@dataclass
class EventType:
    """Event type definition"""
    name: str
    category: EventCategory
    default_severity: Severity
    description: str
    compliance_tags: List[str] = field(default_factory=list)

    def __str__(self):
        return self.name


# ==================== Entity Events ====================

ENTITY_CREATED = EventType(
    name='entity.created',
    category=EventCategory.DATA_CHANGE,
    default_severity=Severity.INFO,
    description='A new entity was created',
    compliance_tags=['sox', 'soc2']
)

ENTITY_UPDATED = EventType(
    name='entity.updated',
    category=EventCategory.DATA_CHANGE,
    default_severity=Severity.INFO,
    description='An entity was modified',
    compliance_tags=['sox', 'soc2']
)

ENTITY_DELETED = EventType(
    name='entity.deleted',
    category=EventCategory.DATA_CHANGE,
    default_severity=Severity.WARNING,
    description='An entity was deleted',
    compliance_tags=['sox', 'soc2', 'gdpr']
)

ENTITY_VIEWED = EventType(
    name='entity.viewed',
    category=EventCategory.DATA_CHANGE,
    default_severity=Severity.DEBUG,
    description='An entity was viewed',
    compliance_tags=['gdpr', 'hipaa']
)

ENTITY_EXPORTED = EventType(
    name='entity.exported',
    category=EventCategory.DATA_CHANGE,
    default_severity=Severity.WARNING,
    description='Entity data was exported',
    compliance_tags=['gdpr', 'sox', 'pci']
)


# ==================== Authentication Events ====================

AUTH_LOGIN_SUCCESS = EventType(
    name='auth.login_success',
    category=EventCategory.AUTHENTICATION,
    default_severity=Severity.INFO,
    description='User successfully logged in',
    compliance_tags=['sox', 'soc2']
)

AUTH_LOGIN_FAILED = EventType(
    name='auth.login_failed',
    category=EventCategory.AUTHENTICATION,
    default_severity=Severity.WARNING,
    description='Login attempt failed',
    compliance_tags=['sox', 'soc2']
)

AUTH_LOGOUT = EventType(
    name='auth.logout',
    category=EventCategory.AUTHENTICATION,
    default_severity=Severity.INFO,
    description='User logged out',
    compliance_tags=['soc2']
)

AUTH_PASSWORD_CHANGED = EventType(
    name='auth.password_changed',
    category=EventCategory.AUTHENTICATION,
    default_severity=Severity.INFO,
    description='User password was changed',
    compliance_tags=['sox', 'soc2']
)

AUTH_MFA_ENABLED = EventType(
    name='auth.mfa_enabled',
    category=EventCategory.AUTHENTICATION,
    default_severity=Severity.INFO,
    description='MFA was enabled for user',
    compliance_tags=['sox', 'soc2', 'pci']
)

AUTH_MFA_DISABLED = EventType(
    name='auth.mfa_disabled',
    category=EventCategory.AUTHENTICATION,
    default_severity=Severity.WARNING,
    description='MFA was disabled for user',
    compliance_tags=['sox', 'soc2', 'pci']
)


# ==================== Authorization Events ====================

PERM_GRANTED = EventType(
    name='permission.granted',
    category=EventCategory.AUTHORIZATION,
    default_severity=Severity.INFO,
    description='Permission was granted to user',
    compliance_tags=['sox', 'soc2']
)

PERM_REVOKED = EventType(
    name='permission.revoked',
    category=EventCategory.AUTHORIZATION,
    default_severity=Severity.INFO,
    description='Permission was revoked from user',
    compliance_tags=['sox', 'soc2']
)

ROLE_ASSIGNED = EventType(
    name='role.assigned',
    category=EventCategory.AUTHORIZATION,
    default_severity=Severity.INFO,
    description='Role was assigned to user',
    compliance_tags=['sox', 'soc2']
)

ROLE_REMOVED = EventType(
    name='role.removed',
    category=EventCategory.AUTHORIZATION,
    default_severity=Severity.INFO,
    description='Role was removed from user',
    compliance_tags=['sox', 'soc2']
)


# ==================== Financial Events ====================

INVOICE_CREATED = EventType(
    name='invoice.created',
    category=EventCategory.DATA_CHANGE,
    default_severity=Severity.INFO,
    description='Invoice was created',
    compliance_tags=['sox']
)

INVOICE_APPROVED = EventType(
    name='invoice.approved',
    category=EventCategory.DATA_CHANGE,
    default_severity=Severity.INFO,
    description='Invoice was approved',
    compliance_tags=['sox']
)

PAYMENT_PROCESSED = EventType(
    name='payment.processed',
    category=EventCategory.DATA_CHANGE,
    default_severity=Severity.INFO,
    description='Payment was processed',
    compliance_tags=['sox', 'pci']
)


# ==================== System Events ====================

SYSTEM_CONFIG_CHANGED = EventType(
    name='system.config_changed',
    category=EventCategory.SYSTEM,
    default_severity=Severity.WARNING,
    description='System configuration was changed',
    compliance_tags=['sox', 'soc2']
)

INTEGRATION_CONNECTED = EventType(
    name='integration.connected',
    category=EventCategory.SYSTEM,
    default_severity=Severity.INFO,
    description='External integration was connected',
    compliance_tags=['soc2']
)

DATA_IMPORTED = EventType(
    name='data.imported',
    category=EventCategory.DATA_CHANGE,
    default_severity=Severity.WARNING,
    description='Data was imported into the system',
    compliance_tags=['sox', 'soc2']
)


# ==================== Compliance Events ====================

COMPLIANCE_CHECK_RUN = EventType(
    name='compliance.check_run',
    category=EventCategory.COMPLIANCE,
    default_severity=Severity.INFO,
    description='Compliance check was executed',
    compliance_tags=['sox', 'soc2']
)

COMPLIANCE_VIOLATION = EventType(
    name='compliance.violation',
    category=EventCategory.COMPLIANCE,
    default_severity=Severity.ERROR,
    description='Compliance violation detected',
    compliance_tags=['sox', 'soc2', 'gdpr', 'pci', 'hipaa']
)


# ==================== Security Events ====================

SECURITY_SUSPICIOUS_ACTIVITY = EventType(
    name='security.suspicious_activity',
    category=EventCategory.SECURITY,
    default_severity=Severity.WARNING,
    description='Suspicious activity detected',
    compliance_tags=['sox', 'soc2']
)

SECURITY_BRUTE_FORCE = EventType(
    name='security.brute_force',
    category=EventCategory.SECURITY,
    default_severity=Severity.ERROR,
    description='Possible brute force attack detected',
    compliance_tags=['sox', 'soc2']
)


# ==================== Event Registry ====================

EVENT_REGISTRY = {
    # Entity events
    'entity.created': ENTITY_CREATED,
    'entity.updated': ENTITY_UPDATED,
    'entity.deleted': ENTITY_DELETED,
    'entity.viewed': ENTITY_VIEWED,
    'entity.exported': ENTITY_EXPORTED,

    # Auth events
    'auth.login_success': AUTH_LOGIN_SUCCESS,
    'auth.login_failed': AUTH_LOGIN_FAILED,
    'auth.logout': AUTH_LOGOUT,
    'auth.password_changed': AUTH_PASSWORD_CHANGED,
    'auth.mfa_enabled': AUTH_MFA_ENABLED,
    'auth.mfa_disabled': AUTH_MFA_DISABLED,

    # Permission events
    'permission.granted': PERM_GRANTED,
    'permission.revoked': PERM_REVOKED,
    'role.assigned': ROLE_ASSIGNED,
    'role.removed': ROLE_REMOVED,

    # Financial events
    'invoice.created': INVOICE_CREATED,
    'invoice.approved': INVOICE_APPROVED,
    'payment.processed': PAYMENT_PROCESSED,

    # System events
    'system.config_changed': SYSTEM_CONFIG_CHANGED,
    'integration.connected': INTEGRATION_CONNECTED,
    'data.imported': DATA_IMPORTED,

    # Compliance events
    'compliance.check_run': COMPLIANCE_CHECK_RUN,
    'compliance.violation': COMPLIANCE_VIOLATION,

    # Security events
    'security.suspicious_activity': SECURITY_SUSPICIOUS_ACTIVITY,
    'security.brute_force': SECURITY_BRUTE_FORCE,
}


def get_event_type(name: str) -> Optional[EventType]:
    """Get event type by name"""
    return EVENT_REGISTRY.get(name)


def get_all_event_types() -> List[EventType]:
    """Get all registered event types"""
    return list(EVENT_REGISTRY.values())


def get_event_types_by_category(category: EventCategory) -> List[EventType]:
    """Get event types filtered by category"""
    return [et for et in EVENT_REGISTRY.values() if et.category == category]


def get_event_types_by_compliance(tag: str) -> List[EventType]:
    """Get event types filtered by compliance tag"""
    return [et for et in EVENT_REGISTRY.values() if tag in et.compliance_tags]
