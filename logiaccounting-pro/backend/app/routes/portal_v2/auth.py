"""
Portal v2 Authentication Routes
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.services.portal.auth_service import portal_auth_service


router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TwoFactorRequest(BaseModel):
    temp_token: str
    code: str


class RefreshRequest(BaseModel):
    refresh_token: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    contact_id: str
    company_id: str
    tenant_id: str


class MagicLinkRequest(BaseModel):
    email: EmailStr
    tenant_id: str


class MagicLinkVerifyRequest(BaseModel):
    token: str


@router.post("/login")
async def login(data: LoginRequest, request: Request):
    """Authenticate portal user."""
    try:
        result = portal_auth_service.authenticate(
            email=data.email,
            password=data.password,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/verify-2fa")
async def verify_2fa(data: TwoFactorRequest, request: Request):
    """Verify 2FA code."""
    try:
        result = portal_auth_service.verify_2fa(
            temp_token=data.temp_token,
            code=data.code,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/refresh")
async def refresh_token(data: RefreshRequest):
    """Refresh access token."""
    try:
        return portal_auth_service.refresh_session(data.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
async def logout(request: Request):
    """End portal session."""
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        from app.utils.auth import decode_token
        try:
            payload = decode_token(token)
            session_id = payload.get("session_id")
            if session_id:
                portal_auth_service.logout(session_id)
        except:
            pass
    return {"success": True}


@router.post("/register")
async def register(data: RegisterRequest):
    """Register new portal user (admin use)."""
    try:
        result = portal_auth_service.register_portal_user(
            email=data.email,
            password=data.password,
            contact_id=data.contact_id,
            company_id=data.company_id,
            tenant_id=data.tenant_id,
            name=data.name,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/magic-link/request")
async def request_magic_link(data: MagicLinkRequest):
    """Request magic link for passwordless login."""
    try:
        token = portal_auth_service.create_magic_link(
            email=data.email,
            tenant_id=data.tenant_id,
        )
        # In production, send email with link
        return {"success": True, "message": "Magic link sent to email"}
    except ValueError as e:
        # Don't reveal if user exists
        return {"success": True, "message": "Magic link sent to email"}


@router.post("/magic-link/verify")
async def verify_magic_link(data: MagicLinkVerifyRequest, request: Request):
    """Verify magic link and login."""
    try:
        result = portal_auth_service.verify_magic_link(
            token=data.token,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
