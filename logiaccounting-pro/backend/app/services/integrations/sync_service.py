"""
Sync Service
Handles data synchronization between LogiAccounting and integrations
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4
from app.utils.datetime_utils import utc_now
from enum import Enum
import logging
import asyncio

from app.integrations.connection import connection_manager, Connection
from app.integrations.base import SyncResult

logger = logging.getLogger(__name__)


class SyncDirection(str, Enum):
    PULL = "pull"  # From provider to LogiAccounting
    PUSH = "push"  # From LogiAccounting to provider
    BIDIRECTIONAL = "bidirectional"


class SyncSchedule(str, Enum):
    MANUAL = "manual"
    HOURLY = "hourly"
    DAILY = "daily"
    REALTIME = "realtime"


class SyncJob:
    """Represents a sync job."""

    def __init__(self, connection_id: str, entity_type: str, direction: SyncDirection):
        self.id = f"sync_{uuid4().hex[:12]}"
        self.connection_id = connection_id
        self.entity_type = entity_type
        self.direction = direction
        self.status = "pending"
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[SyncResult] = None
        self.error: Optional[str] = None


class SyncConfig:
    """Configuration for sync between entities."""

    def __init__(self, connection_id: str, entity_type: str):
        self.connection_id = connection_id
        self.entity_type = entity_type
        self.direction = SyncDirection.BIDIRECTIONAL
        self.schedule = SyncSchedule.MANUAL
        self.field_mappings: Dict[str, str] = {}
        self.filters: Dict[str, Any] = {}
        self.enabled = True
        self.last_sync_at: Optional[datetime] = None


class SyncService:
    """Manages data synchronization."""

    ENTITY_TYPES = [
        "customers",
        "invoices",
        "payments",
        "products",
        "projects",
        "expenses",
        "contacts",
    ]

    def __init__(self):
        self._jobs: Dict[str, SyncJob] = {}
        self._configs: Dict[str, SyncConfig] = {}
        self._running_jobs: Dict[str, asyncio.Task] = {}

    # ==================== Sync Configuration ====================

    def configure_sync(self, connection_id: str, entity_type: str, config: Dict) -> SyncConfig:
        """Configure sync for an entity type."""
        if entity_type not in self.ENTITY_TYPES:
            raise ValueError(f"Unknown entity type: {entity_type}")

        key = f"{connection_id}:{entity_type}"

        sync_config = SyncConfig(connection_id, entity_type)

        if "direction" in config:
            sync_config.direction = SyncDirection(config["direction"])
        if "schedule" in config:
            sync_config.schedule = SyncSchedule(config["schedule"])
        if "field_mappings" in config:
            sync_config.field_mappings = config["field_mappings"]
        if "filters" in config:
            sync_config.filters = config["filters"]
        if "enabled" in config:
            sync_config.enabled = config["enabled"]

        self._configs[key] = sync_config
        return sync_config

    def get_sync_config(self, connection_id: str, entity_type: str) -> Optional[SyncConfig]:
        """Get sync configuration."""
        key = f"{connection_id}:{entity_type}"
        return self._configs.get(key)

    def get_connection_configs(self, connection_id: str) -> List[SyncConfig]:
        """Get all sync configs for a connection."""
        return [
            config for key, config in self._configs.items()
            if key.startswith(f"{connection_id}:")
        ]

    # ==================== Sync Execution ====================

    async def sync(self, connection_id: str, entity_type: str, direction: str = None, force: bool = False) -> SyncJob:
        """Execute a sync job."""
        # Get connection
        connection = connection_manager.get_connection_by_id(connection_id)
        if not connection:
            raise ValueError(f"Connection not found: {connection_id}")

        # Get or create config
        config = self.get_sync_config(connection_id, entity_type)
        if not config:
            config = SyncConfig(connection_id, entity_type)

        # Determine direction
        sync_direction = SyncDirection(direction) if direction else config.direction

        # Check if already running
        job_key = f"{connection_id}:{entity_type}"
        if job_key in self._running_jobs and not force:
            existing_job_id = list(self._jobs.keys())[-1]
            return self._jobs[existing_job_id]

        # Create job
        job = SyncJob(connection_id, entity_type, sync_direction)
        self._jobs[job.id] = job

        # Start sync task
        task = asyncio.create_task(self._execute_sync(job, connection, config))
        self._running_jobs[job_key] = task

        return job

    async def _execute_sync(self, job: SyncJob, connection: Connection, config: SyncConfig):
        """Execute sync job."""
        job.status = "running"
        job.started_at = utc_now()

        try:
            # Get integration instance
            instance = connection_manager.get_instance(connection.id)
            if not instance:
                raise ValueError("Failed to get integration instance")

            # Perform sync based on direction
            if job.direction in [SyncDirection.PULL, SyncDirection.BIDIRECTIONAL]:
                result = await instance.sync(job.entity_type, "pull")
                job.result = result if isinstance(result, SyncResult) else None

            if job.direction in [SyncDirection.PUSH, SyncDirection.BIDIRECTIONAL]:
                result = await instance.sync(job.entity_type, "push")
                if job.result and isinstance(result, SyncResult):
                    # Merge results
                    job.result.created += result.created
                    job.result.updated += result.updated
                elif isinstance(result, SyncResult):
                    job.result = result

            job.status = "completed"
            config.last_sync_at = utc_now()
            connection.last_sync_at = utc_now()

            logger.info(f"Sync job {job.id} completed successfully")

        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            logger.error(f"Sync job {job.id} failed: {e}")

        finally:
            job.completed_at = utc_now()

            # Remove from running jobs
            job_key = f"{connection.id}:{job.entity_type}"
            if job_key in self._running_jobs:
                del self._running_jobs[job_key]

    async def sync_all(self, connection_id: str) -> List[SyncJob]:
        """Sync all configured entities for a connection."""
        configs = self.get_connection_configs(connection_id)
        jobs = []

        for config in configs:
            if config.enabled:
                job = await self.sync(connection_id, config.entity_type)
                jobs.append(job)

        return jobs

    def cancel_sync(self, job_id: str) -> bool:
        """Cancel a running sync job."""
        job = self._jobs.get(job_id)
        if not job or job.status != "running":
            return False

        job_key = f"{job.connection_id}:{job.entity_type}"
        task = self._running_jobs.get(job_key)

        if task:
            task.cancel()
            job.status = "cancelled"
            job.completed_at = utc_now()
            del self._running_jobs[job_key]
            return True

        return False

    # ==================== Status & History ====================

    def get_job(self, job_id: str) -> Optional[SyncJob]:
        """Get sync job by ID."""
        return self._jobs.get(job_id)

    def get_sync_status(self, connection_id: str) -> Dict[str, Any]:
        """Get sync status for a connection."""
        configs = self.get_connection_configs(connection_id)

        entities = {}
        for config in configs:
            job_key = f"{connection_id}:{config.entity_type}"
            is_running = job_key in self._running_jobs

            entities[config.entity_type] = {
                "enabled": config.enabled,
                "direction": config.direction.value,
                "schedule": config.schedule.value,
                "is_syncing": is_running,
                "last_sync_at": config.last_sync_at.isoformat() if config.last_sync_at else None,
            }

        return {
            "connection_id": connection_id,
            "entities": entities,
            "has_running_jobs": len(self._running_jobs) > 0,
        }

    def get_sync_history(self, connection_id: str, limit: int = 20) -> List[Dict]:
        """Get sync history for a connection."""
        jobs = [
            j for j in self._jobs.values()
            if j.connection_id == connection_id
        ]

        jobs = sorted(jobs, key=lambda j: j.started_at or datetime.min, reverse=True)

        return [self.job_to_dict(j) for j in jobs[:limit]]

    def job_to_dict(self, job: SyncJob) -> Dict:
        """Convert job to dictionary."""
        return {
            "id": job.id,
            "connection_id": job.connection_id,
            "entity_type": job.entity_type,
            "direction": job.direction.value,
            "status": job.status,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "result": job.result.to_dict() if job.result else None,
            "error": job.error,
        }

    def config_to_dict(self, config: SyncConfig) -> Dict:
        """Convert config to dictionary."""
        return {
            "connection_id": config.connection_id,
            "entity_type": config.entity_type,
            "direction": config.direction.value,
            "schedule": config.schedule.value,
            "field_mappings": config.field_mappings,
            "filters": config.filters,
            "enabled": config.enabled,
            "last_sync_at": config.last_sync_at.isoformat() if config.last_sync_at else None,
        }


# Service instance
sync_service = SyncService()
