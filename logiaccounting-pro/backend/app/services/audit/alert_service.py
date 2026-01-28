"""
Alert Service
Audit alert creation, evaluation, and notification
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

from app.models.audit_store import audit_db
from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


class AlertService:
    """Service for managing audit alerts"""

    def __init__(self, organization_id: str):
        self.organization_id = organization_id

    def evaluate_rules(self, audit_log: Dict) -> List[Dict]:
        """
        Evaluate alert rules against an audit log entry

        Args:
            audit_log: The audit log entry to evaluate

        Returns:
            List of triggered alerts
        """
        triggered_alerts = []

        # Get active rules
        rules = audit_db.alert_rules.find_all({
            "organization_id": self.organization_id,
            "is_active": True
        })

        for rule in rules:
            if self._matches_rule(audit_log, rule):
                if audit_db.alert_rules.can_trigger(rule):
                    alert = self._create_alert(audit_log, rule)
                    if alert:
                        triggered_alerts.append(alert)
                        audit_db.alert_rules.record_trigger(rule["id"])

        return triggered_alerts

    def _matches_rule(self, audit_log: Dict, rule: Dict) -> bool:
        """Check if audit log matches rule conditions"""
        # Check event type
        event_types = rule.get("event_types", [])
        if audit_log.get("event_type") not in event_types:
            return False

        conditions = rule.get("conditions") or {}

        # Check field matches
        if 'field_match' in conditions:
            for field, expected in conditions['field_match'].items():
                actual = audit_log.get(field)
                if actual is None:
                    actual = audit_log.get("metadata", {}).get(field)

                if actual != expected:
                    return False

        # Check count-based conditions
        if 'count' in conditions:
            count_condition = conditions['count']
            timeframe = conditions.get('timeframe_minutes', 60)

            # Count recent matching events
            since = (utc_now() - timedelta(minutes=timeframe)).isoformat()
            recent_logs = audit_db.audit_logs.find_all({
                "organization_id": self.organization_id,
                "from_date": since
            }, limit=10000)

            # Filter by event types
            matching = [l for l in recent_logs if l.get("event_type") in event_types]
            count = len(matching)

            for op, value in count_condition.items():
                if op == '>' and not (count > value):
                    return False
                if op == '>=' and not (count >= value):
                    return False
                if op == '<' and not (count < value):
                    return False
                if op == '==' and not (count == value):
                    return False

        # Check severity threshold
        if 'min_severity' in conditions:
            severity_order = {'debug': 0, 'info': 1, 'warning': 2, 'error': 3, 'critical': 4}
            min_level = severity_order.get(conditions['min_severity'], 0)
            actual_level = severity_order.get(audit_log.get("severity"), 0)

            if actual_level < min_level:
                return False

        return True

    def _create_alert(self, audit_log: Dict, rule: Dict) -> Optional[Dict]:
        """Create alert from rule match"""
        try:
            alert = audit_db.alerts.create({
                "organization_id": self.organization_id,
                "alert_type": rule.get("alert_type"),
                "triggered_by_log_id": audit_log.get("id"),
                "severity": rule.get("severity"),
                "title": f"{rule.get('name')}: {audit_log.get('event_type')}",
                "description": self._generate_description(audit_log, rule),
                "affected_entity_type": audit_log.get("entity_type"),
                "affected_entity_id": audit_log.get("entity_id"),
                "affected_user_id": audit_log.get("user_id"),
                "evidence": {
                    'event_type': audit_log.get('event_type'),
                    'action': audit_log.get('action'),
                    'entity': f"{audit_log.get('entity_type')}/{audit_log.get('entity_id')}",
                    'user': audit_log.get('user_email'),
                    'ip_address': audit_log.get('ip_address'),
                    'occurred_at': audit_log.get('occurred_at'),
                },
            })

            # Send notifications
            self._send_notifications(alert, rule)

            logger.info(f"Alert created: {alert.get('title')}")
            return alert

        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            return None

    def _generate_description(self, audit_log: Dict, rule: Dict) -> str:
        """Generate alert description"""
        parts = [
            f"Rule '{rule.get('name')}' triggered.",
            f"Event: {audit_log.get('event_type')}",
        ]

        if audit_log.get('entity_type'):
            parts.append(f"Entity: {audit_log.get('entity_type')}")

        if audit_log.get('user_email'):
            parts.append(f"User: {audit_log.get('user_email')}")

        if audit_log.get('ip_address'):
            parts.append(f"IP: {audit_log.get('ip_address')}")

        return " | ".join(parts)

    def _send_notifications(self, alert: Dict, rule: Dict):
        """Send alert notifications"""
        channels = rule.get("notification_channels") or []

        if 'email' in channels:
            self._send_email_notification(alert, rule)

        if 'slack' in channels:
            self._send_slack_notification(alert, rule)

        if 'webhook' in channels:
            self._send_webhook_notification(alert, rule)

        if 'in_app' in channels:
            self._send_in_app_notification(alert, rule)

    def _send_email_notification(self, alert: Dict, rule: Dict):
        """Send email notification"""
        logger.info(f"Email notification for alert {alert.get('id')}")
        # Would integrate with email service

    def _send_slack_notification(self, alert: Dict, rule: Dict):
        """Send Slack notification"""
        logger.info(f"Slack notification for alert {alert.get('id')}")
        # Would integrate with Slack

    def _send_webhook_notification(self, alert: Dict, rule: Dict):
        """Send webhook notification"""
        logger.info(f"Webhook notification for alert {alert.get('id')}")
        # Would make HTTP request to webhook URL

    def _send_in_app_notification(self, alert: Dict, rule: Dict):
        """Create in-app notification"""
        logger.info(f"In-app notification for alert {alert.get('id')}")
        # Would create notification in notification store

    # Alert management methods

    def get_alerts(
        self,
        status: str = None,
        severity: str = None,
        alert_type: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get alerts with filters"""
        filters = {"organization_id": self.organization_id}

        if status:
            filters["status"] = status
        if severity:
            filters["severity"] = severity
        if alert_type:
            filters["alert_type"] = alert_type

        return audit_db.alerts.find_all(filters, limit=limit)

    def get_alert(self, alert_id: str) -> Optional[Dict]:
        """Get alert by ID"""
        alert = audit_db.alerts.find_by_id(alert_id)
        if alert and alert.get("organization_id") == self.organization_id:
            return alert
        return None

    def get_stats(self, days: int = 30) -> Dict:
        """Get alert statistics"""
        return audit_db.alerts.get_stats(self.organization_id, days)

    def acknowledge_alert(self, alert_id: str, user_id: str) -> Optional[Dict]:
        """Acknowledge an alert"""
        alert = self.get_alert(alert_id)
        if not alert:
            return None
        return audit_db.alerts.acknowledge(alert_id, user_id)

    def resolve_alert(self, alert_id: str, user_id: str, notes: str = None) -> Optional[Dict]:
        """Resolve an alert"""
        alert = self.get_alert(alert_id)
        if not alert:
            return None
        return audit_db.alerts.resolve(alert_id, user_id, notes)

    def dismiss_alert(self, alert_id: str, user_id: str, reason: str = None) -> Optional[Dict]:
        """Dismiss an alert"""
        alert = self.get_alert(alert_id)
        if not alert:
            return None
        return audit_db.alerts.dismiss(alert_id, user_id, reason)

    # Alert rules management

    def get_rules(self) -> List[Dict]:
        """Get all alert rules"""
        return audit_db.alert_rules.find_all({"organization_id": self.organization_id})

    def get_rule(self, rule_id: str) -> Optional[Dict]:
        """Get alert rule by ID"""
        rule = audit_db.alert_rules.find_by_id(rule_id)
        if rule and rule.get("organization_id") == self.organization_id:
            return rule
        return None

    def create_rule(self, data: Dict) -> Dict:
        """Create alert rule"""
        data["organization_id"] = self.organization_id
        return audit_db.alert_rules.create(data)

    def update_rule(self, rule_id: str, data: Dict) -> Optional[Dict]:
        """Update alert rule"""
        rule = self.get_rule(rule_id)
        if not rule:
            return None
        return audit_db.alert_rules.update(rule_id, data)

    def delete_rule(self, rule_id: str) -> bool:
        """Delete alert rule"""
        rule = self.get_rule(rule_id)
        if not rule:
            return False
        return audit_db.alert_rules.delete(rule_id)


def setup_default_rules(organization_id: str):
    """Setup default alert rules for an organization"""
    default_rules = [
        {
            "name": "Multiple Failed Logins",
            "description": "Alert on multiple failed login attempts",
            "event_types": ["auth.login_failed"],
            "conditions": {"count": {">": 5}, "timeframe_minutes": 10},
            "alert_type": "brute_force",
            "severity": "high",
            "notification_channels": ["email", "in_app"],
        },
        {
            "name": "Bulk Data Delete",
            "description": "Alert on bulk data deletion",
            "event_types": ["entity.deleted"],
            "conditions": {"count": {">": 10}, "timeframe_minutes": 5},
            "alert_type": "bulk_delete",
            "severity": "critical",
            "notification_channels": ["email", "slack", "in_app"],
        },
        {
            "name": "Admin Role Assigned",
            "description": "Alert when admin role is assigned",
            "event_types": ["role.assigned"],
            "conditions": {"field_match": {"role": "admin"}},
            "alert_type": "permission_escalation",
            "severity": "medium",
            "notification_channels": ["email", "in_app"],
        },
        {
            "name": "Large Data Export",
            "description": "Alert on data exports",
            "event_types": ["entity.exported", "data.exported"],
            "conditions": {},
            "alert_type": "data_export",
            "severity": "medium",
            "notification_channels": ["email"],
        },
    ]

    service = AlertService(organization_id)
    existing_rules = service.get_rules()
    existing_names = {r.get("name") for r in existing_rules}

    for rule_data in default_rules:
        if rule_data["name"] not in existing_names:
            service.create_rule(rule_data)
