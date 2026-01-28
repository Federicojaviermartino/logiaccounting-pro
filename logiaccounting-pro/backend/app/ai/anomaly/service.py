"""
Anomaly Detection Service
High-level service for anomaly detection features
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4
import logging

from app.utils.datetime_utils import utc_now
from app.ai.base import AIResult, Anomaly, AlertSeverity
from app.ai.anomaly.detector import AnomalyDetector, anomaly_detector

logger = logging.getLogger(__name__)


class AnomalyService:
    """Service layer for anomaly detection."""

    def __init__(self, detector: AnomalyDetector = None):
        self.detector = detector or anomaly_detector
        self._alerts: Dict[str, List[Dict]] = {}

    async def train_models(self, customer_id: str, historical_data: List[Dict]) -> AIResult:
        """Train anomaly detection models."""
        logger.info(f"Training anomaly models for customer {customer_id}")

        if not historical_data:
            return AIResult.fail("No historical data provided")

        return await self.detector.train(customer_id, historical_data)

    async def analyze_transaction(self, customer_id: str, transaction: Dict) -> AIResult:
        """Analyze a transaction for anomalies."""
        logger.info(f"Analyzing transaction for customer {customer_id}")

        try:
            # Detect anomalies
            anomalies = await self.detector.detect(customer_id, transaction)

            # Calculate fraud score
            fraud_score = self.detector.calculate_fraud_score(anomalies)

            # Create alerts for significant anomalies
            alerts_created = []
            for anomaly in anomalies:
                if anomaly.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH, AlertSeverity.MEDIUM]:
                    alert = self._create_alert(customer_id, anomaly, transaction)
                    alerts_created.append(alert)

            # Determine if transaction is safe
            is_safe = fraud_score["risk_level"] in ["low", "medium"]

            return AIResult.ok({
                "is_safe": is_safe,
                "fraud_score": fraud_score,
                "anomalies": [a.to_dict() for a in anomalies],
                "alerts_created": alerts_created,
            })

        except Exception as e:
            logger.error(f"Transaction analysis failed: {e}")
            return AIResult.fail(str(e))

    async def batch_analyze(self, customer_id: str, transactions: List[Dict]) -> AIResult:
        """Analyze multiple transactions."""
        results = []

        for tx in transactions:
            result = await self.analyze_transaction(customer_id, tx)
            results.append({
                "transaction_id": tx.get("id"),
                "is_safe": result.data.get("is_safe") if result.success else True,
                "fraud_score": result.data.get("fraud_score", {}) if result.success else {},
            })

        flagged = sum(1 for r in results if not r.get("is_safe", True))

        return AIResult.ok({
            "total": len(transactions),
            "flagged": flagged,
            "safe": len(transactions) - flagged,
            "results": results,
        })

    def _create_alert(self, customer_id: str, anomaly: Anomaly, transaction: Dict) -> Dict:
        """Create an alert from an anomaly."""
        alert = {
            "id": f"alert_{uuid4().hex[:12]}",
            "customer_id": customer_id,
            "anomaly_id": anomaly.id,
            "type": anomaly.type,
            "severity": anomaly.severity.value,
            "title": self._get_alert_title(anomaly),
            "description": anomaly.description,
            "entity_type": anomaly.entity_type,
            "entity_id": anomaly.entity_id,
            "details": anomaly.details,
            "recommended_action": anomaly.recommended_action,
            "status": "pending",
            "created_at": utc_now().isoformat(),
            "acknowledged_at": None,
            "resolved_at": None,
            "acknowledged_by": None,
            "resolved_by": None,
            "notes": None,
        }

        # Store alert
        if customer_id not in self._alerts:
            self._alerts[customer_id] = []
        self._alerts[customer_id].insert(0, alert)

        return alert

    def _get_alert_title(self, anomaly: Anomaly) -> str:
        """Generate alert title from anomaly."""
        titles = {
            "unusual_amount": "Unusual Transaction Amount",
            "duplicate_transaction": "Potential Duplicate Transaction",
            "unusual_timing": "Unusual Transaction Timing",
            "unusual_vendor": "New Vendor Alert",
            "round_number": "Round Number Transaction",
            "frequency_spike": "Transaction Frequency Spike",
            "pattern_break": "Pattern Break Detected",
            "split_transaction": "Potential Split Transaction",
        }
        return titles.get(anomaly.type, "Anomaly Detected")

    def get_alerts(
        self,
        customer_id: str,
        status: str = None,
        severity: str = None,
        limit: int = 50,
    ) -> List[Dict]:
        """Get alerts for customer."""
        alerts = self._alerts.get(customer_id, [])

        if status:
            alerts = [a for a in alerts if a.get("status") == status]

        if severity:
            alerts = [a for a in alerts if a.get("severity") == severity]

        return alerts[:limit]

    def get_alert_summary(self, customer_id: str) -> Dict:
        """Get alert summary for customer."""
        alerts = self._alerts.get(customer_id, [])

        summary = {
            "total": len(alerts),
            "pending": sum(1 for a in alerts if a.get("status") == "pending"),
            "acknowledged": sum(1 for a in alerts if a.get("status") == "acknowledged"),
            "resolved": sum(1 for a in alerts if a.get("status") == "resolved"),
            "dismissed": sum(1 for a in alerts if a.get("status") == "dismissed"),
            "critical_pending": sum(1 for a in alerts if a.get("status") == "pending" and a.get("severity") == "critical"),
            "high_pending": sum(1 for a in alerts if a.get("status") == "pending" and a.get("severity") == "high"),
            "by_status": {},
            "by_severity": {},
        }

        # Group by status
        for alert in alerts:
            status = alert.get("status", "unknown")
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1

        # Group by severity
        for alert in alerts:
            severity = alert.get("severity", "unknown")
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1

        return summary

    def acknowledge_alert(self, alert_id: str, user_id: str) -> Optional[Dict]:
        """Acknowledge an alert."""
        for customer_alerts in self._alerts.values():
            for alert in customer_alerts:
                if alert["id"] == alert_id:
                    alert["status"] = "acknowledged"
                    alert["acknowledged_at"] = utc_now().isoformat()
                    alert["acknowledged_by"] = user_id
                    return alert
        return None

    def resolve_alert(self, alert_id: str, user_id: str, notes: str = None) -> Optional[Dict]:
        """Resolve an alert."""
        for customer_alerts in self._alerts.values():
            for alert in customer_alerts:
                if alert["id"] == alert_id:
                    alert["status"] = "resolved"
                    alert["resolved_at"] = utc_now().isoformat()
                    alert["resolved_by"] = user_id
                    if notes:
                        alert["notes"] = notes
                    return alert
        return None

    def dismiss_alert(self, alert_id: str, user_id: str, reason: str = None) -> Optional[Dict]:
        """Dismiss an alert."""
        for customer_alerts in self._alerts.values():
            for alert in customer_alerts:
                if alert["id"] == alert_id:
                    alert["status"] = "dismissed"
                    alert["resolved_at"] = utc_now().isoformat()
                    alert["resolved_by"] = user_id
                    if reason:
                        alert["notes"] = f"Dismissed: {reason}"
                    return alert
        return None


# Global service instance
anomaly_service = AnomalyService()
