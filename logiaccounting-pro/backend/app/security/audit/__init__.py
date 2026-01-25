"""
Audit module for LogiAccounting Pro.
"""

from .events import (
    AuditEventType,
    AuditOutcome,
    AuditSeverity,
    AuditCategory,
    AuditActor,
    AuditTarget,
    AuditChanges,
    AuditEvent,
    create_auth_event,
    create_data_event,
    create_security_event,
)

from .logger import (
    AuditLoggerConfig,
    AuditLogger,
    get_audit_logger,
    set_audit_logger,
    log_event,
    log_auth,
)

from .storage import (
    AuditLogModel,
    AuditQueryFilter,
    AuditStorageService,
    get_audit_storage,
    set_audit_storage,
)

__all__ = [
    "AuditEventType",
    "AuditOutcome",
    "AuditSeverity",
    "AuditCategory",
    "AuditActor",
    "AuditTarget",
    "AuditChanges",
    "AuditEvent",
    "create_auth_event",
    "create_data_event",
    "create_security_event",
    "AuditLoggerConfig",
    "AuditLogger",
    "get_audit_logger",
    "set_audit_logger",
    "log_event",
    "log_auth",
    "AuditLogModel",
    "AuditQueryFilter",
    "AuditStorageService",
    "get_audit_storage",
    "set_audit_storage",
]
