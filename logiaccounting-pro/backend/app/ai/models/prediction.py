"""
Prediction Models
Store AI predictions for tracking and validation
"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import uuid


# In-memory storage
predictions_db: Dict[str, 'AIPrediction'] = {}
cashflow_forecasts_db: Dict[str, 'CashFlowForecast'] = {}


@dataclass
class AIPrediction:
    """AI prediction record"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ''
    prediction_type: str = ''
    model_name: str = ''
    model_version: Optional[str] = None
    input_data: Dict = field(default_factory=dict)
    prediction: Dict = field(default_factory=dict)
    confidence: Optional[float] = None
    actual_value: Optional[Dict] = None
    was_accurate: Optional[bool] = None
    accuracy_score: Optional[float] = None
    processing_time_ms: Optional[int] = None
    token_usage: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    validated_at: Optional[datetime] = None

    def save(self):
        predictions_db[self.id] = self

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'prediction_type': self.prediction_type,
            'model_name': self.model_name,
            'prediction': self.prediction,
            'confidence': self.confidence,
            'was_accurate': self.was_accurate,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class CashFlowForecast:
    """Cash flow forecast record"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ''
    forecast_date: date = field(default_factory=date.today)
    horizon_days: int = 30
    current_balance: Optional[float] = None
    daily_predictions: List[Dict] = field(default_factory=list)
    predicted_min_balance: Optional[float] = None
    predicted_max_balance: Optional[float] = None
    predicted_end_balance: Optional[float] = None
    risk_score: Optional[float] = None
    risk_factors: Optional[List[Dict]] = None
    insights: Optional[List[str]] = None
    recommendations: Optional[List[Dict]] = None
    model_name: Optional[str] = None
    model_metrics: Optional[Dict] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def save(self):
        cashflow_forecasts_db[self.id] = self

    @classmethod
    def get_by_tenant(cls, tenant_id: str, limit: int = 10) -> List['CashFlowForecast']:
        """Get forecasts for tenant"""
        forecasts = [f for f in cashflow_forecasts_db.values() if f.tenant_id == tenant_id]
        forecasts.sort(key=lambda x: x.created_at, reverse=True)
        return forecasts[:limit]

    @classmethod
    def get_by_id(cls, forecast_id: str, tenant_id: str) -> Optional['CashFlowForecast']:
        """Get forecast by ID"""
        forecast = cashflow_forecasts_db.get(forecast_id)
        if forecast and forecast.tenant_id == tenant_id:
            return forecast
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'forecast_date': self.forecast_date.isoformat() if self.forecast_date else None,
            'horizon_days': self.horizon_days,
            'current_balance': self.current_balance,
            'daily_predictions': self.daily_predictions,
            'predicted_min_balance': self.predicted_min_balance,
            'predicted_max_balance': self.predicted_max_balance,
            'predicted_end_balance': self.predicted_end_balance,
            'risk_score': self.risk_score,
            'risk_factors': self.risk_factors,
            'insights': self.insights,
            'recommendations': self.recommendations,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
