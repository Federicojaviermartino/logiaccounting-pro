"""
SCIM 2.0 Provisioning API Routes
"""

from fastapi import APIRouter, HTTPException, status, Request, Header, Response
from fastapi.responses import JSONResponse
from typing import Optional
from app.models.store import db
from app.services.sso_service import sso_service, SSOServiceError
from app.auth.sso.scim import (
    SCIMProcessor,
    SCIMException,
    SCIMUser,
    SCIMUserCreate,
    SCIMUserPatch,
    SCIMListResponse,
)

router = APIRouter()


def get_scim_processor(connection_id: str, authorization: str) -> SCIMProcessor:
    """Validate SCIM token and get processor"""
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not sso_service.validate_scim_token(connection_id, authorization):
        raise HTTPException(
            status_code=401,
            detail="Invalid bearer token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        return sso_service.get_scim_processor(connection_id)
    except SSOServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


def scim_response(data: dict, status_code: int = 200) -> JSONResponse:
    """Create SCIM-compliant JSON response"""
    return JSONResponse(
        content=data,
        status_code=status_code,
        media_type="application/scim+json"
    )


def scim_error(status_code: int, detail: str, scim_type: str = None) -> JSONResponse:
    """Create SCIM error response"""
    error = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
        "status": str(status_code),
        "detail": detail,
    }
    if scim_type:
        error["scimType"] = scim_type

    return JSONResponse(
        content=error,
        status_code=status_code,
        media_type="application/scim+json"
    )


# ===================
# SCIM Discovery Endpoints
# ===================

@router.get("/{connection_id}/ServiceProviderConfig")
async def get_service_provider_config(
    connection_id: str,
    authorization: str = Header(None)
):
    """SCIM Service Provider Configuration"""
    processor = get_scim_processor(connection_id, authorization)
    config = processor.get_service_provider_config()
    return scim_response(config.model_dump(by_alias=True))


@router.get("/{connection_id}/ResourceTypes")
async def get_resource_types(
    connection_id: str,
    authorization: str = Header(None)
):
    """SCIM Resource Types"""
    processor = get_scim_processor(connection_id, authorization)
    resource_types = processor.get_resource_types()
    return scim_response({
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": len(resource_types),
        "Resources": [rt.model_dump(by_alias=True) for rt in resource_types]
    })


@router.get("/{connection_id}/ResourceTypes/{resource_type}")
async def get_resource_type(
    connection_id: str,
    resource_type: str,
    authorization: str = Header(None)
):
    """Get specific Resource Type"""
    processor = get_scim_processor(connection_id, authorization)
    resource_types = processor.get_resource_types()

    for rt in resource_types:
        if rt.id == resource_type:
            return scim_response(rt.model_dump(by_alias=True))

    return scim_error(404, f"Resource type '{resource_type}' not found")


@router.get("/{connection_id}/Schemas")
async def get_schemas(
    connection_id: str,
    authorization: str = Header(None)
):
    """SCIM Schemas"""
    processor = get_scim_processor(connection_id, authorization)
    schemas = processor.get_schemas()
    return scim_response({
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": len(schemas),
        "Resources": [s.model_dump(by_alias=True) for s in schemas]
    })


# ===================
# SCIM Users Endpoints
# ===================

@router.get("/{connection_id}/Users")
async def list_users(
    connection_id: str,
    filter: Optional[str] = None,
    startIndex: int = 1,
    count: int = 100,
    authorization: str = Header(None)
):
    """List users (SCIM)"""
    processor = get_scim_processor(connection_id, authorization)

    filters = processor.parse_filter(filter)

    all_users = db.users.find_all()
    filtered_users = all_users

    if filters.get("userName"):
        filtered_users = [u for u in filtered_users if u.get("email") == filters["userName"]]
    if filters.get("email"):
        filtered_users = [u for u in filtered_users if u.get("email") == filters["email"]]
    if filters.get("externalId"):
        identity = db.external_identities.find_by_external_id(connection_id, filters["externalId"])
        if identity:
            filtered_users = [u for u in filtered_users if u["id"] == identity.get("user_id")]
        else:
            filtered_users = []

    total_results = len(filtered_users)
    start_idx = startIndex - 1
    end_idx = start_idx + count
    paginated_users = filtered_users[start_idx:end_idx]

    scim_users = []
    for user in paginated_users:
        identity = db.external_identities.find_by_external_id(connection_id, user["id"])
        scim_user = processor.user_to_scim(user, identity)
        scim_users.append(scim_user.model_dump(exclude_none=True, by_alias=True))

    response = processor.create_list_response(
        resources=scim_users,
        total_results=total_results,
        start_index=startIndex,
        items_per_page=count,
    )

    db.scim_logs.create({
        "connection_id": connection_id,
        "operation": "list_users",
        "status": "success",
        "details": {"total": total_results, "filter": filter},
    })

    return scim_response(response.model_dump(by_alias=True))


@router.post("/{connection_id}/Users")
async def create_user(
    connection_id: str,
    request: Request,
    authorization: str = Header(None)
):
    """Create user (SCIM)"""
    processor = get_scim_processor(connection_id, authorization)

    try:
        body = await request.json()
        scim_user = SCIMUserCreate(**body)
    except Exception as e:
        return scim_error(400, f"Invalid request body: {str(e)}", "invalidSyntax")

    existing = db.users.find_by_email(scim_user.userName)
    if existing:
        return scim_error(409, f"User with userName '{scim_user.userName}' already exists", "uniqueness")

    user_data = processor.scim_to_user_data(scim_user)
    user_data["password"] = ""
    user_data["sso_only"] = True

    connection = db.sso_connections.find_by_id(connection_id)
    if connection:
        user_data["role"] = connection.get("configuration", {}).get("default_role", "client")

    user = db.users.create(user_data)

    if scim_user.externalId:
        db.external_identities.create({
            "user_id": user["id"],
            "connection_id": connection_id,
            "external_user_id": scim_user.externalId,
            "external_email": scim_user.userName,
        })

    db.scim_logs.create({
        "connection_id": connection_id,
        "operation": "create_user",
        "status": "success",
        "details": {"user_id": user["id"], "email": user.get("email")},
    })

    identity = db.external_identities.find_by_external_id(connection_id, scim_user.externalId) if scim_user.externalId else None
    response_user = processor.user_to_scim(user, identity)

    return scim_response(response_user.model_dump(exclude_none=True, by_alias=True), 201)


@router.get("/{connection_id}/Users/{user_id}")
async def get_user(
    connection_id: str,
    user_id: str,
    authorization: str = Header(None)
):
    """Get user (SCIM)"""
    processor = get_scim_processor(connection_id, authorization)

    user = db.users.find_by_id(user_id)
    if not user:
        return scim_error(404, f"User '{user_id}' not found")

    identity = None
    identities = db.external_identities.find_all({"user_id": user_id, "connection_id": connection_id})
    if identities:
        identity = identities[0]

    response_user = processor.user_to_scim(user, identity)
    return scim_response(response_user.model_dump(exclude_none=True, by_alias=True))


@router.put("/{connection_id}/Users/{user_id}")
async def replace_user(
    connection_id: str,
    user_id: str,
    request: Request,
    authorization: str = Header(None)
):
    """Replace user (SCIM PUT)"""
    processor = get_scim_processor(connection_id, authorization)

    user = db.users.find_by_id(user_id)
    if not user:
        return scim_error(404, f"User '{user_id}' not found")

    try:
        body = await request.json()
        scim_user = SCIMUserCreate(**body)
    except Exception as e:
        return scim_error(400, f"Invalid request body: {str(e)}", "invalidSyntax")

    user_data = processor.scim_to_user_data(scim_user)
    updated_user = db.users.update(user_id, user_data)

    if scim_user.externalId:
        identities = db.external_identities.find_all({"user_id": user_id, "connection_id": connection_id})
        if identities:
            db.external_identities.update(identities[0]["id"], {
                "external_user_id": scim_user.externalId,
                "external_email": scim_user.userName,
            })
        else:
            db.external_identities.create({
                "user_id": user_id,
                "connection_id": connection_id,
                "external_user_id": scim_user.externalId,
                "external_email": scim_user.userName,
            })

    db.scim_logs.create({
        "connection_id": connection_id,
        "operation": "replace_user",
        "status": "success",
        "details": {"user_id": user_id},
    })

    identity = db.external_identities.find_by_external_id(connection_id, scim_user.externalId) if scim_user.externalId else None
    response_user = processor.user_to_scim(updated_user, identity)

    return scim_response(response_user.model_dump(exclude_none=True, by_alias=True))


@router.patch("/{connection_id}/Users/{user_id}")
async def patch_user(
    connection_id: str,
    user_id: str,
    request: Request,
    authorization: str = Header(None)
):
    """Patch user (SCIM PATCH)"""
    processor = get_scim_processor(connection_id, authorization)

    user = db.users.find_by_id(user_id)
    if not user:
        return scim_error(404, f"User '{user_id}' not found")

    try:
        body = await request.json()
        patch_request = SCIMUserPatch(**body)
    except Exception as e:
        return scim_error(400, f"Invalid request body: {str(e)}", "invalidSyntax")

    try:
        updated_data = processor.apply_patch_operations(user, patch_request.Operations)
    except SCIMException as e:
        return scim_error(e.status, e.detail, e.scim_type)

    safe_data = {k: v for k, v in updated_data.items() if k not in ["id", "created_at", "password"]}
    updated_user = db.users.update(user_id, safe_data)

    db.scim_logs.create({
        "connection_id": connection_id,
        "operation": "patch_user",
        "status": "success",
        "details": {"user_id": user_id, "operations": len(patch_request.Operations)},
    })

    identities = db.external_identities.find_all({"user_id": user_id, "connection_id": connection_id})
    identity = identities[0] if identities else None

    response_user = processor.user_to_scim(updated_user, identity)
    return scim_response(response_user.model_dump(exclude_none=True, by_alias=True))


@router.delete("/{connection_id}/Users/{user_id}")
async def delete_user(
    connection_id: str,
    user_id: str,
    authorization: str = Header(None)
):
    """Delete user (SCIM)"""
    processor = get_scim_processor(connection_id, authorization)

    user = db.users.find_by_id(user_id)
    if not user:
        return scim_error(404, f"User '{user_id}' not found")

    db.users.update(user_id, {"status": "inactive"})

    identities = db.external_identities.find_all({"user_id": user_id, "connection_id": connection_id})
    for identity in identities:
        db.external_identities.delete(identity["id"])

    db.scim_logs.create({
        "connection_id": connection_id,
        "operation": "delete_user",
        "status": "success",
        "details": {"user_id": user_id, "email": user.get("email")},
    })

    return Response(status_code=204)


# ===================
# SCIM Groups Endpoints (Read-only)
# ===================

@router.get("/{connection_id}/Groups")
async def list_groups(
    connection_id: str,
    filter: Optional[str] = None,
    startIndex: int = 1,
    count: int = 100,
    authorization: str = Header(None)
):
    """List groups (SCIM) - Returns empty as groups managed externally"""
    processor = get_scim_processor(connection_id, authorization)

    response = processor.create_list_response(
        resources=[],
        total_results=0,
        start_index=startIndex,
        items_per_page=count,
    )

    return scim_response(response.model_dump(by_alias=True))


@router.get("/{connection_id}/Groups/{group_id}")
async def get_group(
    connection_id: str,
    group_id: str,
    authorization: str = Header(None)
):
    """Get group (SCIM)"""
    get_scim_processor(connection_id, authorization)
    return scim_error(404, f"Group '{group_id}' not found")
