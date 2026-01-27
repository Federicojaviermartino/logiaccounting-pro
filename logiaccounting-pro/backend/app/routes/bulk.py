"""
Bulk operations routes - Import, Export, Mass Update, Mass Delete
"""

import csv
import io
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.models.store import db
from app.utils.auth import require_roles
from app.utils.activity_logger import activity_logger

router = APIRouter()


class BulkDeleteRequest(BaseModel):
    ids: List[str]


class BulkUpdateRequest(BaseModel):
    ids: List[str]
    updates: dict


# Supported entities and their configurations
ENTITY_CONFIG = {
    "materials": {
        "store": lambda: db.materials,
        "fields": ["reference", "name", "description", "category_id", "unit", "quantity", "min_stock", "unit_cost", "state"],
        "required": ["name", "quantity"],
        "searchable": ["name", "reference"]
    },
    "transactions": {
        "store": lambda: db.transactions,
        "fields": ["type", "amount", "description", "category_id", "date", "vendor_name", "invoice_number"],
        "required": ["type", "amount"],
        "searchable": ["description", "vendor_name"]
    },
    "payments": {
        "store": lambda: db.payments,
        "fields": ["type", "amount", "due_date", "description", "reference", "status"],
        "required": ["type", "amount", "due_date"],
        "searchable": ["description", "reference"]
    },
    "projects": {
        "store": lambda: db.projects,
        "fields": ["name", "client", "description", "budget", "status", "start_date", "end_date"],
        "required": ["name"],
        "searchable": ["name", "client"]
    }
}


@router.get("/template/{entity}")
async def get_import_template(
    entity: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Download CSV template for import"""
    if entity not in ENTITY_CONFIG:
        raise HTTPException(status_code=400, detail=f"Unsupported entity: {entity}")

    config = ENTITY_CONFIG[entity]
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(config["fields"])

    # Write example row
    example_row = []
    for field in config["fields"]:
        if field == "type":
            example_row.append("expense")
        elif field == "amount" or field == "budget" or field == "unit_cost":
            example_row.append("1000.00")
        elif field == "quantity" or field == "min_stock":
            example_row.append("100")
        elif "date" in field:
            example_row.append("2024-01-15")
        elif field == "status":
            example_row.append("active")
        elif field == "state":
            example_row.append("available")
        else:
            example_row.append(f"Example {field}")
    writer.writerow(example_row)

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={entity}_template.csv"}
    )


@router.post("/import/{entity}")
async def import_data(
    entity: str,
    file: UploadFile = File(...),
    skip_errors: bool = Query(default=False),
    current_user: dict = Depends(require_roles("admin"))
):
    """Import data from CSV file"""
    if entity not in ENTITY_CONFIG:
        raise HTTPException(status_code=400, detail=f"Unsupported entity: {entity}")

    config = ENTITY_CONFIG[entity]
    store = config["store"]()

    # Read file
    content = await file.read()
    try:
        text = content.decode('utf-8')
    except UnicodeDecodeError:
        text = content.decode('latin-1')

    reader = csv.DictReader(io.StringIO(text))

    results = {
        "total_rows": 0,
        "imported": 0,
        "skipped": 0,
        "errors": [],
        "imported_ids": []
    }

    for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
        results["total_rows"] += 1

        try:
            # Validate required fields
            for field in config["required"]:
                if not row.get(field):
                    raise ValueError(f"Missing required field: {field}")

            # Clean and convert data
            clean_row = {}
            for field in config["fields"]:
                value = row.get(field, "").strip()
                if value:
                    # Convert numeric fields
                    if field in ["amount", "budget", "unit_cost", "quantity", "min_stock"]:
                        try:
                            value = float(value)
                        except ValueError:
                            raise ValueError(f"Invalid number in field: {field}")
                    clean_row[field] = value

            # Create record
            clean_row["created_by"] = current_user["id"]
            record = store.create(clean_row)
            results["imported"] += 1
            results["imported_ids"].append(record["id"])

        except Exception as e:
            if skip_errors:
                results["skipped"] += 1
                results["errors"].append({
                    "row": row_num,
                    "error": str(e),
                    "data": dict(row)
                })
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Error at row {row_num}: {str(e)}"
                )

    # Log activity
    activity_logger.log(
        user_id=current_user["id"],
        user_email=current_user["email"],
        user_role=current_user["role"],
        action="IMPORT",
        entity_type=entity,
        details={
            "total_rows": results["total_rows"],
            "imported": results["imported"],
            "skipped": results["skipped"]
        }
    )

    return results


@router.post("/export/{entity}")
async def export_data(
    entity: str,
    ids: Optional[List[str]] = None,
    format: str = Query(default="csv"),
    current_user: dict = Depends(require_roles("admin"))
):
    """Export data to CSV or JSON"""
    if entity not in ENTITY_CONFIG:
        raise HTTPException(status_code=400, detail=f"Unsupported entity: {entity}")

    config = ENTITY_CONFIG[entity]
    store = config["store"]()

    # Get data
    if ids:
        data = [store.find_by_id(id) for id in ids if store.find_by_id(id)]
    else:
        data = store.find_all()

    # Log activity
    activity_logger.log(
        user_id=current_user["id"],
        user_email=current_user["email"],
        user_role=current_user["role"],
        action="EXPORT",
        entity_type=entity,
        details={"format": format, "record_count": len(data)}
    )

    if format == "json":
        return StreamingResponse(
            iter([json.dumps(data, indent=2)]),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={entity}_export.json"}
        )

    # CSV format
    output = io.StringIO()
    if data:
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={entity}_export.csv"}
    )


@router.post("/delete/{entity}")
async def bulk_delete(
    entity: str,
    request: BulkDeleteRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Bulk delete records"""
    if entity not in ENTITY_CONFIG:
        raise HTTPException(status_code=400, detail=f"Unsupported entity: {entity}")

    if entity in ["payments", "projects"]:
        raise HTTPException(status_code=403, detail=f"Bulk delete not allowed for {entity}")

    store = ENTITY_CONFIG[entity]["store"]()

    deleted = 0
    failed = []

    for id in request.ids:
        if store.delete(id):
            deleted += 1
        else:
            failed.append(id)

    # Log activity
    activity_logger.log(
        user_id=current_user["id"],
        user_email=current_user["email"],
        user_role=current_user["role"],
        action="DELETE",
        entity_type=entity,
        details={"deleted_count": deleted, "failed_count": len(failed)}
    )

    return {
        "deleted": deleted,
        "failed": len(failed),
        "failed_ids": failed
    }


@router.post("/update/{entity}")
async def bulk_update(
    entity: str,
    request: BulkUpdateRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Bulk update records"""
    if entity not in ENTITY_CONFIG:
        raise HTTPException(status_code=400, detail=f"Unsupported entity: {entity}")

    store = ENTITY_CONFIG[entity]["store"]()

    updated = 0
    failed = []

    for id in request.ids:
        if store.update(id, request.updates):
            updated += 1
        else:
            failed.append(id)

    # Log activity
    activity_logger.log(
        user_id=current_user["id"],
        user_email=current_user["email"],
        user_role=current_user["role"],
        action="UPDATE",
        entity_type=entity,
        details={
            "updated_count": updated,
            "failed_count": len(failed),
            "fields_updated": list(request.updates.keys())
        }
    )

    return {
        "updated": updated,
        "failed": len(failed),
        "failed_ids": failed
    }
