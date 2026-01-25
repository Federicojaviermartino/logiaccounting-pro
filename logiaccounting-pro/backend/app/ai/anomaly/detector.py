"""
Anomaly Detector
Detects unusual patterns and potential fraud
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import logging

from app.ai.base import Anomaly, AlertSeverity, BaseDetector, AIResult
from app.ai.utils import calculate_z_scores, detect_outliers

logger = logging.getLogger(__name__)


class AnomalyType(str, Enum):
    """Types of anomalies."""
    UNUSUAL_AMOUNT = "unusual_amount"
    UNUSUAL_TIMING = "unusual_timing"
    DUPLICATE_TRANSACTION = "duplicate_transaction"
    ROUND_NUMBER = "round_number"
    UNUSUAL_VENDOR = "unusual_vendor"
    FREQUENCY_SPIKE = "frequency_spike"
    PATTERN_BREAK = "pattern_break"
    SPLIT_TRANSACTION = "split_transaction"


@dataclass
class AnomalyRule:
    """Rule for anomaly detection."""
    name: str
    anomaly_type: AnomalyType
    check_fn: Callable
    severity: AlertSeverity = AlertSeverity.MEDIUM
    enabled: bool = True
    description: str = ""


class AnomalyDetector(BaseDetector):
    """Detects anomalies in transactions and financial data."""

    def __init__(self):
        self._customer_baselines: Dict[str, Dict] = {}
        self._rules: List[AnomalyRule] = []
        self._alerts: Dict[str, List[Dict]] = {}
        self._setup_default_rules()

    def _setup_default_rules(self):
        """Set up default detection rules."""
        self._rules = [
            AnomalyRule(
                name="unusual_amount",
                anomaly_type=AnomalyType.UNUSUAL_AMOUNT,
                check_fn=self._check_unusual_amount,
                severity=AlertSeverity.HIGH,
                description="Amount significantly differs from historical patterns",
            ),
            AnomalyRule(
                name="round_number",
                anomaly_type=AnomalyType.ROUND_NUMBER,
                check_fn=self._check_round_number,
                severity=AlertSeverity.LOW,
                description="Suspiciously round amount",
            ),
            AnomalyRule(
                name="duplicate",
                anomaly_type=AnomalyType.DUPLICATE_TRANSACTION,
                check_fn=self._check_duplicate,
                severity=AlertSeverity.HIGH,
                description="Potential duplicate transaction",
            ),
            AnomalyRule(
                name="unusual_timing",
                anomaly_type=AnomalyType.UNUSUAL_TIMING,
                check_fn=self._check_unusual_timing,
                severity=AlertSeverity.MEDIUM,
                description="Transaction at unusual time",
            ),
            AnomalyRule(
                name="new_vendor_large",
                anomaly_type=AnomalyType.UNUSUAL_VENDOR,
                check_fn=self._check_new_vendor_large_amount,
                severity=AlertSeverity.HIGH,
                description="Large transaction with new vendor",
            ),
        ]

    async def train(self, customer_id: str, historical_data: List[Dict], **kwargs) -> AIResult:
        """Train baseline from historical data."""
        try:
            if len(historical_data) < 10:
                return AIResult.fail("Insufficient data for training")

            # Calculate statistics
            amounts = [t.get("amount", 0) for t in historical_data]

            self._customer_baselines[customer_id] = {
                "mean_amount": np.mean(amounts),
                "std_amount": np.std(amounts),
                "max_amount": np.max(amounts),
                "median_amount": np.median(amounts),
                "transaction_count": len(historical_data),
                "vendors": set(t.get("vendor", "") for t in historical_data),
                "recent_transactions": historical_data[-100:],
                "trained_at": datetime.utcnow(),
            }

            return AIResult.ok({
                "status": "trained",
                "transaction_count": len(historical_data),
            })

        except Exception as e:
            logger.error(f"Training failed: {e}")
            return AIResult.fail(str(e))

    async def detect(self, customer_id: str, transaction: Dict, **kwargs) -> List[Anomaly]:
        """Detect anomalies in a transaction."""
        anomalies = []
        baseline = self._customer_baselines.get(customer_id, {})

        for rule in self._rules:
            if not rule.enabled:
                continue

            try:
                result = rule.check_fn(transaction, baseline)
                if result:
                    anomaly = Anomaly(
                        type=rule.anomaly_type.value,
                        severity=result.get("severity", rule.severity),
                        score=result.get("score", 0.5),
                        description=result.get("description", rule.description),
                        entity_type="transaction",
                        entity_id=transaction.get("id", ""),
                        details=result.get("details", {}),
                        recommended_action=result.get("recommended_action"),
                    )
                    anomalies.append(anomaly)
            except Exception as e:
                logger.error(f"Rule {rule.name} failed: {e}")

        return anomalies

    def _check_unusual_amount(self, tx: Dict, baseline: Dict) -> Optional[Dict]:
        """Check for unusual transaction amount."""
        amount = tx.get("amount", 0)
        mean = baseline.get("mean_amount", 0)
        std = baseline.get("std_amount", 1)

        if std == 0:
            return None

        z_score = abs(amount - mean) / std

        if z_score > 3:
            return {
                "score": min(1.0, z_score / 5),
                "severity": AlertSeverity.CRITICAL if z_score > 5 else AlertSeverity.HIGH,
                "description": f"Amount ${amount:,.2f} is {z_score:.1f} standard deviations from average",
                "details": {"z_score": z_score, "mean": mean, "amount": amount},
                "recommended_action": "Review this transaction for accuracy",
            }

        return None

    def _check_round_number(self, tx: Dict, baseline: Dict) -> Optional[Dict]:
        """Check for suspicious round numbers."""
        amount = tx.get("amount", 0)

        # Check if it's a round number (divisible by 1000)
        if amount >= 1000 and amount % 1000 == 0:
            return {
                "score": 0.3,
                "severity": AlertSeverity.LOW,
                "description": f"Round amount ${amount:,.2f} may warrant review",
                "details": {"amount": amount},
            }

        return None

    def _check_duplicate(self, tx: Dict, baseline: Dict) -> Optional[Dict]:
        """Check for potential duplicate transactions."""
        recent = baseline.get("recent_transactions", [])
        amount = tx.get("amount", 0)
        vendor = tx.get("vendor", "")
        tx_date = tx.get("date", "")

        for recent_tx in recent:
            if (recent_tx.get("amount") == amount and
                recent_tx.get("vendor") == vendor and
                recent_tx.get("id") != tx.get("id")):

                return {
                    "score": 0.8,
                    "severity": AlertSeverity.HIGH,
                    "description": f"Potential duplicate: Same amount ${amount:,.2f} and vendor '{vendor}'",
                    "details": {
                        "original_transaction": recent_tx.get("id"),
                        "amount": amount,
                        "vendor": vendor,
                    },
                    "recommended_action": "Verify this is not a duplicate payment",
                }

        return None

    def _check_unusual_timing(self, tx: Dict, baseline: Dict) -> Optional[Dict]:
        """Check for transactions at unusual times."""
        tx_datetime = tx.get("datetime")
        if not tx_datetime:
            return None

        if isinstance(tx_datetime, str):
            try:
                tx_datetime = datetime.fromisoformat(tx_datetime)
            except:
                return None

        # Check for weekend transactions
        if tx_datetime.weekday() >= 5:
            return {
                "score": 0.4,
                "severity": AlertSeverity.MEDIUM,
                "description": "Transaction submitted on weekend",
                "details": {"day": tx_datetime.strftime("%A")},
            }

        # Check for after-hours transactions
        hour = tx_datetime.hour
        if hour < 6 or hour > 22:
            return {
                "score": 0.5,
                "severity": AlertSeverity.MEDIUM,
                "description": f"Transaction at unusual hour ({hour}:00)",
                "details": {"hour": hour},
            }

        return None

    def _check_new_vendor_large_amount(self, tx: Dict, baseline: Dict) -> Optional[Dict]:
        """Check for large transactions with new vendors."""
        vendor = tx.get("vendor", "")
        amount = tx.get("amount", 0)
        known_vendors = baseline.get("vendors", set())
        mean_amount = baseline.get("mean_amount", 0)

        if vendor and vendor not in known_vendors and amount > mean_amount * 2:
            return {
                "score": 0.7,
                "severity": AlertSeverity.HIGH,
                "description": f"Large transaction (${amount:,.2f}) with new vendor '{vendor}'",
                "details": {
                    "vendor": vendor,
                    "amount": amount,
                    "is_new_vendor": True,
                },
                "recommended_action": "Verify vendor details and transaction legitimacy",
            }

        return None

    def calculate_fraud_score(self, anomalies: List[Anomaly]) -> Dict:
        """Calculate overall fraud score from anomalies."""
        if not anomalies:
            return {"fraud_score": 0, "risk_level": "low"}

        # Weight by severity
        severity_weights = {
            AlertSeverity.CRITICAL: 1.0,
            AlertSeverity.HIGH: 0.8,
            AlertSeverity.MEDIUM: 0.5,
            AlertSeverity.LOW: 0.2,
            AlertSeverity.INFO: 0.1,
        }

        weighted_scores = []
        for anomaly in anomalies:
            weight = severity_weights.get(anomaly.severity, 0.5)
            weighted_scores.append(anomaly.score * weight)

        fraud_score = min(1.0, sum(weighted_scores))

        if fraud_score > 0.7:
            risk_level = "critical"
        elif fraud_score > 0.5:
            risk_level = "high"
        elif fraud_score > 0.3:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "fraud_score": round(fraud_score, 2),
            "risk_level": risk_level,
            "anomaly_count": len(anomalies),
        }

    def get_customer_alerts(
        self,
        customer_id: str,
        status: str = None,
        severity: str = None,
        limit: int = 50,
    ) -> List[Dict]:
        """Get alerts for a customer."""
        alerts = self._alerts.get(customer_id, [])

        # Filter by status
        if status:
            alerts = [a for a in alerts if a.get("status") == status]

        # Filter by severity
        if severity:
            alerts = [a for a in alerts if a.get("severity") == severity]

        return alerts[:limit]


# Global detector instance
anomaly_detector = AnomalyDetector()
