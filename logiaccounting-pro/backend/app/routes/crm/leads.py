"""
CRM Leads API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel, EmailStr

from app.utils.auth import get_current_user
from app.services.crm.lead_service import lead_service


router = APIRouter()


# ============================================
# PYDANTIC MODELS
# ============================================

class LeadCreate(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    source: Optional[str] = "website"
    notes: Optional[str] = None


class LeadUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    bant_budget: Optional[bool] = None
    bant_authority: Optional[bool] = None
    bant_need: Optional[bool] = None
    bant_timeline: Optional[bool] = None


class LeadConvert(BaseModel):
    create_contact: Optional[bool] = True
    create_opportunity: Optional[bool] = True
    opportunity_amount: Optional[float] = None
    opportunity_name: Optional[str] = None


class LeadAssign(BaseModel):
    owner_id: str


class BulkAssign(BaseModel):
    lead_ids: List[str]
    owner_id: str


class LeadImport(BaseModel):
    leads: List[dict]


# ============================================
# ENDPOINTS
# ============================================

@router.get("")
async def list_leads(
    status: Optional[str] = None,
    source: Optional[str] = None,
    owner_id: Optional[str] = None,
    rating: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """List leads with filters"""
    return lead_service.list_leads(
        tenant_id=current_user.get("tenant_id"),
        status=status,
        source=source,
        owner_id=owner_id,
        rating=rating,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.post("")
async def create_lead(
    data: LeadCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new lead"""
    return lead_service.create_lead(
        tenant_id=current_user.get("tenant_id"),
        owner_id=current_user["id"],
        **data.dict(exclude_none=True),
    )


@router.get("/sources")
async def get_lead_sources():
    """Get available lead sources"""
    return lead_service.LEAD_SOURCES


@router.get("/statuses")
async def get_lead_statuses():
    """Get available lead statuses"""
    return lead_service.LEAD_STATUSES


@router.get("/sources/stats")
async def get_lead_source_stats(
    current_user: dict = Depends(get_current_user),
):
    """Get lead statistics by source"""
    return lead_service.get_lead_sources_stats(
        tenant_id=current_user.get("tenant_id"),
    )


@router.post("/import")
async def import_leads(
    data: LeadImport,
    current_user: dict = Depends(get_current_user),
):
    """Bulk import leads"""
    return lead_service.import_leads(
        tenant_id=current_user.get("tenant_id"),
        user_id=current_user["id"],
        leads_data=data.leads,
    )


@router.post("/bulk-assign")
async def bulk_assign_leads(
    data: BulkAssign,
    current_user: dict = Depends(get_current_user),
):
    """Bulk assign leads to a user"""
    count = lead_service.bulk_assign(
        lead_ids=data.lead_ids,
        owner_id=data.owner_id,
        assigned_by=current_user["id"],
    )
    return {"assigned": count}


@router.get("/{lead_id}")
async def get_lead(
    lead_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get lead by ID"""
    lead = lead_service.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.put("/{lead_id}")
async def update_lead(
    lead_id: str,
    data: LeadUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update lead"""
    lead = lead_service.update_lead(
        lead_id=lead_id,
        user_id=current_user["id"],
        **data.dict(exclude_none=True),
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete lead"""
    if not lead_service.delete_lead(lead_id, current_user["id"]):
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"success": True}


@router.post("/{lead_id}/convert")
async def convert_lead(
    lead_id: str,
    data: LeadConvert,
    current_user: dict = Depends(get_current_user),
):
    """Convert lead to contact and/or opportunity"""
    return lead_service.convert_lead(
        lead_id=lead_id,
        user_id=current_user["id"],
        **data.dict(exclude_none=True),
    )


@router.post("/{lead_id}/assign")
async def assign_lead(
    lead_id: str,
    data: LeadAssign,
    current_user: dict = Depends(get_current_user),
):
    """Assign lead to a user"""
    return lead_service.assign_lead(
        lead_id=lead_id,
        owner_id=data.owner_id,
        assigned_by=current_user["id"],
    )


@router.put("/{lead_id}/status")
async def change_status(
    lead_id: str,
    status: str,
    current_user: dict = Depends(get_current_user),
):
    """Change lead status"""
    return lead_service.change_status(
        lead_id=lead_id,
        user_id=current_user["id"],
        status=status,
    )
