"""
BI Reports API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from typing import Optional, List
from pydantic import BaseModel

from app.utils.auth import get_current_user
from app.utils.datetime_utils import utc_now
from app.services.bi.scheduler_service import SchedulerService
from app.services.bi.metrics_service import MetricsService
from app.models.bi_store import bi_store

router = APIRouter()

scheduler_service = SchedulerService()
metrics_service = MetricsService()


# ============================================
# PYDANTIC MODELS
# ============================================

class ReportCreate(BaseModel):
    name: str
    description: str = ""
    category_id: Optional[str] = None
    data_source: dict
    query: dict
    layout: dict


class ReportUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    query: Optional[dict] = None
    layout: Optional[dict] = None


class ReportExecute(BaseModel):
    parameters: Optional[dict] = None


class ScheduleCreate(BaseModel):
    name: str
    cron_expression: str
    format: str
    recipients: List[str]
    parameters: Optional[dict] = None
    subject_template: Optional[str] = None
    body_template: Optional[str] = None


class MetricCreate(BaseModel):
    name: str
    code: str
    description: str
    formula: str
    data_type: str
    category: str
    aggregation: Optional[str] = None
    base_table: Optional[str] = None
    base_field: Optional[str] = None
    filters: Optional[List[dict]] = None
    depends_on: Optional[List[str]] = None
    format: Optional[str] = None


# ============================================
# REPORT CRUD ENDPOINTS
# ============================================

@router.get("")
async def list_reports(
    category_id: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """List reports accessible to the user"""
    reports = bi_store.list_reports(
        user_id=current_user["id"],
        category_id=category_id,
        search=search
    )

    # Pagination
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "data": reports[start:end],
        "total": len(reports),
        "page": page,
        "page_size": page_size
    }


@router.post("")
async def create_report(
    data: ReportCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new report"""
    from uuid import uuid4

    report = {
        "id": str(uuid4()),
        "name": data.name,
        "description": data.description,
        "category_id": data.category_id,
        "data_source": data.data_source,
        "query": data.query,
        "layout": data.layout,
        "created_by": current_user["id"],
        "created_at": utc_now().isoformat(),
        "updated_at": utc_now().isoformat(),
        "is_public": False,
        "shared_with": [],
    }

    return bi_store.create_report(report)


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get report definition"""
    report = bi_store.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Track recent access
    bi_store.add_recent(current_user["id"], report_id)

    return report


@router.put("/{report_id}")
async def update_report(
    report_id: str,
    data: ReportUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update report definition"""
    report = bi_store.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    updates = data.dict(exclude_none=True)
    updates["updated_at"] = utc_now().isoformat()

    return bi_store.update_report(report_id, updates)


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a report"""
    report = bi_store.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    bi_store.delete_report(report_id)
    return {"success": True}


# ============================================
# REPORT EXECUTION ENDPOINTS
# ============================================

@router.post("/{report_id}/execute")
async def execute_report(
    report_id: str,
    data: ReportExecute,
    current_user: dict = Depends(get_current_user)
):
    """Execute report and return data"""
    report = bi_store.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Return sample execution result
    return {
        "report_id": report_id,
        "report_name": report["name"],
        "executed_at": utc_now().isoformat(),
        "parameters": data.parameters,
        "data": {
            "components": []
        }
    }


@router.get("/{report_id}/export/{format}")
async def export_report(
    report_id: str,
    format: str,
    current_user: dict = Depends(get_current_user)
):
    """Export report to specified format"""
    if format not in ["pdf", "xlsx", "csv", "html", "json", "pptx"]:
        raise HTTPException(status_code=400, detail="Invalid format")

    report = bi_store.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    content_types = {
        "pdf": "application/pdf",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "csv": "text/csv",
        "html": "text/html",
        "json": "application/json",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }

    # Return empty content for now
    return Response(
        content=b"",
        media_type=content_types[format],
        headers={
            "Content-Disposition": f"attachment; filename=report.{format}"
        }
    )


# ============================================
# FAVORITES & RECENT
# ============================================

@router.post("/{report_id}/favorite")
async def toggle_favorite(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Toggle report as favorite"""
    is_favorite = bi_store.toggle_favorite(current_user["id"], report_id)
    return {"is_favorite": is_favorite}


@router.get("/user/favorites")
async def get_favorites(current_user: dict = Depends(get_current_user)):
    """Get user's favorite reports"""
    return {"data": bi_store.get_favorites(current_user["id"])}


@router.get("/user/recent")
async def get_recent(current_user: dict = Depends(get_current_user)):
    """Get recently accessed reports"""
    return {"data": bi_store.get_recent(current_user["id"])}


# ============================================
# CATEGORIES
# ============================================

@router.get("/categories")
async def get_categories(current_user: dict = Depends(get_current_user)):
    """Get all report categories"""
    return {"data": bi_store.get_categories()}


# ============================================
# SCHEDULING ENDPOINTS
# ============================================

@router.get("/{report_id}/schedules")
async def list_schedules(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """List schedules for a report"""
    return {"data": scheduler_service.list_schedules(report_id=report_id)}


@router.post("/{report_id}/schedules")
async def create_schedule(
    report_id: str,
    data: ScheduleCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new schedule"""
    return scheduler_service.create_schedule(
        report_id=report_id,
        name=data.name,
        cron_expression=data.cron_expression,
        format=data.format,
        recipients=data.recipients,
        parameters=data.parameters,
        user_id=current_user["id"],
        subject_template=data.subject_template,
        body_template=data.body_template
    )


@router.put("/{report_id}/schedules/{schedule_id}")
async def update_schedule(
    report_id: str,
    schedule_id: str,
    data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update a schedule"""
    return scheduler_service.update_schedule(
        schedule_id=schedule_id,
        user_id=current_user["id"],
        **data
    )


@router.delete("/{report_id}/schedules/{schedule_id}")
async def delete_schedule(
    report_id: str,
    schedule_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a schedule"""
    scheduler_service.delete_schedule(schedule_id, current_user["id"])
    return {"success": True}


@router.post("/{report_id}/schedules/{schedule_id}/run")
async def run_schedule_now(
    report_id: str,
    schedule_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Run a schedule immediately"""
    return await scheduler_service.execute_schedule(schedule_id)


# ============================================
# METRICS ENDPOINTS
# ============================================

@router.get("/metrics")
async def list_metrics(
    category: Optional[str] = None,
    certified_only: bool = False,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List available metrics"""
    return {
        "data": metrics_service.list_metrics(
            category=category,
            certified_only=certified_only,
            search=search
        )
    }


@router.post("/metrics")
async def create_metric(
    data: MetricCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a custom metric"""
    return metrics_service.create_metric(
        name=data.name,
        code=data.code,
        description=data.description,
        formula=data.formula,
        data_type=data.data_type,
        category=data.category,
        user_id=current_user["id"],
        aggregation=data.aggregation,
        base_table=data.base_table,
        base_field=data.base_field,
        filters=data.filters,
        depends_on=data.depends_on,
        format=data.format
    )


@router.get("/metrics/{metric_id}")
async def get_metric(
    metric_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get metric details"""
    metric = metrics_service.get_metric(metric_id)
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    return metric


@router.put("/metrics/{metric_id}")
async def update_metric(
    metric_id: str,
    data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update a metric"""
    return metrics_service.update_metric(
        metric_id=metric_id,
        user_id=current_user["id"],
        **data
    )


@router.delete("/metrics/{metric_id}")
async def delete_metric(
    metric_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a metric"""
    metrics_service.delete_metric(metric_id, current_user["id"])
    return {"success": True}


@router.post("/metrics/{metric_id}/calculate")
async def calculate_metric(
    metric_id: str,
    filters: Optional[dict] = None,
    date_range: Optional[dict] = None,
    current_user: dict = Depends(get_current_user)
):
    """Calculate metric value"""
    value = metrics_service.calculate_metric(
        metric_id=metric_id,
        filters=filters,
        date_range=date_range
    )
    return {"metric_id": metric_id, "value": value}


@router.get("/metrics/categories")
async def get_metric_categories(
    current_user: dict = Depends(get_current_user)
):
    """Get all metric categories"""
    return {"data": metrics_service.get_categories()}
