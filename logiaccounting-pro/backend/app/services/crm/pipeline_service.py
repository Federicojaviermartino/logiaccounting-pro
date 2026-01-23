"""
Pipeline Configuration Service
Manages sales pipelines and stages
"""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from app.models.crm_store import crm_store


class PipelineService:
    """
    Service for managing sales pipelines
    """

    def create_pipeline(
        self,
        tenant_id: str,
        name: str,
        is_default: bool = False,
        stages: List[dict] = None,
    ) -> dict:
        """Create a new pipeline with stages"""
        pipeline = crm_store.create_pipeline({
            "tenant_id": tenant_id,
            "name": name,
            "is_default": is_default,
        })

        # Create stages
        if stages:
            for i, stage_data in enumerate(stages):
                crm_store.create_stage({
                    "pipeline_id": pipeline["id"],
                    "name": stage_data.get("name"),
                    "probability": stage_data.get("probability", 0),
                    "position": i + 1,
                    "color": stage_data.get("color"),
                    "is_won": stage_data.get("is_won", False),
                    "is_lost": stage_data.get("is_lost", False),
                })

        return self.get_pipeline(pipeline["id"])

    def get_pipeline(self, pipeline_id: str) -> dict:
        """Get pipeline with stages"""
        return crm_store.get_pipeline(pipeline_id)

    def list_pipelines(self, tenant_id: str = None) -> List[dict]:
        """List all pipelines"""
        pipelines = crm_store.list_pipelines(tenant_id)

        # Add stage count to each pipeline
        for pipeline in pipelines:
            full_pipeline = crm_store.get_pipeline(pipeline["id"])
            pipeline["stages_count"] = len(full_pipeline.get("stages", []))

        return pipelines

    def update_pipeline(self, pipeline_id: str, **updates) -> dict:
        """Update pipeline settings"""
        pipeline = crm_store._pipelines.get(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline not found: {pipeline_id}")

        pipeline.update(updates)
        return self.get_pipeline(pipeline_id)

    def delete_pipeline(self, pipeline_id: str):
        """Delete a pipeline (if no opportunities)"""
        opps, _ = crm_store.list_opportunities(pipeline_id=pipeline_id, limit=1)
        if opps:
            raise ValueError("Cannot delete pipeline with existing opportunities")

        # Delete stages
        stage_ids = [
            s["id"] for s in crm_store._stages.values()
            if s.get("pipeline_id") == pipeline_id
        ]
        for sid in stage_ids:
            del crm_store._stages[sid]

        # Delete pipeline
        del crm_store._pipelines[pipeline_id]

    def add_stage(
        self,
        pipeline_id: str,
        name: str,
        probability: int = 0,
        position: int = None,
        color: str = None,
        is_won: bool = False,
        is_lost: bool = False,
    ) -> dict:
        """Add a stage to pipeline"""
        pipeline = crm_store.get_pipeline(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline not found: {pipeline_id}")

        # Auto-position if not specified
        if position is None:
            existing_positions = [
                s.get("position", 0) for s in pipeline.get("stages", [])
            ]
            position = max(existing_positions) + 1 if existing_positions else 1

        stage = crm_store.create_stage({
            "pipeline_id": pipeline_id,
            "name": name,
            "probability": probability,
            "position": position,
            "color": color,
            "is_won": is_won,
            "is_lost": is_lost,
        })

        return stage

    def update_stage(self, stage_id: str, **updates) -> dict:
        """Update stage settings"""
        stage = crm_store._stages.get(stage_id)
        if not stage:
            raise ValueError(f"Stage not found: {stage_id}")

        stage.update(updates)
        return stage

    def delete_stage(self, stage_id: str, move_to_stage_id: str = None):
        """Delete a stage (move opportunities to another stage)"""
        stage = crm_store._stages.get(stage_id)
        if not stage:
            raise ValueError(f"Stage not found: {stage_id}")

        # Move opportunities
        opps, _ = crm_store.list_opportunities(stage_id=stage_id, limit=1000)
        if opps:
            if not move_to_stage_id:
                raise ValueError("Must specify target stage for existing opportunities")
            for opp in opps:
                crm_store.update_opportunity(opp["id"], {"stage_id": move_to_stage_id})

        del crm_store._stages[stage_id]

    def reorder_stages(self, pipeline_id: str, stage_order: List[str]):
        """Reorder stages in pipeline"""
        for i, stage_id in enumerate(stage_order):
            stage = crm_store._stages.get(stage_id)
            if stage and stage.get("pipeline_id") == pipeline_id:
                stage["position"] = i + 1

    def get_pipeline_stats(self, pipeline_id: str, tenant_id: str = None) -> dict:
        """Get pipeline statistics"""
        return crm_store.get_pipeline_stats(pipeline_id, tenant_id)

    def duplicate_pipeline(
        self,
        pipeline_id: str,
        tenant_id: str,
        new_name: str,
    ) -> dict:
        """Duplicate a pipeline with its stages"""
        original = crm_store.get_pipeline(pipeline_id)
        if not original:
            raise ValueError(f"Pipeline not found: {pipeline_id}")

        # Create new pipeline
        new_pipeline = crm_store.create_pipeline({
            "tenant_id": tenant_id,
            "name": new_name,
            "is_default": False,
        })

        # Copy stages
        for stage in original.get("stages", []):
            crm_store.create_stage({
                "pipeline_id": new_pipeline["id"],
                "name": stage["name"],
                "probability": stage.get("probability", 0),
                "position": stage.get("position"),
                "color": stage.get("color"),
                "is_won": stage.get("is_won", False),
                "is_lost": stage.get("is_lost", False),
            })

        return self.get_pipeline(new_pipeline["id"])


# Service instance
pipeline_service = PipelineService()
