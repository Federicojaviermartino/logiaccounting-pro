"""
Audit Trail routes
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from app.services.audit_service import audit_service
from app.utils.auth import require_roles

router = APIRouter()


@router.get("/actions")
async def get_action_types():
    """Get available action types"""
    return {"actions": audit_service.ACTION_TYPES}


@router.get("/entities")
async def get_entity_types():
    """Get available entity types"""
    return {"entities": audit_service.ENTITY_TYPES}


@router.get("")
async def search_logs(
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    ip_address: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    current_user: dict = Depends(require_roles("admin"))
):
    """Search audit logs"""
    return audit_service.search(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        user_email=user_email,
        ip_address=ip_address,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset
    )


@router.get("/statistics")
async def get_statistics(
    days: int = 30,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get audit statistics"""
    return audit_service.get_statistics(days)


@router.get("/anomalies")
async def get_anomalies(
    current_user: dict = Depends(require_roles("admin"))
):
    """Detect security anomalies"""
    return {"anomalies": audit_service.detect_anomalies()}


@router.get("/entity/{entity_type}/{entity_id}")
async def get_entity_history(
    entity_type: str,
    entity_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get complete history for an entity"""
    return {"history": audit_service.get_entity_history(entity_type, entity_id)}


@router.get("/user/{user_id}")
async def get_user_activity(
    user_id: str,
    days: int = 30,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get user activity"""
    return {"activity": audit_service.get_user_activity(user_id, days)}


@router.get("/export")
async def export_logs(
    format: str = "json",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(require_roles("admin"))
):
    """Export audit logs"""
    data = audit_service.export(format, date_from, date_to)

    if format == "csv":
        return {
            "content": data,
            "filename": f"audit_logs_{date_from or 'all'}_{date_to or 'now'}.csv",
            "content_type": "text/csv"
        }

    return {"data": data if isinstance(data, list) else None, "content": data if isinstance(data, str) else None}


@router.get("/{log_id}")
async def get_log(
    log_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get a specific log entry"""
    log = audit_service.get_log(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return log
