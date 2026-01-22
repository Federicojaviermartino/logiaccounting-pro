"""
AI Usage Tracking Routes
"""

from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query

from app.utils.auth import get_current_user, require_roles
from ..models.ai_usage import AIUsage
from ..config import get_ai_config

router = APIRouter()


@router.get("/usage")
async def get_usage(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(require_roles("admin"))
):
    """Get AI usage statistics"""
    tenant_id = current_user.get("tenant_id", "default")
    start_date = datetime.utcnow() - timedelta(days=days)

    return AIUsage.get_usage_summary(
        tenant_id=tenant_id,
        start_date=start_date,
    )


@router.get("/usage/by-feature")
async def get_usage_by_feature(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(require_roles("admin"))
):
    """Get AI usage broken down by feature"""
    tenant_id = current_user.get("tenant_id", "default")
    start_date = datetime.utcnow() - timedelta(days=days)

    summary = AIUsage.get_usage_summary(tenant_id, start_date)

    return {
        "period_days": days,
        "by_feature": summary.get("by_feature", {}),
        "total_requests": summary.get("total_requests", 0),
    }


@router.get("/usage/costs")
async def get_usage_costs(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(require_roles("admin"))
):
    """Get AI usage costs"""
    tenant_id = current_user.get("tenant_id", "default")
    start_date = datetime.utcnow() - timedelta(days=days)

    summary = AIUsage.get_usage_summary(tenant_id, start_date)

    return {
        "period_days": days,
        "total_cost": summary.get("total_cost", 0),
        "by_model": summary.get("by_model", {}),
        "total_tokens": summary.get("total_input_tokens", 0) + summary.get("total_output_tokens", 0),
    }


@router.get("/config")
async def get_ai_config_status(
    current_user: dict = Depends(require_roles("admin"))
):
    """Get AI configuration status"""
    config = get_ai_config()

    return {
        "llm": {
            "provider": config.llm.provider.value,
            "anthropic_configured": bool(config.llm.anthropic_api_key),
            "openai_configured": bool(config.llm.openai_api_key),
            "default_model_tier": config.llm.default_model_tier.value,
        },
        "ocr": {
            "tesseract_path": config.ocr.tesseract_path,
            "default_language": config.ocr.default_language,
        },
        "cashflow": {
            "default_horizon_days": config.cashflow.default_horizon_days,
            "use_prophet": config.cashflow.use_prophet,
        },
        "anomaly": {
            "zscore_threshold": config.anomaly.zscore_threshold,
            "min_historical_data": config.anomaly.min_historical_data,
        },
    }


@router.get("/health")
async def ai_health_check():
    """Check AI services health"""
    config = get_ai_config()

    checks = {
        "llm_configured": False,
        "ocr_available": False,
        "prophet_available": False,
    }

    # Check LLM
    if config.llm.anthropic_api_key or config.llm.openai_api_key:
        checks["llm_configured"] = True

    # Check OCR
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        checks["ocr_available"] = True
    except Exception:
        pass

    # Check Prophet
    try:
        import prophet
        checks["prophet_available"] = True
    except ImportError:
        pass

    all_healthy = all(checks.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks,
        "message": "All AI services operational" if all_healthy else "Some AI services unavailable",
    }
