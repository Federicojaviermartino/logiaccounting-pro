"""Audit log schemas."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class AuditLogCreate(BaseModel):
    action: str
    severity: str = "low"
    resource_type: str
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    description: Optional[str] = None
    old_values: Optional[dict] = None
    new_values: Optional[dict] = None
    changed_fields: Optional[List[str]] = None
    metadata: Optional[dict] = None
    is_sensitive: bool = False


class AuditLogResponse(BaseModel):
    id: UUID
    timestamp: datetime
    user_id: Optional[UUID]
    user_email: Optional[str]
    user_name: Optional[str]
    action: str
    severity: str
    resource_type: str
    resource_id: Optional[str]
    resource_name: Optional[str]
    description: Optional[str]
    changed_fields: Optional[List[str]]
    ip_address: Optional[str]
    endpoint: Optional[str]
    class Config:
        from_attributes = True


class AuditLogDetail(AuditLogResponse):
    old_values: Optional[dict]
    new_values: Optional[dict]
    user_agent: Optional[str]
    request_id: Optional[str]
    metadata: Optional[dict]


class AuditLogFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_id: Optional[UUID] = None
    action: Optional[str] = None
    actions: Optional[List[str]] = None
    severity: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    search: Optional[str] = None


class AuditSummary(BaseModel):
    period_start: datetime
    period_end: datetime
    total_events: int
    events_by_action: dict
    events_by_severity: dict
    events_by_resource: dict
    top_users: List[dict]
    recent_critical: List[AuditLogResponse]


class DataChangeResponse(BaseModel):
    id: UUID
    audit_log_id: UUID
    table_name: str
    record_id: str
    field_name: str
    old_value: Optional[str]
    new_value: Optional[str]
    timestamp: datetime
    class Config:
        from_attributes = True


class EntitySnapshotResponse(BaseModel):
    id: UUID
    entity_type: str
    entity_id: str
    snapshot_data: dict
    reason: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True
