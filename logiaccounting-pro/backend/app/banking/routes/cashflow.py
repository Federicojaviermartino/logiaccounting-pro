"""
Cash Flow Forecasting API Routes
"""

from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.banking.cashflow.service import CashFlowService
from app.banking.cashflow.schemas import (
    ForecastCreate, ForecastUpdate, ForecastResponse, ForecastDetailResponse,
    PlannedTransactionCreate, PlannedTransactionUpdate, PlannedTransactionResponse,
    CashPositionResponse, ForecastSummary
)
from app.banking.cashflow.models import ForecastStatus, TransactionType

router = APIRouter(prefix="/cashflow", tags=["Cash Flow Forecasting"])

DEMO_CUSTOMER_ID = UUID("00000000-0000-0000-0000-000000000001")
DEMO_USER_ID = UUID("00000000-0000-0000-0000-000000000002")


def get_customer_id() -> UUID:
    return DEMO_CUSTOMER_ID


def get_user_id() -> UUID:
    return DEMO_USER_ID


@router.get("/summary", response_model=ForecastSummary)
def get_forecast_summary(
    db: Session = Depends(get_db)
):
    """Get cash flow forecast summary for dashboard"""
    service = CashFlowService(db, get_customer_id())
    return service.get_forecast_summary()


@router.get("/forecasts", response_model=dict)
def list_forecasts(
    status: Optional[ForecastStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List cash flow forecasts"""
    service = CashFlowService(db, get_customer_id())

    forecasts, total = service.get_forecasts(
        status=status,
        skip=skip,
        limit=limit
    )

    return {
        "items": [ForecastResponse.model_validate(f) for f in forecasts],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("/forecasts", response_model=ForecastResponse, status_code=status.HTTP_201_CREATED)
def create_forecast(
    data: ForecastCreate,
    db: Session = Depends(get_db)
):
    """Create a new cash flow forecast"""
    service = CashFlowService(db, get_customer_id())
    try:
        forecast = service.create_forecast(data, get_user_id())
        return ForecastResponse.model_validate(forecast)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/forecasts/{forecast_id}", response_model=ForecastDetailResponse)
def get_forecast(
    forecast_id: UUID,
    db: Session = Depends(get_db)
):
    """Get forecast details with lines"""
    service = CashFlowService(db, get_customer_id())
    try:
        forecast = service.get_forecast_by_id(forecast_id)
        return ForecastDetailResponse.model_validate(forecast)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/forecasts/{forecast_id}/generate", response_model=ForecastDetailResponse)
def generate_forecast(
    forecast_id: UUID,
    db: Session = Depends(get_db)
):
    """Generate or regenerate forecast lines"""
    service = CashFlowService(db, get_customer_id())
    try:
        forecast = service.generate_forecast(forecast_id, get_user_id())
        return ForecastDetailResponse.model_validate(forecast)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/planned-transactions", response_model=dict)
def list_planned_transactions(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    transaction_type: Optional[TransactionType] = None,
    is_active: Optional[bool] = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List planned cash transactions"""
    service = CashFlowService(db, get_customer_id())

    transactions, total = service.get_planned_transactions(
        start_date=start_date,
        end_date=end_date,
        transaction_type=transaction_type,
        is_active=is_active,
        skip=skip,
        limit=limit
    )

    return {
        "items": [PlannedTransactionResponse.model_validate(t) for t in transactions],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("/planned-transactions", response_model=PlannedTransactionResponse, status_code=status.HTTP_201_CREATED)
def create_planned_transaction(
    data: PlannedTransactionCreate,
    db: Session = Depends(get_db)
):
    """Create a planned cash transaction"""
    service = CashFlowService(db, get_customer_id())
    try:
        transaction = service.create_planned_transaction(data, get_user_id())
        return PlannedTransactionResponse.model_validate(transaction)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/planned-transactions/{transaction_id}", response_model=PlannedTransactionResponse)
def update_planned_transaction(
    transaction_id: UUID,
    data: PlannedTransactionUpdate,
    db: Session = Depends(get_db)
):
    """Update a planned transaction"""
    service = CashFlowService(db, get_customer_id())
    try:
        transaction = service.update_planned_transaction(transaction_id, data)
        return PlannedTransactionResponse.model_validate(transaction)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/positions/snapshot", response_model=CashPositionResponse)
def create_cash_position_snapshot(
    db: Session = Depends(get_db)
):
    """Create a daily cash position snapshot"""
    service = CashFlowService(db, get_customer_id())
    position = service.create_cash_position_snapshot()
    return CashPositionResponse.model_validate(position)
