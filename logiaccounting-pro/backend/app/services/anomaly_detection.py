"""
Anomaly Detection & Fraud Prevention Service
Detects duplicate invoices, unusual price variations, and anomalous spending patterns
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import math

# Optional ML imports
try:
    import numpy as np
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


@dataclass
class Anomaly:
    """Detected anomaly structure"""
    id: str
    type: str  # duplicate_invoice, price_variation, spending_spike, unusual_pattern
    severity: str  # low, medium, high, critical
    title: str
    description: str
    affected_items: List[Dict]
    detection_method: str
    confidence: float
    recommendations: List[str]
    detected_at: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AnomalyReport:
    """Complete anomaly detection report"""
    generated_at: str
    total_anomalies: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    anomalies: List[Dict]
    risk_score: float
    summary: str

    def to_dict(self) -> Dict:
        return asdict(self)


class AnomalyDetectionService:
    """
    Intelligent Anomaly Detection for Financial Data

    Features:
    - Duplicate invoice detection
    - Price variation analysis
    - Spending pattern anomalies
    - Vendor behavior analysis
    - Statistical outlier detection
    - ML-based pattern recognition
    """

    # Thresholds for anomaly detection
    PRICE_VARIATION_THRESHOLD = 0.25  # 25% price change triggers alert
    SPENDING_SPIKE_MULTIPLIER = 2.5   # 2.5x average triggers spike alert
    DUPLICATE_SIMILARITY_THRESHOLD = 0.9
    Z_SCORE_THRESHOLD = 2.5  # Standard deviations for outlier

    def __init__(self, db):
        self.db = db
        self._anomaly_counter = 0

    def run_full_scan(self) -> AnomalyReport:
        """
        Run comprehensive anomaly detection across all data
        """
        anomalies = []

        # Run all detection methods
        anomalies.extend(self._detect_duplicate_invoices())
        anomalies.extend(self._detect_price_variations())
        anomalies.extend(self._detect_spending_spikes())
        anomalies.extend(self._detect_vendor_anomalies())

        if SKLEARN_AVAILABLE:
            anomalies.extend(self._detect_ml_anomalies())

        # Count by severity
        critical = len([a for a in anomalies if a.severity == "critical"])
        high = len([a for a in anomalies if a.severity == "high"])
        medium = len([a for a in anomalies if a.severity == "medium"])
        low = len([a for a in anomalies if a.severity == "low"])

        # Calculate risk score (0-100)
        risk_score = min(100, critical * 25 + high * 15 + medium * 5 + low * 2)

        # Generate summary
        if critical > 0:
            summary = f"CRITICAL: {critical} critical anomalies require immediate attention"
        elif high > 0:
            summary = f"WARNING: {high} high-severity anomalies detected"
        elif medium > 0:
            summary = f"NOTICE: {medium} medium-severity anomalies found"
        elif low > 0:
            summary = f"INFO: {low} low-severity anomalies detected"
        else:
            summary = "No anomalies detected. All data appears normal."

        return AnomalyReport(
            generated_at=datetime.utcnow().isoformat(),
            total_anomalies=len(anomalies),
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            anomalies=[a.to_dict() for a in anomalies],
            risk_score=risk_score,
            summary=summary
        )

    def _generate_anomaly_id(self) -> str:
        """Generate unique anomaly ID"""
        self._anomaly_counter += 1
        return f"ANO-{datetime.utcnow().strftime('%Y%m%d')}-{self._anomaly_counter:04d}"

    def _detect_duplicate_invoices(self) -> List[Anomaly]:
        """
        Detect potential duplicate invoices based on:
        - Same invoice number
        - Same amount and date
        - Same vendor and similar amount
        """
        anomalies = []
        transactions = self.db.transactions.find_all()

        # Group by invoice number
        by_invoice = defaultdict(list)
        for tx in transactions:
            inv_num = tx.get("invoice_number")
            if inv_num:
                by_invoice[inv_num.upper().strip()].append(tx)

        # Check for exact duplicates
        for inv_num, txs in by_invoice.items():
            if len(txs) > 1:
                total_amount = sum(t.get("amount", 0) for t in txs)
                anomalies.append(Anomaly(
                    id=self._generate_anomaly_id(),
                    type="duplicate_invoice",
                    severity="high",
                    title=f"Duplicate Invoice: {inv_num}",
                    description=f"Invoice {inv_num} appears {len(txs)} times with total amount ${total_amount:,.2f}",
                    affected_items=[{"transaction_id": t["id"], "amount": t.get("amount")} for t in txs],
                    detection_method="exact_match",
                    confidence=1.0,
                    recommendations=[
                        "Review transactions for duplicate entry",
                        "Verify with vendor if multiple payments were intended",
                        "Check if refund or reversal is needed"
                    ],
                    detected_at=datetime.utcnow().isoformat()
                ))

        # Check for same amount + date combinations (potential duplicates without invoice numbers)
        by_amount_date = defaultdict(list)
        for tx in transactions:
            if tx.get("type") == "expense":
                amount = tx.get("amount", 0)
                date = (tx.get("date") or tx.get("created_at", ""))[:10]
                key = f"{amount:.2f}_{date}"
                by_amount_date[key].append(tx)

        for key, txs in by_amount_date.items():
            if len(txs) > 1:
                # Only flag if significant amount
                amount = txs[0].get("amount", 0)
                if amount >= 100:  # Only flag amounts >= $100
                    anomalies.append(Anomaly(
                        id=self._generate_anomaly_id(),
                        type="duplicate_invoice",
                        severity="medium",
                        title=f"Potential Duplicate: Same Amount & Date",
                        description=f"{len(txs)} transactions of ${amount:,.2f} on the same date",
                        affected_items=[{"transaction_id": t["id"], "description": t.get("description")} for t in txs],
                        detection_method="amount_date_match",
                        confidence=0.7,
                        recommendations=[
                            "Verify these are separate legitimate transactions",
                            "Check for data entry errors",
                            "Add invoice numbers to prevent future confusion"
                        ],
                        detected_at=datetime.utcnow().isoformat()
                    ))

        return anomalies

    def _detect_price_variations(self) -> List[Anomaly]:
        """
        Detect unusual price variations for same vendor/item
        """
        anomalies = []
        transactions = self.db.transactions.find_all()

        # Group by vendor
        by_vendor = defaultdict(list)
        for tx in transactions:
            vendor = tx.get("vendor_name") or tx.get("supplier_id")
            if vendor and tx.get("type") == "expense":
                by_vendor[vendor].append(tx)

        for vendor, txs in by_vendor.items():
            if len(txs) < 3:
                continue

            amounts = [t.get("amount", 0) for t in txs]
            avg_amount = sum(amounts) / len(amounts)
            std_amount = self._calculate_std(amounts)

            if std_amount == 0:
                continue

            # Find outliers
            outliers = []
            for tx in txs:
                amount = tx.get("amount", 0)
                z_score = abs(amount - avg_amount) / std_amount

                if z_score > self.Z_SCORE_THRESHOLD:
                    variation = (amount - avg_amount) / avg_amount if avg_amount > 0 else 0
                    if abs(variation) > self.PRICE_VARIATION_THRESHOLD:
                        outliers.append({
                            "transaction_id": tx["id"],
                            "amount": amount,
                            "average": round(avg_amount, 2),
                            "variation_percent": round(variation * 100, 1),
                            "date": tx.get("date") or tx.get("created_at", "")[:10]
                        })

            if outliers:
                severity = "high" if any(o["variation_percent"] > 50 for o in outliers) else "medium"
                anomalies.append(Anomaly(
                    id=self._generate_anomaly_id(),
                    type="price_variation",
                    severity=severity,
                    title=f"Unusual Price Variation: {vendor[:30] if isinstance(vendor, str) else 'Vendor'}",
                    description=f"{len(outliers)} transaction(s) with unusual amounts (avg: ${avg_amount:,.2f})",
                    affected_items=outliers,
                    detection_method="statistical_z_score",
                    confidence=0.85,
                    recommendations=[
                        "Review pricing agreements with vendor",
                        "Verify invoice amounts are correct",
                        "Check for pricing errors or unauthorized changes"
                    ],
                    detected_at=datetime.utcnow().isoformat()
                ))

        return anomalies

    def _detect_spending_spikes(self) -> List[Anomaly]:
        """
        Detect unusual spending spikes compared to historical patterns
        """
        anomalies = []
        transactions = self.db.transactions.find_all()

        # Group expenses by week
        weekly_spending = defaultdict(float)
        for tx in transactions:
            if tx.get("type") == "expense":
                date_str = tx.get("date") or tx.get("created_at", "")[:10]
                try:
                    date = datetime.fromisoformat(date_str)
                    week_key = date.strftime("%Y-W%W")
                    weekly_spending[week_key] += tx.get("amount", 0)
                except (ValueError, TypeError):
                    pass

        if len(weekly_spending) < 4:
            return anomalies

        # Calculate average and detect spikes
        amounts = list(weekly_spending.values())
        avg_weekly = sum(amounts) / len(amounts)
        std_weekly = self._calculate_std(amounts)

        if std_weekly == 0:
            return anomalies

        for week, amount in weekly_spending.items():
            multiplier = amount / avg_weekly if avg_weekly > 0 else 0

            if multiplier > self.SPENDING_SPIKE_MULTIPLIER:
                z_score = (amount - avg_weekly) / std_weekly

                # Find transactions in this week
                week_txs = [
                    t for t in transactions
                    if t.get("type") == "expense" and
                    (t.get("date") or t.get("created_at", ""))[:10].replace("-", "").startswith(week.replace("-W", ""))
                ]

                severity = "critical" if multiplier > 4 else "high" if multiplier > 3 else "medium"

                anomalies.append(Anomaly(
                    id=self._generate_anomaly_id(),
                    type="spending_spike",
                    severity=severity,
                    title=f"Spending Spike: Week {week}",
                    description=f"${amount:,.2f} spent ({multiplier:.1f}x average of ${avg_weekly:,.2f})",
                    affected_items=[{
                        "transaction_id": t["id"],
                        "amount": t.get("amount"),
                        "description": t.get("description")
                    } for t in week_txs[:10]],
                    detection_method="weekly_comparison",
                    confidence=min(0.95, 0.5 + z_score * 0.1),
                    recommendations=[
                        "Review all transactions in this period",
                        "Identify major purchases or unusual items",
                        "Verify budget approval for large expenses"
                    ],
                    detected_at=datetime.utcnow().isoformat()
                ))

        return anomalies

    def _detect_vendor_anomalies(self) -> List[Anomaly]:
        """
        Detect anomalous vendor behavior patterns
        """
        anomalies = []
        transactions = self.db.transactions.find_all()
        users = self.db.users.find_all()

        vendor_map = {u["id"]: u for u in users if u.get("role") == "supplier"}

        # Analyze vendor patterns
        vendor_stats = defaultdict(lambda: {
            "total": 0,
            "count": 0,
            "dates": [],
            "amounts": [],
            "name": "Unknown"
        })

        for tx in transactions:
            if tx.get("type") == "expense":
                vendor_id = tx.get("supplier_id")
                if vendor_id:
                    vendor_stats[vendor_id]["total"] += tx.get("amount", 0)
                    vendor_stats[vendor_id]["count"] += 1
                    vendor_stats[vendor_id]["amounts"].append(tx.get("amount", 0))
                    date_str = tx.get("date") or tx.get("created_at", "")[:10]
                    vendor_stats[vendor_id]["dates"].append(date_str)
                    if vendor_id in vendor_map:
                        vendor_stats[vendor_id]["name"] = vendor_map[vendor_id].get("company_name", "Unknown")

        # Detect sudden new high-value vendors
        today = datetime.utcnow()
        thirty_days_ago = (today - timedelta(days=30)).isoformat()[:10]

        for vendor_id, stats in vendor_stats.items():
            # New vendor with high spending
            if stats["dates"]:
                first_date = min(stats["dates"])
                if first_date >= thirty_days_ago and stats["total"] > 10000:
                    anomalies.append(Anomaly(
                        id=self._generate_anomaly_id(),
                        type="unusual_pattern",
                        severity="medium",
                        title=f"New High-Value Vendor: {stats['name'][:30]}",
                        description=f"New vendor with ${stats['total']:,.2f} in spending over {stats['count']} transactions",
                        affected_items=[{
                            "vendor_id": vendor_id,
                            "vendor_name": stats["name"],
                            "total_spending": stats["total"],
                            "transaction_count": stats["count"]
                        }],
                        detection_method="new_vendor_analysis",
                        confidence=0.75,
                        recommendations=[
                            "Verify vendor credentials and legitimacy",
                            "Review all transactions with this vendor",
                            "Ensure proper vendor onboarding was completed"
                        ],
                        detected_at=datetime.utcnow().isoformat()
                    ))

            # Unusual transaction frequency
            if stats["count"] > 10:
                # Check for suspiciously round amounts
                round_amounts = [a for a in stats["amounts"] if a == int(a) and a % 100 == 0]
                if len(round_amounts) / stats["count"] > 0.8:
                    anomalies.append(Anomaly(
                        id=self._generate_anomaly_id(),
                        type="unusual_pattern",
                        severity="low",
                        title=f"Round Amount Pattern: {stats['name'][:30]}",
                        description=f"{len(round_amounts)} of {stats['count']} transactions are suspiciously round amounts",
                        affected_items=[{
                            "vendor_id": vendor_id,
                            "vendor_name": stats["name"],
                            "round_amount_count": len(round_amounts),
                            "total_transactions": stats["count"]
                        }],
                        detection_method="pattern_analysis",
                        confidence=0.6,
                        recommendations=[
                            "Review invoice details for these transactions",
                            "Verify actual services/goods received",
                            "Consider more detailed expense tracking"
                        ],
                        detected_at=datetime.utcnow().isoformat()
                    ))

        return anomalies

    def _detect_ml_anomalies(self) -> List[Anomaly]:
        """
        Use Isolation Forest for ML-based anomaly detection
        """
        if not SKLEARN_AVAILABLE:
            return []

        anomalies = []
        transactions = self.db.transactions.find_all()

        if len(transactions) < 20:
            return anomalies

        # Prepare features for ML
        features = []
        tx_ids = []

        for tx in transactions:
            if tx.get("type") == "expense":
                amount = tx.get("amount", 0)
                tax = tx.get("tax_amount", 0)
                date_str = tx.get("date") or tx.get("created_at", "")[:10]

                try:
                    date = datetime.fromisoformat(date_str)
                    day_of_week = date.weekday()
                    day_of_month = date.day
                    hour = date.hour if hasattr(date, 'hour') else 12
                except (ValueError, TypeError):
                    day_of_week = 0
                    day_of_month = 15
                    hour = 12

                features.append([amount, tax, day_of_week, day_of_month, hour])
                tx_ids.append(tx["id"])

        if len(features) < 10:
            return anomalies

        # Scale features
        X = np.array(features)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Train Isolation Forest
        clf = IsolationForest(
            contamination=0.1,  # Expect ~10% anomalies
            random_state=42,
            n_estimators=100
        )
        predictions = clf.fit_predict(X_scaled)
        scores = clf.decision_function(X_scaled)

        # Find anomalies (predictions == -1)
        for i, (pred, score) in enumerate(zip(predictions, scores)):
            if pred == -1:
                tx_id = tx_ids[i]
                tx = next((t for t in transactions if t["id"] == tx_id), None)
                if tx:
                    # Normalize score to confidence
                    confidence = min(1.0, max(0.5, 0.5 - score))

                    anomalies.append(Anomaly(
                        id=self._generate_anomaly_id(),
                        type="unusual_pattern",
                        severity="medium" if confidence > 0.7 else "low",
                        title=f"ML-Detected Anomaly: ${tx.get('amount', 0):,.2f}",
                        description=f"Machine learning detected unusual pattern in transaction",
                        affected_items=[{
                            "transaction_id": tx_id,
                            "amount": tx.get("amount"),
                            "description": tx.get("description"),
                            "date": tx.get("date") or tx.get("created_at", "")[:10],
                            "anomaly_score": round(-score, 3)
                        }],
                        detection_method="isolation_forest_ml",
                        confidence=round(confidence, 2),
                        recommendations=[
                            "Review transaction details manually",
                            "Verify transaction authenticity",
                            "Check for data entry errors"
                        ],
                        detected_at=datetime.utcnow().isoformat()
                    ))

        return anomalies[:10]  # Limit ML anomalies to top 10

    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)

    def check_single_transaction(self, transaction: Dict) -> List[Anomaly]:
        """
        Check a single transaction for anomalies (for real-time detection)
        """
        anomalies = []
        transactions = self.db.transactions.find_all()

        amount = transaction.get("amount", 0)
        invoice_num = transaction.get("invoice_number")
        vendor = transaction.get("vendor_name") or transaction.get("supplier_id")

        # Check for duplicate invoice
        if invoice_num:
            existing = [t for t in transactions
                       if t.get("invoice_number", "").upper() == invoice_num.upper()
                       and t["id"] != transaction.get("id")]
            if existing:
                anomalies.append(Anomaly(
                    id=self._generate_anomaly_id(),
                    type="duplicate_invoice",
                    severity="high",
                    title=f"Duplicate Invoice Detected: {invoice_num}",
                    description="This invoice number already exists in the system",
                    affected_items=[{"transaction_id": e["id"]} for e in existing],
                    detection_method="real_time_check",
                    confidence=1.0,
                    recommendations=["Verify this is not a duplicate entry"],
                    detected_at=datetime.utcnow().isoformat()
                ))

        # Check price variation for vendor
        if vendor:
            vendor_txs = [t for t in transactions
                        if (t.get("vendor_name") == vendor or t.get("supplier_id") == vendor)
                        and t.get("type") == "expense"]

            if len(vendor_txs) >= 3:
                amounts = [t.get("amount", 0) for t in vendor_txs]
                avg = sum(amounts) / len(amounts)
                std = self._calculate_std(amounts)

                if std > 0:
                    z_score = abs(amount - avg) / std
                    if z_score > self.Z_SCORE_THRESHOLD:
                        variation = (amount - avg) / avg if avg > 0 else 0
                        anomalies.append(Anomaly(
                            id=self._generate_anomaly_id(),
                            type="price_variation",
                            severity="medium",
                            title=f"Unusual Amount for Vendor",
                            description=f"Amount ${amount:,.2f} varies {abs(variation)*100:.1f}% from average ${avg:,.2f}",
                            affected_items=[{"amount": amount, "average": round(avg, 2)}],
                            detection_method="real_time_check",
                            confidence=0.8,
                            recommendations=["Verify the amount is correct"],
                            detected_at=datetime.utcnow().isoformat()
                        ))

        return anomalies


# Service instance factory
def create_anomaly_detector(db) -> AnomalyDetectionService:
    return AnomalyDetectionService(db)
