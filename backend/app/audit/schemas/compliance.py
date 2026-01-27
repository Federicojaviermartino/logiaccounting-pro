"""Compliance schemas."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class RetentionPolicyCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    resource_type: str = Field(..., max_length=100)
    retention_days: int = Field(..., gt=0)
    archive_after_days: Optional[int] = Field(None, gt=0)
    compliance_standard: Optional[str] = None
    regulation_reference: Optional[str] = None
    action_on_expiry: str = "archive"


class RetentionPolicyResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    resource_type: str
    retention_days: int
    archive_after_days: Optional[int]
    compliance_standard: Optional[str]
    action_on_expiry: str
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True


class ComplianceRuleCreate(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    compliance_standard: str
    category: str = Field(..., max_length=50)
    rule_type: str
    rule_config: Optional[dict] = None
    severity: str = "medium"
    alert_on_violation: bool = True
    block_on_violation: bool = False
    notify_users: Optional[List[UUID]] = None


class ComplianceRuleResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str]
    compliance_standard: str
    category: str
    rule_type: str
    severity: str
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True


class ComplianceViolationResponse(BaseModel):
    id: UUID
    rule_id: UUID
    violation_type: str
    severity: str
    description: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    status: str
    detected_at: datetime
    resolved_at: Optional[datetime]
    class Config:
        from_attributes = True


class ViolationResolve(BaseModel):
    status: str
    resolution_notes: str = Field(..., max_length=1000)


class AccessLogResponse(BaseModel):
    id: UUID
    user_id: UUID
    user_email: str
    resource_type: str
    resource_id: str
    resource_name: Optional[str]
    access_type: str
    data_classification: str
    contains_pii: bool
    ip_address: Optional[str]
    accessed_at: datetime
    class Config:
        from_attributes = True


class ComplianceDashboard(BaseModel):
    total_rules: int
    active_rules: int
    open_violations: int
    violations_by_severity: dict
    violations_by_standard: dict
    retention_policies: int
    recent_violations: List[ComplianceViolationResponse]
    compliance_score: float


class AccessReport(BaseModel):
    period_start: datetime
    period_end: datetime
    total_accesses: int
    accesses_by_type: dict
    accesses_by_classification: dict
    pii_accesses: int
    financial_accesses: int
    top_accessors: List[dict]
