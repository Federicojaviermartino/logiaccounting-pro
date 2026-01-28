"""
Audit & Compliance Data Store
Phase 15 - Audit trail, compliance, and regulatory framework
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
from typing import Optional, List, Dict, Any
from uuid import uuid4
import hashlib
import json


class AuditLogStore:
    """
    Immutable audit log store with hash chain integrity.
    All changes are tracked with cryptographic verification.
    """

    def __init__(self):
        self._data: List[Dict[str, Any]] = []
        self._sequence_counters: Dict[str, int] = {}  # org_id -> sequence

    def _get_next_sequence(self, organization_id: str) -> int:
        """Get next sequence number for organization"""
        if organization_id not in self._sequence_counters:
            self._sequence_counters[organization_id] = 0
        self._sequence_counters[organization_id] += 1
        return self._sequence_counters[organization_id]

    def _get_previous_hash(self, organization_id: str) -> Optional[str]:
        """Get hash of previous entry for chain linking"""
        org_logs = [l for l in self._data if l.get("organization_id") == organization_id]
        if org_logs:
            return org_logs[-1].get("data_hash")
        return None

    def _compute_hash(self, data: Dict) -> str:
        """Compute SHA-256 hash of audit data"""
        hash_data = {
            'event_type': data.get('event_type'),
            'event_category': data.get('event_category'),
            'entity_type': data.get('entity_type'),
            'entity_id': data.get('entity_id'),
            'user_id': data.get('user_id'),
            'action': data.get('action'),
            'changes': data.get('changes'),
            'occurred_at': data.get('occurred_at'),
            'previous_hash': data.get('previous_hash'),
            'sequence_number': data.get('sequence_number'),
        }
        json_str = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def create(self, data: Dict) -> Dict:
        """Create audit log entry (immutable)"""
        organization_id = data.get("organization_id")
        sequence_number = self._get_next_sequence(organization_id)
        previous_hash = self._get_previous_hash(organization_id)

        occurred_at = data.get("occurred_at", datetime.utcnow().isoformat())

        item = {
            "id": str(uuid4()),
            **data,
            "sequence_number": sequence_number,
            "previous_hash": previous_hash,
            "occurred_at": occurred_at,
            "recorded_at": datetime.utcnow().isoformat(),
            "is_archived": False,
        }

        # Compute and add hash
        item["data_hash"] = self._compute_hash(item)

        self._data.append(item)
        return item

    def find_all(self, filters: Optional[Dict] = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Find audit logs with filters"""
        results = sorted(self._data, key=lambda x: x.get("occurred_at", ""), reverse=True)

        if filters:
            if filters.get("organization_id"):
                results = [l for l in results if l.get("organization_id") == filters["organization_id"]]
            if filters.get("event_type"):
                results = [l for l in results if l.get("event_type") == filters["event_type"]]
            if filters.get("event_category"):
                results = [l for l in results if l.get("event_category") == filters["event_category"]]
            if filters.get("severity"):
                results = [l for l in results if l.get("severity") == filters["severity"]]
            if filters.get("user_id"):
                results = [l for l in results if l.get("user_id") == filters["user_id"]]
            if filters.get("entity_type"):
                results = [l for l in results if l.get("entity_type") == filters["entity_type"]]
            if filters.get("entity_id"):
                results = [l for l in results if l.get("entity_id") == filters["entity_id"]]
            if filters.get("action"):
                results = [l for l in results if l.get("action") == filters["action"]]
            if filters.get("from_date"):
                from_date = filters["from_date"]
                results = [l for l in results if l.get("occurred_at", "") >= from_date]
            if filters.get("to_date"):
                to_date = filters["to_date"]
                results = [l for l in results if l.get("occurred_at", "") <= to_date]
            if filters.get("search"):
                search = filters["search"].lower()
                results = [l for l in results if
                          search in l.get("entity_name", "").lower() or
                          search in l.get("user_email", "").lower() or
                          search in l.get("event_type", "").lower()]
            if filters.get("compliance_tags"):
                tags = filters["compliance_tags"]
                results = [l for l in results if
                          any(t in l.get("compliance_tags", []) for t in tags)]

        return results[offset:offset + limit]

    def find_by_id(self, log_id: str) -> Optional[Dict]:
        """Find audit log by ID"""
        return next((l for l in self._data if l["id"] == log_id), None)

    def count(self, filters: Optional[Dict] = None) -> int:
        """Count audit logs matching filters"""
        return len(self.find_all(filters, limit=100000))

    def verify_integrity(self, log_id: str) -> bool:
        """Verify hash integrity of a single log entry"""
        log = self.find_by_id(log_id)
        if not log:
            return False
        return log.get("data_hash") == self._compute_hash(log)

    def verify_chain(self, organization_id: str, start_seq: int = None, end_seq: int = None) -> tuple:
        """Verify audit log chain integrity"""
        logs = sorted(
            [l for l in self._data if l.get("organization_id") == organization_id],
            key=lambda x: x.get("sequence_number", 0)
        )

        if start_seq:
            logs = [l for l in logs if l.get("sequence_number", 0) >= start_seq]
        if end_seq:
            logs = [l for l in logs if l.get("sequence_number", 0) <= end_seq]

        issues = []
        previous_hash = None
        expected_sequence = logs[0].get("sequence_number", 1) if logs else 1

        for log in logs:
            # Check sequence continuity
            if log.get("sequence_number") != expected_sequence:
                issues.append({
                    "type": "sequence_gap",
                    "log_id": log["id"],
                    "expected": expected_sequence,
                    "actual": log.get("sequence_number")
                })

            # Check hash integrity
            if log.get("data_hash") != self._compute_hash(log):
                issues.append({
                    "type": "hash_mismatch",
                    "log_id": log["id"],
                    "sequence": log.get("sequence_number")
                })

            # Check chain linkage
            if previous_hash and log.get("previous_hash") != previous_hash:
                issues.append({
                    "type": "chain_broken",
                    "log_id": log["id"],
                    "sequence": log.get("sequence_number")
                })

            previous_hash = log.get("data_hash")
            expected_sequence = log.get("sequence_number", 0) + 1

        return len(issues) == 0, issues

    def get_chain_status(self, organization_id: str) -> Dict:
        """Get chain status summary"""
        logs = [l for l in self._data if l.get("organization_id") == organization_id]

        if not logs:
            return {
                "total_entries": 0,
                "first_sequence": None,
                "last_sequence": None,
                "first_timestamp": None,
                "last_timestamp": None,
                "has_sequence_gaps": False,
                "chain_hash": None
            }

        sorted_logs = sorted(logs, key=lambda x: x.get("sequence_number", 0))
        first = sorted_logs[0]
        last = sorted_logs[-1]

        expected_count = last.get("sequence_number", 0) - first.get("sequence_number", 0) + 1

        return {
            "total_entries": len(logs),
            "first_sequence": first.get("sequence_number"),
            "last_sequence": last.get("sequence_number"),
            "first_timestamp": first.get("occurred_at"),
            "last_timestamp": last.get("occurred_at"),
            "has_sequence_gaps": len(logs) != expected_count,
            "chain_hash": last.get("data_hash")
        }


class ChangeHistoryStore:
    """Store for entity change history with before/after snapshots"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []
        self._version_counters: Dict[str, int] = {}  # entity_key -> version

    def _get_entity_key(self, entity_type: str, entity_id: str) -> str:
        return f"{entity_type}:{entity_id}"

    def _get_next_version(self, entity_type: str, entity_id: str) -> int:
        key = self._get_entity_key(entity_type, entity_id)
        if key not in self._version_counters:
            self._version_counters[key] = 0
        self._version_counters[key] += 1
        return self._version_counters[key]

    def create(self, data: Dict) -> Dict:
        """Create change history entry"""
        entity_type = data.get("entity_type")
        entity_id = data.get("entity_id")

        item = {
            "id": str(uuid4()),
            **data,
            "version_number": self._get_next_version(entity_type, entity_id),
            "created_at": datetime.utcnow().isoformat()
        }
        self._data.append(item)
        return item

    def find_by_id(self, history_id: str) -> Optional[Dict]:
        return next((h for h in self._data if h["id"] == history_id), None)

    def find_entity_history(self, entity_type: str, entity_id: str, limit: int = 50) -> List[Dict]:
        """Get change history for an entity"""
        results = [
            h for h in self._data
            if h.get("entity_type") == entity_type and h.get("entity_id") == entity_id
        ]
        results = sorted(results, key=lambda x: x.get("version_number", 0), reverse=True)
        return results[:limit]

    def find_version(self, entity_type: str, entity_id: str, version: int) -> Optional[Dict]:
        """Get specific version"""
        return next(
            (h for h in self._data
             if h.get("entity_type") == entity_type and
                h.get("entity_id") == entity_id and
                h.get("version_number") == version),
            None
        )

    def get_diff(self, history: Dict) -> Dict:
        """Get differences between before and after snapshots"""
        before = history.get("before_snapshot") or {}
        after = history.get("after_snapshot") or {}

        diff = {}
        all_keys = set(before.keys()) | set(after.keys())

        for key in all_keys:
            old_val = before.get(key)
            new_val = after.get(key)
            if old_val != new_val:
                diff[key] = {"old": old_val, "new": new_val}

        return diff


class AccessLogStore:
    """Store for authentication and access events"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []

    def create(self, data: Dict) -> Dict:
        item = {
            "id": str(uuid4()),
            **data,
            "occurred_at": data.get("occurred_at", datetime.utcnow().isoformat())
        }
        self._data.append(item)
        return item

    def find_all(self, filters: Optional[Dict] = None, limit: int = 100) -> List[Dict]:
        results = sorted(self._data, key=lambda x: x.get("occurred_at", ""), reverse=True)

        if filters:
            if filters.get("organization_id"):
                results = [l for l in results if l.get("organization_id") == filters["organization_id"]]
            if filters.get("user_id"):
                results = [l for l in results if l.get("user_id") == filters["user_id"]]
            if filters.get("user_email"):
                results = [l for l in results if l.get("user_email") == filters["user_email"]]
            if filters.get("event_type"):
                results = [l for l in results if l.get("event_type") == filters["event_type"]]
            if filters.get("success") is not None:
                results = [l for l in results if l.get("success") == filters["success"]]
            if filters.get("ip_address"):
                results = [l for l in results if l.get("ip_address") == filters["ip_address"]]
            if filters.get("from_date"):
                results = [l for l in results if l.get("occurred_at", "") >= filters["from_date"]]
            if filters.get("to_date"):
                results = [l for l in results if l.get("occurred_at", "") <= filters["to_date"]]

        return results[:limit]

    def count_failed_attempts(self, ip_address: str = None, user_email: str = None, minutes: int = 30) -> int:
        """Count recent failed login attempts"""
        since = (datetime.utcnow() - timedelta(minutes=minutes)).isoformat()

        results = [
            l for l in self._data
            if l.get("event_type") == "login_failed" and
               l.get("occurred_at", "") >= since
        ]

        if ip_address:
            results = [l for l in results if l.get("ip_address") == ip_address]
        if user_email:
            results = [l for l in results if l.get("user_email") == user_email]

        return len(results)

    def log_login_success(self, user_id: str, organization_id: str, ip_address: str, **kwargs) -> Dict:
        """Log successful login"""
        return self.create({
            "organization_id": organization_id,
            "event_type": "login_success",
            "user_id": user_id,
            "ip_address": ip_address,
            "success": True,
            **kwargs
        })

    def log_login_failed(self, user_email: str, ip_address: str, failure_reason: str, **kwargs) -> Dict:
        """Log failed login attempt"""
        return self.create({
            "event_type": "login_failed",
            "user_email": user_email,
            "ip_address": ip_address,
            "success": False,
            "failure_reason": failure_reason,
            **kwargs
        })


class AuditAlertStore:
    """Store for audit alerts"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []

    def create(self, data: Dict) -> Dict:
        item = {
            "id": str(uuid4()),
            **data,
            "status": data.get("status", "open"),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        self._data.append(item)
        return item

    def find_by_id(self, alert_id: str) -> Optional[Dict]:
        return next((a for a in self._data if a["id"] == alert_id), None)

    def find_all(self, filters: Optional[Dict] = None, limit: int = 50) -> List[Dict]:
        results = sorted(self._data, key=lambda x: x.get("created_at", ""), reverse=True)

        if filters:
            if filters.get("organization_id"):
                results = [a for a in results if a.get("organization_id") == filters["organization_id"]]
            if filters.get("status"):
                results = [a for a in results if a.get("status") == filters["status"]]
            if filters.get("severity"):
                results = [a for a in results if a.get("severity") == filters["severity"]]
            if filters.get("alert_type"):
                results = [a for a in results if a.get("alert_type") == filters["alert_type"]]

        return results[:limit]

    def update(self, alert_id: str, data: Dict) -> Optional[Dict]:
        for i, alert in enumerate(self._data):
            if alert["id"] == alert_id:
                self._data[i] = {
                    **alert,
                    **data,
                    "updated_at": datetime.utcnow().isoformat()
                }
                return self._data[i]
        return None

    def acknowledge(self, alert_id: str, user_id: str) -> Optional[Dict]:
        return self.update(alert_id, {
            "status": "acknowledged",
            "assigned_to": user_id
        })

    def resolve(self, alert_id: str, user_id: str, notes: str = None) -> Optional[Dict]:
        return self.update(alert_id, {
            "status": "resolved",
            "resolved_by": user_id,
            "resolved_at": datetime.utcnow().isoformat(),
            "resolution_notes": notes
        })

    def dismiss(self, alert_id: str, user_id: str, reason: str = None) -> Optional[Dict]:
        return self.update(alert_id, {
            "status": "dismissed",
            "resolved_by": user_id,
            "resolved_at": datetime.utcnow().isoformat(),
            "resolution_notes": reason
        })

    def get_stats(self, organization_id: str, days: int = 30) -> Dict:
        """Get alert statistics"""
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        alerts = [
            a for a in self._data
            if a.get("organization_id") == organization_id and
               a.get("created_at", "") >= since
        ]

        return {
            "total_30d": len(alerts),
            "open": len([a for a in alerts if a.get("status") == "open"]),
            "acknowledged": len([a for a in alerts if a.get("status") == "acknowledged"]),
            "investigating": len([a for a in alerts if a.get("status") == "investigating"]),
            "resolved": len([a for a in alerts if a.get("status") == "resolved"]),
            "dismissed": len([a for a in alerts if a.get("status") == "dismissed"]),
            "by_severity": {
                "critical": len([a for a in alerts if a.get("severity") == "critical"]),
                "high": len([a for a in alerts if a.get("severity") == "high"]),
                "medium": len([a for a in alerts if a.get("severity") == "medium"]),
                "low": len([a for a in alerts if a.get("severity") == "low"]),
            }
        }


class AlertRuleStore:
    """Store for configurable alert rules"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []

    def create(self, data: Dict) -> Dict:
        item = {
            "id": str(uuid4()),
            **data,
            "is_active": data.get("is_active", True),
            "cooldown_minutes": data.get("cooldown_minutes", 60),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        self._data.append(item)
        return item

    def find_by_id(self, rule_id: str) -> Optional[Dict]:
        return next((r for r in self._data if r["id"] == rule_id), None)

    def find_all(self, filters: Optional[Dict] = None) -> List[Dict]:
        results = self._data.copy()

        if filters:
            if filters.get("organization_id"):
                results = [r for r in results if r.get("organization_id") == filters["organization_id"]]
            if filters.get("is_active") is not None:
                results = [r for r in results if r.get("is_active") == filters["is_active"]]
            if filters.get("alert_type"):
                results = [r for r in results if r.get("alert_type") == filters["alert_type"]]

        return results

    def update(self, rule_id: str, data: Dict) -> Optional[Dict]:
        for i, rule in enumerate(self._data):
            if rule["id"] == rule_id:
                self._data[i] = {
                    **rule,
                    **data,
                    "updated_at": datetime.utcnow().isoformat()
                }
                return self._data[i]
        return None

    def delete(self, rule_id: str) -> bool:
        for i, rule in enumerate(self._data):
            if rule["id"] == rule_id:
                self._data.pop(i)
                return True
        return False

    def can_trigger(self, rule: Dict) -> bool:
        """Check if rule can trigger (not in cooldown)"""
        if not rule.get("is_active"):
            return False

        last_triggered = rule.get("last_triggered_at")
        if not last_triggered:
            return True

        cooldown = rule.get("cooldown_minutes", 60)
        cooldown_end = datetime.fromisoformat(last_triggered) + timedelta(minutes=cooldown)
        return datetime.utcnow() >= cooldown_end

    def record_trigger(self, rule_id: str) -> Optional[Dict]:
        """Record that rule was triggered"""
        return self.update(rule_id, {"last_triggered_at": datetime.utcnow().isoformat()})


class RetentionPolicyStore:
    """Store for data retention policies"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []

    def create(self, data: Dict) -> Dict:
        item = {
            "id": str(uuid4()),
            **data,
            "is_active": data.get("is_active", True),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        self._data.append(item)
        return item

    def find_by_id(self, policy_id: str) -> Optional[Dict]:
        return next((p for p in self._data if p["id"] == policy_id), None)

    def find_all(self, filters: Optional[Dict] = None) -> List[Dict]:
        results = self._data.copy()

        if filters:
            if filters.get("organization_id"):
                results = [p for p in results if p.get("organization_id") == filters["organization_id"]]
            if filters.get("is_active") is not None:
                results = [p for p in results if p.get("is_active") == filters["is_active"]]

        return results

    def update(self, policy_id: str, data: Dict) -> Optional[Dict]:
        for i, policy in enumerate(self._data):
            if policy["id"] == policy_id:
                self._data[i] = {
                    **policy,
                    **data,
                    "updated_at": datetime.utcnow().isoformat()
                }
                return self._data[i]
        return None

    def delete(self, policy_id: str) -> bool:
        for i, policy in enumerate(self._data):
            if policy["id"] == policy_id:
                self._data.pop(i)
                return True
        return False


class ComplianceCheckStore:
    """Store for compliance check results"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []

    def create(self, data: Dict) -> Dict:
        item = {
            "id": str(uuid4()),
            **data,
            "checked_at": data.get("checked_at", datetime.utcnow().isoformat()),
            "created_at": datetime.utcnow().isoformat()
        }
        self._data.append(item)
        return item

    def find_by_id(self, check_id: str) -> Optional[Dict]:
        return next((c for c in self._data if c["id"] == check_id), None)

    def find_all(self, filters: Optional[Dict] = None, limit: int = 100) -> List[Dict]:
        results = sorted(self._data, key=lambda x: x.get("checked_at", ""), reverse=True)

        if filters:
            if filters.get("organization_id"):
                results = [c for c in results if c.get("organization_id") == filters["organization_id"]]
            if filters.get("framework"):
                results = [c for c in results if c.get("framework") == filters["framework"]]
            if filters.get("status"):
                results = [c for c in results if c.get("status") == filters["status"]]
            if filters.get("control_id"):
                results = [c for c in results if c.get("control_id") == filters["control_id"]]

        return results[:limit]

    def find_latest_by_framework(self, organization_id: str, framework: str) -> List[Dict]:
        """Get latest check results for a framework"""
        results = [
            c for c in self._data
            if c.get("organization_id") == organization_id and
               c.get("framework") == framework
        ]

        # Group by control_id and get latest
        latest = {}
        for check in results:
            control_id = check.get("control_id")
            if control_id not in latest or check.get("checked_at", "") > latest[control_id].get("checked_at", ""):
                latest[control_id] = check

        return list(latest.values())

    def update(self, check_id: str, data: Dict) -> Optional[Dict]:
        for i, check in enumerate(self._data):
            if check["id"] == check_id:
                self._data[i] = {**check, **data}
                return self._data[i]
        return None


# Global audit store instances
class AuditDatabase:
    """Container for all audit-related stores"""

    def __init__(self):
        self.audit_logs = AuditLogStore()
        self.change_history = ChangeHistoryStore()
        self.access_logs = AccessLogStore()
        self.alerts = AuditAlertStore()
        self.alert_rules = AlertRuleStore()
        self.retention_policies = RetentionPolicyStore()
        self.compliance_checks = ComplianceCheckStore()


# Global instance
audit_db = AuditDatabase()


def init_audit_database():
    """Initialize audit database with default data"""
    # Create default alert rules for demo organization
    default_rules = [
        {
            "organization_id": "org-demo-001",
            "name": "Multiple Failed Logins",
            "description": "Alert on multiple failed login attempts",
            "event_types": ["auth.login_failed"],
            "conditions": {"count": {">": 5}, "timeframe_minutes": 10},
            "alert_type": "brute_force",
            "severity": "high",
            "notification_channels": ["email", "in_app"],
        },
        {
            "organization_id": "org-demo-001",
            "name": "Bulk Data Delete",
            "description": "Alert on bulk data deletion",
            "event_types": ["entity.deleted"],
            "conditions": {"count": {">": 10}, "timeframe_minutes": 5},
            "alert_type": "bulk_delete",
            "severity": "critical",
            "notification_channels": ["email", "slack", "in_app"],
        },
        {
            "organization_id": "org-demo-001",
            "name": "Admin Role Assigned",
            "description": "Alert when admin role is assigned",
            "event_types": ["role.assigned"],
            "conditions": {"field_match": {"role": "admin"}},
            "alert_type": "permission_escalation",
            "severity": "medium",
            "notification_channels": ["email", "in_app"],
        },
        {
            "organization_id": "org-demo-001",
            "name": "Large Data Export",
            "description": "Alert on large data exports",
            "event_types": ["entity.exported", "data.exported"],
            "conditions": {},
            "alert_type": "data_export",
            "severity": "medium",
            "notification_channels": ["email"],
        },
    ]

    for rule in default_rules:
        audit_db.alert_rules.create(rule)

    # Create default retention policy
    audit_db.retention_policies.create({
        "organization_id": "org-demo-001",
        "name": "Standard Audit Retention",
        "description": "Retain audit logs for 7 years for compliance",
        "retention_days": 2555,  # ~7 years
        "archive_after_days": 365,
        "compliance_framework": "sox",
        "is_active": True,
    })

    # Create some sample audit logs
    sample_logs = [
        {
            "organization_id": "org-demo-001",
            "event_type": "entity.created",
            "event_category": "data_change",
            "severity": "info",
            "entity_type": "invoices",
            "entity_id": "inv-001",
            "entity_name": "Invoice #INV-2024-001",
            "user_id": "user-admin-001",
            "user_email": "admin@demo.com",
            "user_role": "admin",
            "action": "create",
            "ip_address": "192.168.1.100",
            "compliance_tags": ["sox", "soc2"],
            "metadata": {"amount": 1500.00, "client": "Acme Corp"}
        },
        {
            "organization_id": "org-demo-001",
            "event_type": "auth.login_success",
            "event_category": "authentication",
            "severity": "info",
            "user_id": "user-admin-001",
            "user_email": "admin@demo.com",
            "user_role": "admin",
            "action": "execute",
            "ip_address": "192.168.1.100",
            "compliance_tags": ["sox", "soc2"],
            "metadata": {"auth_method": "password", "mfa_used": True}
        },
        {
            "organization_id": "org-demo-001",
            "event_type": "entity.updated",
            "event_category": "data_change",
            "severity": "info",
            "entity_type": "materials",
            "entity_id": "mat-001",
            "entity_name": "Steel Beam A36",
            "user_id": "user-admin-001",
            "user_email": "admin@demo.com",
            "user_role": "admin",
            "action": "update",
            "ip_address": "192.168.1.100",
            "changes": {"quantity": {"old": 100, "new": 150}},
            "compliance_tags": ["sox"],
            "metadata": {}
        },
    ]

    for log in sample_logs:
        audit_db.audit_logs.create(log)

    logger.info("Audit database initialized with default data")
