"""
Enterprise SSO API Routes
"""

from fastapi import APIRouter, HTTPException, status, Depends, Request, Response, Header
from fastapi.responses import RedirectResponse
from typing import Optional, List
from app.models.store import db
from app.utils.auth import get_current_user, require_roles, create_access_token
from app.services.sso_service import sso_service, SSOServiceError
from app.schemas.sso import (
    SSOConnectionCreate,
    SSOConnectionUpdate,
    SSOConnectionResponse,
    SSOLoginInitiate,
    SSOLoginInitiateResponse,
    SSOLoginResponse,
    DomainDiscoveryRequest,
    DomainDiscoveryResponse,
    SCIMTokenResponse,
    SCIMConfigUpdate,
)

router = APIRouter()


# ===================
# SSO Connection Management (Admin)
# ===================

@router.get("/connections", response_model=List[SSOConnectionResponse])
async def list_connections(
    status: Optional[str] = None,
    current_user: dict = Depends(require_roles(["admin"]))
):
    """List all SSO connections"""
    filters = {}
    if status:
        filters["status"] = status

    connections = sso_service.get_connections(filters)
    return connections


@router.post("/connections", response_model=SSOConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(
    data: SSOConnectionCreate,
    current_user: dict = Depends(require_roles(["admin"]))
):
    """Create new SSO connection"""
    connection_data = data.model_dump()

    config = connection_data.get("configuration", {})
    if config.get("client_secret"):
        connection_data["client_secret"] = config.pop("client_secret")

    connection = sso_service.create_connection(connection_data)
    return connection


@router.get("/connections/{connection_id}", response_model=SSOConnectionResponse)
async def get_connection(
    connection_id: str,
    current_user: dict = Depends(require_roles(["admin"]))
):
    """Get SSO connection details"""
    connection = sso_service.get_connection(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    return connection


@router.put("/connections/{connection_id}", response_model=SSOConnectionResponse)
async def update_connection(
    connection_id: str,
    data: SSOConnectionUpdate,
    current_user: dict = Depends(require_roles(["admin"]))
):
    """Update SSO connection"""
    update_data = data.model_dump(exclude_unset=True)

    config = update_data.get("configuration", {})
    if config and config.get("client_secret"):
        update_data["client_secret"] = config.pop("client_secret")

    connection = sso_service.update_connection(connection_id, update_data)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    return connection


@router.delete("/connections/{connection_id}")
async def delete_connection(
    connection_id: str,
    current_user: dict = Depends(require_roles(["admin"]))
):
    """Delete SSO connection"""
    if not sso_service.delete_connection(connection_id):
        raise HTTPException(status_code=404, detail="Connection not found")
    return {"success": True, "message": "Connection deleted"}


@router.post("/connections/{connection_id}/activate")
async def activate_connection(
    connection_id: str,
    current_user: dict = Depends(require_roles(["admin"]))
):
    """Activate SSO connection"""
    connection = sso_service.update_connection(connection_id, {"status": "active"})
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    return {"success": True, "connection": connection}


@router.post("/connections/{connection_id}/deactivate")
async def deactivate_connection(
    connection_id: str,
    current_user: dict = Depends(require_roles(["admin"]))
):
    """Deactivate SSO connection"""
    connection = sso_service.update_connection(connection_id, {"status": "inactive"})
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    return {"success": True, "connection": connection}


# ===================
# SCIM Configuration
# ===================

@router.post("/connections/{connection_id}/scim/token", response_model=SCIMTokenResponse)
async def generate_scim_token(
    connection_id: str,
    current_user: dict = Depends(require_roles(["admin"]))
):
    """Generate new SCIM bearer token"""
    try:
        token = sso_service.generate_scim_token(connection_id)
        return {
            "token": token,
            "endpoint": f"{sso_service.base_url}/api/v1/scim/{connection_id}"
        }
    except SSOServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/connections/{connection_id}/scim")
async def update_scim_config(
    connection_id: str,
    data: SCIMConfigUpdate,
    current_user: dict = Depends(require_roles(["admin"]))
):
    """Enable/disable SCIM for connection"""
    connection = sso_service.update_connection(connection_id, {"scim_enabled": data.scim_enabled})
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    return {"success": True, "scim_enabled": data.scim_enabled}


# ===================
# Domain Discovery
# ===================

@router.post("/discover", response_model=DomainDiscoveryResponse)
async def discover_sso(data: DomainDiscoveryRequest):
    """Discover SSO connection from email domain"""
    connection = sso_service.discover_connection(data.email)

    if connection:
        return {
            "sso_enabled": True,
            "connection_id": connection["id"],
            "connection_name": connection.get("name"),
            "protocol": connection.get("protocol"),
            "provider_type": connection.get("provider_type"),
        }

    return {"sso_enabled": False}


# ===================
# SAML Authentication
# ===================

@router.get("/saml/{connection_id}/login")
async def saml_login(connection_id: str, relay_state: Optional[str] = None):
    """Initiate SAML login"""
    try:
        redirect_url, request_id = sso_service.initiate_saml_login(connection_id, relay_state)
        return RedirectResponse(url=redirect_url, status_code=302)
    except SSOServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/saml/{connection_id}/acs")
async def saml_acs(connection_id: str, request: Request):
    """SAML Assertion Consumer Service endpoint"""
    form_data = await request.form()
    saml_response = form_data.get("SAMLResponse")
    relay_state = form_data.get("RelayState")

    if not saml_response:
        raise HTTPException(status_code=400, detail="SAMLResponse is required")

    try:
        result = sso_service.process_saml_response(connection_id, saml_response, relay_state)

        token = create_access_token({
            "user_id": result["user"]["id"],
            "role": result["user"]["role"]
        })

        frontend_url = f"{sso_service.base_url}/sso/callback?token={token}"
        if relay_state:
            frontend_url += f"&redirect={relay_state}"

        return RedirectResponse(url=frontend_url, status_code=302)

    except SSOServiceError as e:
        error_url = f"{sso_service.base_url}/sso/error?message={e}"
        return RedirectResponse(url=error_url, status_code=302)


@router.get("/saml/{connection_id}/metadata")
async def saml_metadata(connection_id: str):
    """Get SAML SP metadata"""
    connection = db.sso_connections.find_by_id(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    from app.auth.sso.saml import SAMLMetadataGenerator

    config = connection.get("configuration", {})
    generator = SAMLMetadataGenerator(
        entity_id=f"{sso_service.base_url}/sso/saml/{connection_id}/metadata",
        acs_url=f"{sso_service.base_url}/api/v1/sso/saml/{connection_id}/acs",
        sls_url=f"{sso_service.base_url}/api/v1/sso/saml/{connection_id}/sls",
        certificate=config.get("sp_certificate", ""),
    )

    metadata_xml = generator.generate()

    return Response(
        content=metadata_xml,
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename=sp-metadata-{connection_id}.xml"}
    )


@router.get("/saml/{connection_id}/sls")
async def saml_sls(
    connection_id: str,
    SAMLRequest: Optional[str] = None,
    SAMLResponse: Optional[str] = None,
    RelayState: Optional[str] = None,
):
    """SAML Single Logout Service endpoint"""
    logout_url = f"{sso_service.base_url}/logout"
    if RelayState:
        logout_url = RelayState

    return RedirectResponse(url=logout_url, status_code=302)


# ===================
# OAuth2/OIDC Authentication
# ===================

@router.get("/oauth/{connection_id}/login")
async def oauth_login(connection_id: str, login_hint: Optional[str] = None):
    """Initiate OAuth2/OIDC login"""
    try:
        redirect_url, state = sso_service.initiate_oauth_login(connection_id, login_hint)
        return RedirectResponse(url=redirect_url, status_code=302)
    except SSOServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/oauth/{connection_id}/callback")
async def oauth_callback(
    connection_id: str,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
):
    """OAuth2/OIDC callback endpoint"""
    if error:
        error_url = f"{sso_service.base_url}/sso/error?message={error_description or error}"
        return RedirectResponse(url=error_url, status_code=302)

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    try:
        result = await sso_service.process_oauth_callback(connection_id, code, state)

        token = create_access_token({
            "user_id": result["user"]["id"],
            "role": result["user"]["role"]
        })

        frontend_url = f"{sso_service.base_url}/sso/callback?token={token}"
        return RedirectResponse(url=frontend_url, status_code=302)

    except SSOServiceError as e:
        error_url = f"{sso_service.base_url}/sso/error?message={e}"
        return RedirectResponse(url=error_url, status_code=302)


# ===================
# API-based SSO Login (for SPA)
# ===================

@router.post("/login/initiate", response_model=SSOLoginInitiateResponse)
async def initiate_sso_login(data: SSOLoginInitiate):
    """Initiate SSO login and get redirect URL (for SPA)"""
    connection = None

    if data.connection_id:
        connection = sso_service.get_connection(data.connection_id)
    elif data.email:
        connection = sso_service.discover_connection(data.email)

    if not connection:
        raise HTTPException(status_code=404, detail="No SSO connection found")

    protocol = connection.get("protocol")

    try:
        if protocol == "saml":
            redirect_url, state = sso_service.initiate_saml_login(connection["id"])
        else:
            login_hint = data.email if data.email else None
            redirect_url, state = sso_service.initiate_oauth_login(connection["id"], login_hint)

        return {
            "redirect_url": redirect_url,
            "state": state,
            "connection_id": connection["id"],
            "protocol": protocol,
        }

    except SSOServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===================
# External Identities
# ===================

@router.get("/identities")
async def list_external_identities(
    user_id: Optional[str] = None,
    connection_id: Optional[str] = None,
    current_user: dict = Depends(require_roles(["admin"]))
):
    """List external identities"""
    filters = {}
    if user_id:
        filters["user_id"] = user_id
    if connection_id:
        filters["connection_id"] = connection_id

    identities = db.external_identities.find_all(filters)
    return identities


@router.delete("/identities/{identity_id}")
async def unlink_external_identity(
    identity_id: str,
    current_user: dict = Depends(require_roles(["admin"]))
):
    """Unlink external identity from user"""
    if not db.external_identities.delete(identity_id):
        raise HTTPException(status_code=404, detail="Identity not found")
    return {"success": True, "message": "Identity unlinked"}


# ===================
# SSO Logs
# ===================

@router.get("/logs")
async def get_sso_logs(
    connection_id: Optional[str] = None,
    operation: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(require_roles(["admin"]))
):
    """Get SSO operation logs"""
    filters = {}
    if connection_id:
        filters["connection_id"] = connection_id
    if operation:
        filters["operation"] = operation

    logs = db.scim_logs.find_all(filters)
    return logs[:limit]
