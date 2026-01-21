"""
Audit & Compliance Schemas
Pydantic models for audit API validation
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


# Enums

class SeverityEnum(str, Enum):
    DEBUG = 'debug'
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'


class ActionEnum(str, Enum):
    CREATE = 'create'
    READ = 'read'
    UPDATE = 'update'
    DELETE = 'delete'
    EXECUTE = 'execute'
    EXPORT = 'export'
    IMPORT = 'import'


class AlertStatusEnum(str, Enum):
    OPEN = 'open'
    ACKNOWLEDGED = 'acknowledged'
    INVESTIGATING = 'investigating'
    RESOLVED = 'resolved'
    DISMISSED = 'dismissed'


class AlertSeverityEnum(str, Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


class CheckStatusEnum(str, Enum):
    PASSED = 'passed'
    FAILED = 'failed'
    WARNING = 'warning'
    NOT_APPLICABLE = 'not_applicable'
    PENDING = 'pending'
    ERROR = 'error'


# Audit Log Schemas

class AuditLogBase(BaseModel):
    event_type: str
    event_category: str
    severity: SeverityEnum = SeverityEnum.INFO
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    action: str
    changes: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    compliance_tags: Optional[List[str]] = None


class AuditLogResponse(AuditLogBase):
    id: str
    organization_id: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    sequence_number: int
    data_hash: str
    previous_hash: Optional[str] = None
    occurred_at: str
    recorded_at: str
    is_archived: bool = False


class AuditLogListResponse(BaseModel):
    success: bool = True
    logs: List[AuditLogResponse]
    pagination: Dict[str, Any]


class AuditLogDetailResponse(BaseModel):
    success: bool = True
    log: AuditLogResponse


# Change History Schemas

class ChangeHistoryResponse(BaseModel):
    id: str
    audit_log_id: str
    organization_id: str
    entity_type: str
    entity_id: str
    version_number: int
    before_snapshot: Optional[Dict[str, Any]] = None
    after_snapshot: Optional[Dict[str, Any]] = None
    changed_fields: List[str]
    change_summary: Optional[str] = None
    change_reason: Optional[str] = None
    created_at: str


class ChangeHistoryListResponse(BaseModel):
    success: bool = True
    entity_type: str
    entity_id: str
    versions: List[ChangeHistoryResponse]


class VersionDiffResponse(BaseModel):
    success: bool = True
    v1: int
    v2: int
    diff: Dict[str, Dict[str, Any]]


# Alert Schemas

class AlertBase(BaseModel):
    alert_type: str
    severity: AlertSeverityEnum
    title: str
    description: Optional[str] = None


class AlertCreate(AlertBase):
    triggered_by_log_id: Optional[str] = None
    affected_entity_type: Optional[str] = None
    affected_entity_id: Optional[str] = None
    affected_user_id: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None


class AlertResponse(AlertBase):
    id: str
    organization_id: str
    triggered_by_log_id: Optional[str] = None
    affected_entity_type: Optional[str] = None
    affected_entity_id: Optional[str] = None
    affected_user_id: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None
    status: AlertStatusEnum
    assigned_to: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: str
    updated_at: str


class AlertListResponse(BaseModel):
    success: bool = True
    alerts: List[AlertResponse]


class AlertResolveRequest(BaseModel):
    notes: Optional[str] = None


# Alert Rule Schemas

class AlertRuleBase(BaseModel):
    name: str
    description: Optional[str] = None
    event_types: List[str]
    conditions: Dict[str, Any]
    alert_type: str
    severity: AlertSeverityEnum
    notify_roles: Optional[List[str]] = None
    notification_channels: Optional[List[str]] = None
    cooldown_minutes: int = 60
    is_active: bool = True


class AlertRuleCreate(AlertRuleBase):
    pass


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    event_types: Optional[List[str]] = None
    conditions: Optional[Dict[str, Any]] = None
    severity: Optional[AlertSeverityEnum] = None
    cooldown_minutes: Optional[int] = None
    is_active: Optional[bool] = None


class AlertRuleResponse(AlertRuleBase):
    id: str
    organization_id: str
    last_triggered_at: Optional[str] = None
    created_at: str
    updated_at: str


class AlertRuleListResponse(BaseModel):
    success: bool = True
    rules: List[AlertRuleResponse]


# Compliance Schemas

class ComplianceControlResponse(BaseModel):
    control_id: str
    control_name: str
    status: CheckStatusEnum
    score: float
    findings: List[str]
    evidence: Optional[Dict[str, Any]] = None
    recommendations: List[str]
    checked_at: str


class ComplianceSummaryResponse(BaseModel):
    framework_id: str
    framework_name: str
    version: str
    total_controls: int
    passed: int
    failed: int
    warnings: int
    not_applicable: int
    errors: int
    overall_score: float
    status: str
    checked_at: str


class ComplianceFrameworkResponse(BaseModel):
    success: bool = True
    framework: str
    summary: ComplianceSummaryResponse
    controls: List[ComplianceControlResponse]


class FrameworkInfoResponse(BaseModel):
    id: str
    name: str
    description: str
    region: str
    status: Optional[str] = None


class FrameworkListResponse(BaseModel):
    success: bool = True
    frameworks: List[FrameworkInfoResponse]


class ComplianceDashboardResponse(BaseModel):
    success: bool = True
    dashboard: Dict[str, Any]


# Integrity Schemas

class IntegrityStatusResponse(BaseModel):
    success: bool = True
    status: Dict[str, Any]


class IntegrityVerifyRequest(BaseModel):
    start_sequence: Optional[int] = None
    end_sequence: Optional[int] = None


class IntegrityVerifyResponse(BaseModel):
    success: bool = True
    is_valid: bool
    issues_count: int
    issues: List[Dict[str, Any]]


# Report Schemas

class ReportTypeResponse(BaseModel):
    id: str
    name: str
    description: str


class ReportListResponse(BaseModel):
    success: bool = True
    reports: List[ReportTypeResponse]


class ReportGenerateRequest(BaseModel):
    report_type: str
    parameters: Optional[Dict[str, Any]] = None
    format: str = 'json'


class ReportResponse(BaseModel):
    success: bool = True
    report: Dict[str, Any]


# Statistics Schemas

class AuditStatisticsResponse(BaseModel):
    success: bool = True
    period_days: int
    statistics: Dict[str, Any]


# Export Schemas

class ExportRequest(BaseModel):
    format: str = Field(default='csv', pattern='^(csv|excel|json)$')
    filters: Optional[Dict[str, Any]] = None


# Retention Policy Schemas

class RetentionPolicyBase(BaseModel):
    name: str
    description: Optional[str] = None
    entity_type: Optional[str] = None
    event_types: Optional[List[str]] = None
    retention_days: int
    archive_after_days: Optional[int] = None
    compliance_framework: Optional[str] = None
    legal_hold: bool = False
    is_active: bool = True


class RetentionPolicyCreate(RetentionPolicyBase):
    pass


class RetentionPolicyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    retention_days: Optional[int] = None
    archive_after_days: Optional[int] = None
    is_active: Optional[bool] = None
    legal_hold: Optional[bool] = None


class RetentionPolicyResponse(RetentionPolicyBase):
    id: str
    organization_id: str
    created_at: str
    updated_at: str


class RetentionPolicyListResponse(BaseModel):
    success: bool = True
    policies: List[RetentionPolicyResponse]
