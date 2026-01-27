"""Report definition schemas."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class ReportDefinitionCreate(BaseModel):
    code: str = Field(..., max_length=30)
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    report_type: str
    config: Dict[str, Any] = Field(default_factory=dict)
    default_format: str = "pdf"
    is_public: bool = False


class ReportDefinitionResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str]
    report_type: str
    config: Dict[str, Any]
    default_format: str
    is_public: bool
    is_system: bool
    created_at: datetime
    class Config:
        from_attributes = True


class ReportScheduleCreate(BaseModel):
    name: str = Field(..., max_length=200)
    frequency: str
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    time_of_day: str = "08:00"
    timezone: str = "UTC"
    output_format: str = "pdf"
    email_recipients: Optional[List[str]] = None


class ReportScheduleResponse(BaseModel):
    id: UUID
    report_definition_id: UUID
    name: str
    frequency: str
    time_of_day: str
    output_format: str
    is_active: bool
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    class Config:
        from_attributes = True


class GenerateReportRequest(BaseModel):
    report_type: str
    output_format: str = "json"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    as_of_date: Optional[str] = None
    compare_period: bool = False
    department_id: Optional[UUID] = None
    currency: str = "USD"
