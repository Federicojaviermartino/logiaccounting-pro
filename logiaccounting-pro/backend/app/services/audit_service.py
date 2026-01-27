"""
Advanced Audit Trail Service
Complete action logging for compliance
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import hashlib
import json


class AuditService:
    """Immutable audit logging system"""

    _instance = None
    _logs: List[dict] = []
    _counter = 0

    ACTION_TYPES = [
        "CREATE", "READ", "UPDATE", "DELETE",
        "LOGIN", "LOGOUT", "LOGIN_FAILED",
        "EXPORT", "IMPORT", "BULK_ACTION",
        "APPROVE", "REJECT",
        "SETTINGS_CHANGE", "PASSWORD_CHANGE",
        "API_CALL", "WEBHOOK_TRIGGER"
    ]

    ENTITY_TYPES = [
        "user", "material", "transaction", "payment",
        "project", "category", "location", "document",
        "approval", "budget", "recurring", "report",
        "settings", "api_key", "webhook"
    ]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._logs = []
            cls._counter = 0
        return cls._instance

    def log(
        self,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        user_role: Optional[str] = None,
        before: Optional[dict] = None,
        after: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        duration_ms: Optional[int] = None
    ) -> dict:
        """Create an immutable audit log entry"""
        self._counter += 1

        # Calculate changes if before/after provided
        changes = None
        if before and after:
            changes = self._calculate_changes(before, after)

        # Generate unique ID with hash for integrity
        timestamp = datetime.utcnow().isoformat()
        entry_data = f"{self._counter}{timestamp}{action}{entity_type}{entity_id}{user_id}"
        integrity_hash = hashlib.sha256(entry_data.encode()).hexdigest()[:16]

        log_entry = {
            "id": f"AUD-{self._counter:06d}",
            "hash": integrity_hash,
            "timestamp": timestamp,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "user_id": user_id,
            "user_email": user_email,
            "user_role": user_role,
            "changes": changes,
            "before": before,
            "after": after,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "session_id": session_id,
            "metadata": metadata or {},
            "duration_ms": duration_ms
        }

        # Append-only (immutable)
        self._logs.append(log_entry)

        return log_entry

    def _calculate_changes(self, before: dict, after: dict) -> dict:
        """Calculate diff between before and after states"""
        changes = {}

        all_keys = set(before.keys()) | set(after.keys())

        for key in all_keys:
            old_val = before.get(key)
            new_val = after.get(key)

            if old_val != new_val:
                changes[key] = {
                    "before": old_val,
                    "after": new_val
                }

        return changes if changes else None

    def get_log(self, log_id: str) -> Optional[dict]:
        """Get a specific log entry"""
        for log in self._logs:
            if log["id"] == log_id:
                return log
        return None

    def search(
        self,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> dict:
        """Search audit logs with filters"""
        results = self._logs.copy()

        # Apply filters
        if action:
            results = [l for l in results if l["action"] == action]
        if entity_type:
            results = [l for l in results if l["entity_type"] == entity_type]
        if entity_id:
            results = [l for l in results if l["entity_id"] == entity_id]
        if user_id:
            results = [l for l in results if l["user_id"] == user_id]
        if user_email:
            results = [l for l in results if l["user_email"] == user_email]
        if ip_address:
            results = [l for l in results if l["ip_address"] == ip_address]
        if date_from:
            results = [l for l in results if l["timestamp"] >= date_from]
        if date_to:
            results = [l for l in results if l["timestamp"] <= date_to]

        # Sort by timestamp descending (newest first)
        results = sorted(results, key=lambda x: x["timestamp"], reverse=True)

        total = len(results)
        paginated = results[offset:offset + limit]

        return {
            "logs": paginated,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }

    def get_entity_history(self, entity_type: str, entity_id: str) -> List[dict]:
        """Get complete history for an entity"""
        return sorted(
            [l for l in self._logs if l["entity_type"] == entity_type and l["entity_id"] == entity_id],
            key=lambda x: x["timestamp"],
            reverse=True
        )

    def get_user_activity(self, user_id: str, days: int = 30) -> List[dict]:
        """Get user activity for last N days"""
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        return sorted(
            [l for l in self._logs if l["user_id"] == user_id and l["timestamp"] >= cutoff],
            key=lambda x: x["timestamp"],
            reverse=True
        )

    def get_statistics(self, days: int = 30) -> dict:
        """Get audit statistics"""
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        recent = [l for l in self._logs if l["timestamp"] >= cutoff]

        # Count by action
        by_action = {}
        for log in recent:
            action = log["action"]
            by_action[action] = by_action.get(action, 0) + 1

        # Count by entity
        by_entity = {}
        for log in recent:
            entity = log["entity_type"]
            by_entity[entity] = by_entity.get(entity, 0) + 1

        # Count by user
        by_user = {}
        for log in recent:
            user = log["user_email"] or "system"
            by_user[user] = by_user.get(user, 0) + 1

        # Failed logins
        failed_logins = len([l for l in recent if l["action"] == "LOGIN_FAILED"])

        # Activity by hour
        by_hour = {str(i).zfill(2): 0 for i in range(24)}
        for log in recent:
            hour = log["timestamp"][11:13]
            by_hour[hour] = by_hour.get(hour, 0) + 1

        return {
            "total_logs": len(recent),
            "period_days": days,
            "by_action": by_action,
            "by_entity": by_entity,
            "by_user": dict(sorted(by_user.items(), key=lambda x: x[1], reverse=True)[:10]),
            "failed_logins": failed_logins,
            "by_hour": by_hour
        }

    def export(
        self,
        format: str = "json",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Any:
        """Export audit logs for compliance"""
        results = self._logs.copy()

        if date_from:
            results = [l for l in results if l["timestamp"] >= date_from]
        if date_to:
            results = [l for l in results if l["timestamp"] <= date_to]

        results = sorted(results, key=lambda x: x["timestamp"])

        if format == "json":
            return json.dumps(results, indent=2)

        if format == "csv":
            if not results:
                return "id,timestamp,action,entity_type,entity_id,user_email,ip_address\n"

            lines = ["id,timestamp,action,entity_type,entity_id,user_email,ip_address"]
            for log in results:
                lines.append(
                    f"{log['id']},{log['timestamp']},{log['action']},"
                    f"{log['entity_type']},{log['entity_id'] or ''},"
                    f"{log['user_email'] or ''},{log['ip_address'] or ''}"
                )
            return "\n".join(lines)

        return results

    def detect_anomalies(self) -> List[dict]:
        """Detect suspicious activity patterns"""
        anomalies = []
        now = datetime.utcnow()
        hour_ago = (now - timedelta(hours=1)).isoformat()
        recent = [l for l in self._logs if l["timestamp"] >= hour_ago]

        # Multiple failed logins from same IP
        failed_by_ip = {}
        for log in recent:
            if log["action"] == "LOGIN_FAILED" and log["ip_address"]:
                ip = log["ip_address"]
                failed_by_ip[ip] = failed_by_ip.get(ip, 0) + 1

        for ip, count in failed_by_ip.items():
            if count >= 5:
                anomalies.append({
                    "type": "brute_force_attempt",
                    "severity": "high",
                    "description": f"{count} failed logins from IP {ip} in last hour",
                    "ip_address": ip
                })

        # Unusual bulk operations
        bulk_by_user = {}
        for log in recent:
            if log["action"] in ["DELETE", "BULK_ACTION"]:
                user = log["user_id"]
                bulk_by_user[user] = bulk_by_user.get(user, 0) + 1

        for user, count in bulk_by_user.items():
            if count >= 20:
                anomalies.append({
                    "type": "bulk_deletion",
                    "severity": "medium",
                    "description": f"User performed {count} delete/bulk operations in last hour",
                    "user_id": user
                })

        # Off-hours activity
        for log in recent:
            try:
                hour = int(log["timestamp"][11:13])
                if hour < 6 or hour > 22:  # Outside 6am-10pm
                    if log["action"] in ["SETTINGS_CHANGE", "DELETE", "EXPORT"]:
                        anomalies.append({
                            "type": "off_hours_sensitive",
                            "severity": "low",
                            "description": f"Sensitive action at {hour}:00",
                            "user_id": log["user_id"],
                            "action": log["action"]
                        })
            except:
                pass

        return anomalies


audit_service = AuditService()


# Helper function for route handlers
def log_action(
    action: str,
    entity_type: str,
    entity_id: str = None,
    before: dict = None,
    after: dict = None,
    request = None,
    current_user: dict = None
):
    """Helper to log actions from routes"""
    return audit_service.log(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=current_user.get("id") if current_user else None,
        user_email=current_user.get("email") if current_user else None,
        user_role=current_user.get("role") if current_user else None,
        before=before,
        after=after,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
