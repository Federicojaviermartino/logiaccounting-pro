"""
CRM Contacts API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel, EmailStr

from app.utils.auth import get_current_user
from app.services.crm.contact_service import contact_service


router = APIRouter()


# ============================================
# PYDANTIC MODELS
# ============================================

class ContactCreate(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    company_id: Optional[str] = None


class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    company_id: Optional[str] = None


class MergeContacts(BaseModel):
    primary_id: str
    secondary_id: str


class ContactPreferences(BaseModel):
    do_not_call: Optional[bool] = None
    do_not_email: Optional[bool] = None
    preferred_contact_method: Optional[str] = None


class ContactImport(BaseModel):
    contacts: List[dict]


# ============================================
# ENDPOINTS
# ============================================

@router.get("")
async def list_contacts(
    company_id: Optional[str] = None,
    owner_id: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """List contacts with filters"""
    return contact_service.list_contacts(
        tenant_id=current_user.get("tenant_id"),
        company_id=company_id,
        owner_id=owner_id,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.post("")
async def create_contact(
    data: ContactCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new contact"""
    return contact_service.create_contact(
        tenant_id=current_user.get("tenant_id"),
        owner_id=current_user["id"],
        **data.dict(exclude_none=True),
    )


@router.get("/search")
async def search_contacts(
    q: str,
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
):
    """Quick search for contacts"""
    return contact_service.search_contacts(
        tenant_id=current_user.get("tenant_id"),
        query=q,
        limit=limit,
    )


@router.get("/roles")
async def get_contact_roles():
    """Get available contact roles"""
    return contact_service.CONTACT_ROLES


@router.post("/import")
async def import_contacts(
    data: ContactImport,
    current_user: dict = Depends(get_current_user),
):
    """Bulk import contacts"""
    return contact_service.import_contacts(
        tenant_id=current_user.get("tenant_id"),
        user_id=current_user["id"],
        contacts_data=data.contacts,
    )


@router.get("/export")
async def export_contacts(
    format: str = "csv",
    current_user: dict = Depends(get_current_user),
):
    """Export contacts to CSV"""
    from fastapi.responses import Response
    content = contact_service.export_contacts(
        tenant_id=current_user.get("tenant_id"),
        format=format,
    )
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=contacts.csv"},
    )


@router.post("/merge")
async def merge_contacts(
    data: MergeContacts,
    current_user: dict = Depends(get_current_user),
):
    """Merge two contacts into one"""
    return contact_service.merge_contacts(
        primary_id=data.primary_id,
        secondary_id=data.secondary_id,
        user_id=current_user["id"],
    )


@router.get("/{contact_id}")
async def get_contact(
    contact_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get contact by ID"""
    contact = contact_service.get_contact(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.get("/{contact_id}/360")
async def get_contact_360(
    contact_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get 360-degree view of contact"""
    contact = contact_service.get_contact_360(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.put("/{contact_id}")
async def update_contact(
    contact_id: str,
    data: ContactUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update contact"""
    contact = contact_service.update_contact(
        contact_id=contact_id,
        user_id=current_user["id"],
        **data.dict(exclude_none=True),
    )
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete contact"""
    if not contact_service.delete_contact(contact_id, current_user["id"]):
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"success": True}


@router.put("/{contact_id}/preferences")
async def set_preferences(
    contact_id: str,
    data: ContactPreferences,
    current_user: dict = Depends(get_current_user),
):
    """Update contact communication preferences"""
    return contact_service.set_preferences(
        contact_id=contact_id,
        **data.dict(exclude_none=True),
    )
