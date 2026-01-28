"""
Phase 14: Integration Service
High-level service for managing integrations
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import logging
from app.utils.datetime_utils import utc_now
import asyncio

from app.models.integrations_store import (
    integrations_store,
    sync_configs_store,
    field_mappings_store,
    sync_logs_store,
    sync_records_store,
    webhooks_store,
    webhook_events_store,
    IntegrationStatus,
    SyncDirection,
    SyncStatus,
)

from .base_connector import BaseConnector, ConnectorConfig, SyncResult
from .connectors import get_connector_class, get_available_connectors
from .oauth_manager import IntegrationOAuthService
from .transformer import DataTransformer
from .sync_engine import SyncEngine, ConflictResolver

logger = logging.getLogger(__name__)


class IntegrationService:
    """High-level service for managing integrations"""

    @staticmethod
    def list_available_providers() -> List[Dict]:
        """List all available integration providers"""
        from app.models.integrations_store import PROVIDER_CONFIGS

        providers = []
        for provider_name, config in PROVIDER_CONFIGS.items():
            providers.append({
                'name': provider_name,
                'label': config.get('label', provider_name.title()),
                'category': config.get('category', 'generic'),
                'description': config.get('description', ''),
                'auth_type': config.get('auth_type', 'oauth2'),
                'features': config.get('features', []),
                'supported_entities': config.get('supported_entities', []),
            })

        return providers

    @staticmethod
    def get_provider_info(provider: str) -> Optional[Dict]:
        """Get detailed info about a provider"""
        from app.models.integrations_store import PROVIDER_CONFIGS

        config = PROVIDER_CONFIGS.get(provider)
        if not config:
            return None

        # Get connector class for additional info
        connector_class = get_connector_class(provider)

        info = {
            'name': provider,
            'label': config.get('label', provider.title()),
            'category': config.get('category', 'generic'),
            'description': config.get('description', ''),
            'auth_type': config.get('auth_type', 'oauth2'),
            'features': config.get('features', []),
            'supported_entities': config.get('supported_entities', []),
        }

        if connector_class:
            info['oauth_scopes'] = getattr(connector_class, 'OAUTH_SCOPES', [])
            info['rate_limit'] = {
                'requests': getattr(connector_class, 'RATE_LIMIT_REQUESTS', 100),
                'period': getattr(connector_class, 'RATE_LIMIT_PERIOD', 60),
            }

        return info

    # ==================== Integration Management ====================

    @staticmethod
    def list_integrations(organization_id: str, category: str = None) -> List[Dict]:
        """List all integrations for an organization"""
        integrations = integrations_store.find_by_organization(organization_id)

        if category:
            integrations = [i for i in integrations if i.get('category') == category]

        # Add connection status info
        for integration in integrations:
            integration['is_connected'] = integration.get('status') == IntegrationStatus.ACTIVE.value
            integration['needs_reauth'] = integration.get('status') == IntegrationStatus.ERROR.value

            # Calculate health score
            integration['health'] = IntegrationService._calculate_health(integration['id'])

        return integrations

    @staticmethod
    def get_integration(integration_id: str) -> Optional[Dict]:
        """Get integration by ID with full details"""
        integration = integrations_store.find_by_id(integration_id)
        if not integration:
            return None

        # Add sync configs
        integration['sync_configs'] = sync_configs_store.find_by_integration(integration_id)

        # Add recent sync logs
        integration['recent_syncs'] = sync_logs_store.find_by_integration(
            integration_id, limit=10
        )

        # Add webhooks
        integration['webhooks'] = webhooks_store.find_by_integration(integration_id)

        # Calculate stats
        integration['stats'] = IntegrationService._get_integration_stats(integration_id)

        return integration

    @staticmethod
    def create_integration(
        organization_id: str,
        provider: str,
        name: str = None,
        config: Dict = None
    ) -> Dict:
        """Create a new integration"""
        from app.models.integrations_store import PROVIDER_CONFIGS

        provider_config = PROVIDER_CONFIGS.get(provider)
        if not provider_config:
            raise ValueError(f"Unknown provider: {provider}")

        # Check if integration already exists
        existing = integrations_store.find_by_provider(organization_id, provider)
        if existing:
            raise ValueError(f"Integration with {provider} already exists")

        integration = integrations_store.create({
            'organization_id': organization_id,
            'provider': provider,
            'name': name or provider_config.get('label', provider.title()),
            'category': provider_config.get('category', 'generic'),
            'config': config or {},
        })

        logger.info(f"Created integration {integration['id']} for {provider}")
        return integration

    @staticmethod
    def update_integration(integration_id: str, data: Dict) -> Optional[Dict]:
        """Update integration settings"""
        allowed_fields = ['name', 'config', 'settings']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}

        if update_data:
            integrations_store.update(integration_id, update_data)

        return integrations_store.find_by_id(integration_id)

    @staticmethod
    def delete_integration(integration_id: str) -> bool:
        """Delete an integration and all related data"""
        integration = integrations_store.find_by_id(integration_id)
        if not integration:
            return False

        # Delete related data
        sync_configs = sync_configs_store.find_by_integration(integration_id)
        for config in sync_configs:
            field_mappings_store.delete_by_sync_config(config['id'])

        sync_configs_store.delete_by_integration(integration_id)
        sync_logs_store.delete_by_integration(integration_id)
        webhooks_store.delete_by_integration(integration_id)

        # Delete integration
        integrations_store.delete(integration_id)

        logger.info(f"Deleted integration {integration_id}")
        return True

    # ==================== OAuth Flow ====================

    @staticmethod
    def initiate_oauth(
        organization_id: str,
        provider: str,
        user_id: str,
        redirect_uri: str,
        extra_params: Dict = None
    ) -> str:
        """Start OAuth flow for a provider"""
        return IntegrationOAuthService.initiate_oauth(
            organization_id=organization_id,
            provider=provider,
            user_id=user_id,
            redirect_uri=redirect_uri,
            extra_params=extra_params
        )

    @staticmethod
    async def complete_oauth(
        provider: str,
        code: str,
        state: str,
        redirect_uri: str
    ) -> Dict:
        """Complete OAuth flow"""
        return await IntegrationOAuthService.complete_oauth(
            provider=provider,
            code=code,
            state=state,
            redirect_uri=redirect_uri
        )

    @staticmethod
    async def refresh_token(integration_id: str) -> bool:
        """Refresh OAuth token for an integration"""
        return await IntegrationOAuthService.refresh_integration_token(integration_id)

    # ==================== Connector Operations ====================

    @staticmethod
    def get_connector(integration_id: str) -> Optional[BaseConnector]:
        """Get connector instance for an integration"""
        integration = integrations_store.find_by_id(integration_id)
        if not integration:
            return None

        connector_class = get_connector_class(integration['provider'])
        if not connector_class:
            return None

        config = ConnectorConfig(
            client_id=integration.get('config', {}).get('client_id', ''),
            client_secret=integration.get('config', {}).get('client_secret', ''),
            access_token=integration.get('oauth_access_token', ''),
            refresh_token=integration.get('oauth_refresh_token', ''),
            environment=integration.get('config', {}).get('environment', 'production'),
            extra=integration.get('config', {}),
        )

        return connector_class(config)

    @staticmethod
    async def test_connection(integration_id: str) -> Tuple[bool, str]:
        """Test integration connection"""
        connector = IntegrationService.get_connector(integration_id)
        if not connector:
            return False, "Connector not found"

        try:
            success, message = await connector.test_connection()

            if success:
                integrations_store.update(integration_id, {
                    'status': IntegrationStatus.ACTIVE.value,
                    'last_sync_at': utc_now().isoformat(),
                })
            else:
                integrations_store.mark_error(integration_id, message)

            return success, message

        except Exception as e:
            integrations_store.mark_error(integration_id, str(e))
            return False, str(e)

    # ==================== Sync Configuration ====================

    @staticmethod
    def create_sync_config(
        integration_id: str,
        entity_type: str,
        direction: str = 'bidirectional',
        remote_entity: str = None,
        sync_interval: int = 3600,
        conflict_resolution: str = 'last_write_wins'
    ) -> Dict:
        """Create sync configuration for an entity"""
        integration = integrations_store.find_by_id(integration_id)
        if not integration:
            raise ValueError("Integration not found")

        # Get default remote entity from connector
        connector_class = get_connector_class(integration['provider'])
        if connector_class and not remote_entity:
            remote_entity = connector_class.SUPPORTED_ENTITIES.get(
                entity_type, entity_type
            )

        return sync_configs_store.create({
            'integration_id': integration_id,
            'entity_type': entity_type,
            'remote_entity': remote_entity or entity_type,
            'direction': direction,
            'sync_interval': sync_interval,
            'conflict_resolution': conflict_resolution,
            'enabled': True,
        })

    @staticmethod
    def update_sync_config(sync_config_id: str, data: Dict) -> Optional[Dict]:
        """Update sync configuration"""
        allowed_fields = [
            'direction', 'sync_interval', 'conflict_resolution',
            'enabled', 'filters', 'settings'
        ]
        update_data = {k: v for k, v in data.items() if k in allowed_fields}

        if update_data:
            return sync_configs_store.update(sync_config_id, update_data)
        return sync_configs_store.find_by_id(sync_config_id)

    @staticmethod
    def delete_sync_config(sync_config_id: str) -> bool:
        """Delete sync configuration"""
        field_mappings_store.delete_by_sync_config(sync_config_id)
        return sync_configs_store.delete(sync_config_id)

    # ==================== Field Mapping ====================

    @staticmethod
    def create_field_mapping(
        sync_config_id: str,
        local_field: str,
        remote_field: str,
        transform_type: str = 'direct',
        transform_config: Dict = None,
        direction: str = 'bidirectional'
    ) -> Dict:
        """Create field mapping"""
        return field_mappings_store.create({
            'sync_config_id': sync_config_id,
            'local_field': local_field,
            'remote_field': remote_field,
            'transform_type': transform_type,
            'transform_config': transform_config or {},
            'direction': direction,
        })

    @staticmethod
    def get_field_mappings(sync_config_id: str) -> List[Dict]:
        """Get all field mappings for a sync config"""
        return field_mappings_store.find_by_sync_config(sync_config_id)

    @staticmethod
    def update_field_mapping(mapping_id: str, data: Dict) -> Optional[Dict]:
        """Update field mapping"""
        return field_mappings_store.update(mapping_id, data)

    @staticmethod
    def delete_field_mapping(mapping_id: str) -> bool:
        """Delete field mapping"""
        return field_mappings_store.delete(mapping_id)

    # ==================== Synchronization ====================

    @staticmethod
    async def sync_entity(
        integration_id: str,
        entity_type: str,
        full_sync: bool = False
    ) -> SyncResult:
        """Sync a specific entity type"""
        integration = integrations_store.find_by_id(integration_id)
        if not integration:
            raise ValueError("Integration not found")

        # Get sync config
        sync_configs = sync_configs_store.find_by_integration(integration_id)
        sync_config = next(
            (c for c in sync_configs if c['entity_type'] == entity_type),
            None
        )

        if not sync_config:
            raise ValueError(f"No sync config for entity: {entity_type}")

        if not sync_config.get('enabled', True):
            raise ValueError(f"Sync is disabled for entity: {entity_type}")

        # Create sync log
        sync_log = sync_logs_store.create({
            'integration_id': integration_id,
            'sync_config_id': sync_config['id'],
            'entity_type': entity_type,
            'direction': sync_config.get('direction', 'bidirectional'),
            'status': SyncStatus.IN_PROGRESS.value,
            'started_at': utc_now().isoformat(),
        })

        try:
            # Get connector
            connector = IntegrationService.get_connector(integration_id)
            if not connector:
                raise ValueError("Could not create connector")

            # Get field mappings
            field_mappings = field_mappings_store.find_by_sync_config(sync_config['id'])

            # Create sync engine
            sync_engine = SyncEngine(
                connector=connector,
                transformer=DataTransformer(field_mappings),
                conflict_resolver=ConflictResolver(sync_config.get('conflict_resolution', 'last_write_wins')),
            )

            # Get last sync time
            last_sync = None
            if not full_sync:
                last_sync = sync_config.get('last_sync_at')
                if last_sync:
                    last_sync = datetime.fromisoformat(last_sync)

            # Perform sync
            result = await sync_engine.sync_entity(
                entity_type=entity_type,
                sync_config=sync_config,
                modified_since=last_sync
            )

            # Update sync log
            sync_logs_store.complete(
                sync_log['id'],
                success=result.success,
                records_processed=result.records_processed,
                records_created=result.records_created,
                records_updated=result.records_updated,
                records_failed=result.records_failed,
                error_message=result.error_message
            )

            # Update sync config
            sync_configs_store.update(sync_config['id'], {
                'last_sync_at': utc_now().isoformat(),
            })

            # Update integration
            integrations_store.update(integration_id, {
                'last_sync_at': utc_now().isoformat(),
            })

            logger.info(
                f"Sync completed for {entity_type}: "
                f"processed={result.records_processed}, "
                f"created={result.records_created}, "
                f"updated={result.records_updated}, "
                f"failed={result.records_failed}"
            )

            return result

        except Exception as e:
            logger.error(f"Sync failed for {entity_type}: {e}")

            sync_logs_store.complete(
                sync_log['id'],
                success=False,
                error_message=str(e)
            )

            raise

    @staticmethod
    async def sync_all(integration_id: str, full_sync: bool = False) -> Dict[str, SyncResult]:
        """Sync all configured entities for an integration"""
        sync_configs = sync_configs_store.find_by_integration(integration_id)
        enabled_configs = [c for c in sync_configs if c.get('enabled', True)]

        results = {}

        for config in enabled_configs:
            try:
                result = await IntegrationService.sync_entity(
                    integration_id=integration_id,
                    entity_type=config['entity_type'],
                    full_sync=full_sync
                )
                results[config['entity_type']] = result
            except Exception as e:
                logger.error(f"Sync failed for {config['entity_type']}: {e}")
                results[config['entity_type']] = SyncResult(
                    success=False,
                    error_message=str(e)
                )

        return results

    # ==================== Webhook Management ====================

    @staticmethod
    def register_webhook(
        integration_id: str,
        event_types: List[str],
        url: str,
        secret: str = None
    ) -> Dict:
        """Register a webhook for an integration"""
        import secrets

        webhook = webhooks_store.create({
            'integration_id': integration_id,
            'url': url,
            'event_types': event_types,
            'secret': secret or secrets.token_urlsafe(32),
            'enabled': True,
        })

        logger.info(f"Registered webhook {webhook['id']} for integration {integration_id}")
        return webhook

    @staticmethod
    async def process_webhook(
        integration_id: str,
        event_type: str,
        payload: Dict,
        headers: Dict = None
    ) -> bool:
        """Process incoming webhook"""
        integration = integrations_store.find_by_id(integration_id)
        if not integration:
            logger.warning(f"Webhook received for unknown integration: {integration_id}")
            return False

        # Store webhook event
        webhook_events_store.create({
            'integration_id': integration_id,
            'event_type': event_type,
            'payload': payload,
            'headers': headers,
            'processed': False,
        })

        # Find matching webhooks
        webhooks = webhooks_store.find_by_integration(integration_id)
        matching = [
            w for w in webhooks
            if w.get('enabled', True) and event_type in w.get('event_types', [])
        ]

        if not matching:
            logger.debug(f"No matching webhooks for event: {event_type}")
            return True

        # Trigger sync if webhook indicates data change
        data_change_events = [
            'created', 'updated', 'deleted',
            'order.created', 'order.updated',
            'customer.created', 'customer.updated',
            'transaction.created',
        ]

        if any(evt in event_type.lower() for evt in data_change_events):
            # Determine entity type from event
            entity_type = event_type.split('.')[0] if '.' in event_type else None

            if entity_type:
                try:
                    await IntegrationService.sync_entity(integration_id, entity_type)
                except Exception as e:
                    logger.error(f"Webhook-triggered sync failed: {e}")

        return True

    # ==================== Helper Methods ====================

    @staticmethod
    def _calculate_health(integration_id: str) -> Dict:
        """Calculate integration health score"""
        recent_logs = sync_logs_store.find_by_integration(integration_id, limit=10)

        if not recent_logs:
            return {'score': 100, 'status': 'unknown', 'issues': []}

        # Calculate success rate
        successful = sum(1 for log in recent_logs if log.get('status') == SyncStatus.COMPLETED.value)
        success_rate = (successful / len(recent_logs)) * 100

        # Determine status
        if success_rate >= 90:
            status = 'healthy'
        elif success_rate >= 70:
            status = 'degraded'
        else:
            status = 'unhealthy'

        # Collect issues
        issues = []
        for log in recent_logs:
            if log.get('error_message'):
                issues.append({
                    'date': log.get('started_at'),
                    'error': log.get('error_message'),
                })

        return {
            'score': int(success_rate),
            'status': status,
            'issues': issues[:5],  # Last 5 issues
        }

    @staticmethod
    def _get_integration_stats(integration_id: str) -> Dict:
        """Get statistics for an integration"""
        logs = sync_logs_store.find_by_integration(integration_id, limit=100)

        total_syncs = len(logs)
        successful_syncs = sum(1 for log in logs if log.get('status') == SyncStatus.COMPLETED.value)
        total_records = sum(log.get('records_processed', 0) for log in logs)
        total_errors = sum(log.get('records_failed', 0) for log in logs)

        return {
            'total_syncs': total_syncs,
            'successful_syncs': successful_syncs,
            'failed_syncs': total_syncs - successful_syncs,
            'success_rate': (successful_syncs / total_syncs * 100) if total_syncs > 0 else 0,
            'total_records_processed': total_records,
            'total_errors': total_errors,
        }


class IntegrationScheduler:
    """Scheduler for automatic syncs"""

    def __init__(self):
        self.running = False
        self.tasks = {}

    async def start(self):
        """Start the scheduler"""
        self.running = True
        logger.info("Integration scheduler started")

        while self.running:
            await self._check_and_run_syncs()
            await asyncio.sleep(60)  # Check every minute

    async def stop(self):
        """Stop the scheduler"""
        self.running = False
        logger.info("Integration scheduler stopped")

    async def _check_and_run_syncs(self):
        """Check for and run due syncs"""
        all_integrations = []

        # Get all active integrations
        # Note: In production, this would query the database
        for org_id in integrations_store._data.keys():
            integrations = integrations_store.find_by_organization(org_id)
            all_integrations.extend(integrations)

        for integration in all_integrations:
            if integration.get('status') != IntegrationStatus.ACTIVE.value:
                continue

            sync_configs = sync_configs_store.find_by_integration(integration['id'])

            for config in sync_configs:
                if not config.get('enabled', True):
                    continue

                # Check if sync is due
                last_sync = config.get('last_sync_at')
                sync_interval = config.get('sync_interval', 3600)

                if last_sync:
                    last_sync_time = datetime.fromisoformat(last_sync)
                    next_sync = last_sync_time + timedelta(seconds=sync_interval)

                    if utc_now() < next_sync:
                        continue

                # Run sync
                try:
                    await IntegrationService.sync_entity(
                        integration['id'],
                        config['entity_type']
                    )
                except Exception as e:
                    logger.error(
                        f"Scheduled sync failed for {integration['id']}/{config['entity_type']}: {e}"
                    )
