"""
Payment Analytics routes
"""

from fastapi import APIRouter, Depends
from app.services.payment_analytics_service import payment_analytics_service
from app.utils.auth import require_roles

router = APIRouter()


@router.get("/summary")
async def get_summary(
    days: int = 30,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get payment summary"""
    return payment_analytics_service.get_summary(days)


@router.get("/trend")
async def get_trend(
    days: int = 30,
    granularity: str = "day",
    current_user: dict = Depends(require_roles("admin"))
):
    """Get collection trend"""
    return {"trend": payment_analytics_service.get_trend(days, granularity)}


@router.get("/by-gateway")
async def get_by_gateway(current_user: dict = Depends(require_roles("admin"))):
    """Get analytics by gateway"""
    return {"gateways": payment_analytics_service.get_by_gateway()}


@router.get("/top-clients")
async def get_top_clients(
    limit: int = 10,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get top paying clients"""
    return {"clients": payment_analytics_service.get_top_clients(limit)}


@router.get("/fees")
async def get_fee_report(
    days: int = 30,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get fee analysis report"""
    return payment_analytics_service.get_fee_report(days)
