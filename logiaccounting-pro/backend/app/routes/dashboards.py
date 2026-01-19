"""
Dashboard Builder routes
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.dashboard_service import dashboard_service
from app.utils.auth import get_current_user

router = APIRouter()


class CreateDashboardRequest(BaseModel):
    name: str
    layout: Optional[List[dict]] = None
    is_default: bool = False
    from_template: Optional[str] = None


class UpdateLayoutRequest(BaseModel):
    layout: List[dict]


class AddWidgetRequest(BaseModel):
    type: str
    x: int
    y: int
    w: int
    h: int
    config: dict = {}


class UpdateWidgetRequest(BaseModel):
    x: Optional[int] = None
    y: Optional[int] = None
    w: Optional[int] = None
    h: Optional[int] = None
    config: Optional[dict] = None


@router.get("/widget-types")
async def get_widget_types():
    """Get available widget types"""
    return {"types": dashboard_service.get_widget_types()}


@router.get("/templates")
async def get_templates():
    """Get preset templates"""
    return {"templates": dashboard_service.get_templates()}


@router.get("")
async def list_dashboards(current_user: dict = Depends(get_current_user)):
    """List user's dashboards"""
    return {"dashboards": dashboard_service.list_dashboards(current_user["id"])}


@router.post("")
async def create_dashboard(
    request: CreateDashboardRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new dashboard"""
    return dashboard_service.create_dashboard(
        name=request.name,
        user_id=current_user["id"],
        layout=request.layout,
        is_default=request.is_default,
        from_template=request.from_template
    )


@router.get("/shared/{token}")
async def get_shared_dashboard(token: str):
    """Get shared dashboard by token"""
    dashboard = dashboard_service.get_by_share_token(token)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.get("/{dashboard_id}")
async def get_dashboard(
    dashboard_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific dashboard"""
    dashboard = dashboard_service.get_dashboard(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.put("/{dashboard_id}/layout")
async def update_layout(
    dashboard_id: str,
    request: UpdateLayoutRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update dashboard layout"""
    dashboard = dashboard_service.update_layout(dashboard_id, request.layout)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.post("/{dashboard_id}/widgets")
async def add_widget(
    dashboard_id: str,
    request: AddWidgetRequest,
    current_user: dict = Depends(get_current_user)
):
    """Add widget to dashboard"""
    dashboard = dashboard_service.add_widget(dashboard_id, request.model_dump())
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.put("/{dashboard_id}/widgets/{widget_id}")
async def update_widget(
    dashboard_id: str,
    widget_id: str,
    request: UpdateWidgetRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update a widget"""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    dashboard = dashboard_service.update_widget(dashboard_id, widget_id, updates)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.delete("/{dashboard_id}/widgets/{widget_id}")
async def remove_widget(
    dashboard_id: str,
    widget_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove widget from dashboard"""
    dashboard = dashboard_service.remove_widget(dashboard_id, widget_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.post("/{dashboard_id}/share")
async def share_dashboard(
    dashboard_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Generate share link"""
    token = dashboard_service.share_dashboard(dashboard_id)
    if not token:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return {"share_token": token, "share_url": f"/dashboard/shared/{token}"}


@router.delete("/{dashboard_id}/share")
async def unshare_dashboard(
    dashboard_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove sharing"""
    if dashboard_service.unshare_dashboard(dashboard_id):
        return {"message": "Sharing disabled"}
    raise HTTPException(status_code=404, detail="Dashboard not found")


@router.delete("/{dashboard_id}")
async def delete_dashboard(
    dashboard_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete dashboard"""
    if dashboard_service.delete_dashboard(dashboard_id):
        return {"message": "Dashboard deleted"}
    raise HTTPException(status_code=404, detail="Dashboard not found")


@router.get("/{dashboard_id}/widgets/{widget_id}/data")
async def get_widget_data(
    dashboard_id: str,
    widget_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get data for a widget"""
    dashboard = dashboard_service.get_dashboard(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    widget = next((w for w in dashboard["layout"] if w["widget_id"] == widget_id), None)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    return dashboard_service.get_widget_data(widget["type"], widget.get("config", {}))
