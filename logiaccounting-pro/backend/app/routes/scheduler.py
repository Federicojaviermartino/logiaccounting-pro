"""
Intelligent Payment Scheduler Routes
API endpoints for optimized payment scheduling
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel

from app.utils.auth import get_current_user, require_roles
from app.models.store import db
from app.services.payment_scheduler import create_payment_scheduler

router = APIRouter()


class ScheduleRequest(BaseModel):
    """Request for payment schedule optimization"""
    available_cash: Optional[float] = None
    optimize_for: str = "balanced"


@router.get("/optimize")
async def get_optimized_schedule(
    available_cash: Optional[float] = Query(None, description="Available cash for payments"),
    strategy: str = Query(
        "balanced",
        description="Optimization strategy: balanced, minimize_cost, maximize_discount, prioritize_vendors"
    ),
    current_user: dict = Depends(require_roles("admin"))
):
    """
    Get optimized payment schedule

    Strategies:
    - balanced: Balance between capturing discounts and preserving cash
    - minimize_cost: Minimize total cost (penalties + missed discounts)
    - maximize_discount: Capture all possible early payment discounts
    - prioritize_vendors: Pay strategic/high-value vendors first

    Returns:
    - Prioritized list of payments with recommended dates
    - Daily payment schedule
    - Total potential savings and penalty risks
    - Cash requirements for 7 and 30 days
    """
    valid_strategies = ["balanced", "minimize_cost", "maximize_discount", "prioritize_vendors"]

    if strategy not in valid_strategies:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid strategy. Valid options: {', '.join(valid_strategies)}"
        )

    try:
        scheduler = create_payment_scheduler(db)
        schedule = scheduler.optimize_schedule(
            available_cash=available_cash,
            optimize_for=strategy
        )
        return schedule.to_dict()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Schedule optimization failed: {str(e)}"
        )


@router.get("/summary")
async def get_schedule_summary(
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """
    Get quick summary of pending payments and optimization opportunities
    """
    try:
        scheduler = create_payment_scheduler(db)
        schedule = scheduler.optimize_schedule()

        # Count by action type
        actions = {}
        for rec in schedule.recommendations:
            action = rec.get("action") if isinstance(rec, dict) else rec.action
            actions[action] = actions.get(action, 0) + 1

        return {
            "total_pending": schedule.total_pending,
            "potential_savings": schedule.total_potential_savings,
            "penalty_risk": schedule.total_penalty_risk,
            "cash_required_7_days": schedule.cash_required_7_days,
            "cash_required_30_days": schedule.cash_required_30_days,
            "payment_actions": actions,
            "urgent_count": actions.get("pay_now", 0),
            "optimization_notes": schedule.optimization_notes
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summary failed: {str(e)}"
        )


@router.get("/daily")
async def get_daily_schedule(
    days: int = Query(30, ge=1, le=90, description="Number of days to show"),
    current_user: dict = Depends(require_roles("admin"))
):
    """
    Get day-by-day payment schedule for the specified period
    """
    try:
        scheduler = create_payment_scheduler(db)
        schedule = scheduler.optimize_schedule()

        return {
            "period_days": days,
            "schedule": schedule.daily_schedule[:days] if schedule.daily_schedule else [],
            "total_in_period": sum(
                day.get("total_amount", 0) for day in (schedule.daily_schedule or [])[:days]
            )
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Daily schedule failed: {str(e)}"
        )


@router.get("/payment/{payment_id}/insights")
async def get_payment_insights(
    payment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed payment optimization insights for a specific payment
    """
    try:
        scheduler = create_payment_scheduler(db)
        insights = scheduler.get_payment_insights(payment_id)

        if "error" in insights:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=insights["error"]
            )

        return insights
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Insights generation failed: {str(e)}"
        )


@router.get("/urgent")
async def get_urgent_payments(
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """
    Get list of urgent payments that need immediate attention

    Returns overdue and soon-due payments sorted by priority.
    """
    try:
        scheduler = create_payment_scheduler(db)
        schedule = scheduler.optimize_schedule()

        urgent = [
            rec for rec in schedule.recommendations
            if (rec.get("action") if isinstance(rec, dict) else rec.action) in ["pay_now"]
        ]

        return {
            "urgent_count": len(urgent),
            "total_urgent_amount": sum(
                r.get("amount") if isinstance(r, dict) else r.amount for r in urgent
            ),
            "payments": urgent
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Urgent payments query failed: {str(e)}"
        )


@router.get("/discounts")
async def get_discount_opportunities(
    current_user: dict = Depends(require_roles("admin"))
):
    """
    Get list of payments with early payment discount opportunities
    """
    try:
        scheduler = create_payment_scheduler(db)
        schedule = scheduler.optimize_schedule(optimize_for="maximize_discount")

        with_discount = [
            rec for rec in schedule.recommendations
            if (rec.get("discount_available") if isinstance(rec, dict) else rec.discount_available) > 0
        ]

        total_discount = sum(
            r.get("discount_available") if isinstance(r, dict) else r.discount_available
            for r in with_discount
        )

        return {
            "opportunities_count": len(with_discount),
            "total_potential_savings": total_discount,
            "payments": with_discount
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Discount opportunities query failed: {str(e)}"
        )


@router.post("/simulate")
async def simulate_schedule(
    request: ScheduleRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """
    Simulate payment schedule with custom parameters

    Use this to see how different cash amounts or strategies affect the schedule.
    """
    valid_strategies = ["balanced", "minimize_cost", "maximize_discount", "prioritize_vendors"]

    if request.optimize_for not in valid_strategies:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid strategy. Valid options: {', '.join(valid_strategies)}"
        )

    try:
        scheduler = create_payment_scheduler(db)
        schedule = scheduler.optimize_schedule(
            available_cash=request.available_cash,
            optimize_for=request.optimize_for
        )

        return {
            "simulation_parameters": {
                "available_cash": request.available_cash,
                "strategy": request.optimize_for
            },
            "result": schedule.to_dict()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation failed: {str(e)}"
        )


@router.get("/status")
async def get_scheduler_status():
    """
    Check payment scheduler status and capabilities
    """
    from app.services.payment_scheduler import NUMPY_AVAILABLE, SCIPY_OPTIMIZE_AVAILABLE

    payments = db.payments.find_all()
    pending = [p for p in payments if p.get("status") in ["pending", "overdue"]]

    return {
        "numpy_available": NUMPY_AVAILABLE,
        "scipy_optimize_available": SCIPY_OPTIMIZE_AVAILABLE,
        "optimization_methods": [
            "Priority-based scheduling",
            "Early payment discount optimization",
            "Late penalty avoidance",
            "Cash flow balancing",
            "Vendor priority weighting"
        ],
        "pending_payments": len(pending),
        "total_pending_amount": sum(p.get("amount", 0) for p in pending),
        "strategies_available": [
            "balanced",
            "minimize_cost",
            "maximize_discount",
            "prioritize_vendors"
        ]
    }
