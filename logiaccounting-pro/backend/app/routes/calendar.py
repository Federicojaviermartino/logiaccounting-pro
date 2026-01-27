"""
Calendar routes
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.calendar_service import calendar_service
from app.utils.auth import get_current_user

router = APIRouter()


class CreateEventRequest(BaseModel):
    title: str
    type: str
    start: str
    end: Optional[str] = None
    all_day: bool = False
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    description: str = ""
    color: Optional[str] = None
    reminder: Optional[str] = None


class UpdateEventRequest(BaseModel):
    title: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    all_day: Optional[bool] = None
    description: Optional[str] = None
    color: Optional[str] = None
    reminder: Optional[str] = None


@router.get("/types")
async def get_event_types():
    """Get available event types"""
    return {"types": calendar_service.EVENT_TYPES}


@router.get("")
async def get_events(
    start: str,
    end: str,
    type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get events in date range"""
    return {"events": calendar_service.get_events(start, end, type)}


@router.get("/upcoming")
async def get_upcoming(
    days: int = 7,
    current_user: dict = Depends(get_current_user)
):
    """Get upcoming events"""
    return {"events": calendar_service.get_upcoming(days)}


@router.post("/generate")
async def generate_events(current_user: dict = Depends(get_current_user)):
    """Generate system events from data"""
    events = calendar_service.generate_system_events()
    return {"generated": len(events), "events": events}


@router.post("")
async def create_event(
    request: CreateEventRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create an event"""
    return calendar_service.create_event(
        **request.model_dump(),
        created_by=current_user["id"]
    )


@router.get("/{event_id}")
async def get_event(
    event_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get an event"""
    event = calendar_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.put("/{event_id}")
async def update_event(
    event_id: str,
    request: UpdateEventRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update an event"""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    event = calendar_service.update_event(event_id, updates)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.delete("/{event_id}")
async def delete_event(
    event_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an event"""
    if calendar_service.delete_event(event_id):
        return {"message": "Event deleted"}
    raise HTTPException(status_code=404, detail="Event not found")
