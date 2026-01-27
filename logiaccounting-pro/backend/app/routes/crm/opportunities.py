"""
CRM Opportunities API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel

from app.utils.auth import get_current_user
from app.services.crm.opportunity_service import opportunity_service
from app.services.crm.pipeline_service import pipeline_service


router = APIRouter()


# ============================================
# PYDANTIC MODELS
# ============================================

class OpportunityCreate(BaseModel):
    name: str
    pipeline_id: Optional[str] = None
    stage_id: Optional[str] = None
    amount: Optional[float] = 0
    currency: Optional[str] = "USD"
    probability: Optional[int] = None
    expected_close_date: Optional[str] = None
    contact_id: Optional[str] = None
    company_id: Optional[str] = None
    description: Optional[str] = None


class OpportunityUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = None
    probability: Optional[int] = None
    expected_close_date: Optional[str] = None
    contact_id: Optional[str] = None
    company_id: Optional[str] = None
    description: Optional[str] = None


class MoveStage(BaseModel):
    stage_id: str


class WinOpportunity(BaseModel):
    actual_amount: Optional[float] = None
    notes: Optional[str] = None


class LoseOpportunity(BaseModel):
    lost_reason: Optional[str] = None
    competitor: Optional[str] = None
    notes: Optional[str] = None


class StageCreate(BaseModel):
    name: str
    probability: Optional[int] = 0
    position: Optional[int] = None
    color: Optional[str] = None
    is_won: Optional[bool] = False
    is_lost: Optional[bool] = False


class StageUpdate(BaseModel):
    name: Optional[str] = None
    probability: Optional[int] = None
    color: Optional[str] = None


class PipelineCreate(BaseModel):
    name: str
    stages: Optional[List[StageCreate]] = None


class StageOrder(BaseModel):
    stage_ids: List[str]


# ============================================
# OPPORTUNITY ENDPOINTS
# ============================================

@router.get("")
async def list_opportunities(
    pipeline_id: Optional[str] = None,
    stage_id: Optional[str] = None,
    status: Optional[str] = None,
    owner_id: Optional[str] = None,
    company_id: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """List opportunities with filters"""
    return opportunity_service.list_opportunities(
        tenant_id=current_user.get("tenant_id"),
        pipeline_id=pipeline_id,
        stage_id=stage_id,
        status=status,
        owner_id=owner_id,
        company_id=company_id,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.post("")
async def create_opportunity(
    data: OpportunityCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new opportunity"""
    return opportunity_service.create_opportunity(
        tenant_id=current_user.get("tenant_id"),
        owner_id=current_user["id"],
        **data.dict(exclude_none=True),
    )


@router.get("/board")
async def get_pipeline_board(
    pipeline_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Get Kanban board data for pipeline"""
    return opportunity_service.get_pipeline_board(
        tenant_id=current_user.get("tenant_id"),
        pipeline_id=pipeline_id,
    )


@router.get("/forecast")
async def get_forecast(
    pipeline_id: Optional[str] = None,
    days: int = Query(90, ge=30, le=365),
    current_user: dict = Depends(get_current_user),
):
    """Get sales forecast"""
    return opportunity_service.get_forecast(
        tenant_id=current_user.get("tenant_id"),
        pipeline_id=pipeline_id,
        days=days,
    )


@router.get("/win-loss")
async def get_win_loss_analysis(
    days: int = Query(90, ge=30, le=365),
    current_user: dict = Depends(get_current_user),
):
    """Analyze win/loss rates"""
    return opportunity_service.get_win_loss_analysis(
        tenant_id=current_user.get("tenant_id"),
        days=days,
    )


@router.get("/{opp_id}")
async def get_opportunity(
    opp_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get opportunity by ID"""
    opp = opportunity_service.get_opportunity(opp_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opp


@router.put("/{opp_id}")
async def update_opportunity(
    opp_id: str,
    data: OpportunityUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update opportunity"""
    opp = opportunity_service.update_opportunity(
        opp_id=opp_id,
        user_id=current_user["id"],
        **data.dict(exclude_none=True),
    )
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opp


@router.delete("/{opp_id}")
async def delete_opportunity(
    opp_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete opportunity"""
    if not opportunity_service.delete_opportunity(opp_id, current_user["id"]):
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return {"success": True}


@router.post("/{opp_id}/move")
async def move_stage(
    opp_id: str,
    data: MoveStage,
    current_user: dict = Depends(get_current_user),
):
    """Move opportunity to a new stage"""
    return opportunity_service.move_stage(
        opp_id=opp_id,
        stage_id=data.stage_id,
        user_id=current_user["id"],
    )


@router.post("/{opp_id}/win")
async def win_opportunity(
    opp_id: str,
    data: WinOpportunity,
    current_user: dict = Depends(get_current_user),
):
    """Mark opportunity as won"""
    return opportunity_service.win_opportunity(
        opp_id=opp_id,
        user_id=current_user["id"],
        **data.dict(exclude_none=True),
    )


@router.post("/{opp_id}/lose")
async def lose_opportunity(
    opp_id: str,
    data: LoseOpportunity,
    current_user: dict = Depends(get_current_user),
):
    """Mark opportunity as lost"""
    return opportunity_service.lose_opportunity(
        opp_id=opp_id,
        user_id=current_user["id"],
        **data.dict(exclude_none=True),
    )


@router.post("/{opp_id}/reopen")
async def reopen_opportunity(
    opp_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Reopen a closed opportunity"""
    return opportunity_service.reopen_opportunity(
        opp_id=opp_id,
        user_id=current_user["id"],
    )


# ============================================
# PIPELINE ENDPOINTS
# ============================================

@router.get("/pipelines")
async def list_pipelines(
    current_user: dict = Depends(get_current_user),
):
    """List all pipelines"""
    return pipeline_service.list_pipelines(
        tenant_id=current_user.get("tenant_id"),
    )


@router.post("/pipelines")
async def create_pipeline(
    data: PipelineCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new pipeline"""
    stages = [s.dict() for s in data.stages] if data.stages else None
    return pipeline_service.create_pipeline(
        tenant_id=current_user.get("tenant_id"),
        name=data.name,
        stages=stages,
    )


@router.get("/pipelines/{pipeline_id}")
async def get_pipeline(
    pipeline_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get pipeline with stages"""
    pipeline = pipeline_service.get_pipeline(pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline


@router.get("/pipelines/{pipeline_id}/stats")
async def get_pipeline_stats(
    pipeline_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get pipeline statistics"""
    return pipeline_service.get_pipeline_stats(
        pipeline_id=pipeline_id,
        tenant_id=current_user.get("tenant_id"),
    )


@router.delete("/pipelines/{pipeline_id}")
async def delete_pipeline(
    pipeline_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a pipeline"""
    pipeline_service.delete_pipeline(pipeline_id)
    return {"success": True}


@router.post("/pipelines/{pipeline_id}/stages")
async def add_stage(
    pipeline_id: str,
    data: StageCreate,
    current_user: dict = Depends(get_current_user),
):
    """Add a stage to pipeline"""
    return pipeline_service.add_stage(
        pipeline_id=pipeline_id,
        **data.dict(exclude_none=True),
    )


@router.put("/pipelines/{pipeline_id}/stages/{stage_id}")
async def update_stage(
    pipeline_id: str,
    stage_id: str,
    data: StageUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update stage settings"""
    return pipeline_service.update_stage(
        stage_id=stage_id,
        **data.dict(exclude_none=True),
    )


@router.delete("/pipelines/{pipeline_id}/stages/{stage_id}")
async def delete_stage(
    pipeline_id: str,
    stage_id: str,
    move_to_stage_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Delete a stage"""
    pipeline_service.delete_stage(stage_id, move_to_stage_id)
    return {"success": True}


@router.post("/pipelines/{pipeline_id}/stages/reorder")
async def reorder_stages(
    pipeline_id: str,
    data: StageOrder,
    current_user: dict = Depends(get_current_user),
):
    """Reorder stages in pipeline"""
    pipeline_service.reorder_stages(pipeline_id, data.stage_ids)
    return {"success": True}
