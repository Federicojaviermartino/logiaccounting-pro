# Phase 32: Advanced Security - Part 5: Audit Logging

## Overview
This part covers comprehensive audit logging for security and compliance.

---

## File 1: Audit Events
**Path:** `backend/app/security/audit/events.py`

```python
"""
Audit Events
Event definitions for audit logging
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import uuid4


class AuditEventType(str, Enum):
    """Types of audit events."""
    # Authentication
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_LOGIN_FAILED = "auth.login_failed"
    AUTH_PASSWORD_CHANGE = "auth.password_change"
    AUTH_PASSWORD_RESET = "auth.password_reset"
    AUTH_MFA_ENABLED = "auth.mfa_enabled"
    AUTH_MFA_DISABLED = "auth.mfa_disabled"
    AUTH_MFA_VERIFIED = "auth.mfa_verified"
    AUTH_SESSION_CREATED = "auth.session_created"
    AUTH_SESSION_REVOKED = "auth.session_revoked"
    
    # Authorization
    AUTHZ_PERMISSION_GRANTED = "authz.permission_granted"
    AUTHZ_PERMISSION_DENIED = "authz.permission_denied"
    AUTHZ_ROLE_ASSIGNED = "authz.role_assigned"
    AUTHZ_ROLE_REVOKED = "authz.role_revoked"
    
    # Data Access
    DATA_READ = "data.read"
    DATA_CREATE = "data.create"
    DATA_UPDATE = "data.update"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"
    DATA_IMPORT = "data.import"
    
    # Configuration
    CONFIG_CHANGED = "config.changed"
    SETTINGS_UPDATED = "settings.updated"
    
    # Security
    SECURITY_ALERT = "security.alert"
    SECURITY_THREAT_DETECTED = "security.threat_detected"
    SECURITY_IP_BLOCKED = "security.ip_blocked"
    SECURITY_RATE_LIMITED = "security.rate_limited"
    
    # System
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"


class AuditOutcome(str, Enum):
    """Audit event outcome."""
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"
    DENIED = "denied"


class AuditSeverity(str, Enum):
    """Audit event severity."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event record."""
    id: str
    timestamp: datetime
    event_type: AuditEventType
    outcome: AuditOutcome
    severity: AuditSeverity = AuditSeverity.INFO
    
    # Actor information
    user_id: Optional[str] = None
    customer_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Request information
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    
    # Resource information
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    
    # Event details
    action: str = ""
    description: str = ""
    details: Dict = field(default_factory=dict)
    
    # Changes (for update events)
    old_values: Optional[Dict] = None
    new_values: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "outcome": self.outcome.value,
            "severity": self.severity.value,
            "user_id": self.user_id,
            "customer_id": self.customer_id,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "request_id": self.request_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "description": self.description,
            "details": self.details,
            "old_values": self.old_values,
            "new_values": self.new_values,
        }
    
    @classmethod
    def create(
        cls,
        event_type: AuditEventType,
        outcome: AuditOutcome = AuditOutcome.SUCCESS,
        **kwargs,
    ) -> "AuditEvent":
        """Factory method to create audit event."""
        return cls(
            id=f"audit_{uuid4().hex[:16]}",
            timestamp=datetime.utcnow(),
            event_type=event_type,
            outcome=outcome,
            **kwargs,
        )
```

---

## File 2: Audit Logger
**Path:** `backend/app/security/audit/logger.py`

```python
"""
Audit Logger
Core audit logging functionality
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import logging
import json
from collections import deque
from threading import Lock

from app.security.audit.events import AuditEvent, AuditEventType, AuditOutcome, AuditSeverity

logger = logging.getLogger(__name__)


class AuditLogger:
    """Audit logging system."""
    
    # Sensitive fields to redact
    REDACTED_FIELDS = {
        "password", "secret", "token", "api_key", "credit_card",
        "ssn", "tax_id", "bank_account", "routing_number",
    }
    
    def __init__(self, max_buffer_size: int = 10000):
        self._buffer: deque = deque(maxlen=max_buffer_size)
        self._lock = Lock()
        self._handlers: List[Callable] = []
        self._filters: List[Callable] = []
    
    def log(self, event: AuditEvent):
        """Log an audit event."""
        # Apply filters
        for filter_fn in self._filters:
            if not filter_fn(event):
                return
        
        # Redact sensitive data
        event = self._redact_sensitive(event)
        
        # Add to buffer
        with self._lock:
            self._buffer.append(event)
        
        # Call handlers
        for handler in self._handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Audit handler error: {e}")
        
        # Also log to standard logger
        log_level = self._severity_to_level(event.severity)
        logger.log(
            log_level,
            f"AUDIT: {event.event_type.value} - {event.outcome.value} - {event.description}",
            extra={"audit_event": event.to_dict()},
        )
    
    def log_auth_event(
        self,
        event_type: AuditEventType,
        user_id: str = None,
        success: bool = True,
        ip_address: str = None,
        details: Dict = None,
    ):
        """Log authentication event."""
        event = AuditEvent.create(
            event_type=event_type,
            outcome=AuditOutcome.SUCCESS if success else AuditOutcome.FAILURE,
            severity=AuditSeverity.INFO if success else AuditSeverity.WARNING,
            user_id=user_id,
            ip_address=ip_address,
            action=event_type.value,
            details=details or {},
        )
        self.log(event)
    
    def log_data_event(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: str = None,
        customer_id: str = None,
        old_values: Dict = None,
        new_values: Dict = None,
    ):
        """Log data access/modification event."""
        event_type_map = {
            "read": AuditEventType.DATA_READ,
            "create": AuditEventType.DATA_CREATE,
            "update": AuditEventType.DATA_UPDATE,
            "delete": AuditEventType.DATA_DELETE,
            "export": AuditEventType.DATA_EXPORT,
        }
        
        event = AuditEvent.create(
            event_type=event_type_map.get(action, AuditEventType.DATA_READ),
            outcome=AuditOutcome.SUCCESS,
            user_id=user_id,
            customer_id=customer_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            old_values=old_values,
            new_values=new_values,
        )
        self.log(event)
    
    def log_security_event(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity,
        description: str,
        ip_address: str = None,
        details: Dict = None,
    ):
        """Log security event."""
        event = AuditEvent.create(
            event_type=event_type,
            outcome=AuditOutcome.SUCCESS,
            severity=severity,
            ip_address=ip_address,
            description=description,
            details=details or {},
        )
        self.log(event)
    
    def query(
        self,
        event_type: AuditEventType = None,
        user_id: str = None,
        customer_id: str = None,
        resource_type: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """Query audit logs."""
        with self._lock:
            events = list(self._buffer)
        
        # Apply filters
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        
        if customer_id:
            events = [e for e in events if e.customer_id == customer_id]
        
        if resource_type:
            events = [e for e in events if e.resource_type == resource_type]
        
        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        
        if end_time:
            events = [e for e in events if e.timestamp <= end_time]
        
        # Sort by timestamp descending
        events.sort(key=lambda e: e.timestamp, reverse=True)
        
        return events[:limit]
    
    def get_summary(
        self,
        start_time: datetime = None,
        end_time: datetime = None,
    ) -> Dict:
        """Get audit summary statistics."""
        if not start_time:
            start_time = datetime.utcnow() - timedelta(days=1)
        if not end_time:
            end_time = datetime.utcnow()
        
        events = self.query(start_time=start_time, end_time=end_time, limit=10000)
        
        by_type = {}
        by_outcome = {}
        by_severity = {}
        
        for event in events:
            by_type[event.event_type.value] = by_type.get(event.event_type.value, 0) + 1
            by_outcome[event.outcome.value] = by_outcome.get(event.outcome.value, 0) + 1
            by_severity[event.severity.value] = by_severity.get(event.severity.value, 0) + 1
        
        return {
            "total_events": len(events),
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
            "by_type": by_type,
            "by_outcome": by_outcome,
            "by_severity": by_severity,
        }
    
    def add_handler(self, handler: Callable):
        """Add event handler."""
        self._handlers.append(handler)
    
    def add_filter(self, filter_fn: Callable):
        """Add event filter."""
        self._filters.append(filter_fn)
    
    def export(
        self,
        start_time: datetime = None,
        end_time: datetime = None,
        format: str = "json",
    ) -> str:
        """Export audit logs."""
        events = self.query(start_time=start_time, end_time=end_time, limit=100000)
        
        if format == "json":
            return json.dumps([e.to_dict() for e in events], indent=2)
        elif format == "csv":
            return self._to_csv(events)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _to_csv(self, events: List[AuditEvent]) -> str:
        """Convert events to CSV."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "id", "timestamp", "event_type", "outcome", "severity",
            "user_id", "customer_id", "resource_type", "resource_id",
            "action", "description", "ip_address",
        ])
        
        # Rows
        for event in events:
            writer.writerow([
                event.id, event.timestamp.isoformat(), event.event_type.value,
                event.outcome.value, event.severity.value,
                event.user_id, event.customer_id, event.resource_type, event.resource_id,
                event.action, event.description, event.ip_address,
            ])
        
        return output.getvalue()
    
    def _redact_sensitive(self, event: AuditEvent) -> AuditEvent:
        """Redact sensitive data from event."""
        if event.details:
            event.details = self._redact_dict(event.details)
        if event.old_values:
            event.old_values = self._redact_dict(event.old_values)
        if event.new_values:
            event.new_values = self._redact_dict(event.new_values)
        return event
    
    def _redact_dict(self, data: Dict) -> Dict:
        """Redact sensitive fields in dictionary."""
        result = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in self.REDACTED_FIELDS):
                result[key] = "[REDACTED]"
            elif isinstance(value, dict):
                result[key] = self._redact_dict(value)
            else:
                result[key] = value
        return result
    
    def _severity_to_level(self, severity: AuditSeverity) -> int:
        """Convert severity to logging level."""
        mapping = {
            AuditSeverity.DEBUG: logging.DEBUG,
            AuditSeverity.INFO: logging.INFO,
            AuditSeverity.WARNING: logging.WARNING,
            AuditSeverity.ERROR: logging.ERROR,
            AuditSeverity.CRITICAL: logging.CRITICAL,
        }
        return mapping.get(severity, logging.INFO)


# Global audit logger
audit_logger = AuditLogger()


def get_audit_logger() -> AuditLogger:
    """Get audit logger instance."""
    return audit_logger
```

---

## File 3: Audit Storage
**Path:** `backend/app/security/audit/storage.py`

```python
"""
Audit Storage
Persistent storage for audit logs
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, JSON, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID, INET
import uuid
import logging

from app.database import Base
from app.security.audit.events import AuditEvent, AuditEventType, AuditOutcome, AuditSeverity

logger = logging.getLogger(__name__)


class AuditLogModel(Base):
    """Database model for audit logs."""
    
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    outcome = Column(String(20), nullable=False)
    severity = Column(String(20), nullable=False)
    
    user_id = Column(UUID(as_uuid=True), index=True)
    customer_id = Column(UUID(as_uuid=True), index=True)
    session_id = Column(UUID(as_uuid=True))
    
    ip_address = Column(INET)
    user_agent = Column(String(500))
    request_id = Column(UUID(as_uuid=True))
    
    resource_type = Column(String(50), index=True)
    resource_id = Column(UUID(as_uuid=True))
    
    action = Column(String(100))
    description = Column(String(500))
    details = Column(JSON, default={})
    
    old_values = Column(JSON)
    new_values = Column(JSON)
    
    # Indexes
    __table_args__ = (
        Index('ix_audit_user_time', 'user_id', 'timestamp'),
        Index('ix_audit_customer_time', 'customer_id', 'timestamp'),
        Index('ix_audit_type_time', 'event_type', 'timestamp'),
    )
    
    def to_event(self) -> AuditEvent:
        """Convert to AuditEvent."""
        return AuditEvent(
            id=str(self.id),
            timestamp=self.timestamp,
            event_type=AuditEventType(self.event_type),
            outcome=AuditOutcome(self.outcome),
            severity=AuditSeverity(self.severity),
            user_id=str(self.user_id) if self.user_id else None,
            customer_id=str(self.customer_id) if self.customer_id else None,
            session_id=str(self.session_id) if self.session_id else None,
            ip_address=str(self.ip_address) if self.ip_address else None,
            user_agent=self.user_agent,
            request_id=str(self.request_id) if self.request_id else None,
            resource_type=self.resource_type,
            resource_id=str(self.resource_id) if self.resource_id else None,
            action=self.action,
            description=self.description,
            details=self.details or {},
            old_values=self.old_values,
            new_values=self.new_values,
        )
    
    @classmethod
    def from_event(cls, event: AuditEvent) -> "AuditLogModel":
        """Create from AuditEvent."""
        return cls(
            id=uuid.UUID(event.id.replace("audit_", "")) if event.id.startswith("audit_") else uuid.uuid4(),
            timestamp=event.timestamp,
            event_type=event.event_type.value,
            outcome=event.outcome.value,
            severity=event.severity.value,
            user_id=uuid.UUID(event.user_id) if event.user_id else None,
            customer_id=uuid.UUID(event.customer_id) if event.customer_id else None,
            session_id=uuid.UUID(event.session_id) if event.session_id else None,
            ip_address=event.ip_address,
            user_agent=event.user_agent,
            request_id=uuid.UUID(event.request_id) if event.request_id else None,
            resource_type=event.resource_type,
            resource_id=uuid.UUID(event.resource_id) if event.resource_id else None,
            action=event.action,
            description=event.description,
            details=event.details,
            old_values=event.old_values,
            new_values=event.new_values,
        )


class AuditStorageService:
    """Service for persisting audit logs."""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def save(self, event: AuditEvent):
        """Save audit event to database."""
        try:
            record = AuditLogModel.from_event(event)
            self.db.add(record)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to save audit log: {e}")
            self.db.rollback()
    
    def query(
        self,
        event_type: str = None,
        user_id: str = None,
        customer_id: str = None,
        resource_type: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEvent]:
        """Query audit logs from database."""
        query = self.db.query(AuditLogModel)
        
        if event_type:
            query = query.filter(AuditLogModel.event_type == event_type)
        if user_id:
            query = query.filter(AuditLogModel.user_id == uuid.UUID(user_id))
        if customer_id:
            query = query.filter(AuditLogModel.customer_id == uuid.UUID(customer_id))
        if resource_type:
            query = query.filter(AuditLogModel.resource_type == resource_type)
        if start_time:
            query = query.filter(AuditLogModel.timestamp >= start_time)
        if end_time:
            query = query.filter(AuditLogModel.timestamp <= end_time)
        
        records = query.order_by(AuditLogModel.timestamp.desc()).offset(offset).limit(limit).all()
        
        return [r.to_event() for r in records]
    
    def cleanup(self, retention_days: int):
        """Delete audit logs older than retention period."""
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        
        try:
            deleted = self.db.query(AuditLogModel).filter(
                AuditLogModel.timestamp < cutoff
            ).delete()
            
            self.db.commit()
            logger.info(f"Cleaned up {deleted} old audit logs")
            return deleted
        except Exception as e:
            logger.error(f"Audit cleanup failed: {e}")
            self.db.rollback()
            return 0
```

---

## File 4: Audit Module Init
**Path:** `backend/app/security/audit/__init__.py`

```python
"""
Audit Module
Comprehensive audit logging
"""

from app.security.audit.events import (
    AuditEvent,
    AuditEventType,
    AuditOutcome,
    AuditSeverity,
)

from app.security.audit.logger import (
    AuditLogger,
    audit_logger,
    get_audit_logger,
)

from app.security.audit.storage import (
    AuditLogModel,
    AuditStorageService,
)


__all__ = [
    'AuditEvent',
    'AuditEventType',
    'AuditOutcome',
    'AuditSeverity',
    'AuditLogger',
    'audit_logger',
    'get_audit_logger',
    'AuditLogModel',
    'AuditStorageService',
]
```

---

## Summary Part 5

| File | Description | Lines |
|------|-------------|-------|
| `audit/events.py` | Audit event definitions | ~150 |
| `audit/logger.py` | Audit logging | ~280 |
| `audit/storage.py` | Persistent storage | ~170 |
| `audit/__init__.py` | Audit module exports | ~35 |
| **Total** | | **~635 lines** |
