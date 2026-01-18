"""
Cash Flow Predictor Routes
Intelligent 30-60-90 day cash flow prediction API endpoints
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel

from app.utils.auth import get_current_user, require_roles
from app.models.store import db
from app.services.cashflow_predictor import create_cashflow_predictor

router = APIRouter()


class PredictionRequest(BaseModel):
    """Request for cash flow prediction"""
    days: int = 90
    include_pending_payments: bool = True


@router.get("/predict")
async def get_cashflow_prediction(
    days: int = Query(90, ge=7, le=365, description="Number of days to predict"),
    include_pending: bool = Query(True, description="Include pending payments in prediction"),
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """
    Generate cash flow predictions for the specified period

    Available periods:
    - 30 days: Short-term planning
    - 60 days: Medium-term planning
    - 90 days: Standard quarterly forecast

    Returns daily predictions with confidence intervals, insights, and risk alerts.
    """
    try:
        predictor = create_cashflow_predictor(db)
        forecast = predictor.predict(days=days, include_pending_payments=include_pending)
        return forecast.to_dict()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@router.get("/predict/summary")
async def get_cashflow_summary(
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """
    Get a quick summary of cash flow predictions for 30, 60, and 90 days
    """
    try:
        predictor = create_cashflow_predictor(db)
        forecast = predictor.predict(days=90, include_pending_payments=True)

        return {
            "generated_at": forecast.generated_at,
            "current_balance": forecast.current_balance,
            "periods": forecast.summary.get("periods", {}),
            "top_insights": forecast.insights[:3],
            "risk_alerts": forecast.risk_alerts[:3]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summary generation failed: {str(e)}"
        )


@router.get("/predict/daily")
async def get_daily_predictions(
    days: int = Query(30, ge=1, le=90),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """
    Get paginated daily predictions for charting
    """
    try:
        predictor = create_cashflow_predictor(db)
        forecast = predictor.predict(days=days + offset, include_pending_payments=True)

        predictions = forecast.predictions[offset:offset + days]

        return {
            "predictions": predictions,
            "total": len(forecast.predictions),
            "offset": offset,
            "limit": days
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get daily predictions: {str(e)}"
        )


@router.get("/insights")
async def get_cashflow_insights(
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """
    Get detailed cash flow insights and recommendations
    """
    try:
        predictor = create_cashflow_predictor(db)
        forecast = predictor.predict(days=90, include_pending_payments=True)

        # Calculate additional metrics
        predictions = forecast.predictions

        # Find worst and best days
        if predictions:
            worst_day = min(predictions, key=lambda x: x.get("predicted_net", 0) if isinstance(x, dict) else x.predicted_net)
            best_day = max(predictions, key=lambda x: x.get("predicted_net", 0) if isinstance(x, dict) else x.predicted_net)
        else:
            worst_day = best_day = None

        return {
            "insights": forecast.insights,
            "risk_alerts": forecast.risk_alerts,
            "project_impacts": forecast.project_impacts,
            "metrics": {
                "current_balance": forecast.current_balance,
                "projected_90_day_balance": forecast.summary.get("projected_end_balance", 0),
                "total_predicted_income": forecast.summary.get("total_predicted_income", 0),
                "total_predicted_expenses": forecast.summary.get("total_predicted_expenses", 0),
                "avg_daily_net": forecast.summary.get("avg_daily_net", 0),
                "worst_day": worst_day,
                "best_day": best_day
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate insights: {str(e)}"
        )


@router.get("/risk-assessment")
async def get_risk_assessment(
    current_user: dict = Depends(require_roles("admin"))
):
    """
    Get comprehensive risk assessment for cash flow
    """
    try:
        predictor = create_cashflow_predictor(db)
        forecast = predictor.predict(days=90, include_pending_payments=True)

        # Calculate risk score
        risk_factors = []
        risk_score = 0

        # Check projected balance
        end_balance = forecast.summary.get("projected_end_balance", 0)
        current = forecast.current_balance

        if end_balance < 0:
            risk_factors.append({"factor": "Negative projected balance", "severity": "high", "impact": 30})
            risk_score += 30
        elif end_balance < current * 0.3:
            risk_factors.append({"factor": "Significant balance decrease", "severity": "medium", "impact": 20})
            risk_score += 20

        # Check for overdue payments
        payments = db.payments.find_all({"status": "overdue"})
        if payments:
            total_overdue = sum(p.get("amount", 0) for p in payments)
            if total_overdue > current * 0.2:
                risk_factors.append({"factor": f"High overdue payments: ${total_overdue:.2f}", "severity": "high", "impact": 25})
                risk_score += 25
            else:
                risk_factors.append({"factor": f"Overdue payments: ${total_overdue:.2f}", "severity": "medium", "impact": 15})
                risk_score += 15

        # Check daily net trend
        avg_net = forecast.summary.get("avg_daily_net", 0)
        if avg_net < 0:
            risk_factors.append({"factor": "Negative daily cash flow trend", "severity": "medium", "impact": 15})
            risk_score += 15

        # Determine overall risk level
        if risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 25:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "risk_level": risk_level,
            "risk_score": min(risk_score, 100),
            "risk_factors": risk_factors,
            "alerts": forecast.risk_alerts,
            "recommendations": [
                "Review and follow up on overdue payments" if any(f["factor"].startswith("Overdue") or f["factor"].startswith("High overdue") for f in risk_factors) else None,
                "Consider cost optimization measures" if avg_net < 0 else None,
                "Accelerate receivables collection" if end_balance < current * 0.5 else None,
                "Maintain current financial strategy" if risk_level == "low" else None
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk assessment failed: {str(e)}"
        )


@router.get("/status")
async def get_predictor_status():
    """
    Check cash flow predictor status and capabilities
    """
    try:
        from app.services.cashflow_predictor import PANDAS_AVAILABLE, PROPHET_AVAILABLE
    except ImportError:
        PANDAS_AVAILABLE = False
        PROPHET_AVAILABLE = False

    # Count historical data
    transactions = db.transactions.find_all()
    payments = db.payments.find_all()

    income_count = len([t for t in transactions if t.get("type") == "income"])
    expense_count = len([t for t in transactions if t.get("type") == "expense"])

    return {
        "pandas_available": PANDAS_AVAILABLE,
        "prophet_available": PROPHET_AVAILABLE,
        "prediction_method": "prophet" if PROPHET_AVAILABLE and PANDAS_AVAILABLE else "statistical" if PANDAS_AVAILABLE else "simple",
        "historical_data": {
            "income_transactions": income_count,
            "expense_transactions": expense_count,
            "pending_payments": len([p for p in payments if p.get("status") == "pending"]),
            "has_sufficient_data": income_count >= 7 or expense_count >= 7
        },
        "capabilities": {
            "time_series_forecasting": PROPHET_AVAILABLE,
            "seasonal_analysis": PROPHET_AVAILABLE,
            "confidence_intervals": True,
            "risk_assessment": True,
            "project_impact_analysis": True
        }
    }
