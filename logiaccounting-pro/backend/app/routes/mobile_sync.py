"""
Mobile Sync API - Bidirectional data synchronization endpoints
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User

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
    resolution: str  # 'use_local' | 'use_server' | 'merge'
    merged_data: Optional[dict] = None


@router.get("/{entity_type}", response_model=SyncResponse)
async def get_changes(
    entity_type: str,
    since: Optional[str] = Query(None, description="ISO timestamp for incremental sync"),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get changes for a specific entity type since a given timestamp.
    Used for pulling server changes to mobile devices.
    """
    valid_entities = ["invoices", "inventory", "customers", "expenses", "projects"]
    if entity_type not in valid_entities:
        raise HTTPException(status_code=400, detail=f"Invalid entity type: {entity_type}")

    since_dt = datetime.fromisoformat(since) if since else datetime.min

    changes = []

    if entity_type == "invoices":
        from app.models.invoice import Invoice

        query = db.query(Invoice).filter(
            Invoice.organization_id == current_user.organization_id,
            Invoice.updated_at > since_dt
        ).order_by(Invoice.updated_at.asc()).offset(offset).limit(limit + 1)

        items = query.all()
        has_more = len(items) > limit
        items = items[:limit]

        for item in items:
            changes.append(SyncChange(
                id=str(item.id),
                entity_type=entity_type,
                data=item.to_dict(),
                updated_at=item.updated_at.isoformat(),
                deleted=item.deleted_at is not None
            ))

    elif entity_type == "inventory":
        from app.models.inventory import InventoryItem

        query = db.query(InventoryItem).filter(
            InventoryItem.organization_id == current_user.organization_id,
            InventoryItem.updated_at > since_dt
        ).order_by(InventoryItem.updated_at.asc()).offset(offset).limit(limit + 1)

        items = query.all()
        has_more = len(items) > limit
        items = items[:limit]

        for item in items:
            changes.append(SyncChange(
                id=str(item.id),
                entity_type=entity_type,
                data=item.to_dict(),
                updated_at=item.updated_at.isoformat(),
                deleted=item.deleted_at is not None
            ))

    elif entity_type == "customers":
        from app.models.customer import Customer

        query = db.query(Customer).filter(
            Customer.organization_id == current_user.organization_id,
            Customer.updated_at > since_dt
        ).order_by(Customer.updated_at.asc()).offset(offset).limit(limit + 1)

        items = query.all()
        has_more = len(items) > limit
        items = items[:limit]

        for item in items:
            changes.append(SyncChange(
                id=str(item.id),
                entity_type=entity_type,
                data=item.to_dict(),
                updated_at=item.updated_at.isoformat(),
                deleted=getattr(item, 'deleted_at', None) is not None
            ))

    elif entity_type == "expenses":
        from app.models.expense import Expense

        query = db.query(Expense).filter(
            Expense.organization_id == current_user.organization_id,
            Expense.updated_at > since_dt
        ).order_by(Expense.updated_at.asc()).offset(offset).limit(limit + 1)

        items = query.all()
        has_more = len(items) > limit
        items = items[:limit]

        for item in items:
            changes.append(SyncChange(
                id=str(item.id),
                entity_type=entity_type,
                data=item.to_dict(),
                updated_at=item.updated_at.isoformat(),
                deleted=getattr(item, 'deleted_at', None) is not None
            ))

    return SyncResponse(
        changes=changes,
        server_time=datetime.utcnow().isoformat(),
        has_more=has_more
    )


@router.post("/{entity_type}/push", response_model=PushChangesResponse)
async def push_changes(
    entity_type: str,
    request: PushChangesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Push local changes from mobile device to server.
    Handles conflict detection and resolution.
    """
    valid_entities = ["invoices", "inventory", "customers", "expenses"]
    if entity_type not in valid_entities:
        raise HTTPException(status_code=400, detail=f"Invalid entity type: {entity_type}")

    synced = 0
    failed = 0
    conflicts = []

    for change in request.changes:
        try:
            entity_id = change.get("id")
            operation = change.get("operation", "update")
            data = change.get("data", {})
            client_modified_at = change.get("local_modified_at")

            existing = await _get_entity(db, entity_type, entity_id, current_user.organization_id)

            if existing:
                server_modified_at = existing.updated_at.isoformat() if existing.updated_at else None

                if server_modified_at and client_modified_at:
                    if datetime.fromisoformat(server_modified_at) > datetime.fromisoformat(client_modified_at):
                        conflicts.append({
                            "id": entity_id,
                            "entity_type": entity_type,
                            "server_data": existing.to_dict(),
                            "client_data": data,
                            "server_modified_at": server_modified_at,
                            "client_modified_at": client_modified_at,
                        })
                        continue

            if operation == "delete":
                if existing:
                    existing.deleted_at = datetime.utcnow()
                    db.commit()
                    synced += 1
            elif operation == "create":
                await _create_entity(db, entity_type, data, current_user.organization_id)
                synced += 1
            else:
                if existing:
                    await _update_entity(db, entity_type, existing, data)
                    synced += 1
                else:
                    await _create_entity(db, entity_type, data, current_user.organization_id)
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Manually resolve a sync conflict.
    """
    entity = await _get_entity(db, request.entity_type, request.entity_id, current_user.organization_id)

    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    if request.resolution == "use_local":
        if request.merged_data:
            await _update_entity(db, request.entity_type, entity, request.merged_data)
    elif request.resolution == "use_server":
        pass
    elif request.resolution == "merge" and request.merged_data:
        await _update_entity(db, request.entity_type, entity, request.merged_data)

    return {"status": "resolved", "entity_id": request.entity_id}


@router.get("/status")
async def get_sync_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get sync status and statistics.
    """
    from app.models.invoice import Invoice
    from app.models.inventory import InventoryItem

    org_id = current_user.organization_id

    invoice_count = db.query(Invoice).filter(Invoice.organization_id == org_id).count()
    inventory_count = db.query(InventoryItem).filter(InventoryItem.organization_id == org_id).count()

    return {
        "server_time": datetime.utcnow().isoformat(),
        "counts": {
            "invoices": invoice_count,
            "inventory": inventory_count,
        },
        "sync_available": True,
    }


async def _get_entity(db: Session, entity_type: str, entity_id: str, organization_id: int):
    """Get entity by type and ID."""
    if entity_type == "invoices":
        from app.models.invoice import Invoice
        return db.query(Invoice).filter(
            Invoice.id == entity_id,
            Invoice.organization_id == organization_id
        ).first()
    elif entity_type == "inventory":
        from app.models.inventory import InventoryItem
        return db.query(InventoryItem).filter(
            InventoryItem.id == entity_id,
            InventoryItem.organization_id == organization_id
        ).first()
    elif entity_type == "customers":
        from app.models.customer import Customer
        return db.query(Customer).filter(
            Customer.id == entity_id,
            Customer.organization_id == organization_id
        ).first()
    elif entity_type == "expenses":
        from app.models.expense import Expense
        return db.query(Expense).filter(
            Expense.id == entity_id,
            Expense.organization_id == organization_id
        ).first()
    return None


async def _create_entity(db: Session, entity_type: str, data: dict, organization_id: int):
    """Create a new entity."""
    data["organization_id"] = organization_id
    data["created_at"] = datetime.utcnow()
    data["updated_at"] = datetime.utcnow()

    if entity_type == "invoices":
        from app.models.invoice import Invoice
        entity = Invoice(**data)
    elif entity_type == "inventory":
        from app.models.inventory import InventoryItem
        entity = InventoryItem(**data)
    elif entity_type == "customers":
        from app.models.customer import Customer
        entity = Customer(**data)
    elif entity_type == "expenses":
        from app.models.expense import Expense
        entity = Expense(**data)
    else:
        return None

    db.add(entity)
    db.commit()
    return entity


async def _update_entity(db: Session, entity_type: str, entity, data: dict):
    """Update an existing entity."""
    for key, value in data.items():
        if hasattr(entity, key) and key not in ["id", "organization_id", "created_at"]:
            setattr(entity, key, value)

    entity.updated_at = datetime.utcnow()
    db.commit()
    return entity
