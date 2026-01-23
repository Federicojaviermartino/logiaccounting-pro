"""
CRM Companies API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel

from app.utils.auth import get_current_user
from app.services.crm.company_service import company_service


router = APIRouter()


# ============================================
# PYDANTIC MODELS
# ============================================

class CompanyCreate(BaseModel):
    name: str
    website: Optional[str] = None
    industry: Optional[str] = None
    employees_count: Optional[int] = None
    annual_revenue: Optional[float] = None
    type: Optional[str] = "prospect"
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    employees_count: Optional[int] = None
    annual_revenue: Optional[float] = None
    type: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None


class SetParentCompany(BaseModel):
    parent_id: str


class LinkToClient(BaseModel):
    client_id: str


# ============================================
# ENDPOINTS
# ============================================

@router.get("")
async def list_companies(
    type: Optional[str] = None,
    industry: Optional[str] = None,
    owner_id: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """List companies with filters"""
    return company_service.list_companies(
        tenant_id=current_user.get("tenant_id"),
        type=type,
        industry=industry,
        owner_id=owner_id,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.post("")
async def create_company(
    data: CompanyCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new company"""
    return company_service.create_company(
        tenant_id=current_user.get("tenant_id"),
        owner_id=current_user["id"],
        **data.dict(exclude_none=True),
    )


@router.get("/types")
async def get_company_types():
    """Get available company types"""
    return company_service.COMPANY_TYPES


@router.get("/industries")
async def get_industries():
    """Get available industries"""
    return company_service.INDUSTRIES


@router.get("/top")
async def get_top_accounts(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
):
    """Get top accounts by revenue"""
    return company_service.get_top_accounts(
        tenant_id=current_user.get("tenant_id"),
        limit=limit,
    )


@router.get("/at-risk")
async def get_at_risk_accounts(
    current_user: dict = Depends(get_current_user),
):
    """Get accounts with low health scores"""
    return company_service.get_at_risk_accounts(
        tenant_id=current_user.get("tenant_id"),
    )


@router.get("/{company_id}")
async def get_company(
    company_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get company by ID"""
    company = company_service.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.get("/{company_id}/summary")
async def get_company_summary(
    company_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get company with full summary"""
    summary = company_service.get_company_summary(company_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Company not found")
    return summary


@router.put("/{company_id}")
async def update_company(
    company_id: str,
    data: CompanyUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update company"""
    company = company_service.update_company(
        company_id=company_id,
        user_id=current_user["id"],
        **data.dict(exclude_none=True),
    )
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.delete("/{company_id}")
async def delete_company(
    company_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete company"""
    if not company_service.delete_company(company_id, current_user["id"]):
        raise HTTPException(status_code=404, detail="Company not found")
    return {"success": True}


@router.post("/{company_id}/parent")
async def set_parent_company(
    company_id: str,
    data: SetParentCompany,
    current_user: dict = Depends(get_current_user),
):
    """Set parent company (company hierarchy)"""
    return company_service.set_parent_company(
        company_id=company_id,
        parent_id=data.parent_id,
        user_id=current_user["id"],
    )


@router.get("/{company_id}/subsidiaries")
async def get_subsidiaries(
    company_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get subsidiary companies"""
    return company_service.get_subsidiaries(company_id)


@router.post("/{company_id}/link-client")
async def link_to_client(
    company_id: str,
    data: LinkToClient,
    current_user: dict = Depends(get_current_user),
):
    """Link CRM company to existing client record"""
    return company_service.link_to_client(
        company_id=company_id,
        client_id=data.client_id,
        user_id=current_user["id"],
    )
