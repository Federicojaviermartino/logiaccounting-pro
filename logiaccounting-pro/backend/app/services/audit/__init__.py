"""
Audit & Compliance Services
Phase 15 - Enterprise Audit Trail, Compliance & Regulatory Framework
"""

from .event_types import (
    EventCategory, Severity, Action, EventType,
    EVENT_REGISTRY, get_event_type,
    # Event type constants
    ENTITY_CREATED, ENTITY_UPDATED, ENTITY_DELETED, ENTITY_VIEWED, ENTITY_EXPORTED,
    AUTH_LOGIN_SUCCESS, AUTH_LOGIN_FAILED, AUTH_LOGOUT, AUTH_PASSWORD_CHANGED,
    AUTH_MFA_ENABLED, AUTH_MFA_DISABLED,
    PERM_GRANTED, PERM_REVOKED, ROLE_ASSIGNED, ROLE_REMOVED,
    INVOICE_CREATED, INVOICE_APPROVED, PAYMENT_PROCESSED,
    SYSTEM_CONFIG_CHANGED, INTEGRATION_CONNECTED, DATA_IMPORTED,
    COMPLIANCE_CHECK_RUN, COMPLIANCE_VIOLATION,
    SECURITY_SUSPICIOUS_ACTIVITY, SECURITY_BRUTE_FORCE
)

from .audit_service import AuditService, audit_service, log_audit, log_create, log_update, log_delete
from .compliance_service import ComplianceService
from .alert_service import AlertService
from .report_service import ReportService

__all__ = [
    # Event types
    'EventCategory', 'Severity', 'Action', 'EventType',
    'EVENT_REGISTRY', 'get_event_type',
    'ENTITY_CREATED', 'ENTITY_UPDATED', 'ENTITY_DELETED', 'ENTITY_VIEWED', 'ENTITY_EXPORTED',
    'AUTH_LOGIN_SUCCESS', 'AUTH_LOGIN_FAILED', 'AUTH_LOGOUT', 'AUTH_PASSWORD_CHANGED',
    'AUTH_MFA_ENABLED', 'AUTH_MFA_DISABLED',
    'PERM_GRANTED', 'PERM_REVOKED', 'ROLE_ASSIGNED', 'ROLE_REMOVED',
    'INVOICE_CREATED', 'INVOICE_APPROVED', 'PAYMENT_PROCESSED',
    'SYSTEM_CONFIG_CHANGED', 'INTEGRATION_CONNECTED', 'DATA_IMPORTED',
    'COMPLIANCE_CHECK_RUN', 'COMPLIANCE_VIOLATION',
    'SECURITY_SUSPICIOUS_ACTIVITY', 'SECURITY_BRUTE_FORCE',
    # Services
    'AuditService', 'audit_service', 'log_audit', 'log_create', 'log_update', 'log_delete',
    'ComplianceService',
    'AlertService',
    'ReportService',
]
