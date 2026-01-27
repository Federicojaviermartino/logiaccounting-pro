"""
Mobile Sync API - Bidirectional data synchronization endpoints
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.utils.auth import get_current_user
from app.models.store import db

router = APIRouter(prefix="/sync", tags=["Mobile Sync"])


class SyncChange(BaseModel):
    id: str
    entity_type: str
    data: dict
    updated_at: str
    deleted: bool = False


class SyncResponse(BaseModel):
    changes: List[SyncChange]
    server_time: str
    has_more: bool = False


class PushChangesRequest(BaseModel):
    entity_type: str
    changes: List[dict]


class PushChangesResponse(BaseModel):
    synced: int
    failed: int
    conflicts: List[dict]
    server_time: str


class ConflictResolutionRequest(BaseModel):
    entity_type: str
    entity_id: str
    resolution: str
    merged_data: Optional[dict] = None


def get_store(entity_type: str):
    """Get the appropriate store for entity type."""
    stores = {
        "invoices": db.payments,
        "inventory": db.materials,
        "customers": db.users,
        "projects": db.projects,
        "transactions": db.transactions,
    }
    return stores.get(entity_type)


@router.get("/{entity_type}", response_model=SyncResponse)
async def get_changes(
    entity_type: str,
    since: Optional[str] = Query(None, description="ISO timestamp for incremental sync"),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    current_user: dict = Depends(get_current_user),
):
    """
    Get changes for a specific entity type since a given timestamp.
    """
    store = get_store(entity_type)
    if not store:
        raise HTTPException(status_code=400, detail=f"Invalid entity type: {entity_type}")

    since_dt = datetime.fromisoformat(since) if since else datetime.min
    all_items = store.find_all()

    changes = []
    for item in all_items:
        item_updated = item.get("updated_at", item.get("created_at", ""))
        try:
            if item_updated and datetime.fromisoformat(item_updated.replace("Z", "")) > since_dt:
                changes.append(SyncChange(
                    id=item["id"],
                    entity_type=entity_type,
                    data=item,
                    updated_at=item_updated,
                    deleted=item.get("deleted", False)
                ))
        except (ValueError, TypeError):
            continue

    changes = sorted(changes, key=lambda x: x.updated_at)
    has_more = len(changes) > offset + limit
    changes = changes[offset:offset + limit]

    return SyncResponse(
        changes=changes,
        server_time=datetime.utcnow().isoformat(),
        has_more=has_more
    )


@router.post("/{entity_type}/push", response_model=PushChangesResponse)
async def push_changes(
    entity_type: str,
    request: PushChangesRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Push local changes from mobile device to server.
    """
    store = get_store(entity_type)
    if not store:
        raise HTTPException(status_code=400, detail=f"Invalid entity type: {entity_type}")

    synced = 0
    failed = 0
    conflicts = []

    for change in request.changes:
        try:
            entity_id = change.get("id")
            operation = change.get("operation", "update")
            data = change.get("data", change)
            client_modified_at = change.get("local_modified_at")

            existing = store.find_by_id(entity_id) if entity_id else None

            if existing:
                server_modified_at = existing.get("updated_at")

                if server_modified_at and client_modified_at:
                    try:
                        server_time = datetime.fromisoformat(server_modified_at.replace("Z", ""))
                        client_time = datetime.fromisoformat(client_modified_at.replace("Z", ""))
                        if server_time > client_time:
                            conflicts.append({
                                "id": entity_id,
                                "entity_type": entity_type,
                                "server_data": existing,
                                "client_data": data,
                                "server_modified_at": server_modified_at,
                                "client_modified_at": client_modified_at,
                            })
                            continue
                    except (ValueError, TypeError):
                        pass

            if operation == "delete":
                if existing:
                    store.delete(entity_id)
                    synced += 1
            elif operation == "create" or not existing:
                store.create(data)
                synced += 1
            else:
                store.update(entity_id, data)
                synced += 1

        except Exception as e:
            failed += 1
            print(f"Sync error for {entity_type}/{change.get('id')}: {str(e)}")

    return PushChangesResponse(
        synced=synced,
        failed=failed,
        conflicts=conflicts,
        server_time=datetime.utcnow().isoformat()
    )


@router.post("/resolve-conflict")
async def resolve_conflict(
    request: ConflictResolutionRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Manually resolve a sync conflict.
    """
    store = get_store(request.entity_type)
    if not store:
        raise HTTPException(status_code=400, detail=f"Invalid entity type: {request.entity_type}")

    entity = store.find_by_id(request.entity_id)

    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    if request.resolution == "use_local" and request.merged_data:
        store.update(request.entity_id, request.merged_data)
    elif request.resolution == "merge" and request.merged_data:
        store.update(request.entity_id, request.merged_data)

    return {"status": "resolved", "entity_id": request.entity_id}


@router.get("/status")
async def get_sync_status(
    current_user: dict = Depends(get_current_user),
):
    """
    Get sync status and statistics.
    """
    return {
        "server_time": datetime.utcnow().isoformat(),
        "counts": {
            "invoices": len(db.payments.find_all()),
            "inventory": len(db.materials.find_all()),
            "projects": len(db.projects.find_all()),
            "transactions": len(db.transactions.find_all()),
        },
        "sync_available": True,
    }
