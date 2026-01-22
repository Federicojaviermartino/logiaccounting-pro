"""
Business rule model.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import uuid4

from app.workflows.config import TriggerType


class RuleCondition(BaseModel):
    """Single rule condition."""
    field: str
    operator: str
    value: Any


class RuleConditionGroup(BaseModel):
    """Group of conditions with AND/OR/NONE logic."""
    type: str = "all"
    rules: List[Any] = []


class RuleAction(BaseModel):
    """Action to execute when rule matches."""
    type: str
    name: Optional[str] = None
    config: Dict[str, Any] = {}


class RuleTrigger(BaseModel):
    """Rule trigger configuration."""
    type: TriggerType
    cron: Optional[str] = None
    timezone: Optional[str] = "UTC"
    entity: Optional[str] = None
    event: Optional[str] = None


class RuleScope(BaseModel):
    """Rule scope - which entities to evaluate."""
    entity: str
    filter: Dict[str, Any] = {}


class BusinessRule(BaseModel):
    """Business rule definition."""
    id: str = Field(default_factory=lambda: f"rule_{uuid4().hex[:12]}")
    name: str
    description: Optional[str] = None
    status: str = "active"
    priority: int = 100
    tenant_id: str

    trigger: RuleTrigger
    scope: RuleScope
    conditions: List[RuleConditionGroup] = []
    actions: List[RuleAction]

    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None

    version: int = 1
    execution_count: int = 0
    last_executed: Optional[datetime] = None
    affected_count: int = 0


class RuleCreate(BaseModel):
    """Schema for creating a rule."""
    name: str
    description: Optional[str] = None
    priority: int = 100
    trigger: RuleTrigger
    scope: RuleScope
    conditions: List[RuleConditionGroup] = []
    actions: List[RuleAction]


class RuleUpdate(BaseModel):
    """Schema for updating a rule."""
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = None
    trigger: Optional[RuleTrigger] = None
    scope: Optional[RuleScope] = None
    conditions: Optional[List[RuleConditionGroup]] = None
    actions: Optional[List[RuleAction]] = None
