"""
Digital Signature Routes - Phase 13
E-signature workflow API endpoints
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel, EmailStr
import logging

from app.utils.auth import get_current_user
from app.services.signature_service import signature_service

logger = logging.getLogger(__name__)

router = APIRouter()


# Request Models
class RecipientModel(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    role: str = "signer"
    order: Optional[int] = None


class CreateSignatureRequestModel(BaseModel):
    document_id: str
    title: str
    recipients: List[RecipientModel]
    message: Optional[str] = None
    signing_order: str = "parallel"
    expires_in_days: int = 30
    reminder_frequency: int = 3


class SignDocumentModel(BaseModel):
    signature_data: str  # Base64 encoded signature image


class DeclineSignatureModel(BaseModel):
    reason: Optional[str] = None


# Signature Request Endpoints
@router.post("/requests")
async def create_signature_request(
    request: CreateSignatureRequestModel,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new signature request

    Args:
        document_id: ID of document to sign
        title: Title of the signature request
        recipients: List of recipients with email, name, role, order
        message: Optional message to signers
        signing_order: 'sequential' or 'parallel'
        expires_in_days: Days until request expires
        reminder_frequency: Days between reminders
    """
    org_id = current_user.get("organization_id", "default")

    result = signature_service.create_request(
        document_id=request.document_id,
        organization_id=org_id,
        created_by=current_user["id"],
        title=request.title,
        recipients=[r.model_dump() for r in request.recipients],
        message=request.message,
        signing_order=request.signing_order,
        expires_in_days=request.expires_in_days,
        reminder_frequency=request.reminder_frequency
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.post("/requests/{request_id}/send")
async def send_signature_request(
    request_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Send signature request to recipients"""
    org_id = current_user.get("organization_id", "default")

    result = signature_service.send_request(request_id, org_id)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.get("/requests")
async def list_signature_requests(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """List signature requests for organization"""
    org_id = current_user.get("organization_id", "default")

    result = signature_service.list_requests(
        organization_id=org_id,
        status=status,
        page=page,
        per_page=per_page
    )

    return result


@router.get("/requests/{request_id}")
async def get_signature_request(
    request_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get signature request details"""
    org_id = current_user.get("organization_id", "default")

    result = signature_service.get_request_status(request_id, org_id)

    if not result:
        raise HTTPException(status_code=404, detail="Request not found")

    return {"request": result}


@router.post("/requests/{request_id}/cancel")
async def cancel_signature_request(
    request_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Cancel a signature request"""
    org_id = current_user.get("organization_id", "default")

    result = signature_service.cancel_request(
        request_id=request_id,
        organization_id=org_id,
        cancelled_by=current_user["id"]
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.get("/requests/{request_id}/verify")
async def verify_signatures(
    request_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Verify all signatures on a completed request"""
    org_id = current_user.get("organization_id", "default")

    result = signature_service.verify_signatures(request_id, org_id)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


# Public Signing Endpoints (no auth required)
@router.get("/sign/{access_token}")
async def get_signing_document(access_token: str):
    """
    Get document for signing (public endpoint)

    Returns document info and signing context for the recipient
    """
    result = signature_service.get_signing_document(access_token)

    if not result:
        raise HTTPException(status_code=404, detail="Invalid or expired signing link")

    if "error" in result:
        raise HTTPException(status_code=403, detail=result["error"])

    return result


@router.post("/sign/{access_token}")
async def sign_document(
    access_token: str,
    body: SignDocumentModel,
    request: Request
):
    """
    Sign a document (public endpoint)

    Args:
        signature_data: Base64 encoded signature image
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    result = signature_service.sign_document(
        access_token=access_token,
        signature_data=body.signature_data,
        ip_address=ip_address,
        user_agent=user_agent
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.post("/sign/{access_token}/decline")
async def decline_signature(
    access_token: str,
    body: DeclineSignatureModel
):
    """
    Decline to sign a document (public endpoint)

    Args:
        reason: Optional reason for declining
    """
    result = signature_service.decline_signature(
        access_token=access_token,
        reason=body.reason
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result
