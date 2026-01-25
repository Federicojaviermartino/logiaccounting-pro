"""
Audit log storage for LogiAccounting Pro.
"""

import hashlib
import json
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from uuid import uuid4

from .events import (
    AuditEvent,
    AuditEventType,
    AuditOutcome,
    AuditSeverity,
    AuditCategory,
)


@dataclass
class AuditLogModel:
    """Audit log database model."""

    id: str
    event_type: str
    outcome: str
    severity: str
    category: str
    timestamp: datetime
    organization_id: Optional[str] = None
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    action: str = ""
    message: str = ""
    changes: Optional[Dict[str, Any]] = None
    details: Dict[str, Any] = field(default_factory=dict)
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    duration_ms: Optional[int] = None
    compliance_tags: List[str] = field(default_factory=list)
    sequence_number: int = 0
    previous_hash: Optional[str] = None
    data_hash: Optional[str] = None
    is_archived: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_event(cls, event: AuditEvent, organization_id: Optional[str] = None) -> "AuditLogModel":
        """Create model from audit event."""
        actor = event.actor
        target = event.target

        return cls(
            id=event.id,
            event_type=event.event_type.value,
            outcome=event.outcome.value,
            severity=event.severity.value,
            category=event.category.value,
            timestamp=event.timestamp,
            organization_id=organization_id or (actor.organization_id if actor else None),
            tenant_id=actor.tenant_id if actor else None,
            user_id=actor.user_id if actor else None,
            user_email=actor.email if actor else None,
            user_role=actor.role if actor else None,
            ip_address=actor.ip_address if actor else None,
            user_agent=actor.user_agent if actor else None,
            entity_type=target.entity_type if target else None,
            entity_id=target.entity_id if target else None,
            entity_name=target.entity_name if target else None,
            action=event.action,
            message=event.message,
            changes=event.changes.to_dict() if event.changes else None,
            details=event.details,
            request_id=event.request_id,
            correlation_id=event.correlation_id,
            duration_ms=event.duration_ms,
            compliance_tags=event.compliance_tags,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "outcome": self.outcome,
            "severity": self.severity,
            "category": self.category,
            "timestamp": self.timestamp.isoformat(),
            "organization_id": self.organization_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "user_role": self.user_role,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "action": self.action,
            "message": self.message,
            "changes": self.changes,
            "details": self.details,
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "duration_ms": self.duration_ms,
            "compliance_tags": self.compliance_tags,
            "sequence_number": self.sequence_number,
            "previous_hash": self.previous_hash,
            "data_hash": self.data_hash,
            "is_archived": self.is_archived,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class AuditQueryFilter:
    """Filter criteria for audit log queries."""

    organization_id: Optional[str] = None
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    event_types: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    severities: Optional[List[str]] = None
    outcomes: Optional[List[str]] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    ip_address: Optional[str] = None
    compliance_tags: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search_text: Optional[str] = None


class AuditStorageService:
    """Service for storing and querying audit logs."""

    def __init__(self):
        self._logs: List[AuditLogModel] = []
        self._sequence_counters: Dict[str, int] = {}
        self._hash_chain: Dict[str, str] = {}

    def _get_next_sequence(self, organization_id: str) -> int:
        """Get next sequence number for organization."""
        org_id = organization_id or "global"
        if org_id not in self._sequence_counters:
            self._sequence_counters[org_id] = 0
        self._sequence_counters[org_id] += 1
        return self._sequence_counters[org_id]

    def _get_previous_hash(self, organization_id: str) -> Optional[str]:
        """Get hash of previous entry for chain linking."""
        org_id = organization_id or "global"
        return self._hash_chain.get(org_id)

    def _compute_hash(self, log: AuditLogModel) -> str:
        """Compute SHA-256 hash of audit log."""
        hash_data = {
            "id": log.id,
            "event_type": log.event_type,
            "timestamp": log.timestamp.isoformat(),
            "organization_id": log.organization_id,
            "user_id": log.user_id,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "action": log.action,
            "changes": log.changes,
            "sequence_number": log.sequence_number,
            "previous_hash": log.previous_hash,
        }
        json_str = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def store(self, event: AuditEvent, organization_id: Optional[str] = None) -> AuditLogModel:
        """Store an audit event."""
        log = AuditLogModel.from_event(event, organization_id)

        org_id = log.organization_id or "global"
        log.sequence_number = self._get_next_sequence(org_id)
        log.previous_hash = self._get_previous_hash(org_id)
        log.data_hash = self._compute_hash(log)

        self._hash_chain[org_id] = log.data_hash
        self._logs.append(log)

        return log

    def store_batch(self, events: List[AuditEvent], organization_id: Optional[str] = None) -> List[AuditLogModel]:
        """Store multiple audit events."""
        logs = []
        for event in events:
            log = self.store(event, organization_id)
            logs.append(log)
        return logs

    def get_by_id(self, log_id: str) -> Optional[AuditLogModel]:
        """Get audit log by ID."""
        return next((log for log in self._logs if log.id == log_id), None)

    def query(
        self,
        filters: AuditQueryFilter,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "timestamp",
        order_desc: bool = True,
    ) -> Tuple[List[AuditLogModel], int]:
        """Query audit logs with filters."""
        results = self._logs.copy()

        if filters.organization_id:
            results = [l for l in results if l.organization_id == filters.organization_id]
        if filters.tenant_id:
            results = [l for l in results if l.tenant_id == filters.tenant_id]
        if filters.user_id:
            results = [l for l in results if l.user_id == filters.user_id]
        if filters.user_email:
            results = [l for l in results if l.user_email == filters.user_email]
        if filters.event_types:
            results = [l for l in results if l.event_type in filters.event_types]
        if filters.categories:
            results = [l for l in results if l.category in filters.categories]
        if filters.severities:
            results = [l for l in results if l.severity in filters.severities]
        if filters.outcomes:
            results = [l for l in results if l.outcome in filters.outcomes]
        if filters.entity_type:
            results = [l for l in results if l.entity_type == filters.entity_type]
        if filters.entity_id:
            results = [l for l in results if l.entity_id == filters.entity_id]
        if filters.ip_address:
            results = [l for l in results if l.ip_address == filters.ip_address]
        if filters.compliance_tags:
            results = [l for l in results if any(t in l.compliance_tags for t in filters.compliance_tags)]
        if filters.start_date:
            results = [l for l in results if l.timestamp >= filters.start_date]
        if filters.end_date:
            results = [l for l in results if l.timestamp <= filters.end_date]
        if filters.search_text:
            search = filters.search_text.lower()
            results = [
                l for l in results
                if search in (l.entity_name or "").lower() or
                   search in (l.user_email or "").lower() or
                   search in l.event_type.lower() or
                   search in l.action.lower() or
                   search in l.message.lower()
            ]

        total = len(results)

        if order_by == "timestamp":
            results = sorted(results, key=lambda l: l.timestamp, reverse=order_desc)
        elif order_by == "severity":
            severity_order = ["emergency", "alert", "critical", "error", "warning", "notice", "info", "debug"]
            results = sorted(
                results,
                key=lambda l: severity_order.index(l.severity) if l.severity in severity_order else 99,
                reverse=not order_desc
            )
        elif order_by == "sequence_number":
            results = sorted(results, key=lambda l: l.sequence_number, reverse=order_desc)

        return results[offset:offset + limit], total

    def get_entity_history(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 50,
    ) -> List[AuditLogModel]:
        """Get audit history for an entity."""
        results = [
            l for l in self._logs
            if l.entity_type == entity_type and l.entity_id == entity_id
        ]
        results = sorted(results, key=lambda l: l.timestamp, reverse=True)
        return results[:limit]

    def get_user_activity(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditLogModel]:
        """Get activity history for a user."""
        results = [l for l in self._logs if l.user_id == user_id]

        if start_date:
            results = [l for l in results if l.timestamp >= start_date]
        if end_date:
            results = [l for l in results if l.timestamp <= end_date]

        results = sorted(results, key=lambda l: l.timestamp, reverse=True)
        return results[:limit]

    def verify_integrity(self, log_id: str) -> bool:
        """Verify hash integrity of a single log entry."""
        log = self.get_by_id(log_id)
        if not log:
            return False
        return log.data_hash == self._compute_hash(log)

    def verify_chain(
        self,
        organization_id: str,
        start_seq: Optional[int] = None,
        end_seq: Optional[int] = None,
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Verify audit log chain integrity."""
        logs = sorted(
            [l for l in self._logs if l.organization_id == organization_id],
            key=lambda l: l.sequence_number
        )

        if start_seq:
            logs = [l for l in logs if l.sequence_number >= start_seq]
        if end_seq:
            logs = [l for l in logs if l.sequence_number <= end_seq]

        issues = []
        previous_hash = None
        expected_sequence = logs[0].sequence_number if logs else 1

        for log in logs:
            if log.sequence_number != expected_sequence:
                issues.append({
                    "type": "sequence_gap",
                    "log_id": log.id,
                    "expected": expected_sequence,
                    "actual": log.sequence_number,
                })

            if log.data_hash != self._compute_hash(log):
                issues.append({
                    "type": "hash_mismatch",
                    "log_id": log.id,
                    "sequence": log.sequence_number,
                })

            if previous_hash and log.previous_hash != previous_hash:
                issues.append({
                    "type": "chain_broken",
                    "log_id": log.id,
                    "sequence": log.sequence_number,
                })

            previous_hash = log.data_hash
            expected_sequence = log.sequence_number + 1

        return len(issues) == 0, issues

    def get_statistics(
        self,
        organization_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get audit log statistics."""
        logs = [l for l in self._logs if l.organization_id == organization_id]

        if start_date:
            logs = [l for l in logs if l.timestamp >= start_date]
        if end_date:
            logs = [l for l in logs if l.timestamp <= end_date]

        by_type = {}
        by_category = {}
        by_severity = {}
        by_outcome = {}
        by_user = {}

        for log in logs:
            by_type[log.event_type] = by_type.get(log.event_type, 0) + 1
            by_category[log.category] = by_category.get(log.category, 0) + 1
            by_severity[log.severity] = by_severity.get(log.severity, 0) + 1
            by_outcome[log.outcome] = by_outcome.get(log.outcome, 0) + 1
            if log.user_id:
                by_user[log.user_id] = by_user.get(log.user_id, 0) + 1

        return {
            "total_events": len(logs),
            "by_event_type": by_type,
            "by_category": by_category,
            "by_severity": by_severity,
            "by_outcome": by_outcome,
            "by_user": by_user,
            "unique_users": len(by_user),
            "date_range": {
                "start": min(l.timestamp for l in logs).isoformat() if logs else None,
                "end": max(l.timestamp for l in logs).isoformat() if logs else None,
            },
        }

    def archive_old_logs(
        self,
        organization_id: str,
        older_than_days: int = 90,
    ) -> int:
        """Mark old logs as archived."""
        cutoff = datetime.utcnow() - timedelta(days=older_than_days)
        count = 0

        for log in self._logs:
            if log.organization_id == organization_id and log.timestamp < cutoff and not log.is_archived:
                log.is_archived = True
                count += 1

        return count

    def delete_archived(self, organization_id: str) -> int:
        """Delete archived logs."""
        initial_count = len(self._logs)
        self._logs = [
            l for l in self._logs
            if not (l.organization_id == organization_id and l.is_archived)
        ]
        return initial_count - len(self._logs)

    def export_logs(
        self,
        filters: AuditQueryFilter,
        format: str = "json",
    ) -> str:
        """Export audit logs in specified format."""
        logs, _ = self.query(filters, limit=10000)

        if format == "json":
            return json.dumps([l.to_dict() for l in logs], indent=2, default=str)

        if format == "csv":
            import csv
            from io import StringIO
            output = StringIO()
            if logs:
                writer = csv.DictWriter(output, fieldnames=logs[0].to_dict().keys())
                writer.writeheader()
                for log in logs:
                    writer.writerow(log.to_dict())
            return output.getvalue()

        raise ValueError(f"Unsupported export format: {format}")


_audit_storage: Optional[AuditStorageService] = None


def get_audit_storage() -> AuditStorageService:
    """Get the global audit storage instance."""
    global _audit_storage
    if _audit_storage is None:
        _audit_storage = AuditStorageService()
    return _audit_storage


def set_audit_storage(storage: AuditStorageService) -> None:
    """Set the global audit storage instance."""
    global _audit_storage
    _audit_storage = storage
