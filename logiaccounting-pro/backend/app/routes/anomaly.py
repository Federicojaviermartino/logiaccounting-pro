"""
Anomaly Detection & Fraud Prevention Routes
API endpoints for detecting financial anomalies
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel

from app.utils.auth import get_current_user, require_roles
from app.models.store import db
from app.services.anomaly_detection import create_anomaly_detector, SCIPY_AVAILABLE, SKLEARN_AVAILABLE

router = APIRouter()


class TransactionCheck(BaseModel):
    """Transaction to check for anomalies"""
    amount: float
    invoice_number: Optional[str] = None
    vendor_name: Optional[str] = None
    supplier_id: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None


@router.get("/scan")
async def run_anomaly_scan(
    current_user: dict = Depends(require_roles("admin"))
):
    """
    Run a full anomaly detection scan across all data

    Detects:
    - Duplicate invoices
    - Unusual price variations
    - Spending spikes
    - Suspicious vendor patterns
    - ML-detected anomalies (if sklearn available)

    Returns comprehensive anomaly report with risk assessment.
    """
    try:
        detector = create_anomaly_detector(db)
        report = detector.run_full_scan()
        return report.to_dict()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Anomaly scan failed: {str(e)}"
        )


@router.get("/summary")
async def get_anomaly_summary(
    current_user: dict = Depends(require_roles("admin"))
):
    """
    Get a quick summary of detected anomalies

    Returns counts by severity and overall risk score.
    """
    try:
        detector = create_anomaly_detector(db)
        report = detector.run_full_scan()

        return {
            "total_anomalies": report.total_anomalies,
            "risk_score": report.risk_score,
            "risk_level": "critical" if report.risk_score >= 75 else
                         "high" if report.risk_score >= 50 else
                         "medium" if report.risk_score >= 25 else "low",
            "by_severity": {
                "critical": report.critical_count,
                "high": report.high_count,
                "medium": report.medium_count,
                "low": report.low_count
            },
            "summary": report.summary
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summary generation failed: {str(e)}"
        )


@router.get("/by-type/{anomaly_type}")
async def get_anomalies_by_type(
    anomaly_type: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """
    Get anomalies filtered by type

    Types:
    - duplicate_invoice: Potential duplicate invoices
    - price_variation: Unusual price changes
    - spending_spike: Abnormal spending periods
    - unusual_pattern: Other suspicious patterns
    """
    valid_types = ["duplicate_invoice", "price_variation", "spending_spike", "unusual_pattern"]

    if anomaly_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid type. Valid types: {', '.join(valid_types)}"
        )

    try:
        detector = create_anomaly_detector(db)
        report = detector.run_full_scan()

        filtered = [a for a in report.anomalies if a.get("type") == anomaly_type]

        return {
            "type": anomaly_type,
            "count": len(filtered),
            "anomalies": filtered
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Filter failed: {str(e)}"
        )


@router.get("/by-severity/{severity}")
async def get_anomalies_by_severity(
    severity: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """
    Get anomalies filtered by severity level

    Severity levels: critical, high, medium, low
    """
    valid_severities = ["critical", "high", "medium", "low"]

    if severity not in valid_severities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid severity. Valid levels: {', '.join(valid_severities)}"
        )

    try:
        detector = create_anomaly_detector(db)
        report = detector.run_full_scan()

        filtered = [a for a in report.anomalies if a.get("severity") == severity]

        return {
            "severity": severity,
            "count": len(filtered),
            "anomalies": filtered
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Filter failed: {str(e)}"
        )


@router.post("/check-transaction")
async def check_transaction(
    transaction: TransactionCheck,
    current_user: dict = Depends(get_current_user)
):
    """
    Check a single transaction for anomalies in real-time

    Use this before confirming a new transaction to detect issues early.
    """
    try:
        detector = create_anomaly_detector(db)
        anomalies = detector.check_single_transaction(transaction.model_dump())

        return {
            "transaction_ok": len(anomalies) == 0,
            "anomalies_detected": len(anomalies),
            "anomalies": [a.to_dict() for a in anomalies],
            "recommendation": "Review flagged issues before proceeding" if anomalies else "No issues detected"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Check failed: {str(e)}"
        )


@router.get("/duplicates")
async def check_duplicate_invoices(
    invoice_number: Optional[str] = Query(None, description="Specific invoice to check"),
    current_user: dict = Depends(get_current_user)
):
    """
    Specifically check for duplicate invoices

    If invoice_number is provided, checks for that specific invoice.
    Otherwise, returns all detected duplicates.
    """
    detector = create_anomaly_detector(db)

    if invoice_number:
        # Check specific invoice
        transactions = db.transactions.find_all()
        matches = [t for t in transactions
                  if t.get("invoice_number", "").upper() == invoice_number.upper()]

        return {
            "invoice_number": invoice_number,
            "occurrences": len(matches),
            "is_duplicate": len(matches) > 1,
            "transactions": [
                {
                    "id": t["id"],
                    "amount": t.get("amount"),
                    "date": t.get("date") or t.get("created_at", "")[:10],
                    "description": t.get("description")
                }
                for t in matches
            ]
        }

    # Get all duplicates
    report = detector.run_full_scan()
    duplicates = [a for a in report.anomalies if a.get("type") == "duplicate_invoice"]

    return {
        "total_duplicates": len(duplicates),
        "duplicates": duplicates
    }


@router.get("/vendor/{vendor_id}/analysis")
async def analyze_vendor(
    vendor_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """
    Get detailed anomaly analysis for a specific vendor
    """
    transactions = db.transactions.find_all()
    vendor_txs = [t for t in transactions if t.get("supplier_id") == vendor_id]

    if not vendor_txs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No transactions found for this vendor"
        )

    # Calculate statistics
    amounts = [t.get("amount", 0) for t in vendor_txs]
    avg_amount = sum(amounts) / len(amounts)

    # Get vendor info
    users = db.users.find_all()
    vendor = next((u for u in users if u["id"] == vendor_id), None)

    # Check for anomalies
    detector = create_anomaly_detector(db)
    report = detector.run_full_scan()
    vendor_anomalies = [
        a for a in report.anomalies
        if any(item.get("vendor_id") == vendor_id for item in a.get("affected_items", []))
    ]

    return {
        "vendor_id": vendor_id,
        "vendor_name": vendor.get("company_name") if vendor else "Unknown",
        "statistics": {
            "total_transactions": len(vendor_txs),
            "total_amount": sum(amounts),
            "average_amount": round(avg_amount, 2),
            "min_amount": min(amounts),
            "max_amount": max(amounts),
            "first_transaction": min(t.get("date") or t.get("created_at", "") for t in vendor_txs)[:10],
            "last_transaction": max(t.get("date") or t.get("created_at", "") for t in vendor_txs)[:10]
        },
        "anomalies_detected": len(vendor_anomalies),
        "anomalies": vendor_anomalies,
        "risk_assessment": "high" if len(vendor_anomalies) >= 3 else
                         "medium" if len(vendor_anomalies) >= 1 else "low"
    }


@router.get("/status")
async def get_detector_status():
    """
    Check anomaly detection service status and capabilities
    """
    return {
        "scipy_available": SCIPY_AVAILABLE,
        "sklearn_available": SKLEARN_AVAILABLE,
        "ml_detection_enabled": SKLEARN_AVAILABLE,
        "detection_methods": [
            "Duplicate invoice detection",
            "Price variation analysis",
            "Spending spike detection",
            "Vendor behavior analysis",
            "Isolation Forest ML" if SKLEARN_AVAILABLE else None
        ],
        "capabilities": {
            "real_time_checking": True,
            "batch_scanning": True,
            "ml_anomaly_detection": SKLEARN_AVAILABLE,
            "statistical_analysis": SCIPY_AVAILABLE or True,
            "vendor_profiling": True
        }
    }
