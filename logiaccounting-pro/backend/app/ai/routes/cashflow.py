"""
AI Cash Flow Routes
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel

from app.utils.auth import get_current_user, require_roles
from ..services.cashflow import ForecastService

router = APIRouter()
forecast_service = ForecastService()


class TransactionInput(BaseModel):
    """Transaction input for forecasting"""
    id: str
    date: str
    amount: float
    type: str
    category: Optional[str] = None


class ForecastRequest(BaseModel):
    """Forecast request"""
    transactions: List[TransactionInput]
    current_balance: float
    horizon_days: int = 30


@router.post("/forecast")
async def generate_forecast(
    request: ForecastRequest,
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """Generate AI-powered cash flow forecast"""
    try:
        tenant_id = current_user.get("tenant_id", "default")
        transactions = [t.model_dump() for t in request.transactions]

        result = await forecast_service.generate_forecast(
            tenant_id=tenant_id,
            transactions=transactions,
            current_balance=request.current_balance,
            horizon_days=request.horizon_days,
        )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecast generation failed: {str(e)}"
        )


@router.get("/forecast/{forecast_id}")
async def get_forecast(
    forecast_id: str,
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """Get forecast by ID"""
    tenant_id = current_user.get("tenant_id", "default")
    result = await forecast_service.get_forecast(tenant_id, forecast_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Forecast not found"
        )

    return result


@router.get("/forecasts")
async def get_recent_forecasts(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """Get recent forecasts"""
    tenant_id = current_user.get("tenant_id", "default")
    return await forecast_service.get_recent_forecasts(tenant_id, limit)


@router.get("/summary")
async def get_forecast_summary(
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """Get summary of latest forecast"""
    tenant_id = current_user.get("tenant_id", "default")
    return await forecast_service.get_forecast_summary(tenant_id)
