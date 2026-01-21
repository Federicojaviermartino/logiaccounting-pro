# LogiAccounting Pro - Phase 15 Tasks Part 1

## CORE AUDIT SYSTEM & CHANGE TRACKING

---

## TASK 1: DATABASE MODELS

### 1.1 Audit Log Model

**File:** `backend/app/audit/models/audit_log.py`

```python
"""
Audit Log Model
Immutable audit trail for all system events
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy import event
from app.extensions import db
import uuid
import hashlib
import json


class AuditLog(db.Model):
    """Immutable audit log entry"""
    
    __tablename__ = 'audit_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    
    # Event Classification
    event_type = Column(String(100), nullable=False)
    # 'entity.created', 'entity.updated', 'entity.deleted', 'entity.viewed',
    # 'auth.login', 'auth.logout', 'auth.failed', 'auth.password_changed',
    # 'permission.granted', 'permission.revoked', 'export.data', 'import.data'
    
    event_category = Column(String(50), nullable=False)
    # 'data_change', 'authentication', 'authorization', 'system', 'compliance'
    
    severity = Column(String(20), default='info')
    # 'debug', 'info', 'warning', 'error', 'critical'
    
    # Entity Information
    entity_type = Column(String(100))
    entity_id = Column(UUID(as_uuid=True))
    entity_name = Column(String(255))
    
    # Actor Information
    user_id = Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    user_email = Column(String(255))
    user_role = Column(String(100))
    
    # Context
    ip_address = Column(INET)
    user_agent = Column(Text)
    session_id = Column(String(100))
    request_id = Column(String(100))
    
    # Change Data
    action = Column(String(50), nullable=False)
    # 'create', 'read', 'update', 'delete', 'execute', 'export', 'import'
    changes = Column(JSONB)  # {field: {old: ..., new: ...}}
    metadata = Column(JSONB, default=dict)
    
    # Integrity
    data_hash = Column(String(64), nullable=False)
    previous_hash = Column(String(64))
    sequence_number = Column(BigInteger, nullable=False)
    
    # Timestamps
    occurred_at = Column(db.DateTime, nullable=False, default=datetime.utcnow)
    recorded_at = Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Compliance Tags
    compliance_tags = Column(ARRAY(Text), default=[])
    
    # Retention
    retention_until = Column(db.DateTime)
    is_archived = Column(Boolean, default=False)
    
    # Relationships
    organization = relationship('Organization', backref='audit_logs')
    user = relationship('User', foreign_keys=[user_id])
    change_history = relationship('ChangeHistory', back_populates='audit_log', uselist=False)
    
    def __init__(self, **kwargs):
        # Calculate hash before saving
        super().__init__(**kwargs)
        if not self.data_hash:
            self.data_hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute SHA-256 hash of audit data"""
        data = {
            'event_type': self.event_type,
            'event_category': self.event_category,
            'entity_type': self.entity_type,
            'entity_id': str(self.entity_id) if self.entity_id else None,
            'user_id': str(self.user_id) if self.user_id else None,
            'action': self.action,
            'changes': self.changes,
            'occurred_at': self.occurred_at.isoformat() if self.occurred_at else None,
            'previous_hash': self.previous_hash,
            'sequence_number': self.sequence_number,
        }
        
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def verify_integrity(self) -> bool:
        """Verify the hash matches the data"""
        return self.data_hash == self._compute_hash()
    
    @classmethod
    def get_next_sequence(cls, organization_id: str) -> int:
        """Get next sequence number for organization"""
        last = cls.query.filter(
            cls.organization_id == organization_id
        ).order_by(cls.sequence_number.desc()).first()
        
        return (last.sequence_number + 1) if last else 1
    
    @classmethod
    def get_previous_hash(cls, organization_id: str) -> Optional[str]:
        """Get hash of previous entry for chain linking"""
        last = cls.query.filter(
            cls.organization_id == organization_id
        ).order_by(cls.sequence_number.desc()).first()
        
        return last.data_hash if last else None
    
    def to_dict(self, include_changes: bool = False) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            'id': str(self.id),
            'organization_id': str(self.organization_id),
            'event_type': self.event_type,
            'event_category': self.event_category,
            'severity': self.severity,
            'entity_type': self.entity_type,
            'entity_id': str(self.entity_id) if self.entity_id else None,
            'entity_name': self.entity_name,
            'user_id': str(self.user_id) if self.user_id else None,
            'user_email': self.user_email,
            'user_role': self.user_role,
            'ip_address': str(self.ip_address) if self.ip_address else None,
            'action': self.action,
            'occurred_at': self.occurred_at.isoformat() if self.occurred_at else None,
            'compliance_tags': self.compliance_tags,
            'metadata': self.metadata,
        }
        
        if include_changes:
            data['changes'] = self.changes
        
        return data


# Prevent updates and deletes on audit logs
@event.listens_for(AuditLog, 'before_update')
def prevent_audit_update(mapper, connection, target):
    raise ValueError("Audit logs are immutable and cannot be updated")


@event.listens_for(AuditLog, 'before_delete')
def prevent_audit_delete(mapper, connection, target):
    # Allow archival deletes only via retention policy
    if not getattr(target, '_allow_delete', False):
        raise ValueError("Audit logs cannot be deleted")
```

### 1.2 Change History Model

**File:** `backend/app/audit/models/change_history.py`

```python
"""
Change History Model
Complete before/after snapshots of entity changes
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from app.extensions import db
import uuid


class ChangeHistory(db.Model):
    """Full entity state snapshots for change tracking"""
    
    __tablename__ = 'change_history'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_log_id = Column(UUID(as_uuid=True), db.ForeignKey('audit_logs.id'), nullable=False)
    organization_id = Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    
    # Entity
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Version
    version_number = Column(Integer, nullable=False)
    
    # Snapshots
    before_snapshot = Column(JSONB)
    after_snapshot = Column(JSONB)
    
    # Change Summary
    changed_fields = Column(ARRAY(Text), nullable=False, default=[])
    change_summary = Column(Text)
    
    # Metadata
    change_reason = Column(Text)
    
    created_at = Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    audit_log = relationship('AuditLog', back_populates='change_history')
    
    __table_args__ = (
        db.UniqueConstraint('entity_type', 'entity_id', 'version_number', name='uq_change_version'),
    )
    
    @classmethod
    def get_next_version(cls, entity_type: str, entity_id: str) -> int:
        """Get next version number for entity"""
        last = cls.query.filter(
            cls.entity_type == entity_type,
            cls.entity_id == entity_id
        ).order_by(cls.version_number.desc()).first()
        
        return (last.version_number + 1) if last else 1
    
    @classmethod
    def get_entity_history(
        cls,
        entity_type: str,
        entity_id: str,
        limit: int = 50
    ) -> List['ChangeHistory']:
        """Get change history for an entity"""
        return cls.query.filter(
            cls.entity_type == entity_type,
            cls.entity_id == entity_id
        ).order_by(cls.version_number.desc()).limit(limit).all()
    
    @classmethod
    def get_version(
        cls,
        entity_type: str,
        entity_id: str,
        version: int
    ) -> Optional['ChangeHistory']:
        """Get specific version"""
        return cls.query.filter(
            cls.entity_type == entity_type,
            cls.entity_id == entity_id,
            cls.version_number == version
        ).first()
    
    def get_diff(self) -> Dict[str, Dict[str, Any]]:
        """Get differences between before and after"""
        if not self.before_snapshot or not self.after_snapshot:
            return {}
        
        diff = {}
        
        # Find changed fields
        all_keys = set(self.before_snapshot.keys()) | set(self.after_snapshot.keys())
        
        for key in all_keys:
            old_val = self.before_snapshot.get(key)
            new_val = self.after_snapshot.get(key)
            
            if old_val != new_val:
                diff[key] = {
                    'old': old_val,
                    'new': new_val
                }
        
        return diff
    
    def to_dict(self, include_snapshots: bool = False) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            'id': str(self.id),
            'audit_log_id': str(self.audit_log_id),
            'entity_type': self.entity_type,
            'entity_id': str(self.entity_id),
            'version_number': self.version_number,
            'changed_fields': self.changed_fields,
            'change_summary': self.change_summary,
            'change_reason': self.change_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        
        if include_snapshots:
            data['before_snapshot'] = self.before_snapshot
            data['after_snapshot'] = self.after_snapshot
            data['diff'] = self.get_diff()
        
        return data
```

### 1.3 Access Log Model

**File:** `backend/app/audit/models/access_log.py`

```python
"""
Access Log Model
Authentication and authorization event logging
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from app.extensions import db
import uuid


class AccessLog(db.Model):
    """Authentication and access logging"""
    
    __tablename__ = 'access_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'))
    
    # Event
    event_type = Column(String(50), nullable=False)
    # 'login_success', 'login_failed', 'logout', 'token_refresh',
    # 'password_change', 'mfa_enabled', 'mfa_disabled', 'session_expired'
    
    # User
    user_id = Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    user_email = Column(String(255))
    
    # Authentication Details
    auth_method = Column(String(50))
    # 'password', 'sso', 'mfa', 'api_key', 'oauth'
    auth_provider = Column(String(100))
    # 'local', 'google', 'azure_ad', 'okta', etc.
    
    # Context
    ip_address = Column(INET, nullable=False)
    user_agent = Column(Text)
    device_fingerprint = Column(String(64))
    geo_location = Column(JSONB)
    # {country, country_code, city, region, lat, lon, timezone}
    
    # Result
    success = Column(Boolean, nullable=False)
    failure_reason = Column(String(255))
    
    # Risk Assessment
    risk_score = Column(Integer)  # 0-100
    risk_factors = Column(JSONB)
    # ['new_device', 'unusual_location', 'brute_force', 'impossible_travel']
    
    # Session
    session_id = Column(String(100))
    session_duration_seconds = Column(Integer)
    
    occurred_at = Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    organization = relationship('Organization')
    user = relationship('User')
    
    @classmethod
    def log_login_success(
        cls,
        user_id: str,
        organization_id: str,
        ip_address: str,
        user_agent: str = None,
        auth_method: str = 'password',
        auth_provider: str = 'local',
        session_id: str = None,
        geo_location: Dict = None
    ) -> 'AccessLog':
        """Log successful login"""
        from app.extensions import db
        
        log = cls(
            organization_id=organization_id,
            event_type='login_success',
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            auth_method=auth_method,
            auth_provider=auth_provider,
            success=True,
            session_id=session_id,
            geo_location=geo_location,
        )
        
        db.session.add(log)
        db.session.commit()
        
        return log
    
    @classmethod
    def log_login_failed(
        cls,
        user_email: str,
        ip_address: str,
        failure_reason: str,
        user_agent: str = None,
        organization_id: str = None,
        risk_score: int = None,
        risk_factors: List[str] = None
    ) -> 'AccessLog':
        """Log failed login attempt"""
        from app.extensions import db
        
        log = cls(
            organization_id=organization_id,
            event_type='login_failed',
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            failure_reason=failure_reason,
            risk_score=risk_score,
            risk_factors=risk_factors,
        )
        
        db.session.add(log)
        db.session.commit()
        
        return log
    
    @classmethod
    def get_failed_attempts(
        cls,
        ip_address: str = None,
        user_email: str = None,
        minutes: int = 30
    ) -> int:
        """Count recent failed login attempts"""
        from datetime import timedelta
        
        since = datetime.utcnow() - timedelta(minutes=minutes)
        
        query = cls.query.filter(
            cls.event_type == 'login_failed',
            cls.occurred_at >= since
        )
        
        if ip_address:
            query = query.filter(cls.ip_address == ip_address)
        
        if user_email:
            query = query.filter(cls.user_email == user_email)
        
        return query.count()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'organization_id': str(self.organization_id) if self.organization_id else None,
            'event_type': self.event_type,
            'user_id': str(self.user_id) if self.user_id else None,
            'user_email': self.user_email,
            'auth_method': self.auth_method,
            'auth_provider': self.auth_provider,
            'ip_address': str(self.ip_address) if self.ip_address else None,
            'success': self.success,
            'failure_reason': self.failure_reason,
            'risk_score': self.risk_score,
            'risk_factors': self.risk_factors,
            'geo_location': self.geo_location,
            'occurred_at': self.occurred_at.isoformat() if self.occurred_at else None,
        }
```

### 1.4 Alert Model

**File:** `backend/app/audit/models/alert.py`

```python
"""
Audit Alert Models
Alert definitions and instances
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from app.extensions import db
import uuid


class AuditAlert(db.Model):
    """Audit alert instance"""
    
    __tablename__ = 'audit_alerts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    
    # Alert Type
    alert_type = Column(String(100), nullable=False)
    # 'suspicious_login', 'bulk_delete', 'permission_escalation',
    # 'data_export', 'compliance_violation', 'unusual_activity'
    
    # Trigger
    triggered_by_log_id = Column(UUID(as_uuid=True), db.ForeignKey('audit_logs.id'))
    
    # Alert Details
    severity = Column(String(20), nullable=False)
    # 'low', 'medium', 'high', 'critical'
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Context
    affected_entity_type = Column(String(100))
    affected_entity_id = Column(UUID(as_uuid=True))
    affected_user_id = Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    
    # Evidence
    evidence = Column(JSONB)
    
    # Status
    status = Column(String(20), default='open')
    # 'open', 'acknowledged', 'investigating', 'resolved', 'dismissed'
    
    # Resolution
    assigned_to = Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    resolved_by = Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    resolved_at = Column(db.DateTime)
    resolution_notes = Column(Text)
    
    created_at = Column(db.DateTime, default=datetime.utcnow)
    updated_at = Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship('Organization')
    triggered_by_log = relationship('AuditLog')
    affected_user = relationship('User', foreign_keys=[affected_user_id])
    assigned_user = relationship('User', foreign_keys=[assigned_to])
    resolved_by_user = relationship('User', foreign_keys=[resolved_by])
    
    SEVERITY_ORDER = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
    
    def acknowledge(self, user_id: str):
        """Acknowledge the alert"""
        self.status = 'acknowledged'
        self.assigned_to = user_id
        self.updated_at = datetime.utcnow()
    
    def start_investigation(self, user_id: str):
        """Mark as under investigation"""
        self.status = 'investigating'
        if not self.assigned_to:
            self.assigned_to = user_id
        self.updated_at = datetime.utcnow()
    
    def resolve(self, user_id: str, notes: str = None):
        """Resolve the alert"""
        self.status = 'resolved'
        self.resolved_by = user_id
        self.resolved_at = datetime.utcnow()
        self.resolution_notes = notes
        self.updated_at = datetime.utcnow()
    
    def dismiss(self, user_id: str, reason: str = None):
        """Dismiss the alert"""
        self.status = 'dismissed'
        self.resolved_by = user_id
        self.resolved_at = datetime.utcnow()
        self.resolution_notes = reason
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'organization_id': str(self.organization_id),
            'alert_type': self.alert_type,
            'severity': self.severity,
            'title': self.title,
            'description': self.description,
            'affected_entity_type': self.affected_entity_type,
            'affected_entity_id': str(self.affected_entity_id) if self.affected_entity_id else None,
            'affected_user_id': str(self.affected_user_id) if self.affected_user_id else None,
            'evidence': self.evidence,
            'status': self.status,
            'assigned_to': str(self.assigned_to) if self.assigned_to else None,
            'resolved_by': str(self.resolved_by) if self.resolved_by else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolution_notes': self.resolution_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class AlertRule(db.Model):
    """Configurable alert rule"""
    
    __tablename__ = 'alert_rules'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    
    # Rule Definition
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Trigger Conditions
    event_types = Column(ARRAY(Text), nullable=False)
    conditions = Column(JSONB, nullable=False)
    # e.g., {"count": {">": 5}, "timeframe_minutes": 10, "field_match": {"action": "delete"}}
    
    # Alert Settings
    alert_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    
    # Notifications
    notify_roles = Column(ARRAY(Text))
    notify_users = Column(ARRAY(UUID(as_uuid=True)))
    notification_channels = Column(ARRAY(Text))
    # ['email', 'slack', 'webhook', 'in_app']
    
    # Throttling
    cooldown_minutes = Column(Integer, default=60)
    last_triggered_at = Column(db.DateTime)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    created_at = Column(db.DateTime, default=datetime.utcnow)
    updated_at = Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('organization_id', 'name', name='uq_alert_rule_name'),
    )
    
    def can_trigger(self) -> bool:
        """Check if rule can trigger (not in cooldown)"""
        if not self.is_active:
            return False
        
        if not self.last_triggered_at:
            return True
        
        from datetime import timedelta
        cooldown_end = self.last_triggered_at + timedelta(minutes=self.cooldown_minutes)
        return datetime.utcnow() >= cooldown_end
    
    def record_trigger(self):
        """Record that the rule was triggered"""
        self.last_triggered_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'organization_id': str(self.organization_id),
            'name': self.name,
            'description': self.description,
            'event_types': self.event_types,
            'conditions': self.conditions,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'notify_roles': self.notify_roles,
            'notification_channels': self.notification_channels,
            'cooldown_minutes': self.cooldown_minutes,
            'is_active': self.is_active,
            'last_triggered_at': self.last_triggered_at.isoformat() if self.last_triggered_at else None,
        }
```

---

## TASK 2: AUDIT LOGGER CORE

### 2.1 Event Types Definition

**File:** `backend/app/audit/core/event_types.py`

```python
"""
Audit Event Types
Standardized event type definitions
"""

from enum import Enum
from dataclasses import dataclass
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
    """CRUD + actions"""
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
    compliance_tags: List[str] = None
    
    def __str__(self):
        return self.name


# Entity Events
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

# Authentication Events
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

# Authorization Events
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

# Financial Events
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

# System Events
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

# Compliance Events
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

# Security Events
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


# Event registry for lookup
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
```

### 2.2 Context Provider

**File:** `backend/app/audit/core/context_provider.py`

```python
"""
Audit Context Provider
Captures request context for audit logging
"""

from flask import request, g, has_request_context
from typing import Optional, Dict, Any
from dataclasses import dataclass
import uuid


@dataclass
class AuditContext:
    """Audit context data"""
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    organization_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'user_email': self.user_email,
            'user_role': self.user_role,
            'organization_id': self.organization_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'session_id': self.session_id,
            'request_id': self.request_id,
        }


class ContextProvider:
    """Provides audit context from Flask request"""
    
    @staticmethod
    def get_current_context() -> AuditContext:
        """Get audit context from current request"""
        context = AuditContext()
        
        if not has_request_context():
            return context
        
        # Request ID
        context.request_id = getattr(g, 'request_id', None) or str(uuid.uuid4())
        
        # IP Address
        context.ip_address = ContextProvider._get_client_ip()
        
        # User Agent
        context.user_agent = request.headers.get('User-Agent')
        
        # User context (from JWT or session)
        if hasattr(g, 'current_user') and g.current_user:
            user = g.current_user
            context.user_id = str(user.id) if user.id else None
            context.user_email = user.email
            context.user_role = user.role
            context.organization_id = str(user.organization_id) if user.organization_id else None
        
        # Session ID
        context.session_id = request.cookies.get('session_id') or getattr(g, 'session_id', None)
        
        return context
    
    @staticmethod
    def _get_client_ip() -> Optional[str]:
        """Get client IP address, handling proxies"""
        if not has_request_context():
            return None
        
        # Check for forwarded headers (reverse proxy)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # Take the first IP (client IP)
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.remote_addr
    
    @staticmethod
    def set_context_user(user):
        """Set user in context (for use outside request)"""
        if not has_request_context():
            return
        
        g.current_user = user
    
    @staticmethod
    def get_geo_location(ip_address: str) -> Optional[Dict[str, Any]]:
        """Get geo location from IP (requires external service)"""
        # This would integrate with a service like MaxMind, IP-API, etc.
        # For now, return None
        return None


def audit_context_middleware():
    """Flask middleware to set up audit context"""
    g.request_id = str(uuid.uuid4())
```

### 2.3 Audit Logger Service

**File:** `backend/app/audit/core/audit_logger.py`

```python
"""
Audit Logger
Core service for logging audit events
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

from app.extensions import db
from app.audit.models.audit_log import AuditLog
from app.audit.models.change_history import ChangeHistory
from app.audit.core.context_provider import ContextProvider, AuditContext
from app.audit.core.event_types import (
    EventType, get_event_type, EventCategory, Severity, Action,
    ENTITY_CREATED, ENTITY_UPDATED, ENTITY_DELETED
)

logger = logging.getLogger(__name__)


class AuditLogger:
    """Service for logging audit events"""
    
    def __init__(self):
        self._batch = []
        self._batch_size = 100
    
    def log(
        self,
        event_type: str | EventType,
        action: str | Action,
        entity_type: str = None,
        entity_id: str = None,
        entity_name: str = None,
        changes: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
        context: AuditContext = None,
        severity: str | Severity = None,
        compliance_tags: List[str] = None,
        before_snapshot: Dict = None,
        after_snapshot: Dict = None
    ) -> Optional[AuditLog]:
        """
        Log an audit event
        
        Args:
            event_type: Event type name or EventType object
            action: Action performed
            entity_type: Type of entity affected
            entity_id: ID of entity affected
            entity_name: Human-readable entity name
            changes: Field changes {field: {old: ..., new: ...}}
            metadata: Additional metadata
            context: Audit context (auto-captured if not provided)
            severity: Override default severity
            compliance_tags: Override default compliance tags
            before_snapshot: Complete entity state before change
            after_snapshot: Complete entity state after change
            
        Returns:
            Created AuditLog entry
        """
        try:
            # Get context
            if context is None:
                context = ContextProvider.get_current_context()
            
            # Resolve event type
            if isinstance(event_type, str):
                event_type_obj = get_event_type(event_type)
                event_type_name = event_type
            else:
                event_type_obj = event_type
                event_type_name = event_type.name
            
            # Resolve action
            if isinstance(action, Action):
                action = action.value
            
            # Resolve severity
            if severity is None:
                severity = event_type_obj.default_severity.value if event_type_obj else 'info'
            elif isinstance(severity, Severity):
                severity = severity.value
            
            # Resolve compliance tags
            if compliance_tags is None and event_type_obj:
                compliance_tags = event_type_obj.compliance_tags or []
            
            # Get organization ID
            organization_id = context.organization_id
            if not organization_id:
                logger.warning("Audit log without organization_id")
                return None
            
            # Get sequence and previous hash
            sequence_number = AuditLog.get_next_sequence(organization_id)
            previous_hash = AuditLog.get_previous_hash(organization_id)
            
            # Create audit log
            audit_log = AuditLog(
                organization_id=organization_id,
                event_type=event_type_name,
                event_category=event_type_obj.category.value if event_type_obj else 'system',
                severity=severity,
                entity_type=entity_type,
                entity_id=entity_id,
                entity_name=entity_name,
                user_id=context.user_id,
                user_email=context.user_email,
                user_role=context.user_role,
                ip_address=context.ip_address,
                user_agent=context.user_agent,
                session_id=context.session_id,
                request_id=context.request_id,
                action=action,
                changes=changes,
                metadata=metadata or {},
                sequence_number=sequence_number,
                previous_hash=previous_hash,
                compliance_tags=compliance_tags,
                occurred_at=datetime.utcnow(),
            )
            
            db.session.add(audit_log)
            
            # Create change history if snapshots provided
            if before_snapshot is not None or after_snapshot is not None:
                changed_fields = list(changes.keys()) if changes else []
                
                change_history = ChangeHistory(
                    audit_log_id=audit_log.id,
                    organization_id=organization_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    version_number=ChangeHistory.get_next_version(entity_type, entity_id),
                    before_snapshot=before_snapshot,
                    after_snapshot=after_snapshot,
                    changed_fields=changed_fields,
                    change_summary=self._generate_change_summary(changes),
                )
                
                db.session.add(change_history)
            
            db.session.commit()
            
            logger.debug(f"Audit logged: {event_type_name} on {entity_type}/{entity_id}")
            
            return audit_log
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            db.session.rollback()
            return None
    
    def log_create(
        self,
        entity_type: str,
        entity_id: str,
        entity_name: str = None,
        data: Dict = None,
        metadata: Dict = None
    ) -> Optional[AuditLog]:
        """Log entity creation"""
        return self.log(
            event_type=ENTITY_CREATED,
            action=Action.CREATE,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            metadata=metadata,
            after_snapshot=data,
        )
    
    def log_update(
        self,
        entity_type: str,
        entity_id: str,
        entity_name: str = None,
        changes: Dict[str, Dict] = None,
        before_snapshot: Dict = None,
        after_snapshot: Dict = None,
        metadata: Dict = None
    ) -> Optional[AuditLog]:
        """Log entity update"""
        return self.log(
            event_type=ENTITY_UPDATED,
            action=Action.UPDATE,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            changes=changes,
            before_snapshot=before_snapshot,
            after_snapshot=after_snapshot,
            metadata=metadata,
        )
    
    def log_delete(
        self,
        entity_type: str,
        entity_id: str,
        entity_name: str = None,
        before_snapshot: Dict = None,
        metadata: Dict = None
    ) -> Optional[AuditLog]:
        """Log entity deletion"""
        return self.log(
            event_type=ENTITY_DELETED,
            action=Action.DELETE,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            before_snapshot=before_snapshot,
            metadata=metadata,
            severity=Severity.WARNING,
        )
    
    def _generate_change_summary(self, changes: Dict) -> str:
        """Generate human-readable change summary"""
        if not changes:
            return ""
        
        parts = []
        for field, change in changes.items():
            old_val = change.get('old', 'null')
            new_val = change.get('new', 'null')
            
            # Truncate long values
            if isinstance(old_val, str) and len(old_val) > 50:
                old_val = old_val[:50] + '...'
            if isinstance(new_val, str) and len(new_val) > 50:
                new_val = new_val[:50] + '...'
            
            parts.append(f"{field}: {old_val} → {new_val}")
        
        return "; ".join(parts[:5])  # Limit to 5 changes


# Global instance
audit_logger = AuditLogger()


# Convenience functions
def log_audit(event_type: str, action: str, **kwargs) -> Optional[AuditLog]:
    """Log audit event using global logger"""
    return audit_logger.log(event_type=event_type, action=action, **kwargs)


def log_create(entity_type: str, entity_id: str, **kwargs) -> Optional[AuditLog]:
    """Log entity creation"""
    return audit_logger.log_create(entity_type=entity_type, entity_id=entity_id, **kwargs)


def log_update(entity_type: str, entity_id: str, **kwargs) -> Optional[AuditLog]:
    """Log entity update"""
    return audit_logger.log_update(entity_type=entity_type, entity_id=entity_id, **kwargs)


def log_delete(entity_type: str, entity_id: str, **kwargs) -> Optional[AuditLog]:
    """Log entity deletion"""
    return audit_logger.log_delete(entity_type=entity_type, entity_id=entity_id, **kwargs)
```

---

## TASK 3: CHANGE TRACKER (SQLALCHEMY EVENTS)

### 3.1 Automatic Change Tracking

**File:** `backend/app/audit/core/change_tracker.py`

```python
"""
Change Tracker
Automatic change tracking via SQLAlchemy events
"""

from datetime import datetime
from typing import Dict, Any, Set, List, Type
from sqlalchemy import event, inspect
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import History
import logging
import copy

from app.audit.core.audit_logger import audit_logger
from app.audit.core.context_provider import ContextProvider

logger = logging.getLogger(__name__)


# Models to track (register your models here)
TRACKED_MODELS: Set[Type] = set()

# Fields to exclude from tracking
EXCLUDED_FIELDS = {
    'created_at', 'updated_at', 'password_hash', 'password',
    '_sa_instance_state', 'search_vector'
}

# Sensitive fields (values will be masked in logs)
SENSITIVE_FIELDS = {
    'password', 'password_hash', 'api_key', 'secret', 'token',
    'ssn', 'tax_id', 'credit_card', 'bank_account'
}


def register_model(model_class: Type):
    """Register a model for automatic change tracking"""
    TRACKED_MODELS.add(model_class)
    return model_class


def track_changes(cls):
    """Decorator to register a model for tracking"""
    register_model(cls)
    return cls


class ChangeTracker:
    """Tracks changes to SQLAlchemy models"""
    
    def __init__(self):
        self._original_states: Dict[int, Dict] = {}
    
    def capture_original_state(self, instance) -> Dict[str, Any]:
        """Capture the original state of an instance"""
        if type(instance) not in TRACKED_MODELS:
            return {}
        
        state = {}
        mapper = inspect(type(instance))
        
        for column in mapper.columns:
            if column.key in EXCLUDED_FIELDS:
                continue
            
            value = getattr(instance, column.key, None)
            
            # Mask sensitive fields
            if column.key in SENSITIVE_FIELDS and value:
                value = '********'
            
            # Handle special types
            if isinstance(value, datetime):
                value = value.isoformat()
            elif hasattr(value, 'hex'):  # UUID
                value = str(value)
            
            state[column.key] = value
        
        return state
    
    def get_changes(self, instance) -> Dict[str, Dict[str, Any]]:
        """Get changes made to an instance"""
        changes = {}
        mapper = inspect(type(instance))
        
        for column in mapper.columns:
            if column.key in EXCLUDED_FIELDS:
                continue
            
            attr = getattr(inspect(instance).attrs, column.key)
            history: History = attr.history
            
            if history.has_changes():
                old_value = history.deleted[0] if history.deleted else None
                new_value = history.added[0] if history.added else None
                
                # Mask sensitive fields
                if column.key in SENSITIVE_FIELDS:
                    old_value = '********' if old_value else None
                    new_value = '********' if new_value else None
                
                # Handle special types
                if isinstance(old_value, datetime):
                    old_value = old_value.isoformat()
                if isinstance(new_value, datetime):
                    new_value = new_value.isoformat()
                if hasattr(old_value, 'hex'):
                    old_value = str(old_value)
                if hasattr(new_value, 'hex'):
                    new_value = str(new_value)
                
                changes[column.key] = {
                    'old': old_value,
                    'new': new_value
                }
        
        return changes
    
    def get_entity_name(self, instance) -> str:
        """Get human-readable name for entity"""
        # Try common name attributes
        for attr in ['name', 'title', 'email', 'display_name', 'number']:
            if hasattr(instance, attr):
                value = getattr(instance, attr)
                if value:
                    return str(value)
        
        return f"{type(instance).__name__}#{instance.id}"


# Global tracker instance
change_tracker = ChangeTracker()


# SQLAlchemy Event Listeners

@event.listens_for(Session, 'before_flush')
def before_flush(session, flush_context, instances):
    """Capture original state before flush"""
    for instance in session.dirty:
        if type(instance) in TRACKED_MODELS:
            instance_id = id(instance)
            if instance_id not in change_tracker._original_states:
                # Need to load original from database
                original = session.query(type(instance)).get(instance.id)
                if original:
                    change_tracker._original_states[instance_id] = change_tracker.capture_original_state(original)


@event.listens_for(Session, 'after_flush')
def after_flush(session, flush_context):
    """Log changes after flush"""
    
    # Handle new instances (inserts)
    for instance in session.new:
        if type(instance) not in TRACKED_MODELS:
            continue
        
        try:
            after_state = change_tracker.capture_original_state(instance)
            
            audit_logger.log_create(
                entity_type=type(instance).__tablename__,
                entity_id=str(instance.id),
                entity_name=change_tracker.get_entity_name(instance),
                data=after_state,
            )
        except Exception as e:
            logger.error(f"Failed to log create for {type(instance).__name__}: {e}")
    
    # Handle modified instances (updates)
    for instance in session.dirty:
        if type(instance) not in TRACKED_MODELS:
            continue
        
        try:
            instance_id = id(instance)
            before_state = change_tracker._original_states.pop(instance_id, {})
            after_state = change_tracker.capture_original_state(instance)
            changes = change_tracker.get_changes(instance)
            
            if changes:  # Only log if there are actual changes
                audit_logger.log_update(
                    entity_type=type(instance).__tablename__,
                    entity_id=str(instance.id),
                    entity_name=change_tracker.get_entity_name(instance),
                    changes=changes,
                    before_snapshot=before_state,
                    after_snapshot=after_state,
                )
        except Exception as e:
            logger.error(f"Failed to log update for {type(instance).__name__}: {e}")
    
    # Handle deleted instances
    for instance in session.deleted:
        if type(instance) not in TRACKED_MODELS:
            continue
        
        try:
            before_state = change_tracker.capture_original_state(instance)
            
            audit_logger.log_delete(
                entity_type=type(instance).__tablename__,
                entity_id=str(instance.id),
                entity_name=change_tracker.get_entity_name(instance),
                before_snapshot=before_state,
            )
        except Exception as e:
            logger.error(f"Failed to log delete for {type(instance).__name__}: {e}")


def init_change_tracking(app):
    """Initialize change tracking for the application"""
    # Import models to register them
    # This should be called after all models are defined
    pass
```

---

## TASK 4: INTEGRITY SERVICE

### 4.1 Hash Chain Verification

**File:** `backend/app/audit/core/integrity_service.py`

```python
"""
Integrity Service
Hash chain management and verification
"""

from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
import hashlib
import logging

from app.extensions import db
from app.audit.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class IntegrityService:
    """Service for audit log integrity verification"""
    
    def verify_chain(
        self,
        organization_id: str,
        start_sequence: int = None,
        end_sequence: int = None,
        limit: int = 10000
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Verify the integrity of the audit log chain
        
        Args:
            organization_id: Organization to verify
            start_sequence: Starting sequence number (optional)
            end_sequence: Ending sequence number (optional)
            limit: Maximum records to verify
            
        Returns:
            Tuple of (is_valid, issues)
        """
        issues = []
        
        query = AuditLog.query.filter(
            AuditLog.organization_id == organization_id
        ).order_by(AuditLog.sequence_number.asc())
        
        if start_sequence:
            query = query.filter(AuditLog.sequence_number >= start_sequence)
        
        if end_sequence:
            query = query.filter(AuditLog.sequence_number <= end_sequence)
        
        logs = query.limit(limit).all()
        
        if not logs:
            return True, []
        
        previous_hash = None
        expected_sequence = logs[0].sequence_number
        
        for log in logs:
            # Check sequence continuity
            if log.sequence_number != expected_sequence:
                issues.append({
                    'type': 'sequence_gap',
                    'log_id': str(log.id),
                    'expected_sequence': expected_sequence,
                    'actual_sequence': log.sequence_number,
                })
            
            # Check hash integrity
            if not log.verify_integrity():
                issues.append({
                    'type': 'hash_mismatch',
                    'log_id': str(log.id),
                    'sequence': log.sequence_number,
                    'stored_hash': log.data_hash,
                })
            
            # Check chain linkage
            if previous_hash and log.previous_hash != previous_hash:
                issues.append({
                    'type': 'chain_broken',
                    'log_id': str(log.id),
                    'sequence': log.sequence_number,
                    'expected_previous': previous_hash,
                    'actual_previous': log.previous_hash,
                })
            
            previous_hash = log.data_hash
            expected_sequence = log.sequence_number + 1
        
        is_valid = len(issues) == 0
        
        if not is_valid:
            logger.warning(f"Integrity issues found for org {organization_id}: {len(issues)} issues")
        
        return is_valid, issues
    
    def verify_single(self, audit_log: AuditLog) -> Tuple[bool, Optional[str]]:
        """
        Verify a single audit log entry
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Verify hash
        if not audit_log.verify_integrity():
            return False, "Hash mismatch - data may have been tampered"
        
        # Verify chain link
        if audit_log.sequence_number > 1:
            previous = AuditLog.query.filter(
                AuditLog.organization_id == audit_log.organization_id,
                AuditLog.sequence_number == audit_log.sequence_number - 1
            ).first()
            
            if previous and audit_log.previous_hash != previous.data_hash:
                return False, "Chain link broken - previous hash mismatch"
        
        return True, None
    
    def get_chain_status(self, organization_id: str) -> Dict[str, Any]:
        """Get chain status summary"""
        # Get total count
        total_count = AuditLog.query.filter(
            AuditLog.organization_id == organization_id
        ).count()
        
        # Get first and last entries
        first = AuditLog.query.filter(
            AuditLog.organization_id == organization_id
        ).order_by(AuditLog.sequence_number.asc()).first()
        
        last = AuditLog.query.filter(
            AuditLog.organization_id == organization_id
        ).order_by(AuditLog.sequence_number.desc()).first()
        
        # Check for gaps
        if first and last:
            expected_count = last.sequence_number - first.sequence_number + 1
            has_gaps = total_count != expected_count
        else:
            has_gaps = False
        
        return {
            'total_entries': total_count,
            'first_sequence': first.sequence_number if first else None,
            'last_sequence': last.sequence_number if last else None,
            'first_timestamp': first.occurred_at.isoformat() if first else None,
            'last_timestamp': last.occurred_at.isoformat() if last else None,
            'has_sequence_gaps': has_gaps,
            'chain_hash': last.data_hash if last else None,
        }
    
    def export_verification_report(
        self,
        organization_id: str,
        include_issues: bool = True
    ) -> Dict[str, Any]:
        """Export a verification report for compliance"""
        is_valid, issues = self.verify_chain(organization_id)
        status = self.get_chain_status(organization_id)
        
        report = {
            'organization_id': organization_id,
            'verification_timestamp': datetime.utcnow().isoformat(),
            'chain_status': status,
            'is_valid': is_valid,
            'issues_found': len(issues),
        }
        
        if include_issues and issues:
            report['issues'] = issues[:100]  # Limit issues in report
        
        return report


# Global instance
integrity_service = IntegrityService()
```

---

## Continue to Part 2 for Compliance Frameworks & Reporting

---

*Phase 15 Tasks Part 1 - LogiAccounting Pro*
*Core Audit System & Change Tracking*
