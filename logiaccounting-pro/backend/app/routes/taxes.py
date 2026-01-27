"""
Tax Management routes
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.tax_service import tax_service
from app.utils.auth import get_current_user, require_roles

router = APIRouter()


class CreateTaxRequest(BaseModel):
    name: str
    code: str
    type: str
    rate: float
    applies_to: List[str] = ["products", "services"]
    exempt_categories: List[str] = []
    regions: List[str] = []
    is_compound: bool = False
    is_default: bool = False


class UpdateTaxRequest(BaseModel):
    name: Optional[str] = None
    rate: Optional[float] = None
    applies_to: Optional[List[str]] = None
    exempt_categories: Optional[List[str]] = None
    is_default: Optional[bool] = None
    active: Optional[bool] = None


class CalculateTaxRequest(BaseModel):
    amount: float
    tax_id: Optional[str] = None
    tax_code: Optional[str] = None
    is_inclusive: bool = False


@router.get("/types")
async def get_tax_types():
    """Get available tax types"""
    return {"types": tax_service.TAX_TYPES}


@router.get("")
async def list_taxes(
    active_only: bool = True,
    tax_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List all taxes"""
    return {"taxes": tax_service.list_taxes(active_only, tax_type)}


@router.post("")
async def create_tax(
    request: CreateTaxRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Create a tax rate"""
    return tax_service.create_tax(
        name=request.name,
        code=request.code,
        tax_type=request.type,
        rate=request.rate,
        applies_to=request.applies_to,
        exempt_categories=request.exempt_categories,
        regions=request.regions,
        is_compound=request.is_compound,
        is_default=request.is_default
    )


@router.get("/default")
async def get_default_tax(
    tax_type: str = "vat",
    current_user: dict = Depends(get_current_user)
):
    """Get default tax"""
    tax = tax_service.get_default_tax(tax_type)
    if not tax:
        raise HTTPException(status_code=404, detail="No default tax found")
    return tax


@router.post("/calculate")
async def calculate_tax(
    request: CalculateTaxRequest,
    current_user: dict = Depends(get_current_user)
):
    """Calculate tax for an amount"""
    return tax_service.calculate_tax(
        amount=request.amount,
        tax_id=request.tax_id,
        tax_code=request.tax_code,
        is_inclusive=request.is_inclusive
    )


@router.get("/report")
async def get_tax_report(
    period_start: str,
    period_end: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Generate tax report"""
    return tax_service.generate_tax_report(period_start, period_end)


@router.get("/{tax_id}")
async def get_tax(
    tax_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a tax rate"""
    tax = tax_service.get_tax(tax_id)
    if not tax:
        raise HTTPException(status_code=404, detail="Tax not found")
    return tax


@router.put("/{tax_id}")
async def update_tax(
    tax_id: str,
    request: UpdateTaxRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update a tax rate"""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    tax = tax_service.update_tax(tax_id, updates)
    if not tax:
        raise HTTPException(status_code=404, detail="Tax not found")
    return tax


@router.delete("/{tax_id}")
async def delete_tax(
    tax_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Delete a tax rate"""
    if tax_service.delete_tax(tax_id):
        return {"message": "Tax deleted"}
    raise HTTPException(status_code=404, detail="Tax not found")
