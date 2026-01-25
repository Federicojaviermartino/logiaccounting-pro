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
