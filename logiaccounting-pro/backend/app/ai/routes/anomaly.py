"""
AI Anomaly Detection Routes
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel

from app.utils.auth import get_current_user, require_roles
from ..services.anomaly import AnomalyDetector, RuleEngine

router = APIRouter()
detector = AnomalyDetector()
rule_engine = RuleEngine()


class TransactionInput(BaseModel):
    """Transaction input for analysis"""
    id: str
    date: str
    amount: float
    type: str
    category: Optional[str] = None
    vendor: Optional[str] = None
    description: Optional[str] = None
    user_id: Optional[str] = None


class DetectRequest(BaseModel):
    """Detection request"""
    transactions: List[TransactionInput]
    historical_transactions: Optional[List[TransactionInput]] = None


@router.post("/detect")
async def detect_anomalies(
    request: DetectRequest,
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """
    Detect anomalies in transactions

    Detection methods:
    - Z-score analysis for unusual amounts
    - Frequency analysis for unusual activity
    - Timing analysis for off-hours transactions
    - Duplicate detection
    - Custom rule evaluation
    """
    try:
        tenant_id = current_user.get("tenant_id", "default")

        transactions = [t.model_dump() for t in request.transactions]
        historical = [t.model_dump() for t in (request.historical_transactions or [])]

        # Statistical detection
        anomalies = detector.detect_transaction_anomalies(
            tenant_id=tenant_id,
            transactions=transactions,
            historical_transactions=historical,
        )

        # Rule-based detection
        rule_anomalies = rule_engine.evaluate_batch(tenant_id, transactions)

        all_anomalies = anomalies + rule_anomalies

        return {
            "anomalies": [a.to_dict() for a in all_anomalies],
            "summary": {
                "total": len(all_anomalies),
                "by_severity": _count_by_severity(all_anomalies),
                "by_type": _count_by_type(all_anomalies),
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Detection failed: {str(e)}"
        )


def _count_by_severity(anomalies):
    """Count anomalies by severity"""
    counts = {}
    for a in anomalies:
        counts[a.severity] = counts.get(a.severity, 0) + 1
    return counts


def _count_by_type(anomalies):
    """Count anomalies by type"""
    counts = {}
    for a in anomalies:
        counts[a.anomaly_type] = counts.get(a.anomaly_type, 0) + 1
    return counts


@router.get("/anomalies")
async def get_anomalies(
    status: str = Query("open"),
    severity: Optional[str] = None,
    anomaly_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """Get detected anomalies"""
    tenant_id = current_user.get("tenant_id", "default")

    return await detector.get_anomalies(
        tenant_id=tenant_id,
        status=status,
        severity=severity,
        anomaly_type=anomaly_type,
        limit=limit,
    )


@router.get("/anomalies/{anomaly_id}")
async def get_anomaly(
    anomaly_id: str,
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """Get anomaly by ID"""
    from ..models.anomaly import Anomaly

    tenant_id = current_user.get("tenant_id", "default")
    anomaly = Anomaly.get_by_id(anomaly_id, tenant_id)

    if not anomaly:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anomaly not found"
        )

    return anomaly.to_dict()


class ResolveRequest(BaseModel):
    """Resolve request"""
    resolution_notes: Optional[str] = None


@router.post("/anomalies/{anomaly_id}/resolve")
async def resolve_anomaly(
    anomaly_id: str,
    request: ResolveRequest,
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """Resolve an anomaly"""
    tenant_id = current_user.get("tenant_id", "default")
    user_id = current_user.get("id", "unknown")

    result = await detector.resolve_anomaly(
        tenant_id=tenant_id,
        anomaly_id=anomaly_id,
        user_id=user_id,
        resolution_notes=request.resolution_notes,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anomaly not found"
        )

    return result


class DismissRequest(BaseModel):
    """Dismiss request"""
    reason: Optional[str] = None


@router.post("/anomalies/{anomaly_id}/dismiss")
async def dismiss_anomaly(
    anomaly_id: str,
    request: DismissRequest,
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """Dismiss an anomaly as false positive"""
    tenant_id = current_user.get("tenant_id", "default")
    user_id = current_user.get("id", "unknown")

    result = await detector.dismiss_anomaly(
        tenant_id=tenant_id,
        anomaly_id=anomaly_id,
        user_id=user_id,
        reason=request.reason,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anomaly not found"
        )

    return result


@router.get("/stats")
async def get_anomaly_stats(
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """Get anomaly statistics"""
    tenant_id = current_user.get("tenant_id", "default")
    return await detector.get_stats(tenant_id)


@router.get("/rules")
async def get_rules(
    current_user: dict = Depends(require_roles("admin"))
):
    """Get detection rules"""
    return rule_engine.get_rules()


@router.post("/rules/{rule_id}/enable")
async def enable_rule(
    rule_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Enable a detection rule"""
    rule_engine.enable_rule(rule_id)
    return {"status": "enabled"}


@router.post("/rules/{rule_id}/disable")
async def disable_rule(
    rule_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Disable a detection rule"""
    rule_engine.disable_rule(rule_id)
    return {"status": "disabled"}
