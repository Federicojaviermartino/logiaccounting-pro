"""
Activity Log routes
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from app.utils.auth import require_roles
from app.utils.activity_logger import activity_logger
import csv
import io

router = APIRouter()


@router.get("")
async def get_activities(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(require_roles("admin"))
):
    """Get activity log with filters (admin only)"""
    activities, total = activity_logger.get_activities(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset
    )

    return {
        "activities": activities,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }


@router.get("/stats")
async def get_activity_stats(
    days: int = Query(default=30, le=365),
    current_user: dict = Depends(require_roles("admin"))
):
    """Get activity statistics (admin only)"""
    return activity_logger.get_stats(days)


@router.get("/actions")
async def get_available_actions(
    current_user: dict = Depends(require_roles("admin"))
):
    """Get list of available action types"""
    return {
        "actions": [
            {"code": "LOGIN", "label": "User Login"},
            {"code": "LOGOUT", "label": "User Logout"},
            {"code": "CREATE", "label": "Create"},
            {"code": "UPDATE", "label": "Update"},
            {"code": "DELETE", "label": "Delete"},
            {"code": "EXPORT", "label": "Export Data"},
            {"code": "IMPORT", "label": "Import Data"},
            {"code": "STATUS_CHANGE", "label": "Status Change"},
            {"code": "AI_OCR", "label": "AI: OCR Process"},
            {"code": "AI_PREDICT", "label": "AI: Prediction"},
            {"code": "AI_ANOMALY", "label": "AI: Anomaly Scan"},
            {"code": "AI_ASSISTANT", "label": "AI: Assistant Query"}
        ],
        "entities": [
            {"code": "user", "label": "Users"},
            {"code": "material", "label": "Materials"},
            {"code": "project", "label": "Projects"},
            {"code": "transaction", "label": "Transactions"},
            {"code": "payment", "label": "Payments"},
            {"code": "movement", "label": "Movements"},
            {"code": "report", "label": "Reports"},
            {"code": "settings", "label": "Settings"}
        ]
    }


@router.get("/export")
async def export_activities(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(require_roles("admin"))
):
    """Export activity log to CSV (admin only)"""
    activities, _ = activity_logger.get_activities(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        date_from=date_from,
        date_to=date_to,
        limit=10000,
        offset=0
    )

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Timestamp", "User Email", "User Role", "Action",
        "Entity Type", "Entity ID", "Entity Name", "Details"
    ])

    # Data
    for a in activities:
        writer.writerow([
            a["timestamp"],
            a["user_email"],
            a["user_role"],
            a["action"],
            a["entity_type"],
            a["entity_id"] or "",
            a["entity_name"] or "",
            str(a["details"])
        ])

    output.seek(0)

    # Log this export
    activity_logger.log(
        user_id=current_user["id"],
        user_email=current_user["email"],
        user_role=current_user["role"],
        action="EXPORT",
        entity_type="activity_log",
        details={"format": "csv", "record_count": len(activities)}
    )

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=activity_log.csv"}
    )
