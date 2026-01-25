# Phase 31: AI/ML Features - Part 6: API Routes

## Overview
This part covers the API routes for all AI/ML features.

---

## File 1: AI Routes Main
**Path:** `backend/app/routes/ai.py`

```python
"""
AI Routes
API endpoints for AI/ML features
"""

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, BackgroundTasks
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from app.auth.dependencies import get_current_user, get_current_customer_id

# Import services
from app.ai.cashflow.service import cashflow_service
from app.ai.ocr.service import ocr_service
from app.ai.assistant.service import assistant_service
from app.ai.anomaly.service import anomaly_service

router = APIRouter(prefix="/ai", tags=["AI/ML"])


# ==================== Request Models ====================

class CashFlowForecastRequest(BaseModel):
    horizon_days: int = Field(30, ge=1, le=365)
    scenario: str = Field("expected", pattern="^(expected|optimistic|pessimistic)$")
    include_pending: bool = True
    include_recurring: bool = True


class CashFlowTrainRequest(BaseModel):
    historical_data: List[dict]
    current_balance: float


class AssistantChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None
    context: Optional[dict] = {}


class EntityAnalysisRequest(BaseModel):
    entity_type: str
    entity_id: str
    analysis_type: str = "profitability"


class AnomalyTrainRequest(BaseModel):
    historical_data: List[dict]


class TransactionAnalysisRequest(BaseModel):
    transaction: dict


class AlertActionRequest(BaseModel):
    notes: Optional[str] = None
    reason: Optional[str] = None


class OCRUpdateRequest(BaseModel):
    updates: dict


# ==================== Cash Flow Routes ====================

@router.post("/cashflow/train")
async def train_cashflow_model(
    request: CashFlowTrainRequest,
    customer_id: str = Depends(get_current_customer_id),
):
    """Train cash flow prediction model."""
    result = await cashflow_service.train_model(
        customer_id=customer_id,
        historical_data=request.historical_data,
        current_balance=request.current_balance,
    )
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return result.data


@router.post("/cashflow/forecast")
async def get_cashflow_forecast(
    request: CashFlowForecastRequest,
    customer_id: str = Depends(get_current_customer_id),
):
    """Get cash flow forecast."""
    result = await cashflow_service.get_forecast(
        customer_id=customer_id,
        horizon_days=request.horizon_days,
        scenario=request.scenario,
        include_pending=request.include_pending,
        include_recurring=request.include_recurring,
    )
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return result.data


@router.get("/cashflow/status")
async def get_cashflow_model_status(
    customer_id: str = Depends(get_current_customer_id),
):
    """Get cash flow model status."""
    return cashflow_service.get_model_status(customer_id)


# ==================== OCR Routes ====================

@router.post("/ocr/process")
async def process_document(
    file: UploadFile = File(...),
    customer_id: str = Depends(get_current_customer_id),
):
    """Process and extract data from document."""
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    contents = await file.read()
    
    result = await ocr_service.process_document(
        file_data=contents,
        filename=file.filename,
        customer_id=customer_id,
    )
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return result.data


@router.post("/ocr/batch")
async def batch_process_documents(
    files: List[UploadFile] = File(...),
    customer_id: str = Depends(get_current_customer_id),
):
    """Process multiple documents."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    file_data = []
    for file in files:
        contents = await file.read()
        file_data.append((file.filename, contents))
    
    result = await ocr_service.batch_process(file_data, customer_id)
    
    return result.data


@router.get("/ocr/documents")
async def get_processed_documents(
    limit: int = Query(50, ge=1, le=100),
    customer_id: str = Depends(get_current_customer_id),
):
    """Get processed documents for customer."""
    documents = await ocr_service.get_customer_documents(customer_id, limit)
    return {"documents": documents}


@router.get("/ocr/documents/{document_id}")
async def get_document(
    document_id: str,
    customer_id: str = Depends(get_current_customer_id),
):
    """Get specific processed document."""
    document = await ocr_service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.put("/ocr/documents/{document_id}")
async def update_document(
    document_id: str,
    request: OCRUpdateRequest,
    customer_id: str = Depends(get_current_customer_id),
):
    """Update extracted document data."""
    result = await ocr_service.update_document(document_id, request.updates)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return result.data


@router.post("/ocr/documents/{document_id}/approve")
async def approve_document(
    document_id: str,
    customer_id: str = Depends(get_current_customer_id),
):
    """Approve extracted document."""
    result = await ocr_service.approve_document(document_id)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return result.data


# ==================== Assistant Routes ====================

@router.post("/assistant/chat")
async def chat_with_assistant(
    request: AssistantChatRequest,
    customer_id: str = Depends(get_current_customer_id),
):
    """Send message to AI assistant."""
    result = await assistant_service.chat(
        customer_id=customer_id,
        message=request.message,
        conversation_id=request.conversation_id,
        context=request.context,
    )
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return result.data


@router.get("/assistant/insights")
async def get_quick_insights(
    customer_id: str = Depends(get_current_customer_id),
):
    """Get quick AI-generated insights."""
    result = await assistant_service.get_quick_insights(customer_id)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return result.data


@router.post("/assistant/analyze")
async def analyze_entity(
    request: EntityAnalysisRequest,
    customer_id: str = Depends(get_current_customer_id),
):
    """Analyze a specific entity."""
    result = await assistant_service.analyze_entity(
        customer_id=customer_id,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        analysis_type=request.analysis_type,
    )
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return result.data


@router.get("/assistant/conversations")
async def get_conversations(
    limit: int = Query(10, ge=1, le=50),
    customer_id: str = Depends(get_current_customer_id),
):
    """Get conversation history."""
    conversations = assistant_service.get_conversations(customer_id, limit)
    return {"conversations": conversations}


@router.get("/assistant/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    customer_id: str = Depends(get_current_customer_id),
):
    """Get specific conversation."""
    conversation = assistant_service.get_conversation(customer_id, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.delete("/assistant/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    customer_id: str = Depends(get_current_customer_id),
):
    """Delete conversation."""
    assistant_service.delete_conversation(customer_id, conversation_id)
    return {"success": True}


@router.get("/assistant/suggestions")
async def get_suggestions(
    q: str = Query("", max_length=100),
    customer_id: str = Depends(get_current_customer_id),
):
    """Get query suggestions."""
    suggestions = await assistant_service.get_suggestions(customer_id, q)
    return {"suggestions": suggestions}


# ==================== Anomaly Detection Routes ====================

@router.post("/anomaly/train")
async def train_anomaly_models(
    request: AnomalyTrainRequest,
    customer_id: str = Depends(get_current_customer_id),
):
    """Train anomaly detection models."""
    result = await anomaly_service.train_models(
        customer_id=customer_id,
        historical_data=request.historical_data,
    )
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return result.data


@router.post("/anomaly/analyze")
async def analyze_transaction(
    request: TransactionAnalysisRequest,
    customer_id: str = Depends(get_current_customer_id),
):
    """Analyze a transaction for anomalies."""
    result = await anomaly_service.analyze_transaction(
        customer_id=customer_id,
        transaction=request.transaction,
    )
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return result.data


@router.post("/anomaly/batch-analyze")
async def batch_analyze_transactions(
    transactions: List[dict],
    customer_id: str = Depends(get_current_customer_id),
):
    """Analyze multiple transactions."""
    result = await anomaly_service.batch_analyze(
        customer_id=customer_id,
        transactions=transactions,
    )
    
    return result.data


@router.get("/anomaly/alerts")
async def get_alerts(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    customer_id: str = Depends(get_current_customer_id),
):
    """Get anomaly alerts."""
    alerts = anomaly_service.get_alerts(
        customer_id=customer_id,
        status=status,
        severity=severity,
        limit=limit,
    )
    return {"alerts": alerts}


@router.get("/anomaly/alerts/summary")
async def get_alert_summary(
    customer_id: str = Depends(get_current_customer_id),
):
    """Get alert summary."""
    return anomaly_service.get_alert_summary(customer_id)


@router.post("/anomaly/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    user = Depends(get_current_user),
):
    """Acknowledge an alert."""
    result = anomaly_service.acknowledge_alert(alert_id, user.get("id"))
    if not result:
        raise HTTPException(status_code=404, detail="Alert not found")
    return result


@router.post("/anomaly/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    request: AlertActionRequest,
    user = Depends(get_current_user),
):
    """Resolve an alert."""
    result = anomaly_service.resolve_alert(alert_id, user.get("id"), request.notes)
    if not result:
        raise HTTPException(status_code=404, detail="Alert not found")
    return result


@router.post("/anomaly/alerts/{alert_id}/dismiss")
async def dismiss_alert(
    alert_id: str,
    request: AlertActionRequest,
    user = Depends(get_current_user),
):
    """Dismiss an alert."""
    result = anomaly_service.dismiss_alert(alert_id, user.get("id"), request.reason)
    if not result:
        raise HTTPException(status_code=404, detail="Alert not found")
    return result
```

---

## File 2: AI Service Aggregator
**Path:** `backend/app/ai/service.py`

```python
"""
AI Service Aggregator
Unified interface for all AI features
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.ai.cashflow.service import cashflow_service
from app.ai.ocr.service import ocr_service
from app.ai.assistant.service import assistant_service
from app.ai.anomaly.service import anomaly_service
from app.ai.base import AIResult

logger = logging.getLogger(__name__)


class AIServiceAggregator:
    """Aggregates all AI services for unified access."""
    
    def __init__(self):
        self.cashflow = cashflow_service
        self.ocr = ocr_service
        self.assistant = assistant_service
        self.anomaly = anomaly_service
    
    async def get_dashboard_insights(self, customer_id: str) -> Dict:
        """Get AI insights for dashboard."""
        insights = {
            "cashflow": None,
            "anomalies": None,
            "recommendations": [],
            "generated_at": datetime.utcnow().isoformat(),
        }
        
        try:
            # Cash flow forecast
            cf_result = await self.cashflow.get_forecast(
                customer_id=customer_id,
                horizon_days=30,
                scenario="expected",
            )
            if cf_result.success:
                insights["cashflow"] = {
                    "current_balance": cf_result.data.get("summary", {}).get("starting_balance"),
                    "forecast_30_days": cf_result.data.get("summary", {}).get("ending_balance"),
                    "trend": cf_result.data.get("summary", {}).get("trend"),
                    "alerts": cf_result.data.get("alerts", [])[:3],
                }
        except Exception as e:
            logger.error(f"Cash flow insights failed: {e}")
        
        try:
            # Anomaly summary
            anomaly_summary = self.anomaly.get_alert_summary(customer_id)
            insights["anomalies"] = {
                "pending_alerts": anomaly_summary.get("pending", 0),
                "critical": anomaly_summary.get("critical_pending", 0),
                "high": anomaly_summary.get("high_pending", 0),
            }
        except Exception as e:
            logger.error(f"Anomaly insights failed: {e}")
        
        # Generate recommendations
        insights["recommendations"] = self._generate_recommendations(insights)
        
        return insights
    
    def _generate_recommendations(self, insights: Dict) -> List[Dict]:
        """Generate recommendations based on insights."""
        recommendations = []
        
        # Cash flow recommendations
        cf = insights.get("cashflow", {})
        if cf:
            if cf.get("trend") == "decreasing":
                recommendations.append({
                    "type": "cashflow",
                    "priority": "high",
                    "title": "Cash Flow Declining",
                    "description": "Your cash flow trend is decreasing. Review upcoming expenses and accelerate collections.",
                    "action": {"type": "view_cashflow"},
                })
            
            if cf.get("alerts"):
                recommendations.append({
                    "type": "cashflow",
                    "priority": "medium",
                    "title": f"{len(cf['alerts'])} Cash Flow Alerts",
                    "description": "Review your cash flow forecast for potential issues.",
                    "action": {"type": "view_cashflow"},
                })
        
        # Anomaly recommendations
        anomalies = insights.get("anomalies", {})
        if anomalies:
            if anomalies.get("critical", 0) > 0:
                recommendations.append({
                    "type": "anomaly",
                    "priority": "critical",
                    "title": f"{anomalies['critical']} Critical Alerts",
                    "description": "You have critical alerts that require immediate attention.",
                    "action": {"type": "view_anomalies"},
                })
            elif anomalies.get("pending_alerts", 0) > 0:
                recommendations.append({
                    "type": "anomaly",
                    "priority": "medium",
                    "title": f"{anomalies['pending_alerts']} Pending Alerts",
                    "description": "Review and address pending anomaly alerts.",
                    "action": {"type": "view_anomalies"},
                })
        
        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: priority_order.get(x.get("priority"), 4))
        
        return recommendations[:5]
    
    async def process_new_transaction(self, customer_id: str, transaction: Dict) -> Dict:
        """Process a new transaction through AI pipeline."""
        results = {}
        
        # Anomaly detection
        try:
            anomaly_result = await self.anomaly.analyze_transaction(customer_id, transaction)
            results["anomaly_check"] = {
                "is_safe": anomaly_result.data.get("is_safe", True) if anomaly_result.success else True,
                "fraud_score": anomaly_result.data.get("fraud_score", {}).get("fraud_score", 0) if anomaly_result.success else 0,
                "alerts": anomaly_result.data.get("alerts_created", []) if anomaly_result.success else [],
            }
        except Exception as e:
            logger.error(f"Transaction anomaly check failed: {e}")
            results["anomaly_check"] = {"is_safe": True, "error": str(e)}
        
        return results
    
    def get_service_status(self) -> Dict:
        """Get status of all AI services."""
        return {
            "cashflow": {
                "enabled": True,
                "status": "operational",
            },
            "ocr": {
                "enabled": True,
                "status": "operational",
            },
            "assistant": {
                "enabled": True,
                "status": "operational",
            },
            "anomaly": {
                "enabled": True,
                "status": "operational",
            },
        }


# Global service instance
ai_service = AIServiceAggregator()
```

---

## File 3: Recommendations Engine
**Path:** `backend/app/ai/recommendations/engine.py`

```python
"""
Recommendations Engine
Generates actionable recommendations based on business data
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from uuid import uuid4
import logging

from app.ai.base import Recommendation

logger = logging.getLogger(__name__)


class RecommendationType:
    """Types of recommendations."""
    INVOICE_REMINDER = "invoice_reminder"
    PAYMENT_SCHEDULE = "payment_schedule"
    CASH_FLOW = "cash_flow"
    EXPENSE_OPTIMIZATION = "expense_optimization"
    CUSTOMER_RISK = "customer_risk"
    PROJECT_HEALTH = "project_health"
    PRICING = "pricing"


class RecommendationEngine:
    """Generates business recommendations."""
    
    def __init__(self):
        self._generated: Dict[str, List[Recommendation]] = {}
    
    async def generate_recommendations(
        self,
        customer_id: str,
        context: Dict,
    ) -> List[Recommendation]:
        """Generate recommendations based on context."""
        recommendations = []
        
        # Invoice reminders
        if context.get("overdue_invoices"):
            recommendations.extend(
                self._generate_invoice_reminders(context["overdue_invoices"])
            )
        
        # Cash flow recommendations
        if context.get("cashflow_forecast"):
            recommendations.extend(
                self._generate_cashflow_recommendations(context["cashflow_forecast"])
            )
        
        # Customer risk recommendations
        if context.get("customers"):
            recommendations.extend(
                self._generate_customer_recommendations(context["customers"])
            )
        
        # Project health recommendations
        if context.get("projects"):
            recommendations.extend(
                self._generate_project_recommendations(context["projects"])
            )
        
        # Sort by priority
        recommendations.sort(key=lambda r: r.priority, reverse=True)
        
        # Store for customer
        self._generated[customer_id] = recommendations
        
        return recommendations[:10]  # Top 10
    
    def _generate_invoice_reminders(self, invoices: List[Dict]) -> List[Recommendation]:
        """Generate invoice reminder recommendations."""
        recommendations = []
        
        for invoice in invoices:
            days_overdue = invoice.get("days_overdue", 0)
            amount = invoice.get("amount", 0)
            customer = invoice.get("customer_name", "Customer")
            
            if days_overdue > 30:
                priority = 9
                title = f"Escalate Collection: {customer}"
                description = f"Invoice ${amount:,.2f} is {days_overdue} days overdue. Consider escalating to collections or applying late fees."
            elif days_overdue > 14:
                priority = 7
                title = f"Send Final Reminder: {customer}"
                description = f"Invoice ${amount:,.2f} is {days_overdue} days overdue. Send a final payment reminder."
            else:
                priority = 5
                title = f"Send Payment Reminder: {customer}"
                description = f"Invoice ${amount:,.2f} is {days_overdue} days overdue. A friendly reminder may help."
            
            recommendations.append(Recommendation(
                id=f"rec_{uuid4().hex[:12]}",
                type=RecommendationType.INVOICE_REMINDER,
                title=title,
                description=description,
                priority=priority,
                confidence=0.9,
                potential_impact=f"Recover ${amount:,.2f}",
                actions=[
                    {"action": "send_reminder", "invoice_id": invoice.get("id")},
                    {"action": "view_invoice", "invoice_id": invoice.get("id")},
                ],
            ))
        
        return recommendations
    
    def _generate_cashflow_recommendations(self, forecast: Dict) -> List[Recommendation]:
        """Generate cash flow recommendations."""
        recommendations = []
        
        alerts = forecast.get("alerts", [])
        for alert in alerts:
            if alert.get("type") == "low_balance":
                recommendations.append(Recommendation(
                    id=f"rec_{uuid4().hex[:12]}",
                    type=RecommendationType.CASH_FLOW,
                    title="Prepare for Low Cash Period",
                    description=f"Cash balance may drop on {alert.get('date')}. Consider accelerating collections or delaying non-essential payments.",
                    priority=8,
                    confidence=0.8,
                    actions=[
                        {"action": "view_cashflow"},
                        {"action": "view_pending_invoices"},
                    ],
                ))
        
        summary = forecast.get("summary", {})
        if summary.get("trend") == "decreasing":
            recommendations.append(Recommendation(
                id=f"rec_{uuid4().hex[:12]}",
                type=RecommendationType.CASH_FLOW,
                title="Address Declining Cash Flow",
                description="Your cash flow trend is declining. Review revenue sources and expense patterns.",
                priority=7,
                confidence=0.75,
                actions=[
                    {"action": "view_cashflow"},
                    {"action": "view_expenses"},
                ],
            ))
        
        return recommendations
    
    def _generate_customer_recommendations(self, customers: List[Dict]) -> List[Recommendation]:
        """Generate customer-related recommendations."""
        recommendations = []
        
        for customer in customers:
            payment_days = customer.get("avg_payment_days", 30)
            outstanding = customer.get("outstanding_balance", 0)
            
            # Slow payers
            if payment_days > 45 and outstanding > 5000:
                recommendations.append(Recommendation(
                    id=f"rec_{uuid4().hex[:12]}",
                    type=RecommendationType.CUSTOMER_RISK,
                    title=f"Review Terms: {customer.get('name')}",
                    description=f"Customer averages {payment_days} days to pay with ${outstanding:,.2f} outstanding. Consider adjusting payment terms.",
                    priority=6,
                    confidence=0.85,
                    actions=[
                        {"action": "view_customer", "customer_id": customer.get("id")},
                    ],
                ))
        
        return recommendations
    
    def _generate_project_recommendations(self, projects: List[Dict]) -> List[Recommendation]:
        """Generate project recommendations."""
        recommendations = []
        
        for project in projects:
            margin = project.get("margin", 0)
            status = project.get("status", "")
            
            # Low margin projects
            if status == "active" and margin < 0.2:
                recommendations.append(Recommendation(
                    id=f"rec_{uuid4().hex[:12]}",
                    type=RecommendationType.PROJECT_HEALTH,
                    title=f"Low Margin: {project.get('name')}",
                    description=f"Project margin is only {margin:.1%}. Review costs and scope to improve profitability.",
                    priority=6,
                    confidence=0.9,
                    potential_impact="Improve project profitability",
                    actions=[
                        {"action": "view_project", "project_id": project.get("id")},
                    ],
                ))
            
            # Budget overrun
            if project.get("costs", 0) > project.get("budget", float('inf')) * 0.9:
                recommendations.append(Recommendation(
                    id=f"rec_{uuid4().hex[:12]}",
                    type=RecommendationType.PROJECT_HEALTH,
                    title=f"Budget Alert: {project.get('name')}",
                    description="Project is approaching or exceeding budget. Review remaining tasks and costs.",
                    priority=7,
                    confidence=0.95,
                    actions=[
                        {"action": "view_project", "project_id": project.get("id")},
                    ],
                ))
        
        return recommendations
    
    def get_customer_recommendations(self, customer_id: str) -> List[Recommendation]:
        """Get stored recommendations for customer."""
        recommendations = self._generated.get(customer_id, [])
        return [r for r in recommendations if r.expires_at is None or r.expires_at > datetime.utcnow()]


# Global engine instance
recommendation_engine = RecommendationEngine()
```

---

## File 4: AI Module Final Init
**Path:** `backend/app/ai/__init__.py` (updated)

```python
"""
AI/ML Features Module
Intelligent features for LogiAccounting Pro
"""

from app.ai.config import (
    AIConfig,
    AIProvider,
    ModelType,
    ModelConfig,
    ai_config,
    get_model_config,
    MODEL_PRESETS,
)

from app.ai.client import (
    AIClient,
    AnthropicClient,
    OpenAIClient,
    AIClientManager,
    ai_client,
)

from app.ai.base import (
    AIResult,
    Prediction,
    Anomaly,
    Recommendation,
    PredictionConfidence,
    AlertSeverity,
    BasePredictor,
    BaseDetector,
    BaseExtractor,
    BaseAssistant,
)

from app.ai.utils import (
    prepare_time_series,
    calculate_features,
    detect_seasonality,
    calculate_z_scores,
    calculate_iqr_bounds,
    detect_outliers,
    extract_numbers,
    extract_dates,
    clean_text,
    AICache,
    ai_cache,
    format_currency,
    format_percentage,
    format_change,
)

# Import submodules
from app.ai import cashflow
from app.ai import ocr
from app.ai import assistant
from app.ai import anomaly

# Service aggregator
from app.ai.service import ai_service

# Recommendations
from app.ai.recommendations.engine import recommendation_engine


__all__ = [
    # Config
    'AIConfig',
    'AIProvider',
    'ModelType',
    'ModelConfig',
    'ai_config',
    'get_model_config',
    'MODEL_PRESETS',
    
    # Client
    'AIClient',
    'AnthropicClient',
    'OpenAIClient',
    'AIClientManager',
    'ai_client',
    
    # Base classes
    'AIResult',
    'Prediction',
    'Anomaly',
    'Recommendation',
    'PredictionConfidence',
    'AlertSeverity',
    'BasePredictor',
    'BaseDetector',
    'BaseExtractor',
    'BaseAssistant',
    
    # Utilities
    'prepare_time_series',
    'calculate_features',
    'detect_seasonality',
    'calculate_z_scores',
    'calculate_iqr_bounds',
    'detect_outliers',
    'extract_numbers',
    'extract_dates',
    'clean_text',
    'AICache',
    'ai_cache',
    'format_currency',
    'format_percentage',
    'format_change',
    
    # Submodules
    'cashflow',
    'ocr',
    'assistant',
    'anomaly',
    
    # Services
    'ai_service',
    'recommendation_engine',
]


def init_ai_module():
    """Initialize AI module."""
    import logging
    
    logger = logging.getLogger("app.ai")
    logger.info("AI/ML module initialized")
    
    # Verify configuration
    if not ai_config.anthropic_api_key and not ai_config.openai_api_key:
        logger.warning("No AI API keys configured - AI features will be limited")
    
    # Log enabled features
    enabled = [f for f, v in ai_config.features.items() if v]
    logger.info(f"Enabled AI features: {', '.join(enabled)}")
    
    return True
```

---

## Summary Part 6

| File | Description | Lines |
|------|-------------|-------|
| `routes/ai.py` | AI API routes | ~350 |
| `ai/service.py` | Service aggregator | ~180 |
| `ai/recommendations/engine.py` | Recommendations engine | ~230 |
| `ai/__init__.py` | Updated module init | ~130 |
| **Total** | | **~890 lines** |
