"""
Payment Gateway routes
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.gateway_service import gateway_service
from app.utils.auth import require_roles

router = APIRouter()


class UpdateGatewayRequest(BaseModel):
    enabled: Optional[bool] = None
    mode: Optional[str] = None
    credentials: Optional[dict] = None
    is_default: Optional[bool] = None


@router.get("/providers")
async def get_supported_providers():
    """Get list of supported payment providers"""
    return {"providers": list(gateway_service.SUPPORTED_GATEWAYS.keys())}


@router.get("")
async def list_gateways(
    enabled_only: bool = False,
    current_user: dict = Depends(require_roles("admin"))
):
    """List all gateway configurations"""
    return {"gateways": gateway_service.list_gateways(enabled_only)}


@router.get("/default")
async def get_default_gateway(current_user: dict = Depends(require_roles("admin"))):
    """Get default gateway"""
    gateway = gateway_service.get_default_gateway()
    if not gateway:
        raise HTTPException(status_code=404, detail="No gateway configured")
    return gateway


@router.get("/for-currency/{currency}")
async def get_gateways_for_currency(
    currency: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get gateways that support a currency"""
    return {"gateways": gateway_service.get_gateways_for_currency(currency.upper())}


@router.get("/{provider}")
async def get_gateway(
    provider: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get gateway configuration"""
    gateway = gateway_service.get_gateway(provider)
    if not gateway:
        raise HTTPException(status_code=404, detail="Gateway not found")
    return gateway


@router.put("/{provider}")
async def update_gateway(
    provider: str,
    request: UpdateGatewayRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update gateway configuration"""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    gateway = gateway_service.update_gateway(provider, updates)
    if not gateway:
        raise HTTPException(status_code=404, detail="Gateway not found")
    return gateway


@router.post("/{provider}/test")
async def test_gateway(
    provider: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Test gateway connection"""
    return gateway_service.test_connection(provider)


@router.get("/{provider}/calculate-fee")
async def calculate_fee(
    provider: str,
    amount: float,
    current_user: dict = Depends(require_roles("admin"))
):
    """Calculate gateway fee for an amount"""
    result = gateway_service.calculate_fee(provider, amount)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
