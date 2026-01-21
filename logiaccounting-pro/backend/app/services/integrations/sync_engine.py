"""
Phase 14: Sync Engine
Core synchronization engine for bidirectional data sync
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import logging
import hashlib
import json

from app.models.integrations_store import (
    integrations_store, sync_configs_store, sync_logs_store,
    sync_records_store, field_mappings_store,
    SyncDirection, SyncStatus, SyncLogStatus, ConflictResolution
)
from .transformer import DataTransformer
from .base_connector import BaseConnector, SyncResult

logger = logging.getLogger(__name__)


class SyncEngine:
    """Core synchronization engine"""

    def __init__(self, connector: BaseConnector, integration_id: str):
        self.connector = connector
        self.integration_id = integration_id
        self.integration = integrations_store.find_by_id(integration_id)

    async def sync_entity(
        self,
        sync_config_id: str,
        sync_type: str = "incremental",
        direction: str = None,
        triggered_by: str = "manual",
        user_id: str = None
    ) -> Dict:
        """
        Synchronize an entity type

        Args:
            sync_config_id: Sync configuration ID
            sync_type: 'full' or 'incremental'
            direction: 'inbound', 'outbound', or None for bidirectional
            triggered_by: Who triggered the sync
            user_id: User ID who triggered

        Returns:
            Sync log with results
        """
        sync_config = sync_configs_store.find_by_id(sync_config_id)
        if not sync_config:
            raise ValueError(f"Sync config not found: {sync_config_id}")

        # Determine direction
        config_direction = sync_config.get("sync_direction", SyncDirection.BIDIRECTIONAL)
        if direction:
            actual_direction = direction
        else:
            actual_direction = config_direction

        # Create sync log
        sync_log = sync_logs_store.create({
            "integration_id": self.integration_id,
            "sync_config_id": sync_config_id,
            "sync_type": sync_type,
            "direction": actual_direction,
            "entity_type": sync_config["local_entity"],
            "triggered_by": triggered_by,
            "triggered_by_user_id": user_id,
        })

        sync_logs_store.start(sync_log["id"])

        try:
            # Get field mappings
            mappings = field_mappings_store.find_all(sync_config_id)
            transformer = DataTransformer(mappings)

            # Perform sync based on direction
            if actual_direction in [SyncDirection.BIDIRECTIONAL, "bidirectional"]:
                # First pull (inbound), then push (outbound)
                await self._sync_inbound(sync_config, transformer, sync_log, sync_type)
                await self._sync_outbound(sync_config, transformer, sync_log, sync_type)
            elif actual_direction in [SyncDirection.INBOUND, "inbound"]:
                await self._sync_inbound(sync_config, transformer, sync_log, sync_type)
            elif actual_direction in [SyncDirection.OUTBOUND, "outbound"]:
                await self._sync_outbound(sync_config, transformer, sync_log, sync_type)

            # Complete sync
            status = SyncLogStatus.COMPLETED
            log = sync_logs_store.find_by_id(sync_log["id"])
            if log.get("records_failed", 0) > 0:
                status = SyncLogStatus.PARTIAL

            sync_logs_store.complete(sync_log["id"], status)

            # Update integration sync timestamp
            integrations_store.record_sync(self.integration_id)

            # Update sync config timestamp
            sync_configs_store.update(sync_config_id, {
                "last_sync_at": datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            sync_logs_store.add_error(sync_log["id"], {
                "error": str(e),
                "type": "sync_error"
            })
            sync_logs_store.complete(sync_log["id"], SyncLogStatus.FAILED)

        return sync_logs_store.find_by_id(sync_log["id"])

    async def _sync_inbound(
        self,
        sync_config: Dict,
        transformer: DataTransformer,
        sync_log: Dict,
        sync_type: str
    ):
        """Sync data from remote to local"""
        remote_entity = sync_config["remote_entity"]
        local_entity = sync_config["local_entity"]
        filters = sync_config.get("sync_filter", {})

        # For incremental sync, only get records modified since last sync
        modified_since = None
        if sync_type == "incremental" and sync_config.get("last_sync_at"):
            modified_since = datetime.fromisoformat(sync_config["last_sync_at"])

        try:
            # Fetch records from remote
            page = 1
            has_more = True

            while has_more:
                records, has_more = await self.connector.list_records(
                    entity_name=remote_entity,
                    filters=filters,
                    page=page,
                    page_size=100,
                    modified_since=modified_since
                )

                for remote_record in records:
                    await self._process_inbound_record(
                        remote_record,
                        sync_config,
                        transformer,
                        sync_log
                    )

                page += 1

        except Exception as e:
            logger.error(f"Inbound sync error: {e}")
            sync_logs_store.add_error(sync_log["id"], {
                "error": str(e),
                "type": "inbound_error"
            })

    async def _process_inbound_record(
        self,
        remote_record: Dict,
        sync_config: Dict,
        transformer: DataTransformer,
        sync_log: Dict
    ):
        """Process a single inbound record"""
        try:
            # Get remote ID
            schema = self.connector.get_entity_schema(sync_config["remote_entity"])
            id_field = schema.id_field if schema else "id"
            remote_id = str(remote_record.get(id_field, remote_record.get("id", "")))

            if not remote_id:
                sync_logs_store.add_error(sync_log["id"], {
                    "error": "Record has no ID",
                    "record": remote_record
                })
                return

            # Check if we have a sync record
            existing = sync_records_store.find_by_remote_id(
                sync_config["id"],
                remote_id
            )

            # Transform to local format
            local_data = transformer.transform_to_local(remote_record)

            # Compute hash for change detection
            remote_hash = self._compute_hash(remote_record)

            if existing:
                # Check if changed
                if existing.get("remote_hash") == remote_hash:
                    sync_logs_store.increment_stats(sync_log["id"], skipped=1)
                    return

                # Handle conflict if local also changed
                if existing.get("sync_status") == SyncStatus.PENDING_OUTBOUND:
                    await self._handle_conflict(
                        existing,
                        local_data,
                        remote_record,
                        sync_config,
                        sync_log
                    )
                    return

                # Update existing record
                sync_records_store.update(existing["id"], {
                    "remote_hash": remote_hash,
                    "remote_updated_at": datetime.utcnow().isoformat(),
                    "last_synced_at": datetime.utcnow().isoformat(),
                    "sync_status": SyncStatus.SYNCED,
                })

                sync_logs_store.increment_stats(sync_log["id"], updated=1)
            else:
                # Create new sync record
                sync_records_store.create({
                    "integration_id": self.integration_id,
                    "sync_config_id": sync_config["id"],
                    "local_id": str(remote_id),  # Using remote ID as local for now
                    "remote_id": remote_id,
                    "remote_hash": remote_hash,
                    "sync_status": SyncStatus.SYNCED,
                })

                sync_logs_store.increment_stats(sync_log["id"], created=1)

        except Exception as e:
            logger.error(f"Error processing inbound record: {e}")
            sync_logs_store.add_error(sync_log["id"], {
                "error": str(e),
                "record_id": str(remote_record.get("id", "unknown"))
            })

    async def _sync_outbound(
        self,
        sync_config: Dict,
        transformer: DataTransformer,
        sync_log: Dict,
        sync_type: str
    ):
        """Sync data from local to remote"""
        # Find records pending outbound sync
        pending_records = sync_records_store.find_by_status(
            self.integration_id,
            SyncStatus.PENDING_OUTBOUND,
            limit=1000
        )

        for record in pending_records:
            if record["sync_config_id"] != sync_config["id"]:
                continue

            await self._process_outbound_record(
                record,
                sync_config,
                transformer,
                sync_log
            )

    async def _process_outbound_record(
        self,
        sync_record: Dict,
        sync_config: Dict,
        transformer: DataTransformer,
        sync_log: Dict
    ):
        """Process a single outbound record"""
        try:
            # In a real implementation, we would fetch the local record
            # For demo, we'll skip actual outbound processing
            logger.info(f"Would sync outbound record: {sync_record['local_id']}")

            sync_records_store.update(sync_record["id"], {
                "last_synced_at": datetime.utcnow().isoformat(),
                "sync_status": SyncStatus.SYNCED,
            })

            sync_logs_store.increment_stats(sync_log["id"], updated=1)

        except Exception as e:
            logger.error(f"Error processing outbound record: {e}")
            sync_logs_store.add_error(sync_log["id"], {
                "error": str(e),
                "record_id": sync_record["local_id"]
            })
            sync_records_store.update(sync_record["id"], {
                "sync_status": SyncStatus.ERROR,
            })

    async def _handle_conflict(
        self,
        sync_record: Dict,
        local_data: Dict,
        remote_data: Dict,
        sync_config: Dict,
        sync_log: Dict
    ):
        """Handle sync conflict"""
        resolution = sync_config.get("conflict_resolution", ConflictResolution.LAST_WRITE_WINS)
        priority_source = sync_config.get("priority_source", "local")

        if resolution == ConflictResolution.LAST_WRITE_WINS:
            # Compare timestamps
            local_updated = sync_record.get("local_updated_at")
            remote_updated = remote_data.get("updated_at") or remote_data.get("UpdatedAt")

            if local_updated and remote_updated:
                local_dt = datetime.fromisoformat(local_updated) if isinstance(local_updated, str) else local_updated
                remote_dt = datetime.fromisoformat(str(remote_updated).replace('Z', '+00:00'))

                if remote_dt > local_dt:
                    # Remote wins
                    sync_records_store.update(sync_record["id"], {
                        "sync_status": SyncStatus.SYNCED,
                        "remote_hash": self._compute_hash(remote_data),
                    })
                else:
                    # Local wins - keep pending outbound
                    pass
            else:
                # No timestamps, use priority source
                if priority_source == "remote":
                    sync_records_store.update(sync_record["id"], {
                        "sync_status": SyncStatus.SYNCED,
                    })

        elif resolution == ConflictResolution.SOURCE_PRIORITY:
            if priority_source == "remote":
                sync_records_store.update(sync_record["id"], {
                    "sync_status": SyncStatus.SYNCED,
                    "remote_hash": self._compute_hash(remote_data),
                })
            # If local priority, keep pending outbound

        elif resolution == ConflictResolution.MANUAL_REVIEW:
            sync_records_store.update(sync_record["id"], {
                "sync_status": SyncStatus.CONFLICT,
            })

        elif resolution == ConflictResolution.MERGE:
            # Merge non-conflicting fields
            # This is a simplified implementation
            sync_records_store.update(sync_record["id"], {
                "sync_status": SyncStatus.SYNCED,
            })

        sync_logs_store.increment_stats(sync_log["id"], updated=1)

    def _compute_hash(self, record: Dict) -> str:
        """Compute hash of record for change detection"""
        # Remove metadata fields
        clean_record = {k: v for k, v in record.items()
                       if not k.startswith('_') and k not in ['attributes', 'SyncToken']}
        normalized = json.dumps(clean_record, sort_keys=True, default=str)
        return hashlib.sha256(normalized.encode()).hexdigest()

    async def get_pending_count(self, sync_config_id: str = None) -> Dict[str, int]:
        """Get count of pending records by status"""
        records = []
        if sync_config_id:
            for status in [SyncStatus.PENDING_INBOUND, SyncStatus.PENDING_OUTBOUND,
                          SyncStatus.CONFLICT, SyncStatus.ERROR]:
                records.extend(sync_records_store.find_by_status(
                    self.integration_id,
                    status
                ))

        return {
            "pending_inbound": len([r for r in records if r["sync_status"] == SyncStatus.PENDING_INBOUND]),
            "pending_outbound": len([r for r in records if r["sync_status"] == SyncStatus.PENDING_OUTBOUND]),
            "conflicts": len([r for r in records if r["sync_status"] == SyncStatus.CONFLICT]),
            "errors": len([r for r in records if r["sync_status"] == SyncStatus.ERROR]),
        }


class ConflictResolver:
    """Handles conflict resolution strategies"""

    @staticmethod
    def resolve(
        local_record: Dict,
        remote_record: Dict,
        strategy: str,
        priority_source: str = "local"
    ) -> Tuple[Dict, str]:
        """
        Resolve conflict between local and remote records

        Args:
            local_record: Local record data
            remote_record: Remote record data
            strategy: Resolution strategy
            priority_source: Which source takes priority

        Returns:
            Tuple of (resolved_record, winner)
        """
        if strategy == ConflictResolution.LAST_WRITE_WINS:
            local_time = local_record.get("updated_at") or local_record.get("UpdatedAt")
            remote_time = remote_record.get("updated_at") or remote_record.get("UpdatedAt")

            if local_time and remote_time:
                if local_time > remote_time:
                    return local_record, "local"
                return remote_record, "remote"

            # Fall back to priority source
            if priority_source == "local":
                return local_record, "local"
            return remote_record, "remote"

        elif strategy == ConflictResolution.SOURCE_PRIORITY:
            if priority_source == "local":
                return local_record, "local"
            return remote_record, "remote"

        elif strategy == ConflictResolution.MERGE:
            # Merge non-conflicting fields
            merged = {**remote_record, **local_record}
            return merged, "merged"

        else:
            # Default to priority source
            if priority_source == "local":
                return local_record, "local"
            return remote_record, "remote"
