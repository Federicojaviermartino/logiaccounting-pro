"""
AI Payment Optimizer Routes
"""

from typing import Optional, List
from datetime import date
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel

from app.utils.auth import get_current_user, require_roles
from ..services.payments import PaymentOptimizer, PaymentScheduler

router = APIRouter()
optimizer = PaymentOptimizer()
scheduler = PaymentScheduler()


class InvoiceInput(BaseModel):
    """Invoice input for optimization"""
    id: str
    vendor_name: str
    amount: float
    due_date: str
    payment_terms: Optional[str] = None
    early_payment_discount: Optional[float] = None
    discount_deadline: Optional[str] = None
    relationship_priority: str = 'normal'


class InflowInput(BaseModel):
    """Expected inflow"""
    expected_date: str
    amount: float
    source: Optional[str] = None


class OptimizeRequest(BaseModel):
    """Optimization request"""
    invoices: List[InvoiceInput]
    current_balance: float
    expected_inflows: Optional[List[InflowInput]] = None


@router.post("/optimize")
async def optimize_payments(
    request: OptimizeRequest,
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """
    Analyze invoices and generate payment recommendations

    Returns recommendations for:
    - Early payment discounts
    - Batch payment opportunities
    - Payment timing optimization
    - Priority payments
    """
    try:
        tenant_id = current_user.get("tenant_id", "default")

        invoices = [inv.model_dump() for inv in request.invoices]
        inflows = [inf.model_dump() for inf in (request.expected_inflows or [])]

        recommendations = optimizer.analyze_invoices(
            tenant_id=tenant_id,
            invoices=invoices,
            current_balance=request.current_balance,
            expected_inflows=inflows,
        )

        return {
            "recommendations": [r.to_dict() for r in recommendations],
            "summary": {
                "total_recommendations": len(recommendations),
                "potential_savings": sum(r.potential_savings or 0 for r in recommendations),
                "by_type": _count_by_type(recommendations),
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization failed: {str(e)}"
        )


def _count_by_type(recommendations):
    """Count recommendations by type"""
    counts = {}
    for r in recommendations:
        counts[r.recommendation_type] = counts.get(r.recommendation_type, 0) + 1
    return counts


@router.get("/recommendations")
async def get_recommendations(
    status: str = Query("pending"),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """Get payment recommendations"""
    tenant_id = current_user.get("tenant_id", "default")
    return await scheduler.get_recommendations(tenant_id, status, limit)


@router.get("/recommendations/{recommendation_id}")
async def get_recommendation(
    recommendation_id: str,
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """Get recommendation by ID"""
    tenant_id = current_user.get("tenant_id", "default")
    result = await scheduler.get_recommendation(tenant_id, recommendation_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found"
        )

    return result


@router.post("/recommendations/{recommendation_id}/accept")
async def accept_recommendation(
    recommendation_id: str,
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """Accept a payment recommendation"""
    tenant_id = current_user.get("tenant_id", "default")
    user_id = current_user.get("id", "unknown")

    result = await scheduler.accept_recommendation(
        tenant_id=tenant_id,
        recommendation_id=recommendation_id,
        user_id=user_id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found"
        )

    return result


class RejectRequest(BaseModel):
    """Reject request"""
    reason: Optional[str] = None


@router.post("/recommendations/{recommendation_id}/reject")
async def reject_recommendation(
    recommendation_id: str,
    request: RejectRequest,
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """Reject a payment recommendation"""
    tenant_id = current_user.get("tenant_id", "default")
    user_id = current_user.get("id", "unknown")

    result = await scheduler.reject_recommendation(
        tenant_id=tenant_id,
        recommendation_id=recommendation_id,
        user_id=user_id,
        reason=request.reason,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found"
        )

    return result


@router.get("/calendar")
async def get_payment_calendar(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """Get payment calendar with scheduled payments"""
    tenant_id = current_user.get("tenant_id", "default")

    start = date.fromisoformat(start_date) if start_date else None
    end = date.fromisoformat(end_date) if end_date else None

    return await scheduler.get_payment_calendar(tenant_id, start, end)


@router.get("/savings")
async def get_savings_summary(
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """Get savings summary"""
    tenant_id = current_user.get("tenant_id", "default")
    return await scheduler.get_savings_summary(tenant_id)
