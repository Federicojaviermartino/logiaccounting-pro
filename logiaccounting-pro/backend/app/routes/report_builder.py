"""
Custom Report Builder routes
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.models.store import db
from app.utils.auth import require_roles
from app.utils.activity_logger import activity_logger
import csv
import io
import json

router = APIRouter()


class ReportConfig(BaseModel):
    name: str
    type: str
    columns: List[str]
    filters: Dict[str, Any] = {}
    grouping: Optional[str] = None
    sort_by: Optional[str] = None
    sort_order: str = "desc"


class SavedTemplate(BaseModel):
    name: str
    config: ReportConfig


saved_templates: Dict[str, dict] = {}
template_counter = 0


REPORT_COLUMNS = {
    "financial": {
        "available": ["date", "type", "amount", "description", "category", "vendor_name", "invoice_number", "project_name"],
        "required": ["date", "type", "amount"],
        "grouping": ["day", "week", "month", "category", "type"]
    },
    "inventory": {
        "available": ["reference", "name", "category", "location", "quantity", "min_stock", "unit", "unit_cost", "total_value", "state"],
        "required": ["name", "quantity"],
        "grouping": ["category", "location", "state"]
    },
    "projects": {
        "available": ["name", "client", "description", "budget", "spent", "remaining", "progress", "status", "start_date", "end_date"],
        "required": ["name", "status"],
        "grouping": ["status", "client"]
    },
    "payments": {
        "available": ["reference", "type", "amount", "description", "due_date", "paid_date", "status", "project_name"],
        "required": ["type", "amount", "status"],
        "grouping": ["status", "type", "month"]
    }
}


@router.get("/columns/{report_type}")
async def get_available_columns(
    report_type: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get available columns for a report type"""
    if report_type not in REPORT_COLUMNS:
        raise HTTPException(status_code=400, detail=f"Invalid report type: {report_type}")

    return REPORT_COLUMNS[report_type]


@router.post("/preview")
async def preview_report(
    config: ReportConfig,
    limit: int = Query(default=20, le=100),
    current_user: dict = Depends(require_roles("admin"))
):
    """Preview report data"""
    data = generate_report_data(config, limit)
    return {
        "columns": config.columns,
        "data": data,
        "total_rows": len(data),
        "preview": True
    }


@router.post("/generate")
async def generate_report(
    config: ReportConfig,
    format: str = Query(default="json"),
    current_user: dict = Depends(require_roles("admin"))
):
    """Generate full report"""
    data = generate_report_data(config, limit=10000)

    activity_logger.log(
        user_id=current_user["id"],
        user_email=current_user["email"],
        user_role=current_user["role"],
        action="EXPORT",
        entity_type="report",
        details={"report_type": config.type, "format": format, "rows": len(data)}
    )

    if format == "csv":
        return generate_csv_response(config.columns, data, f"{config.type}_report.csv")

    return {
        "columns": config.columns,
        "data": data,
        "total_rows": len(data),
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/templates")
async def get_templates(current_user: dict = Depends(require_roles("admin"))):
    """Get saved report templates"""
    user_templates = [
        {"id": k, **v}
        for k, v in saved_templates.items()
        if v.get("user_id") == current_user["id"]
    ]
    return {"templates": user_templates}


@router.post("/templates")
async def save_template(
    template: SavedTemplate,
    current_user: dict = Depends(require_roles("admin"))
):
    """Save a report template"""
    global template_counter
    template_counter += 1
    template_id = f"TPL-{template_counter:04d}"

    saved_templates[template_id] = {
        "name": template.name,
        "config": template.config.model_dump(),
        "user_id": current_user["id"],
        "created_at": datetime.utcnow().isoformat()
    }

    return {"id": template_id, "message": "Template saved"}


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Delete a report template"""
    if template_id not in saved_templates:
        raise HTTPException(status_code=404, detail="Template not found")

    if saved_templates[template_id]["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    del saved_templates[template_id]
    return {"message": "Template deleted"}


def generate_report_data(config: ReportConfig, limit: int = 1000) -> List[dict]:
    """Generate report data based on configuration"""

    if config.type == "financial":
        raw_data = db.transactions.find_all()
    elif config.type == "inventory":
        raw_data = db.materials.find_all()
    elif config.type == "projects":
        raw_data = db.projects.find_all()
    elif config.type == "payments":
        raw_data = db.payments.find_all()
    else:
        return []

    filtered_data = apply_filters(raw_data, config.filters, config.type)

    selected_data = []
    for item in filtered_data:
        row = {}
        for col in config.columns:
            row[col] = get_column_value(item, col, config.type)
        selected_data.append(row)

    if config.sort_by and config.sort_by in config.columns:
        reverse = config.sort_order == "desc"
        selected_data.sort(key=lambda x: x.get(config.sort_by, ""), reverse=reverse)

    return selected_data[:limit]


def apply_filters(data: List[dict], filters: dict, report_type: str) -> List[dict]:
    """Apply filters to data"""
    filtered = data

    for key, value in filters.items():
        if value is None or value == "":
            continue

        if key == "date_from":
            filtered = [d for d in filtered if d.get("date", d.get("created_at", "")) >= value]
        elif key == "date_to":
            filtered = [d for d in filtered if d.get("date", d.get("created_at", "")) <= value]
        elif key == "type":
            filtered = [d for d in filtered if d.get("type") == value]
        elif key == "status":
            filtered = [d for d in filtered if d.get("status") == value]
        elif key == "min_amount":
            filtered = [d for d in filtered if d.get("amount", 0) >= float(value)]
        elif key == "max_amount":
            filtered = [d for d in filtered if d.get("amount", 0) <= float(value)]

    return filtered


def get_column_value(item: dict, column: str, report_type: str) -> Any:
    """Get column value with transformations"""

    if column in item:
        return item[column]

    if column == "total_value":
        return (item.get("quantity", 0) or 0) * (item.get("unit_cost", 0) or 0)

    if column == "remaining":
        return (item.get("budget", 0) or 0) - (item.get("spent", 0) or 0)

    if column == "progress":
        budget = item.get("budget", 0) or 1
        spent = item.get("spent", 0) or 0
        return round((spent / budget) * 100, 1)

    if column == "project_name":
        project_id = item.get("project_id")
        if project_id:
            project = db.projects.find_by_id(project_id)
            return project.get("name", "N/A") if project else "N/A"
        return "N/A"

    if column == "category":
        category_id = item.get("category_id")
        if category_id:
            category = db.categories.find_by_id(category_id)
            return category.get("name", "N/A") if category else "N/A"
        return "N/A"

    return item.get(column, "")


def generate_csv_response(columns: List[str], data: List[dict], filename: str):
    """Generate CSV file response"""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    writer.writerows(data)
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
