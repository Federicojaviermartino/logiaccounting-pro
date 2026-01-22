"""
Forecast Service
High-level cash flow forecasting operations
"""

from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List

from ...models.prediction import CashFlowForecast
from .predictor import CashFlowPredictor


class ForecastService:
    """High-level forecast operations"""

    def __init__(self):
        self.predictor = CashFlowPredictor()

    async def generate_forecast(
        self,
        tenant_id: str,
        transactions: List[Dict],
        current_balance: float,
        horizon_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Generate a new cash flow forecast

        Args:
            tenant_id: Tenant ID
            transactions: Historical transactions
            current_balance: Current balance
            horizon_days: Forecast horizon

        Returns:
            Forecast data dictionary
        """
        forecast = self.predictor.predict(
            tenant_id=tenant_id,
            transactions=transactions,
            current_balance=current_balance,
            horizon_days=horizon_days,
        )

        return forecast.to_dict()

    async def get_forecast(
        self,
        tenant_id: str,
        forecast_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get forecast by ID"""
        forecast = CashFlowForecast.get_by_id(forecast_id, tenant_id)
        if forecast:
            return forecast.to_dict()
        return None

    async def get_recent_forecasts(
        self,
        tenant_id: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get recent forecasts for tenant"""
        forecasts = CashFlowForecast.get_by_tenant(tenant_id, limit)
        return [f.to_dict() for f in forecasts]

    async def get_forecast_summary(
        self,
        tenant_id: str,
    ) -> Dict[str, Any]:
        """Get summary of latest forecast"""
        forecasts = CashFlowForecast.get_by_tenant(tenant_id, limit=1)

        if not forecasts:
            return {
                'has_forecast': False,
                'message': 'No forecasts available. Generate a forecast to see predictions.',
            }

        latest = forecasts[0]
        return {
            'has_forecast': True,
            'forecast_id': latest.id,
            'forecast_date': latest.forecast_date.isoformat() if latest.forecast_date else None,
            'horizon_days': latest.horizon_days,
            'current_balance': latest.current_balance,
            'predicted_end_balance': latest.predicted_end_balance,
            'risk_score': latest.risk_score,
            'risk_factors_count': len(latest.risk_factors) if latest.risk_factors else 0,
            'insights': latest.insights,
            'top_recommendations': (latest.recommendations or [])[:3],
        }

    async def compare_forecasts(
        self,
        tenant_id: str,
        forecast_id_1: str,
        forecast_id_2: str,
    ) -> Optional[Dict[str, Any]]:
        """Compare two forecasts"""
        f1 = CashFlowForecast.get_by_id(forecast_id_1, tenant_id)
        f2 = CashFlowForecast.get_by_id(forecast_id_2, tenant_id)

        if not f1 or not f2:
            return None

        return {
            'forecast_1': {
                'id': f1.id,
                'date': f1.forecast_date.isoformat() if f1.forecast_date else None,
                'predicted_end_balance': f1.predicted_end_balance,
                'risk_score': f1.risk_score,
            },
            'forecast_2': {
                'id': f2.id,
                'date': f2.forecast_date.isoformat() if f2.forecast_date else None,
                'predicted_end_balance': f2.predicted_end_balance,
                'risk_score': f2.risk_score,
            },
            'comparison': {
                'balance_change': (f2.predicted_end_balance or 0) - (f1.predicted_end_balance or 0),
                'risk_change': (f2.risk_score or 0) - (f1.risk_score or 0),
            },
        }
