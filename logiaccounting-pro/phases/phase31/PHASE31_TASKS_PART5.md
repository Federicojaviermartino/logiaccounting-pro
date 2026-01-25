# Phase 31: AI/ML Features - Part 5: Anomaly Detection & Payment Optimizer

## Overview
This part covers the anomaly detection system for fraud prevention and the payment scheduling optimizer.

---

## File 1: Anomaly Detector
**Path:** `backend/app/ai/anomaly/detector.py`

```python
"""
Anomaly Detection Engine
Detects unusual patterns and potential fraud
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import numpy as np
import logging

from app.ai.base import BaseDetector, Anomaly, AlertSeverity
from app.ai.utils import calculate_z_scores, calculate_iqr_bounds, detect_outliers

logger = logging.getLogger(__name__)


class AnomalyType(str, Enum):
    """Types of anomalies."""
    TRANSACTION_AMOUNT = "transaction_amount"
    TRANSACTION_TIMING = "transaction_timing"
    TRANSACTION_VELOCITY = "transaction_velocity"
    PATTERN_DEVIATION = "pattern_deviation"
    VENDOR_ANOMALY = "vendor_anomaly"
    DUPLICATE_DETECTION = "duplicate_detection"
    GEOGRAPHIC_ANOMALY = "geographic_anomaly"
    USER_BEHAVIOR = "user_behavior"


@dataclass
class AnomalyRule:
    """Rule for anomaly detection."""
    id: str
    name: str
    anomaly_type: AnomalyType
    enabled: bool = True
    severity: AlertSeverity = AlertSeverity.MEDIUM
    threshold: float = 3.0
    parameters: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "anomaly_type": self.anomaly_type.value,
            "enabled": self.enabled,
            "severity": self.severity.value,
            "threshold": self.threshold,
            "parameters": self.parameters,
        }


class AnomalyDetector(BaseDetector):
    """Detects anomalies in financial transactions."""
    
    # Default rules
    DEFAULT_RULES = [
        AnomalyRule(
            id="rule_amount_zscore",
            name="Unusual Transaction Amount",
            anomaly_type=AnomalyType.TRANSACTION_AMOUNT,
            severity=AlertSeverity.HIGH,
            threshold=3.0,
            parameters={"method": "zscore", "min_samples": 10},
        ),
        AnomalyRule(
            id="rule_velocity",
            name="High Transaction Velocity",
            anomaly_type=AnomalyType.TRANSACTION_VELOCITY,
            severity=AlertSeverity.MEDIUM,
            threshold=5,
            parameters={"window_hours": 24, "max_transactions": 5},
        ),
        AnomalyRule(
            id="rule_new_vendor",
            name="Large Payment to New Vendor",
            anomaly_type=AnomalyType.VENDOR_ANOMALY,
            severity=AlertSeverity.HIGH,
            threshold=5000,
            parameters={"vendor_age_days": 30},
        ),
        AnomalyRule(
            id="rule_duplicate",
            name="Potential Duplicate",
            anomaly_type=AnomalyType.DUPLICATE_DETECTION,
            severity=AlertSeverity.MEDIUM,
            parameters={"time_window_hours": 48, "similarity_threshold": 0.95},
        ),
        AnomalyRule(
            id="rule_weekend",
            name="Weekend Transaction",
            anomaly_type=AnomalyType.TRANSACTION_TIMING,
            severity=AlertSeverity.LOW,
            parameters={"check_weekends": True, "check_holidays": True},
        ),
        AnomalyRule(
            id="rule_round_amount",
            name="Suspicious Round Amount",
            anomaly_type=AnomalyType.PATTERN_DEVIATION,
            severity=AlertSeverity.LOW,
            threshold=10000,
            parameters={"check_round_thousands": True},
        ),
    ]
    
    def __init__(self, customer_id: str):
        super().__init__(name="AnomalyDetector", threshold=0.5)
        self.customer_id = customer_id
        self.rules = {r.id: r for r in self.DEFAULT_RULES}
        
        # Statistical baselines
        self._transaction_stats: Dict[str, Dict] = {}
        self._vendor_history: Dict[str, Dict] = {}
        self._recent_transactions: List[Dict] = []
    
    async def fit(self, data: List[Dict], **kwargs):
        """Fit detector to historical data."""
        if not data:
            return
        
        # Calculate transaction statistics
        amounts = [t.get("amount", 0) for t in data]
        if amounts:
            self._transaction_stats["amount"] = {
                "mean": np.mean(amounts),
                "std": np.std(amounts),
                "median": np.median(amounts),
                "q1": np.percentile(amounts, 25),
                "q3": np.percentile(amounts, 75),
            }
        
        # Build vendor history
        for transaction in data:
            vendor_id = transaction.get("vendor_id")
            if vendor_id:
                if vendor_id not in self._vendor_history:
                    self._vendor_history[vendor_id] = {
                        "first_seen": transaction.get("date"),
                        "transaction_count": 0,
                        "total_amount": 0,
                        "amounts": [],
                    }
                
                self._vendor_history[vendor_id]["transaction_count"] += 1
                self._vendor_history[vendor_id]["total_amount"] += transaction.get("amount", 0)
                self._vendor_history[vendor_id]["amounts"].append(transaction.get("amount", 0))
        
        self._is_fitted = True
        logger.info(f"Anomaly detector fitted with {len(data)} transactions")
    
    async def detect(self, data: Dict) -> List[Anomaly]:
        """Detect anomalies in a single transaction."""
        anomalies = []
        
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            detected = await self._apply_rule(rule, data)
            if detected:
                anomalies.append(detected)
        
        # Add to recent transactions for velocity checks
        self._recent_transactions.append({
            **data,
            "timestamp": datetime.utcnow(),
        })
        
        # Keep only last 24 hours
        cutoff = datetime.utcnow() - timedelta(hours=24)
        self._recent_transactions = [
            t for t in self._recent_transactions
            if t.get("timestamp", datetime.utcnow()) > cutoff
        ]
        
        return anomalies
    
    async def detect_batch(self, data: List[Dict]) -> List[Anomaly]:
        """Detect anomalies in batch."""
        all_anomalies = []
        
        for transaction in data:
            anomalies = await self.detect(transaction)
            all_anomalies.extend(anomalies)
        
        return all_anomalies
    
    async def _apply_rule(self, rule: AnomalyRule, data: Dict) -> Optional[Anomaly]:
        """Apply a detection rule to transaction."""
        
        if rule.anomaly_type == AnomalyType.TRANSACTION_AMOUNT:
            return await self._check_amount_anomaly(rule, data)
        
        elif rule.anomaly_type == AnomalyType.TRANSACTION_VELOCITY:
            return await self._check_velocity_anomaly(rule, data)
        
        elif rule.anomaly_type == AnomalyType.VENDOR_ANOMALY:
            return await self._check_vendor_anomaly(rule, data)
        
        elif rule.anomaly_type == AnomalyType.DUPLICATE_DETECTION:
            return await self._check_duplicate(rule, data)
        
        elif rule.anomaly_type == AnomalyType.TRANSACTION_TIMING:
            return await self._check_timing_anomaly(rule, data)
        
        elif rule.anomaly_type == AnomalyType.PATTERN_DEVIATION:
            return await self._check_pattern_deviation(rule, data)
        
        return None
    
    async def _check_amount_anomaly(self, rule: AnomalyRule, data: Dict) -> Optional[Anomaly]:
        """Check for unusual transaction amounts."""
        amount = data.get("amount", 0)
        stats = self._transaction_stats.get("amount", {})
        
        if not stats:
            return None
        
        # Calculate Z-score
        mean = stats.get("mean", 0)
        std = stats.get("std", 1)
        
        if std == 0:
            return None
        
        z_score = abs(amount - mean) / std
        
        if z_score >= rule.threshold:
            return Anomaly(
                id=f"anom_{uuid4().hex[:12]}",
                entity_type=data.get("entity_type", "transaction"),
                entity_id=data.get("id", ""),
                anomaly_type=rule.anomaly_type.value,
                severity=rule.severity,
                score=min(z_score / 10, 1.0),
                description=f"Transaction amount (${amount:,.2f}) is {z_score:.1f} standard deviations from average (${mean:,.2f})",
                details={
                    "amount": amount,
                    "average": mean,
                    "std_dev": std,
                    "z_score": z_score,
                },
                recommended_action="Review this transaction to verify it's legitimate",
            )
        
        return None
    
    async def _check_velocity_anomaly(self, rule: AnomalyRule, data: Dict) -> Optional[Anomaly]:
        """Check for high transaction velocity."""
        window_hours = rule.parameters.get("window_hours", 24)
        max_transactions = rule.parameters.get("max_transactions", 5)
        
        vendor_id = data.get("vendor_id")
        if not vendor_id:
            return None
        
        # Count recent transactions to same vendor
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)
        recent_to_vendor = [
            t for t in self._recent_transactions
            if t.get("vendor_id") == vendor_id and t.get("timestamp", datetime.utcnow()) > cutoff
        ]
        
        if len(recent_to_vendor) >= max_transactions:
            total_amount = sum(t.get("amount", 0) for t in recent_to_vendor)
            
            return Anomaly(
                id=f"anom_{uuid4().hex[:12]}",
                entity_type="vendor",
                entity_id=vendor_id,
                anomaly_type=rule.anomaly_type.value,
                severity=rule.severity,
                score=min(len(recent_to_vendor) / (max_transactions * 2), 1.0),
                description=f"{len(recent_to_vendor)} transactions to same vendor in {window_hours} hours",
                details={
                    "transaction_count": len(recent_to_vendor),
                    "total_amount": total_amount,
                    "window_hours": window_hours,
                },
                recommended_action="Verify these multiple transactions are intentional",
            )
        
        return None
    
    async def _check_vendor_anomaly(self, rule: AnomalyRule, data: Dict) -> Optional[Anomaly]:
        """Check for suspicious vendor activity."""
        vendor_id = data.get("vendor_id")
        amount = data.get("amount", 0)
        
        if not vendor_id:
            return None
        
        vendor_age_days = rule.parameters.get("vendor_age_days", 30)
        amount_threshold = rule.threshold
        
        vendor = self._vendor_history.get(vendor_id)
        
        # New vendor with large payment
        if not vendor or vendor.get("transaction_count", 0) <= 1:
            if amount >= amount_threshold:
                return Anomaly(
                    id=f"anom_{uuid4().hex[:12]}",
                    entity_type="payment",
                    entity_id=data.get("id", ""),
                    anomaly_type=rule.anomaly_type.value,
                    severity=rule.severity,
                    score=min(amount / (amount_threshold * 2), 1.0),
                    description=f"Large payment (${amount:,.2f}) to new vendor",
                    details={
                        "amount": amount,
                        "vendor_id": vendor_id,
                        "is_new_vendor": True,
                    },
                    recommended_action="Verify vendor details and payment authorization",
                )
        
        return None
    
    async def _check_duplicate(self, rule: AnomalyRule, data: Dict) -> Optional[Anomaly]:
        """Check for potential duplicate transactions."""
        time_window = rule.parameters.get("time_window_hours", 48)
        similarity_threshold = rule.parameters.get("similarity_threshold", 0.95)
        
        amount = data.get("amount", 0)
        vendor_id = data.get("vendor_id")
        invoice_number = data.get("invoice_number")
        
        cutoff = datetime.utcnow() - timedelta(hours=time_window)
        
        for recent in self._recent_transactions:
            if recent.get("timestamp", datetime.utcnow()) < cutoff:
                continue
            
            if recent.get("id") == data.get("id"):
                continue
            
            # Check for exact duplicate
            if (recent.get("amount") == amount and 
                recent.get("vendor_id") == vendor_id and
                recent.get("invoice_number") == invoice_number):
                
                return Anomaly(
                    id=f"anom_{uuid4().hex[:12]}",
                    entity_type="transaction",
                    entity_id=data.get("id", ""),
                    anomaly_type=rule.anomaly_type.value,
                    severity=AlertSeverity.HIGH,
                    score=1.0,
                    description=f"Potential duplicate: same amount, vendor, and invoice number",
                    details={
                        "amount": amount,
                        "vendor_id": vendor_id,
                        "invoice_number": invoice_number,
                        "similar_transaction_id": recent.get("id"),
                    },
                    recommended_action="Review for duplicate payment",
                )
            
            # Check for similar amounts to same vendor
            if recent.get("vendor_id") == vendor_id:
                if abs(recent.get("amount", 0) - amount) / max(amount, 1) < (1 - similarity_threshold):
                    return Anomaly(
                        id=f"anom_{uuid4().hex[:12]}",
                        entity_type="transaction",
                        entity_id=data.get("id", ""),
                        anomaly_type=rule.anomaly_type.value,
                        severity=AlertSeverity.MEDIUM,
                        score=0.8,
                        description=f"Similar transaction to same vendor within {time_window} hours",
                        details={
                            "amount": amount,
                            "similar_amount": recent.get("amount"),
                            "vendor_id": vendor_id,
                        },
                        recommended_action="Verify this is not a duplicate",
                    )
        
        return None
    
    async def _check_timing_anomaly(self, rule: AnomalyRule, data: Dict) -> Optional[Anomaly]:
        """Check for unusual transaction timing."""
        timestamp = data.get("timestamp") or datetime.utcnow()
        
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        
        # Weekend check
        if rule.parameters.get("check_weekends") and timestamp.weekday() >= 5:
            return Anomaly(
                id=f"anom_{uuid4().hex[:12]}",
                entity_type="transaction",
                entity_id=data.get("id", ""),
                anomaly_type=rule.anomaly_type.value,
                severity=AlertSeverity.LOW,
                score=0.3,
                description="Transaction occurred on weekend",
                details={
                    "day_of_week": timestamp.strftime("%A"),
                    "timestamp": timestamp.isoformat(),
                },
                recommended_action="Review if weekend transaction is expected",
            )
        
        return None
    
    async def _check_pattern_deviation(self, rule: AnomalyRule, data: Dict) -> Optional[Anomaly]:
        """Check for pattern deviations."""
        amount = data.get("amount", 0)
        
        # Round amount check
        if rule.parameters.get("check_round_thousands"):
            if amount >= rule.threshold and amount % 1000 == 0:
                return Anomaly(
                    id=f"anom_{uuid4().hex[:12]}",
                    entity_type="transaction",
                    entity_id=data.get("id", ""),
                    anomaly_type=rule.anomaly_type.value,
                    severity=AlertSeverity.LOW,
                    score=0.2,
                    description=f"Suspiciously round amount: ${amount:,.0f}",
                    details={"amount": amount},
                    recommended_action="Verify amount matches invoice",
                )
        
        return None
    
    def update_rule(self, rule_id: str, updates: Dict):
        """Update a detection rule."""
        if rule_id in self.rules:
            rule = self.rules[rule_id]
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
    
    def get_rules(self) -> List[Dict]:
        """Get all detection rules."""
        return [r.to_dict() for r in self.rules.values()]
```

---

## File 2: Anomaly Service
**Path:** `backend/app/ai/anomaly/service.py`

```python
"""
Anomaly Detection Service
High-level service for anomaly detection
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from app.ai.anomaly.detector import AnomalyDetector, AnomalyType
from app.ai.base import AIResult, Anomaly, AlertSeverity

logger = logging.getLogger(__name__)


class AnomalyService:
    """Service for anomaly detection and management."""
    
    def __init__(self):
        self._detectors: Dict[str, AnomalyDetector] = {}
        self._anomaly_store: Dict[str, List[Anomaly]] = {}
    
    def get_detector(self, customer_id: str) -> AnomalyDetector:
        """Get or create detector for customer."""
        if customer_id not in self._detectors:
            self._detectors[customer_id] = AnomalyDetector(customer_id)
        return self._detectors[customer_id]
    
    async def train_detector(self, customer_id: str, historical_data: List[Dict]) -> AIResult:
        """Train anomaly detector on historical data."""
        try:
            detector = self.get_detector(customer_id)
            await detector.fit(historical_data)
            
            return AIResult(
                success=True,
                data={"status": "trained", "data_points": len(historical_data)},
            )
        except Exception as e:
            logger.error(f"Detector training failed: {e}")
            return AIResult(success=False, error=str(e))
    
    async def analyze_transaction(self, customer_id: str, transaction: Dict) -> AIResult:
        """Analyze a single transaction for anomalies."""
        import time
        start_time = time.time()
        
        try:
            detector = self.get_detector(customer_id)
            anomalies = await detector.detect(transaction)
            
            # Store detected anomalies
            if anomalies:
                if customer_id not in self._anomaly_store:
                    self._anomaly_store[customer_id] = []
                self._anomaly_store[customer_id].extend(anomalies)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return AIResult(
                success=True,
                data={
                    "transaction_id": transaction.get("id"),
                    "anomalies_detected": len(anomalies),
                    "anomalies": [a.to_dict() for a in anomalies],
                    "risk_score": max([a.score for a in anomalies]) if anomalies else 0,
                },
                processing_time_ms=processing_time,
            )
            
        except Exception as e:
            logger.error(f"Transaction analysis failed: {e}")
            return AIResult(success=False, error=str(e))
    
    async def analyze_batch(self, customer_id: str, transactions: List[Dict]) -> AIResult:
        """Analyze multiple transactions."""
        try:
            detector = self.get_detector(customer_id)
            all_anomalies = await detector.detect_batch(transactions)
            
            # Store anomalies
            if all_anomalies:
                if customer_id not in self._anomaly_store:
                    self._anomaly_store[customer_id] = []
                self._anomaly_store[customer_id].extend(all_anomalies)
            
            # Group by severity
            by_severity = {
                "critical": [],
                "high": [],
                "medium": [],
                "low": [],
            }
            
            for anomaly in all_anomalies:
                by_severity[anomaly.severity.value].append(anomaly.to_dict())
            
            return AIResult(
                success=True,
                data={
                    "transactions_analyzed": len(transactions),
                    "total_anomalies": len(all_anomalies),
                    "by_severity": {k: len(v) for k, v in by_severity.items()},
                    "anomalies": by_severity,
                },
            )
            
        except Exception as e:
            logger.error(f"Batch analysis failed: {e}")
            return AIResult(success=False, error=str(e))
    
    def get_anomalies(
        self,
        customer_id: str,
        severity: str = None,
        status: str = None,
        limit: int = 50,
    ) -> List[Dict]:
        """Get detected anomalies."""
        anomalies = self._anomaly_store.get(customer_id, [])
        
        # Filter by severity
        if severity:
            anomalies = [a for a in anomalies if a.severity.value == severity]
        
        # Filter by status
        if status:
            anomalies = [a for a in anomalies if a.status == status]
        
        # Sort by detected_at descending
        anomalies = sorted(anomalies, key=lambda a: a.detected_at, reverse=True)
        
        return [a.to_dict() for a in anomalies[:limit]]
    
    def get_anomaly_summary(self, customer_id: str) -> Dict:
        """Get anomaly summary for customer."""
        anomalies = self._anomaly_store.get(customer_id, [])
        
        # Count by severity
        by_severity = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
        }
        
        # Count by status
        by_status = {
            "pending_review": 0,
            "reviewed": 0,
            "dismissed": 0,
            "confirmed": 0,
        }
        
        for anomaly in anomalies:
            by_severity[anomaly.severity.value] = by_severity.get(anomaly.severity.value, 0) + 1
            by_status[anomaly.status] = by_status.get(anomaly.status, 0) + 1
        
        return {
            "total": len(anomalies),
            "by_severity": by_severity,
            "by_status": by_status,
            "pending_review": by_status.get("pending_review", 0),
        }
    
    def update_anomaly_status(self, customer_id: str, anomaly_id: str, status: str, notes: str = None) -> bool:
        """Update anomaly status."""
        anomalies = self._anomaly_store.get(customer_id, [])
        
        for anomaly in anomalies:
            if anomaly.id == anomaly_id:
                anomaly.status = status
                if notes:
                    anomaly.details["review_notes"] = notes
                    anomaly.details["reviewed_at"] = datetime.utcnow().isoformat()
                return True
        
        return False
    
    def get_rules(self, customer_id: str) -> List[Dict]:
        """Get detection rules for customer."""
        detector = self.get_detector(customer_id)
        return detector.get_rules()
    
    def update_rule(self, customer_id: str, rule_id: str, updates: Dict) -> bool:
        """Update a detection rule."""
        detector = self.get_detector(customer_id)
        detector.update_rule(rule_id, updates)
        return True


# Global service instance
anomaly_service = AnomalyService()
```

---

## File 3: Payment Optimizer
**Path:** `backend/app/ai/optimizer/payment_scheduler.py`

```python
"""
Payment Scheduling Optimizer
Optimizes payment timing for cash flow and discounts
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class OptimizationGoal(str, Enum):
    """Optimization goals."""
    MAXIMIZE_DISCOUNTS = "maximize_discounts"
    MINIMIZE_PENALTIES = "minimize_penalties"
    OPTIMIZE_CASH_FLOW = "optimize_cash_flow"
    BALANCE_ALL = "balance_all"


@dataclass
class PaymentItem:
    """Item to be scheduled for payment."""
    id: str
    vendor_id: str
    vendor_name: str
    amount: float
    due_date: datetime
    invoice_number: str
    
    # Discount terms
    early_discount_percent: float = 0
    early_discount_days: int = 0
    
    # Penalty terms
    late_penalty_percent: float = 0
    grace_period_days: int = 0
    
    # Priority
    vendor_priority: int = 5  # 1-10, higher = more important
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "vendor_id": self.vendor_id,
            "vendor_name": self.vendor_name,
            "amount": self.amount,
            "due_date": self.due_date.isoformat(),
            "invoice_number": self.invoice_number,
            "early_discount_percent": self.early_discount_percent,
            "early_discount_days": self.early_discount_days,
            "late_penalty_percent": self.late_penalty_percent,
            "vendor_priority": self.vendor_priority,
        }


@dataclass
class ScheduledPayment:
    """Scheduled payment result."""
    item: PaymentItem
    scheduled_date: datetime
    amount_to_pay: float
    discount_captured: float = 0
    penalty_avoided: float = 0
    reason: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "invoice_id": self.item.id,
            "vendor": self.item.vendor_name,
            "invoice_number": self.item.invoice_number,
            "original_amount": self.item.amount,
            "amount_to_pay": self.amount_to_pay,
            "original_due": self.item.due_date.isoformat(),
            "scheduled_date": self.scheduled_date.isoformat(),
            "discount_captured": self.discount_captured,
            "penalty_avoided": self.penalty_avoided,
            "reason": self.reason,
        }


@dataclass
class OptimizationResult:
    """Result of payment optimization."""
    scheduled_payments: List[ScheduledPayment]
    total_amount: float
    total_discounts: float
    total_penalties_avoided: float
    net_savings: float
    ending_cash: float
    daily_cash_flow: List[Dict]
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "schedule": [p.to_dict() for p in self.scheduled_payments],
            "summary": {
                "total_payments": self.total_amount,
                "total_discounts": self.total_discounts,
                "penalties_avoided": self.total_penalties_avoided,
                "net_savings": self.net_savings,
                "ending_cash": self.ending_cash,
            },
            "cash_flow_impact": self.daily_cash_flow,
            "warnings": self.warnings,
        }


class PaymentOptimizer:
    """Optimizes payment scheduling."""
    
    def __init__(self, customer_id: str):
        self.customer_id = customer_id
    
    def optimize(
        self,
        items: List[PaymentItem],
        available_cash: float,
        minimum_reserve: float,
        expected_inflows: List[Dict] = None,
        goal: OptimizationGoal = OptimizationGoal.BALANCE_ALL,
        date_range_days: int = 30,
    ) -> OptimizationResult:
        """Optimize payment schedule."""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = today + timedelta(days=date_range_days)
        
        # Initialize
        scheduled = []
        current_cash = available_cash
        warnings = []
        
        # Convert expected inflows to dict by date
        inflows_by_date = {}
        for inflow in (expected_inflows or []):
            date = inflow.get("date")
            if isinstance(date, str):
                date = datetime.fromisoformat(date.replace("Z", "+00:00")).date()
            elif isinstance(date, datetime):
                date = date.date()
            
            if date not in inflows_by_date:
                inflows_by_date[date] = 0
            inflows_by_date[date] += inflow.get("amount", 0)
        
        # Sort items by optimization criteria
        sorted_items = self._sort_items(items, goal, today)
        
        # Track daily cash
        daily_cash = {today.date(): current_cash}
        
        for item in sorted_items:
            # Determine optimal payment date
            optimal_date, reason = self._find_optimal_date(
                item, today, end_date, goal, current_cash, minimum_reserve
            )
            
            # Calculate amounts
            discount = 0
            penalty_avoided = 0
            amount_to_pay = item.amount
            
            # Check for early discount
            if item.early_discount_percent > 0 and item.early_discount_days > 0:
                discount_deadline = item.due_date - timedelta(days=item.early_discount_days)
                if optimal_date <= discount_deadline:
                    discount = item.amount * (item.early_discount_percent / 100)
                    amount_to_pay = item.amount - discount
                    reason = f"{item.early_discount_percent}% early payment discount"
            
            # Check if we're avoiding a late penalty
            if optimal_date <= item.due_date and item.late_penalty_percent > 0:
                # Calculate what penalty would have been if paid late
                penalty_avoided = item.amount * (item.late_penalty_percent / 100)
            
            # Check cash availability
            # Simulate cash on scheduled date
            simulated_cash = current_cash
            for d in range((optimal_date - today).days):
                check_date = (today + timedelta(days=d)).date()
                simulated_cash += inflows_by_date.get(check_date, 0)
            
            if simulated_cash - amount_to_pay < minimum_reserve:
                # Try to push payment later
                pushed_date = self._find_viable_date(
                    item, optimal_date, end_date, simulated_cash, minimum_reserve, inflows_by_date
                )
                
                if pushed_date:
                    optimal_date = pushed_date
                    reason = "Delayed to maintain cash reserve"
                    discount = 0  # Lost the discount
                    amount_to_pay = item.amount
                else:
                    warnings.append(f"Insufficient cash for {item.vendor_name} (${item.amount:,.2f})")
                    continue
            
            # Schedule payment
            scheduled.append(ScheduledPayment(
                item=item,
                scheduled_date=optimal_date,
                amount_to_pay=amount_to_pay,
                discount_captured=discount,
                penalty_avoided=penalty_avoided,
                reason=reason,
            ))
            
            # Update cash tracking
            pay_date = optimal_date.date()
            if pay_date not in daily_cash:
                daily_cash[pay_date] = simulated_cash
            daily_cash[pay_date] -= amount_to_pay
        
        # Calculate totals
        total_amount = sum(p.amount_to_pay for p in scheduled)
        total_discounts = sum(p.discount_captured for p in scheduled)
        total_penalties_avoided = sum(p.penalty_avoided for p in scheduled)
        
        # Build daily cash flow
        dates = sorted(daily_cash.keys())
        cash_flow = []
        running_balance = available_cash
        
        for d in dates:
            day_payments = sum(
                p.amount_to_pay for p in scheduled
                if p.scheduled_date.date() == d
            )
            day_inflows = inflows_by_date.get(d, 0)
            running_balance = running_balance + day_inflows - day_payments
            
            cash_flow.append({
                "date": d.isoformat(),
                "inflows": day_inflows,
                "outflows": day_payments,
                "balance": running_balance,
            })
        
        return OptimizationResult(
            scheduled_payments=scheduled,
            total_amount=total_amount,
            total_discounts=total_discounts,
            total_penalties_avoided=total_penalties_avoided,
            net_savings=total_discounts + total_penalties_avoided,
            ending_cash=running_balance,
            daily_cash_flow=cash_flow,
            warnings=warnings,
        )
    
    def _sort_items(self, items: List[PaymentItem], goal: OptimizationGoal, today: datetime) -> List[PaymentItem]:
        """Sort items based on optimization goal."""
        
        def score(item: PaymentItem) -> float:
            s = 0
            days_to_due = (item.due_date - today).days
            
            if goal == OptimizationGoal.MAXIMIZE_DISCOUNTS:
                # Prioritize items with early discounts about to expire
                if item.early_discount_percent > 0:
                    discount_value = item.amount * (item.early_discount_percent / 100)
                    days_to_discount = days_to_due - item.early_discount_days
                    if days_to_discount <= 7:
                        s = discount_value * 10  # High priority
                    else:
                        s = discount_value
            
            elif goal == OptimizationGoal.MINIMIZE_PENALTIES:
                # Prioritize items closest to due date
                if days_to_due <= 0:
                    s = 10000 + item.amount  # Past due, highest priority
                elif days_to_due <= 7:
                    s = 5000 + item.amount
                else:
                    s = item.amount
            
            elif goal == OptimizationGoal.OPTIMIZE_CASH_FLOW:
                # Delay payments as long as possible without penalties
                s = -days_to_due * 100  # Negative = later payments first
                
            else:  # BALANCE_ALL
                # Weighted combination
                discount_score = item.amount * (item.early_discount_percent / 100) * 2
                urgency_score = max(0, 30 - days_to_due) * 10
                priority_score = item.vendor_priority * 5
                s = discount_score + urgency_score + priority_score
            
            return s
        
        return sorted(items, key=score, reverse=True)
    
    def _find_optimal_date(
        self,
        item: PaymentItem,
        today: datetime,
        end_date: datetime,
        goal: OptimizationGoal,
        cash: float,
        min_reserve: float,
    ) -> Tuple[datetime, str]:
        """Find optimal payment date for an item."""
        
        # If has early discount and goal includes discounts
        if item.early_discount_percent > 0 and goal in [
            OptimizationGoal.MAXIMIZE_DISCOUNTS,
            OptimizationGoal.BALANCE_ALL,
        ]:
            discount_deadline = item.due_date - timedelta(days=item.early_discount_days)
            if discount_deadline >= today:
                return discount_deadline, f"Capture {item.early_discount_percent}% discount"
        
        # For cash flow optimization, pay on due date
        if goal == OptimizationGoal.OPTIMIZE_CASH_FLOW:
            return item.due_date, "Pay on due date to maximize cash"
        
        # Default: pay a few days before due
        optimal = item.due_date - timedelta(days=3)
        if optimal < today:
            optimal = today
        
        return optimal, "Standard payment timing"
    
    def _find_viable_date(
        self,
        item: PaymentItem,
        start_date: datetime,
        end_date: datetime,
        current_cash: float,
        min_reserve: float,
        inflows: Dict,
    ) -> Optional[datetime]:
        """Find a viable date when cash is available."""
        cash = current_cash
        
        for d in range((end_date - start_date).days):
            check_date = start_date + timedelta(days=d)
            check_date_key = check_date.date()
            
            cash += inflows.get(check_date_key, 0)
            
            if cash - item.amount >= min_reserve:
                return check_date
        
        return None


# Service wrapper
class PaymentOptimizerService:
    """Service for payment optimization."""
    
    def __init__(self):
        self._optimizers: Dict[str, PaymentOptimizer] = {}
    
    def get_optimizer(self, customer_id: str) -> PaymentOptimizer:
        """Get optimizer for customer."""
        if customer_id not in self._optimizers:
            self._optimizers[customer_id] = PaymentOptimizer(customer_id)
        return self._optimizers[customer_id]
    
    def optimize_payments(
        self,
        customer_id: str,
        pending_bills: List[Dict],
        available_cash: float,
        minimum_reserve: float,
        expected_inflows: List[Dict] = None,
        goal: str = "balance_all",
        date_range_days: int = 30,
    ) -> Dict:
        """Optimize payment schedule."""
        optimizer = self.get_optimizer(customer_id)
        
        # Convert bills to PaymentItems
        items = []
        for bill in pending_bills:
            due_date = bill.get("due_date")
            if isinstance(due_date, str):
                due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
            
            items.append(PaymentItem(
                id=bill.get("id"),
                vendor_id=bill.get("vendor_id", ""),
                vendor_name=bill.get("vendor_name", "Unknown"),
                amount=bill.get("amount", 0),
                due_date=due_date,
                invoice_number=bill.get("invoice_number", ""),
                early_discount_percent=bill.get("early_discount_percent", 0),
                early_discount_days=bill.get("early_discount_days", 0),
                late_penalty_percent=bill.get("late_penalty_percent", 0),
                vendor_priority=bill.get("vendor_priority", 5),
            ))
        
        # Run optimization
        result = optimizer.optimize(
            items=items,
            available_cash=available_cash,
            minimum_reserve=minimum_reserve,
            expected_inflows=expected_inflows,
            goal=OptimizationGoal(goal),
            date_range_days=date_range_days,
        )
        
        return result.to_dict()


# Global service instance
payment_optimizer_service = PaymentOptimizerService()
```

---

## File 4: Insights Generator
**Path:** `backend/app/ai/insights/generator.py`

```python
"""
Insights Generator
AI-powered business insights and recommendations
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging

from app.ai.base import Recommendation
from app.ai.client import ai_client

logger = logging.getLogger(__name__)


class InsightType(str, Enum):
    """Types of insights."""
    REVENUE_TREND = "revenue_trend"
    EXPENSE_ALERT = "expense_alert"
    CASH_FLOW = "cash_flow"
    CUSTOMER_BEHAVIOR = "customer_behavior"
    COLLECTION_RISK = "collection_risk"
    PROFITABILITY = "profitability"
    GROWTH_OPPORTUNITY = "growth_opportunity"
    COST_OPTIMIZATION = "cost_optimization"


@dataclass
class Insight:
    """Business insight."""
    id: str
    type: InsightType
    title: str
    summary: str
    details: str
    impact: str  # positive, negative, neutral
    priority: int  # 1-10
    data: Dict = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "summary": self.summary,
            "details": self.details,
            "impact": self.impact,
            "priority": self.priority,
            "data": self.data,
            "recommendations": self.recommendations,
            "created_at": self.created_at.isoformat(),
        }


class InsightsGenerator:
    """Generates business insights from data."""
    
    def __init__(self, customer_id: str):
        self.customer_id = customer_id
    
    async def generate_insights(self, data: Dict) -> List[Insight]:
        """Generate insights from business data."""
        insights = []
        
        # Revenue insights
        if "revenue" in data:
            revenue_insights = self._analyze_revenue(data["revenue"])
            insights.extend(revenue_insights)
        
        # Expense insights
        if "expenses" in data:
            expense_insights = self._analyze_expenses(data["expenses"])
            insights.extend(expense_insights)
        
        # Cash flow insights
        if "cash_flow" in data:
            cash_insights = self._analyze_cash_flow(data["cash_flow"])
            insights.extend(cash_insights)
        
        # Customer insights
        if "customers" in data:
            customer_insights = self._analyze_customers(data["customers"])
            insights.extend(customer_insights)
        
        # Receivables insights
        if "receivables" in data:
            ar_insights = self._analyze_receivables(data["receivables"])
            insights.extend(ar_insights)
        
        # Sort by priority
        insights.sort(key=lambda i: i.priority, reverse=True)
        
        return insights
    
    def _analyze_revenue(self, revenue_data: Dict) -> List[Insight]:
        """Analyze revenue trends."""
        insights = []
        
        current = revenue_data.get("current_period", 0)
        previous = revenue_data.get("previous_period", 0)
        
        if previous > 0:
            change = (current - previous) / previous
            
            if change > 0.1:
                insights.append(Insight(
                    id=f"insight_rev_{datetime.utcnow().timestamp()}",
                    type=InsightType.REVENUE_TREND,
                    title="Revenue Growth",
                    summary=f"Revenue increased {change:.1%} this period",
                    details=f"Your revenue grew from ${previous:,.2f} to ${current:,.2f}, a {change:.1%} increase.",
                    impact="positive",
                    priority=7,
                    data={"current": current, "previous": previous, "change": change},
                    recommendations=[
                        "Identify which customers or products drove growth",
                        "Consider investing in top-performing areas",
                    ],
                ))
            elif change < -0.1:
                insights.append(Insight(
                    id=f"insight_rev_{datetime.utcnow().timestamp()}",
                    type=InsightType.REVENUE_TREND,
                    title="Revenue Decline",
                    summary=f"Revenue decreased {abs(change):.1%} this period",
                    details=f"Your revenue dropped from ${previous:,.2f} to ${current:,.2f}, a {abs(change):.1%} decrease.",
                    impact="negative",
                    priority=9,
                    data={"current": current, "previous": previous, "change": change},
                    recommendations=[
                        "Review lost customers or reduced orders",
                        "Analyze pricing and market conditions",
                        "Consider promotional campaigns",
                    ],
                ))
        
        return insights
    
    def _analyze_expenses(self, expense_data: Dict) -> List[Insight]:
        """Analyze expense patterns."""
        insights = []
        
        categories = expense_data.get("by_category", {})
        total = sum(categories.values())
        
        # Find largest expense category
        if categories:
            largest_cat = max(categories, key=categories.get)
            largest_amt = categories[largest_cat]
            pct = largest_amt / total if total > 0 else 0
            
            if pct > 0.4:
                insights.append(Insight(
                    id=f"insight_exp_{datetime.utcnow().timestamp()}",
                    type=InsightType.EXPENSE_ALERT,
                    title=f"High {largest_cat.title()} Expenses",
                    summary=f"{largest_cat.title()} represents {pct:.0%} of total expenses",
                    details=f"You're spending ${largest_amt:,.2f} on {largest_cat}, which is {pct:.0%} of your total expenses of ${total:,.2f}.",
                    impact="neutral",
                    priority=5,
                    data={"category": largest_cat, "amount": largest_amt, "percentage": pct},
                    recommendations=[
                        f"Review {largest_cat} vendors for better rates",
                        "Consider if all expenses in this category are necessary",
                    ],
                ))
        
        return insights
    
    def _analyze_cash_flow(self, cash_data: Dict) -> List[Insight]:
        """Analyze cash flow health."""
        insights = []
        
        current_balance = cash_data.get("current_balance", 0)
        runway_days = cash_data.get("runway_days", 0)
        burn_rate = cash_data.get("monthly_burn_rate", 0)
        
        if runway_days < 30:
            insights.append(Insight(
                id=f"insight_cash_{datetime.utcnow().timestamp()}",
                type=InsightType.CASH_FLOW,
                title="Low Cash Runway",
                summary=f"Only {runway_days} days of cash remaining",
                details=f"At current burn rate of ${burn_rate:,.2f}/month, your cash balance of ${current_balance:,.2f} will last approximately {runway_days} days.",
                impact="negative",
                priority=10,
                data={"balance": current_balance, "runway": runway_days, "burn_rate": burn_rate},
                recommendations=[
                    "Accelerate collection of receivables",
                    "Negotiate extended payment terms with vendors",
                    "Consider reducing discretionary spending",
                ],
            ))
        elif runway_days < 90:
            insights.append(Insight(
                id=f"insight_cash_{datetime.utcnow().timestamp()}",
                type=InsightType.CASH_FLOW,
                title="Monitor Cash Position",
                summary=f"Approximately {runway_days} days of cash remaining",
                details=f"Your cash position is adequate but should be monitored. Current balance: ${current_balance:,.2f}.",
                impact="neutral",
                priority=6,
                data={"balance": current_balance, "runway": runway_days},
                recommendations=[
                    "Review upcoming large expenses",
                    "Ensure invoices are sent promptly",
                ],
            ))
        
        return insights
    
    def _analyze_customers(self, customer_data: Dict) -> List[Insight]:
        """Analyze customer behavior."""
        insights = []
        
        # Top customers concentration
        top_customers = customer_data.get("top_customers", [])
        total_revenue = customer_data.get("total_revenue", 0)
        
        if top_customers and total_revenue > 0:
            top_revenue = sum(c.get("revenue", 0) for c in top_customers[:3])
            concentration = top_revenue / total_revenue
            
            if concentration > 0.5:
                insights.append(Insight(
                    id=f"insight_cust_{datetime.utcnow().timestamp()}",
                    type=InsightType.CUSTOMER_BEHAVIOR,
                    title="High Customer Concentration",
                    summary=f"Top 3 customers represent {concentration:.0%} of revenue",
                    details="High dependency on few customers increases business risk.",
                    impact="neutral",
                    priority=6,
                    data={"concentration": concentration, "top_customers": top_customers[:3]},
                    recommendations=[
                        "Develop relationships with more customers",
                        "Create customer retention programs for top accounts",
                    ],
                ))
        
        return insights
    
    def _analyze_receivables(self, ar_data: Dict) -> List[Insight]:
        """Analyze accounts receivable."""
        insights = []
        
        total_ar = ar_data.get("total", 0)
        overdue = ar_data.get("overdue", 0)
        avg_days = ar_data.get("average_days", 0)
        
        if total_ar > 0:
            overdue_pct = overdue / total_ar
            
            if overdue_pct > 0.2:
                insights.append(Insight(
                    id=f"insight_ar_{datetime.utcnow().timestamp()}",
                    type=InsightType.COLLECTION_RISK,
                    title="High Overdue Receivables",
                    summary=f"{overdue_pct:.0%} of receivables are overdue",
                    details=f"${overdue:,.2f} of your ${total_ar:,.2f} in receivables is past due.",
                    impact="negative",
                    priority=8,
                    data={"total": total_ar, "overdue": overdue, "percentage": overdue_pct},
                    recommendations=[
                        "Send reminder emails to overdue accounts",
                        "Consider offering early payment discounts",
                        "Review credit terms for repeat offenders",
                    ],
                ))
        
        if avg_days > 45:
            insights.append(Insight(
                id=f"insight_dso_{datetime.utcnow().timestamp()}",
                type=InsightType.COLLECTION_RISK,
                title="High Days Sales Outstanding",
                summary=f"Average collection time is {avg_days:.0f} days",
                details=f"Your customers are taking an average of {avg_days:.0f} days to pay invoices.",
                impact="negative",
                priority=7,
                data={"average_days": avg_days},
                recommendations=[
                    "Consider stricter payment terms for new customers",
                    "Implement automated payment reminders",
                    "Offer incentives for faster payment",
                ],
            ))
        
        return insights
    
    async def generate_ai_summary(self, insights: List[Insight]) -> str:
        """Generate AI-powered natural language summary."""
        if not insights:
            return "No significant insights to report at this time."
        
        # Build context from insights
        insight_texts = []
        for insight in insights[:5]:  # Top 5 insights
            insight_texts.append(f"- {insight.title}: {insight.summary}")
        
        prompt = f"""Based on these business insights, write a brief (2-3 sentence) executive summary:

{chr(10).join(insight_texts)}

Focus on the most important actionable items. Be concise and professional."""
        
        try:
            summary = await ai_client.complete(prompt)
            return summary
        except Exception as e:
            logger.error(f"AI summary generation failed: {e}")
            # Fallback to simple summary
            return f"Key findings: {insights[0].summary if insights else 'No significant changes detected.'}"


# Service wrapper
class InsightsService:
    """Service for business insights."""
    
    def __init__(self):
        self._generators: Dict[str, InsightsGenerator] = {}
    
    def get_generator(self, customer_id: str) -> InsightsGenerator:
        """Get generator for customer."""
        if customer_id not in self._generators:
            self._generators[customer_id] = InsightsGenerator(customer_id)
        return self._generators[customer_id]
    
    async def generate_dashboard_insights(self, customer_id: str, data: Dict) -> Dict:
        """Generate insights for dashboard."""
        generator = self.get_generator(customer_id)
        
        insights = await generator.generate_insights(data)
        summary = await generator.generate_ai_summary(insights)
        
        return {
            "summary": summary,
            "insights": [i.to_dict() for i in insights],
            "generated_at": datetime.utcnow().isoformat(),
        }


# Global service instance
insights_service = InsightsService()
```

---

## File 5: Anomaly Module Init
**Path:** `backend/app/ai/anomaly/__init__.py`

```python
"""
Anomaly Detection Module
"""

from app.ai.anomaly.detector import (
    AnomalyDetector,
    AnomalyType,
    AnomalyRule,
)
from app.ai.anomaly.service import AnomalyService, anomaly_service


__all__ = [
    'AnomalyDetector',
    'AnomalyType',
    'AnomalyRule',
    'AnomalyService',
    'anomaly_service',
]
```

---

## Summary Part 5

| File | Description | Lines |
|------|-------------|-------|
| `anomaly/detector.py` | Anomaly detection engine | ~450 |
| `anomaly/service.py` | Anomaly service layer | ~180 |
| `optimizer/payment_scheduler.py` | Payment optimization | ~400 |
| `insights/generator.py` | Business insights | ~350 |
| `anomaly/__init__.py` | Module initialization | ~20 |
| **Total** | | **~1,400 lines** |
