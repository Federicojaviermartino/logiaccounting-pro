"""
Backup and Restore routes
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.backup_service import backup_service
from app.utils.auth import require_roles
import io

router = APIRouter()


class CreateBackupRequest(BaseModel):
    entities: Optional[List[str]] = None
    include_users: bool = False


class RestoreRequest(BaseModel):
    backup_data: str
    entities: Optional[List[str]] = None
    mode: str = "merge"


@router.post("/create")
async def create_backup(
    request: CreateBackupRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Create a new backup"""
    return backup_service.create_backup(
        user_id=current_user["id"],
        user_email=current_user["email"],
        entities=request.entities,
        include_users=request.include_users
    )


@router.get("/list")
async def list_backups(current_user: dict = Depends(require_roles("admin"))):
    """List all backups"""
    return {"backups": backup_service.list_backups()}


@router.get("/download/{backup_id}")
async def download_backup(
    backup_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Download a backup file"""
    data = backup_service.get_backup_data(backup_id)
    if not data:
        raise HTTPException(status_code=404, detail="Backup not found")

    return StreamingResponse(
        io.BytesIO(data.encode()),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={backup_id}.backup"}
    )


@router.delete("/{backup_id}")
async def delete_backup(
    backup_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Delete a backup"""
    if backup_service.delete_backup(backup_id):
        return {"message": "Backup deleted"}
    raise HTTPException(status_code=404, detail="Backup not found")


@router.post("/restore")
async def restore_backup(
    request: RestoreRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Restore data from a backup"""
    result = backup_service.restore_backup(
        backup_data=request.backup_data,
        user_id=current_user["id"],
        user_email=current_user["email"],
        entities=request.entities,
        mode=request.mode
    )

    if "error" in result and result["error"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/restore/upload")
async def restore_from_file(
    file: UploadFile = File(...),
    mode: str = "merge",
    current_user: dict = Depends(require_roles("admin"))
):
    """Restore from uploaded backup file"""
    content = await file.read()
    backup_data = content.decode()

    result = backup_service.restore_backup(
        backup_data=backup_data,
        user_id=current_user["id"],
        user_email=current_user["email"],
        mode=mode
    )

    if "error" in result and result["error"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result
