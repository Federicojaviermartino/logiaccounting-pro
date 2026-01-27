"""API routes for rolling forecasts."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.database import get_db
from app.auth.dependencies import get_current_user, require_permissions
from app.auth.models import User
from app.budgeting.models.forecast import RollingForecast, ForecastStatus
from app.budgeting.schemas.forecast import (
    ForecastCreate, ForecastUpdate, ForecastResponse, ForecastWithLines
)
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/forecasts", tags=["Rolling Forecasts"])


@router.get("", response_model=dict)
async def get_forecasts(
    budget_id: Optional[UUID] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get rolling forecasts."""
    query = select(RollingForecast).where(
        RollingForecast.customer_id == current_user.customer_id
    )

    if budget_id:
        query = query.where(RollingForecast.budget_id == budget_id)
    if status:
        query = query.where(RollingForecast.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar()

    query = query.order_by(RollingForecast.created_at.desc())
    query = query.offset(skip).limit(limit)

    result = db.execute(query)
    forecasts = result.scalars().all()

    return {
        "items": [ForecastResponse.model_validate(f) for f in forecasts],
        "total": total, "skip": skip, "limit": limit
    }


@router.get("/{forecast_id}", response_model=ForecastWithLines)
async def get_forecast(
    forecast_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get forecast by ID with lines."""
    forecast = db.get(RollingForecast, forecast_id)
    if not forecast or forecast.customer_id != current_user.customer_id:
        raise NotFoundError(f"Forecast not found: {forecast_id}")
    return forecast


@router.post("", response_model=ForecastResponse, status_code=status.HTTP_201_CREATED)
async def create_forecast(
    data: ForecastCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["budgets.edit"]))
):
    """Create rolling forecast."""
    # Generate forecast number
    count = db.execute(
        select(func.count(RollingForecast.id)).where(
            RollingForecast.customer_id == current_user.customer_id
        )
    ).scalar() or 0

    forecast = RollingForecast(
        customer_id=current_user.customer_id,
        forecast_number=f"FCT-{(count + 1):04d}",
        budget_id=data.budget_id,
        name=data.name,
        description=data.description,
        base_date=data.base_date,
        forecast_months=data.forecast_months,
        forecast_method=data.forecast_method,
        created_by=current_user.id,
    )

    db.add(forecast)
    db.commit()
    db.refresh(forecast)
    return forecast


@router.put("/{forecast_id}", response_model=ForecastResponse)
async def update_forecast(
    forecast_id: UUID,
    data: ForecastUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["budgets.edit"]))
):
    """Update forecast."""
    forecast = db.get(RollingForecast, forecast_id)
    if not forecast or forecast.customer_id != current_user.customer_id:
        raise NotFoundError(f"Forecast not found: {forecast_id}")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(forecast, key, value)

    db.commit()
    db.refresh(forecast)
    return forecast


@router.delete("/{forecast_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_forecast(
    forecast_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["budgets.delete"]))
):
    """Delete forecast."""
    forecast = db.get(RollingForecast, forecast_id)
    if not forecast or forecast.customer_id != current_user.customer_id:
        raise NotFoundError(f"Forecast not found: {forecast_id}")

    db.delete(forecast)
    db.commit()


@router.post("/{forecast_id}/generate")
async def generate_forecast(
    forecast_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["budgets.edit"]))
):
    """Generate/regenerate forecast calculations."""
    forecast = db.get(RollingForecast, forecast_id)
    if not forecast or forecast.customer_id != current_user.customer_id:
        raise NotFoundError(f"Forecast not found: {forecast_id}")

    # TODO: Implement forecast generation logic based on method
    # This would analyze historical data and project future values

    return {"message": "Forecast generation not yet implemented", "forecast_id": str(forecast_id)}
