"""
Phase 14: Base Connector Framework
Abstract base class for all integration connectors
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple, Generator, AsyncGenerator
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging
import hashlib
import json

logger = logging.getLogger(__name__)


@dataclass
class ConnectorConfig:
    """Configuration for a connector"""
    client_id: str = None
    client_secret: str = None
    api_key: str = None
    api_secret: str = None
    access_token: str = None
    refresh_token: str = None
    instance_url: str = None
    environment: str = 'production'  # 'sandbox', 'production'
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncResult:
    """Result of a sync operation"""
    success: bool
    records_processed: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_failed: int = 0
    records_skipped: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)

    def add_error(self, record_id: str, error: str, details: Dict = None):
        self.errors.append({
            'record_id': record_id,
            'error': error,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        })
        self.records_failed += 1


@dataclass
class EntityField:
    """Describes a field in an entity"""
    name: str
    label: str
    type: str  # 'string', 'number', 'boolean', 'date', 'datetime', 'object', 'array'
    required: bool = False
    readonly: bool = False
    default: Any = None
    options: List[Dict] = None  # For enum/picklist fields


@dataclass
class EntitySchema:
    """Schema for an entity"""
    name: str
    label: str
    fields: List[EntityField]
    supports_create: bool = True
    supports_update: bool = True
    supports_delete: bool = True
    supports_bulk: bool = False
    id_field: str = 'id'


class BaseConnector(ABC):
    """Abstract base class for integration connectors"""

    # Connector metadata
    PROVIDER_NAME: str = 'base'
    PROVIDER_LABEL: str = 'Base Connector'
    CATEGORY: str = 'generic'

    # OAuth configuration
    OAUTH_AUTHORIZATION_URL: str = None
    OAUTH_TOKEN_URL: str = None
    OAUTH_SCOPES: List[str] = []

    # API configuration
    API_BASE_URL: str = None
    API_VERSION: str = None

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds

    # Supported entities
    SUPPORTED_ENTITIES: Dict[str, str] = {}
    # Maps local entity names to provider entity names
    # e.g., {'customer': 'Contact', 'invoice': 'Invoice'}

    def __init__(self, config: ConnectorConfig):
        self.config = config
        self._http_client = None

    # ==================== Authentication ====================

    @abstractmethod
    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """
        Get OAuth authorization URL

        Args:
            redirect_uri: Callback URL
            state: CSRF state token

        Returns:
            Authorization URL
        """
        pass

    @abstractmethod
    async def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchange authorization code for tokens

        Args:
            code: Authorization code
            redirect_uri: Callback URL (must match original)

        Returns:
            Dict with access_token, refresh_token, expires_in, etc.
        """
        pass

    @abstractmethod
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh expired access token

        Args:
            refresh_token: Refresh token

        Returns:
            Dict with new access_token, refresh_token (optional), expires_in
        """
        pass

    @abstractmethod
    async def test_connection(self) -> Tuple[bool, str]:
        """
        Test if connection is valid

        Returns:
            Tuple of (success, message)
        """
        pass

    # ==================== Entity Operations ====================

    @abstractmethod
    def get_entity_schema(self, entity_name: str) -> Optional[EntitySchema]:
        """
        Get schema for an entity

        Args:
            entity_name: Name of the entity

        Returns:
            EntitySchema with field definitions
        """
        pass

    @abstractmethod
    async def list_records(
        self,
        entity_name: str,
        filters: Dict[str, Any] = None,
        fields: List[str] = None,
        page: int = 1,
        page_size: int = 100,
        modified_since: datetime = None
    ) -> Tuple[List[Dict], bool]:
        """
        List records from the remote system

        Args:
            entity_name: Name of the entity
            filters: Filter conditions
            fields: Fields to retrieve
            page: Page number
            page_size: Records per page
            modified_since: Only records modified after this date

        Returns:
            Tuple of (records, has_more)
        """
        pass

    @abstractmethod
    async def get_record(self, entity_name: str, record_id: str) -> Optional[Dict]:
        """
        Get a single record by ID

        Args:
            entity_name: Name of the entity
            record_id: Record ID

        Returns:
            Record data or None
        """
        pass

    @abstractmethod
    async def create_record(self, entity_name: str, data: Dict) -> Dict:
        """
        Create a new record

        Args:
            entity_name: Name of the entity
            data: Record data

        Returns:
            Created record with ID
        """
        pass

    @abstractmethod
    async def update_record(self, entity_name: str, record_id: str, data: Dict) -> Dict:
        """
        Update an existing record

        Args:
            entity_name: Name of the entity
            record_id: Record ID
            data: Updated data

        Returns:
            Updated record
        """
        pass

    @abstractmethod
    async def delete_record(self, entity_name: str, record_id: str) -> bool:
        """
        Delete a record

        Args:
            entity_name: Name of the entity
            record_id: Record ID

        Returns:
            True if deleted successfully
        """
        pass

    # ==================== Bulk Operations ====================

    async def bulk_create(self, entity_name: str, records: List[Dict]) -> SyncResult:
        """
        Create multiple records (default: iterate over create_record)

        Args:
            entity_name: Name of the entity
            records: List of record data

        Returns:
            SyncResult with statistics
        """
        result = SyncResult(success=True)

        for record in records:
            try:
                await self.create_record(entity_name, record)
                result.records_created += 1
            except Exception as e:
                result.add_error(
                    record_id=record.get('id', 'unknown'),
                    error=str(e)
                )

        result.records_processed = result.records_created + result.records_failed
        result.success = result.records_failed == 0

        return result

    async def bulk_update(self, entity_name: str, records: List[Dict]) -> SyncResult:
        """
        Update multiple records (default: iterate over update_record)

        Args:
            entity_name: Name of the entity
            records: List of record data with IDs

        Returns:
            SyncResult with statistics
        """
        result = SyncResult(success=True)

        for record in records:
            record_id = record.get('id')
            if not record_id:
                result.add_error('unknown', 'Record ID is required')
                continue

            try:
                await self.update_record(entity_name, record_id, record)
                result.records_updated += 1
            except Exception as e:
                result.add_error(record_id=record_id, error=str(e))

        result.records_processed = result.records_updated + result.records_failed
        result.success = result.records_failed == 0

        return result

    # ==================== Webhooks ====================

    async def register_webhook(
        self,
        event_type: str,
        endpoint_url: str,
        secret: str = None
    ) -> Optional[str]:
        """
        Register a webhook with the provider

        Args:
            event_type: Event to subscribe to
            endpoint_url: URL to receive webhooks
            secret: Shared secret for verification

        Returns:
            Webhook ID from provider, or None if not supported
        """
        logger.warning(f"{self.PROVIDER_NAME} does not support webhook registration")
        return None

    async def unregister_webhook(self, webhook_id: str) -> bool:
        """
        Unregister a webhook

        Args:
            webhook_id: Provider webhook ID

        Returns:
            True if successful
        """
        logger.warning(f"{self.PROVIDER_NAME} does not support webhook unregistration")
        return False

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """
        Verify webhook signature

        Args:
            payload: Raw request body
            signature: Signature from headers
            secret: Shared secret

        Returns:
            True if signature is valid
        """
        # Default implementation - override for specific providers
        import hmac
        expected = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected, signature)

    # ==================== Utility Methods ====================

    def compute_record_hash(self, record: Dict) -> str:
        """Compute hash of record for change detection"""
        # Sort keys for consistent hashing
        normalized = json.dumps(record, sort_keys=True, default=str)
        return hashlib.sha256(normalized.encode()).hexdigest()

    async def iterate_all_records(
        self,
        entity_name: str,
        filters: Dict[str, Any] = None,
        modified_since: datetime = None,
        page_size: int = 100
    ) -> AsyncGenerator[Dict, None]:
        """
        Async iterator to fetch all records with pagination

        Yields:
            Individual records
        """
        page = 1
        has_more = True

        while has_more:
            records, has_more = await self.list_records(
                entity_name=entity_name,
                filters=filters,
                page=page,
                page_size=page_size,
                modified_since=modified_since
            )

            for record in records:
                yield record

            page += 1

    def get_remote_entity_name(self, local_entity: str) -> str:
        """Map local entity name to remote entity name"""
        return self.SUPPORTED_ENTITIES.get(local_entity, local_entity)

    def get_local_entity_name(self, remote_entity: str) -> Optional[str]:
        """Map remote entity name to local entity name"""
        for local, remote in self.SUPPORTED_ENTITIES.items():
            if remote == remote_entity:
                return local
        return None

    def supports_entity(self, entity_name: str) -> bool:
        """Check if connector supports an entity"""
        return entity_name in self.SUPPORTED_ENTITIES

    def get_supported_entities(self) -> List[str]:
        """Get list of supported local entity names"""
        return list(self.SUPPORTED_ENTITIES.keys())
