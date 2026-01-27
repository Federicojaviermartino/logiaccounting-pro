"""
Scheduled Reports routes
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.report_scheduler import report_scheduler
from app.utils.auth import require_roles

router = APIRouter()


class CreateScheduleRequest(BaseModel):
    name: str
    report_type: str
    report_config: dict
    frequency: str
    time_of_day: str
    day_of_week: Optional[int] = None
    day_of_month: Optional[int] = None
    recipients: List[str] = []
    format: str = "pdf"


class UpdateScheduleRequest(BaseModel):
    name: Optional[str] = None
    report_config: Optional[dict] = None
    frequency: Optional[str] = None
    time_of_day: Optional[str] = None
    day_of_week: Optional[int] = None
    day_of_month: Optional[int] = None
    recipients: Optional[List[str]] = None
    format: Optional[str] = None


@router.get("/frequencies")
async def get_frequencies():
    """Get available frequencies"""
    return {
        "frequencies": [
            {"value": "daily", "label": "Daily"},
            {"value": "weekly", "label": "Weekly"},
            {"value": "biweekly", "label": "Bi-weekly"},
            {"value": "monthly", "label": "Monthly"},
            {"value": "quarterly", "label": "Quarterly"}
        ]
    }


@router.get("")
async def list_schedules(
    active_only: bool = False,
    current_user: dict = Depends(require_roles("admin"))
):
    """List all schedules"""
    return {"schedules": report_scheduler.list_schedules(active_only)}


@router.post("")
async def create_schedule(
    request: CreateScheduleRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Create a new schedule"""
    return report_scheduler.create_schedule(
        name=request.name,
        report_type=request.report_type,
        report_config=request.report_config,
        frequency=request.frequency,
        time_of_day=request.time_of_day,
        day_of_week=request.day_of_week,
        day_of_month=request.day_of_month,
        recipients=request.recipients,
        format=request.format,
        created_by=current_user["id"]
    )


@router.get("/{schedule_id}")
async def get_schedule(
    schedule_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get a specific schedule"""
    schedule = report_scheduler.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


@router.put("/{schedule_id}")
async def update_schedule(
    schedule_id: str,
    request: UpdateScheduleRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update a schedule"""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    schedule = report_scheduler.update_schedule(schedule_id, updates)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Delete a schedule"""
    if report_scheduler.delete_schedule(schedule_id):
        return {"message": "Schedule deleted"}
    raise HTTPException(status_code=404, detail="Schedule not found")


@router.post("/{schedule_id}/toggle")
async def toggle_schedule(
    schedule_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Toggle schedule active status"""
    schedule = report_scheduler.toggle_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


@router.post("/{schedule_id}/run")
async def run_now(
    schedule_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Manually run a schedule"""
    result = report_scheduler.run_schedule(schedule_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/{schedule_id}/history")
async def get_history(
    schedule_id: str,
    limit: int = 20,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get run history for a schedule"""
    return {"history": report_scheduler.get_history(schedule_id, limit)}
