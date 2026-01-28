"""
Anomaly Detector
Statistical and rule-based anomaly detection
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from app.utils.datetime_utils import utc_now
from ...config import get_ai_config
from ...models.anomaly import Anomaly

logger = logging.getLogger(__name__)


@dataclass
class Transaction:
    """Transaction data for analysis"""
    id: str
    date: datetime
    amount: float
    type: str
    category: Optional[str] = None
    vendor: Optional[str] = None
    description: Optional[str] = None
    user_id: Optional[str] = None


class AnomalyDetector:
    """Detect anomalies in financial data"""

    def __init__(self):
        self.config = get_ai_config()

    def detect_transaction_anomalies(
        self,
        tenant_id: str,
        transactions: List[Dict[str, Any]],
        historical_transactions: List[Dict[str, Any]] = None,
    ) -> List[Anomaly]:
        """
        Detect anomalies in transactions

        Args:
            tenant_id: Tenant ID
            transactions: Recent transactions to analyze
            historical_transactions: Historical data for baseline

        Returns:
            List of detected anomalies
        """
        anomalies = []

        # Parse transactions
        parsed = [self._parse_transaction(t) for t in transactions]
        historical = [self._parse_transaction(t) for t in (historical_transactions or [])]

        # Run detection methods
        anomalies.extend(self._detect_amount_anomalies(tenant_id, parsed, historical))
        anomalies.extend(self._detect_frequency_anomalies(tenant_id, parsed, historical))
        anomalies.extend(self._detect_timing_anomalies(tenant_id, parsed))
        anomalies.extend(self._detect_duplicate_anomalies(tenant_id, parsed))

        # Save anomalies
        for anomaly in anomalies:
            anomaly.save()

        return anomalies

    def _parse_transaction(self, data: Dict[str, Any]) -> Transaction:
        """Parse transaction data"""
        txn_date = data.get('date')
        if isinstance(txn_date, str):
            txn_date = datetime.fromisoformat(txn_date)

        return Transaction(
            id=data.get('id', ''),
            date=txn_date or utc_now(),
            amount=float(data.get('amount', 0)),
            type=data.get('type', 'unknown'),
            category=data.get('category'),
            vendor=data.get('vendor'),
            description=data.get('description'),
            user_id=data.get('user_id'),
        )

    def _detect_amount_anomalies(
        self,
        tenant_id: str,
        transactions: List[Transaction],
        historical: List[Transaction],
    ) -> List[Anomaly]:
        """Detect unusual amounts using z-score"""
        anomalies = []

        if not historical or len(historical) < 10:
            return anomalies

        # Calculate statistics by category
        amounts_by_category = {}
        for txn in historical:
            cat = txn.category or 'uncategorized'
            amounts_by_category.setdefault(cat, []).append(abs(txn.amount))

        for txn in transactions:
            cat = txn.category or 'uncategorized'
            historical_amounts = amounts_by_category.get(cat, [])

            if len(historical_amounts) < 5:
                continue

            mean = statistics.mean(historical_amounts)
            stdev = statistics.stdev(historical_amounts) if len(historical_amounts) > 1 else mean * 0.5

            if stdev == 0:
                continue

            z_score = abs((abs(txn.amount) - mean) / stdev)

            if z_score > self.config.anomaly.zscore_threshold:
                severity = self._calculate_severity(z_score)

                # Check if similar anomaly exists
                if Anomaly.exists(tenant_id, 'transaction', txn.id, 'unusual_amount'):
                    continue

                anomaly = Anomaly(
                    tenant_id=tenant_id,
                    anomaly_type='unusual_amount',
                    severity=severity,
                    risk_score=min(1.0, z_score / 5),
                    entity_type='transaction',
                    entity_id=txn.id,
                    title=f'Unusual transaction amount: ${abs(txn.amount):,.2f}',
                    description=f'Transaction amount is {z_score:.1f} standard deviations from average for {cat}',
                    detection_method='zscore',
                    evidence={
                        'amount': txn.amount,
                        'category': cat,
                        'z_score': z_score,
                        'historical_mean': mean,
                        'historical_stdev': stdev,
                    },
                    related_entities=[
                        {'type': 'vendor', 'id': txn.vendor} if txn.vendor else None,
                    ],
                )
                anomalies.append(anomaly)

        return anomalies

    def _detect_frequency_anomalies(
        self,
        tenant_id: str,
        transactions: List[Transaction],
        historical: List[Transaction],
    ) -> List[Anomaly]:
        """Detect unusual transaction frequency"""
        anomalies = []

        if not historical or len(historical) < 30:
            return anomalies

        # Calculate average daily transactions
        date_counts = {}
        for txn in historical:
            date_key = txn.date.date()
            date_counts[date_key] = date_counts.get(date_key, 0) + 1

        if not date_counts:
            return anomalies

        avg_daily = statistics.mean(date_counts.values())
        stdev_daily = statistics.stdev(date_counts.values()) if len(date_counts) > 1 else avg_daily * 0.5

        # Check recent transaction frequency
        recent_counts = {}
        for txn in transactions:
            date_key = txn.date.date()
            recent_counts[date_key] = recent_counts.get(date_key, 0) + 1

        for date_key, count in recent_counts.items():
            if stdev_daily == 0:
                continue

            z_score = (count - avg_daily) / stdev_daily

            if z_score > self.config.anomaly.zscore_threshold:
                anomaly = Anomaly(
                    tenant_id=tenant_id,
                    anomaly_type='unusual_frequency',
                    severity='medium',
                    risk_score=min(1.0, z_score / 5),
                    entity_type='daily_transactions',
                    entity_id=str(date_key),
                    title=f'Unusual transaction volume on {date_key}',
                    description=f'{count} transactions vs average of {avg_daily:.1f}',
                    detection_method='zscore',
                    evidence={
                        'date': str(date_key),
                        'count': count,
                        'average': avg_daily,
                        'z_score': z_score,
                    },
                )
                anomalies.append(anomaly)

        return anomalies

    def _detect_timing_anomalies(
        self,
        tenant_id: str,
        transactions: List[Transaction],
    ) -> List[Anomaly]:
        """Detect transactions at unusual times"""
        anomalies = []

        for txn in transactions:
            hour = txn.date.hour

            # Flag transactions outside business hours (before 6am or after 10pm)
            if hour < 6 or hour > 22:
                anomaly = Anomaly(
                    tenant_id=tenant_id,
                    anomaly_type='unusual_timing',
                    severity='low',
                    risk_score=0.3,
                    entity_type='transaction',
                    entity_id=txn.id,
                    title=f'Transaction at unusual time: {txn.date.strftime("%H:%M")}',
                    description=f'Transaction recorded outside normal business hours',
                    detection_method='rule',
                    detection_rule='outside_business_hours',
                    evidence={
                        'timestamp': txn.date.isoformat(),
                        'hour': hour,
                        'amount': txn.amount,
                    },
                )
                anomalies.append(anomaly)

        return anomalies

    def _detect_duplicate_anomalies(
        self,
        tenant_id: str,
        transactions: List[Transaction],
    ) -> List[Anomaly]:
        """Detect potential duplicate transactions"""
        anomalies = []

        # Group by amount and vendor
        grouped = {}
        for txn in transactions:
            key = (round(txn.amount, 2), txn.vendor or 'unknown')
            grouped.setdefault(key, []).append(txn)

        for key, txns in grouped.items():
            if len(txns) < 2:
                continue

            amount, vendor = key

            # Check if transactions are within same day
            dates = [txn.date.date() for txn in txns]
            if len(set(dates)) == 1:  # All same day
                # Check if similar anomaly exists
                if Anomaly.exists(tenant_id, 'transaction_group', f'{amount}_{vendor}', 'potential_duplicate'):
                    continue

                anomaly = Anomaly(
                    tenant_id=tenant_id,
                    anomaly_type='potential_duplicate',
                    severity='medium',
                    risk_score=0.6,
                    entity_type='transaction_group',
                    entity_id=f'{amount}_{vendor}',
                    title=f'Potential duplicate: {len(txns)} transactions of ${abs(amount):,.2f}',
                    description=f'Multiple transactions with same amount to {vendor} on same day',
                    detection_method='rule',
                    detection_rule='duplicate_detection',
                    evidence={
                        'amount': amount,
                        'vendor': vendor,
                        'count': len(txns),
                        'transaction_ids': [t.id for t in txns],
                        'dates': [t.date.isoformat() for t in txns],
                    },
                )
                anomalies.append(anomaly)

        return anomalies

    def _calculate_severity(self, z_score: float) -> str:
        """Calculate severity based on z-score"""
        if z_score > 4:
            return Anomaly.SEVERITY_CRITICAL
        elif z_score > 3.5:
            return Anomaly.SEVERITY_HIGH
        elif z_score > 3:
            return Anomaly.SEVERITY_MEDIUM
        else:
            return Anomaly.SEVERITY_LOW

    async def get_anomalies(
        self,
        tenant_id: str,
        status: str = 'open',
        severity: Optional[str] = None,
        anomaly_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get anomalies for tenant"""
        anomalies = Anomaly.get_by_tenant(
            tenant_id=tenant_id,
            status=status,
            severity=severity,
            anomaly_type=anomaly_type,
            limit=limit,
        )
        return [a.to_dict() for a in anomalies]

    async def resolve_anomaly(
        self,
        tenant_id: str,
        anomaly_id: str,
        user_id: str,
        resolution_notes: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Resolve an anomaly"""
        anomaly = Anomaly.get_by_id(anomaly_id, tenant_id)
        if not anomaly:
            return None

        anomaly.status = 'resolved'
        anomaly.resolved_at = utc_now()
        anomaly.resolved_by = user_id
        anomaly.resolution_notes = resolution_notes
        anomaly.save()

        return anomaly.to_dict()

    async def dismiss_anomaly(
        self,
        tenant_id: str,
        anomaly_id: str,
        user_id: str,
        reason: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Dismiss an anomaly as false positive"""
        anomaly = Anomaly.get_by_id(anomaly_id, tenant_id)
        if not anomaly:
            return None

        anomaly.status = 'dismissed'
        anomaly.resolved_at = utc_now()
        anomaly.resolved_by = user_id
        anomaly.resolution_notes = f'Dismissed: {reason}' if reason else 'Dismissed as false positive'
        anomaly.save()

        return anomaly.to_dict()

    async def get_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get anomaly statistics"""
        return Anomaly.get_stats(tenant_id)
