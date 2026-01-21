# LogiAccounting Pro - Phase 14 Tasks Part 1

## CORE INTEGRATION FRAMEWORK & OAUTH MANAGEMENT

---

## TASK 1: DATABASE MODELS

### 1.1 Integration Model

**File:** `backend/app/integrations/models/integration.py`

```python
"""
Integration Model
Represents a connection to an external system
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.extensions import db
from app.utils.encryption import encrypt_value, decrypt_value
import uuid


class Integration(db.Model):
    """External system integration connection"""
    
    __tablename__ = 'integrations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    
    # Integration Type
    provider = Column(String(50), nullable=False)
    # 'salesforce', 'hubspot', 'quickbooks', 'xero', 'shopify', etc.
    category = Column(String(50), nullable=False)
    # 'erp', 'crm', 'accounting', 'ecommerce', 'banking', 'shipping', 'payments'
    
    # Display
    name = Column(String(255), nullable=False)
    description = Column(Text)
    icon_url = Column(Text)
    
    # Connection Status
    status = Column(String(20), default='disconnected')
    # 'disconnected', 'connecting', 'connected', 'error', 'expired'
    
    # OAuth Credentials (encrypted)
    _oauth_access_token = Column('oauth_access_token_encrypted', Text)
    _oauth_refresh_token = Column('oauth_refresh_token_encrypted', Text)
    oauth_token_expires_at = Column(db.DateTime)
    oauth_scope = Column(Text)
    
    # API Credentials (encrypted)
    _api_key = Column('api_key_encrypted', Text)
    _api_secret = Column('api_secret_encrypted', Text)
    
    # Provider-specific config
    config = Column(JSONB, default=dict)
    # e.g., {"instance_url": "...", "company_id": "...", "realm_id": "..."}
    
    # Sync Settings
    sync_enabled = Column(Boolean, default=False)
    sync_direction = Column(String(20), default='bidirectional')
    sync_frequency_minutes = Column(Integer, default=60)
    last_sync_at = Column(db.DateTime)
    next_sync_at = Column(db.DateTime)
    
    # Error Tracking
    last_error = Column(Text)
    last_error_at = Column(db.DateTime)
    error_count = Column(Integer, default=0)
    
    # Metadata
    connected_by = Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    connected_at = Column(db.DateTime)
    created_at = Column(db.DateTime, default=datetime.utcnow)
    updated_at = Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship('Organization', backref='integrations')
    connected_by_user = relationship('User', foreign_keys=[connected_by])
    sync_configs = relationship('SyncConfig', back_populates='integration', cascade='all, delete-orphan')
    sync_logs = relationship('SyncLog', back_populates='integration', cascade='all, delete-orphan')
    webhooks = relationship('IntegrationWebhook', back_populates='integration', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('organization_id', 'provider', name='uq_org_provider'),
    )
    
    # ==================== Properties for encrypted fields ====================
    
    @property
    def oauth_access_token(self) -> Optional[str]:
        if self._oauth_access_token:
            return decrypt_value(self._oauth_access_token)
        return None
    
    @oauth_access_token.setter
    def oauth_access_token(self, value: str):
        if value:
            self._oauth_access_token = encrypt_value(value)
        else:
            self._oauth_access_token = None
    
    @property
    def oauth_refresh_token(self) -> Optional[str]:
        if self._oauth_refresh_token:
            return decrypt_value(self._oauth_refresh_token)
        return None
    
    @oauth_refresh_token.setter
    def oauth_refresh_token(self, value: str):
        if value:
            self._oauth_refresh_token = encrypt_value(value)
        else:
            self._oauth_refresh_token = None
    
    @property
    def api_key(self) -> Optional[str]:
        if self._api_key:
            return decrypt_value(self._api_key)
        return None
    
    @api_key.setter
    def api_key(self, value: str):
        if value:
            self._api_key = encrypt_value(value)
        else:
            self._api_key = None
    
    @property
    def api_secret(self) -> Optional[str]:
        if self._api_secret:
            return decrypt_value(self._api_secret)
        return None
    
    @api_secret.setter
    def api_secret(self, value: str):
        if value:
            self._api_secret = encrypt_value(value)
        else:
            self._api_secret = None
    
    # ==================== Methods ====================
    
    def is_token_expired(self) -> bool:
        """Check if OAuth token is expired"""
        if not self.oauth_token_expires_at:
            return False
        
        # Consider expired 5 minutes before actual expiry
        buffer = timedelta(minutes=5)
        return datetime.utcnow() >= (self.oauth_token_expires_at - buffer)
    
    def update_tokens(
        self,
        access_token: str,
        refresh_token: str = None,
        expires_in: int = None,
        scope: str = None
    ):
        """Update OAuth tokens"""
        self.oauth_access_token = access_token
        
        if refresh_token:
            self.oauth_refresh_token = refresh_token
        
        if expires_in:
            self.oauth_token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        if scope:
            self.oauth_scope = scope
        
        self.status = 'connected'
        self.last_error = None
        self.error_count = 0
    
    def mark_connected(self, user_id: str = None):
        """Mark integration as connected"""
        self.status = 'connected'
        self.connected_at = datetime.utcnow()
        if user_id:
            self.connected_by = user_id
        self.last_error = None
        self.error_count = 0
    
    def mark_error(self, error: str):
        """Mark integration with error"""
        self.status = 'error'
        self.last_error = error
        self.last_error_at = datetime.utcnow()
        self.error_count += 1
    
    def disconnect(self):
        """Disconnect integration"""
        self.status = 'disconnected'
        self._oauth_access_token = None
        self._oauth_refresh_token = None
        self.oauth_token_expires_at = None
        self._api_key = None
        self._api_secret = None
        self.connected_at = None
        self.connected_by = None
        self.sync_enabled = False
    
    def schedule_next_sync(self):
        """Schedule next sync based on frequency"""
        if self.sync_enabled and self.sync_frequency_minutes:
            self.next_sync_at = datetime.utcnow() + timedelta(minutes=self.sync_frequency_minutes)
        else:
            self.next_sync_at = None
    
    def record_sync(self):
        """Record that a sync occurred"""
        self.last_sync_at = datetime.utcnow()
        self.schedule_next_sync()
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a config value"""
        return self.config.get(key, default) if self.config else default
    
    def set_config_value(self, key: str, value: Any):
        """Set a config value"""
        if self.config is None:
            self.config = {}
        self.config[key] = value
    
    def to_dict(self, include_credentials: bool = False) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            'id': str(self.id),
            'organization_id': str(self.organization_id),
            'provider': self.provider,
            'category': self.category,
            'name': self.name,
            'description': self.description,
            'icon_url': self.icon_url,
            'status': self.status,
            'sync_enabled': self.sync_enabled,
            'sync_direction': self.sync_direction,
            'sync_frequency_minutes': self.sync_frequency_minutes,
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'next_sync_at': self.next_sync_at.isoformat() if self.next_sync_at else None,
            'last_error': self.last_error,
            'error_count': self.error_count,
            'connected_at': self.connected_at.isoformat() if self.connected_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'config': {k: v for k, v in (self.config or {}).items() if not k.startswith('_')},
        }
        
        if include_credentials:
            data['has_access_token'] = bool(self._oauth_access_token)
            data['has_refresh_token'] = bool(self._oauth_refresh_token)
            data['token_expires_at'] = self.oauth_token_expires_at.isoformat() if self.oauth_token_expires_at else None
            data['has_api_key'] = bool(self._api_key)
        
        return data


class OAuthState(db.Model):
    """OAuth state for CSRF protection"""
    
    __tablename__ = 'oauth_states'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    state = Column(String(64), nullable=False, unique=True)
    
    organization_id = Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    provider = Column(String(50), nullable=False)
    user_id = Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    
    redirect_uri = Column(Text)
    additional_data = Column(JSONB, default=dict)
    
    expires_at = Column(db.DateTime, nullable=False)
    created_at = Column(db.DateTime, default=datetime.utcnow)
    
    @classmethod
    def create(
        cls,
        organization_id: str,
        provider: str,
        user_id: str,
        redirect_uri: str = None,
        additional_data: Dict = None,
        expires_in_minutes: int = 10
    ) -> 'OAuthState':
        """Create a new OAuth state"""
        import secrets
        
        state = cls(
            state=secrets.token_urlsafe(32),
            organization_id=organization_id,
            provider=provider,
            user_id=user_id,
            redirect_uri=redirect_uri,
            additional_data=additional_data or {},
            expires_at=datetime.utcnow() + timedelta(minutes=expires_in_minutes)
        )
        
        db.session.add(state)
        db.session.commit()
        
        return state
    
    @classmethod
    def validate_and_consume(cls, state: str, provider: str) -> Optional['OAuthState']:
        """Validate state and remove it (one-time use)"""
        oauth_state = cls.query.filter(
            cls.state == state,
            cls.provider == provider,
            cls.expires_at > datetime.utcnow()
        ).first()
        
        if oauth_state:
            db.session.delete(oauth_state)
            db.session.commit()
        
        return oauth_state
```

### 1.2 Sync Configuration Model

**File:** `backend/app/integrations/models/sync_config.py`

```python
"""
Sync Configuration Model
Defines how entities are synchronized between systems
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.extensions import db
import uuid


class SyncConfig(db.Model):
    """Configuration for syncing a specific entity type"""
    
    __tablename__ = 'sync_configs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), db.ForeignKey('integrations.id', ondelete='CASCADE'), nullable=False)
    
    # Entity Mapping
    local_entity = Column(String(100), nullable=False)
    # 'customer', 'invoice', 'product', 'order', 'transaction', etc.
    remote_entity = Column(String(100), nullable=False)
    # Provider's entity name
    
    # Sync Settings
    sync_enabled = Column(Boolean, default=True)
    sync_direction = Column(String(20), default='bidirectional')
    # 'inbound', 'outbound', 'bidirectional'
    
    # Filters
    sync_filter = Column(JSONB, default=dict)
    # e.g., {"status": "active", "created_after": "2024-01-01"}
    
    # Conflict Resolution
    conflict_resolution = Column(String(50), default='last_write_wins')
    # 'last_write_wins', 'source_priority', 'manual_review', 'merge'
    priority_source = Column(String(20), default='local')
    # 'local', 'remote'
    
    # Timestamps
    last_sync_at = Column(db.DateTime)
    created_at = Column(db.DateTime, default=datetime.utcnow)
    updated_at = Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    integration = relationship('Integration', back_populates='sync_configs')
    field_mappings = relationship('FieldMapping', back_populates='sync_config', cascade='all, delete-orphan')
    sync_records = relationship('SyncRecord', back_populates='sync_config', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('integration_id', 'local_entity', 'remote_entity', name='uq_sync_config'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'integration_id': str(self.integration_id),
            'local_entity': self.local_entity,
            'remote_entity': self.remote_entity,
            'sync_enabled': self.sync_enabled,
            'sync_direction': self.sync_direction,
            'sync_filter': self.sync_filter,
            'conflict_resolution': self.conflict_resolution,
            'priority_source': self.priority_source,
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'field_mappings': [m.to_dict() for m in self.field_mappings],
        }


class FieldMapping(db.Model):
    """Field-level mapping between local and remote entities"""
    
    __tablename__ = 'field_mappings'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sync_config_id = Column(UUID(as_uuid=True), db.ForeignKey('sync_configs.id', ondelete='CASCADE'), nullable=False)
    
    # Field Definition
    local_field = Column(String(255), nullable=False)
    remote_field = Column(String(255), nullable=False)
    
    # Transformation
    transform_type = Column(String(50), default='direct')
    # 'direct', 'format', 'lookup', 'compute', 'constant'
    transform_config = Column(JSONB, default=dict)
    # e.g., {"format": "YYYY-MM-DD"}, {"lookup_table": "status_map"}
    
    # Direction
    direction = Column(String(20), default='bidirectional')
    # 'inbound', 'outbound', 'bidirectional'
    
    # Required
    is_required = Column(Boolean, default=False)
    default_value = Column(Text)
    
    created_at = Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sync_config = relationship('SyncConfig', back_populates='field_mappings')
    
    __table_args__ = (
        db.UniqueConstraint('sync_config_id', 'local_field', 'remote_field', name='uq_field_mapping'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'local_field': self.local_field,
            'remote_field': self.remote_field,
            'transform_type': self.transform_type,
            'transform_config': self.transform_config,
            'direction': self.direction,
            'is_required': self.is_required,
            'default_value': self.default_value,
        }


class SyncRecord(db.Model):
    """Track individual record sync state"""
    
    __tablename__ = 'sync_records'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), db.ForeignKey('integrations.id', ondelete='CASCADE'), nullable=False)
    sync_config_id = Column(UUID(as_uuid=True), db.ForeignKey('sync_configs.id', ondelete='CASCADE'), nullable=False)
    
    # Record IDs
    local_id = Column(UUID(as_uuid=True), nullable=False)
    remote_id = Column(String(255), nullable=False)
    
    # Sync State
    local_hash = Column(String(64))
    remote_hash = Column(String(64))
    
    # Timestamps
    local_updated_at = Column(db.DateTime)
    remote_updated_at = Column(db.DateTime)
    last_synced_at = Column(db.DateTime)
    
    # Status
    sync_status = Column(String(20), default='synced')
    # 'synced', 'pending_outbound', 'pending_inbound', 'conflict', 'error'
    
    created_at = Column(db.DateTime, default=datetime.utcnow)
    updated_at = Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sync_config = relationship('SyncConfig', back_populates='sync_records')
    
    __table_args__ = (
        db.UniqueConstraint('sync_config_id', 'local_id', name='uq_sync_record_local'),
        db.UniqueConstraint('sync_config_id', 'remote_id', name='uq_sync_record_remote'),
        db.Index('idx_sync_records_status', 'sync_status'),
    )
    
    @classmethod
    def find_by_local_id(cls, sync_config_id: str, local_id: str) -> Optional['SyncRecord']:
        return cls.query.filter(
            cls.sync_config_id == sync_config_id,
            cls.local_id == local_id
        ).first()
    
    @classmethod
    def find_by_remote_id(cls, sync_config_id: str, remote_id: str) -> Optional['SyncRecord']:
        return cls.query.filter(
            cls.sync_config_id == sync_config_id,
            cls.remote_id == remote_id
        ).first()
```

### 1.3 Sync Log Model

**File:** `backend/app/integrations/models/sync_log.py`

```python
"""
Sync Log Model
Tracks sync operations history
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.extensions import db
import uuid


class SyncLog(db.Model):
    """Log of sync operations"""
    
    __tablename__ = 'sync_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), db.ForeignKey('integrations.id', ondelete='CASCADE'), nullable=False)
    sync_config_id = Column(UUID(as_uuid=True), db.ForeignKey('sync_configs.id', ondelete='SET NULL'))
    
    # Sync Info
    sync_type = Column(String(20), nullable=False)
    # 'full', 'incremental', 'manual', 'webhook'
    direction = Column(String(20), nullable=False)
    # 'inbound', 'outbound'
    entity_type = Column(String(100))
    
    # Status
    status = Column(String(20), nullable=False, default='pending')
    # 'pending', 'running', 'completed', 'failed', 'partial'
    
    # Statistics
    records_processed = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    records_skipped = Column(Integer, default=0)
    
    # Errors
    errors = Column(JSONB, default=list)
    
    # Timing
    started_at = Column(db.DateTime)
    completed_at = Column(db.DateTime)
    duration_ms = Column(Integer)
    
    # Metadata
    triggered_by = Column(String(50))
    # 'schedule', 'webhook', 'manual', 'system'
    triggered_by_user_id = Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    
    created_at = Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    integration = relationship('Integration', back_populates='sync_logs')
    triggered_by_user = relationship('User')
    
    __table_args__ = (
        db.Index('idx_sync_logs_integration', 'integration_id'),
        db.Index('idx_sync_logs_created', 'created_at'),
    )
    
    def start(self):
        """Mark sync as started"""
        self.status = 'running'
        self.started_at = datetime.utcnow()
        db.session.commit()
    
    def complete(self, status: str = 'completed'):
        """Mark sync as completed"""
        self.status = status
        self.completed_at = datetime.utcnow()
        
        if self.started_at:
            self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)
        
        db.session.commit()
    
    def add_error(self, error: Dict[str, Any]):
        """Add an error to the log"""
        if self.errors is None:
            self.errors = []
        self.errors.append({
            **error,
            'timestamp': datetime.utcnow().isoformat()
        })
        self.records_failed += 1
    
    def increment_stats(self, created: int = 0, updated: int = 0, skipped: int = 0):
        """Increment statistics"""
        self.records_created += created
        self.records_updated += updated
        self.records_skipped += skipped
        self.records_processed += created + updated + skipped
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'integration_id': str(self.integration_id),
            'sync_type': self.sync_type,
            'direction': self.direction,
            'entity_type': self.entity_type,
            'status': self.status,
            'records_processed': self.records_processed,
            'records_created': self.records_created,
            'records_updated': self.records_updated,
            'records_failed': self.records_failed,
            'records_skipped': self.records_skipped,
            'errors': self.errors[:10] if self.errors else [],  # Limit errors in response
            'error_count': len(self.errors) if self.errors else 0,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_ms': self.duration_ms,
            'triggered_by': self.triggered_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
```

---

## TASK 2: BASE CONNECTOR FRAMEWORK

### 2.1 Base Connector Class

**File:** `backend/app/integrations/core/base_connector.py`

```python
"""
Base Connector
Abstract base class for all integration connectors
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple, Generator
from datetime import datetime
from dataclasses import dataclass, field
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
    def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Dict[str, Any]:
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
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh expired access token
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            Dict with new access_token, refresh_token (optional), expires_in
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test if connection is valid
        
        Returns:
            Tuple of (success, message)
        """
        pass
    
    # ==================== Entity Operations ====================
    
    @abstractmethod
    def get_entity_schema(self, entity_name: str) -> EntitySchema:
        """
        Get schema for an entity
        
        Args:
            entity_name: Name of the entity
            
        Returns:
            EntitySchema with field definitions
        """
        pass
    
    @abstractmethod
    def list_records(
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
    def get_record(self, entity_name: str, record_id: str) -> Optional[Dict]:
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
    def create_record(self, entity_name: str, data: Dict) -> Dict:
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
    def update_record(self, entity_name: str, record_id: str, data: Dict) -> Dict:
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
    def delete_record(self, entity_name: str, record_id: str) -> bool:
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
    
    def bulk_create(self, entity_name: str, records: List[Dict]) -> SyncResult:
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
                self.create_record(entity_name, record)
                result.records_created += 1
            except Exception as e:
                result.add_error(
                    record_id=record.get('id', 'unknown'),
                    error=str(e)
                )
        
        result.records_processed = result.records_created + result.records_failed
        result.success = result.records_failed == 0
        
        return result
    
    def bulk_update(self, entity_name: str, records: List[Dict]) -> SyncResult:
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
                self.update_record(entity_name, record_id, record)
                result.records_updated += 1
            except Exception as e:
                result.add_error(record_id=record_id, error=str(e))
        
        result.records_processed = result.records_updated + result.records_failed
        result.success = result.records_failed == 0
        
        return result
    
    # ==================== Webhooks ====================
    
    def register_webhook(
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
    
    def unregister_webhook(self, webhook_id: str) -> bool:
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
    
    def iterate_all_records(
        self,
        entity_name: str,
        filters: Dict[str, Any] = None,
        modified_since: datetime = None,
        page_size: int = 100
    ) -> Generator[Dict, None, None]:
        """
        Iterator to fetch all records with pagination
        
        Yields:
            Individual records
        """
        page = 1
        has_more = True
        
        while has_more:
            records, has_more = self.list_records(
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
```

### 2.2 OAuth Manager

**File:** `backend/app/integrations/core/oauth_manager.py`

```python
"""
OAuth Manager
Handles OAuth flows and token management for integrations
"""

from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlencode
import httpx
import logging

from app.extensions import db
from app.integrations.models.integration import Integration, OAuthState

logger = logging.getLogger(__name__)


# Provider OAuth configurations
OAUTH_CONFIGS = {
    'quickbooks': {
        'authorization_url': 'https://appcenter.intuit.com/connect/oauth2',
        'token_url': 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer',
        'scopes': ['com.intuit.quickbooks.accounting'],
    },
    'xero': {
        'authorization_url': 'https://login.xero.com/identity/connect/authorize',
        'token_url': 'https://identity.xero.com/connect/token',
        'scopes': ['openid', 'profile', 'email', 'accounting.transactions', 'accounting.contacts', 'accounting.settings'],
    },
    'salesforce': {
        'authorization_url': 'https://login.salesforce.com/services/oauth2/authorize',
        'token_url': 'https://login.salesforce.com/services/oauth2/token',
        'scopes': ['api', 'refresh_token', 'offline_access'],
    },
    'hubspot': {
        'authorization_url': 'https://app.hubspot.com/oauth/authorize',
        'token_url': 'https://api.hubapi.com/oauth/v1/token',
        'scopes': ['crm.objects.contacts.read', 'crm.objects.contacts.write', 'crm.objects.companies.read', 'crm.objects.deals.read'],
    },
    'shopify': {
        'authorization_url': 'https://{shop}.myshopify.com/admin/oauth/authorize',
        'token_url': 'https://{shop}.myshopify.com/admin/oauth/access_token',
        'scopes': ['read_products', 'write_products', 'read_orders', 'write_orders', 'read_customers', 'write_customers', 'read_inventory', 'write_inventory'],
    },
    'stripe': {
        'authorization_url': 'https://connect.stripe.com/oauth/authorize',
        'token_url': 'https://connect.stripe.com/oauth/token',
        'scopes': ['read_write'],
    },
}


class OAuthManager:
    """Manages OAuth authentication for integrations"""
    
    def __init__(self, provider: str):
        self.provider = provider
        self.config = OAUTH_CONFIGS.get(provider, {})
        
        if not self.config:
            raise ValueError(f"Unknown OAuth provider: {provider}")
    
    def get_authorization_url(
        self,
        client_id: str,
        redirect_uri: str,
        state: str,
        scopes: list = None,
        extra_params: Dict[str, str] = None
    ) -> str:
        """
        Generate OAuth authorization URL
        
        Args:
            client_id: OAuth client ID
            redirect_uri: Callback URL
            state: CSRF state token
            scopes: Override default scopes
            extra_params: Additional URL parameters
            
        Returns:
            Authorization URL
        """
        base_url = self.config['authorization_url']
        
        # Handle Shopify's shop-specific URL
        if self.provider == 'shopify' and extra_params and 'shop' in extra_params:
            base_url = base_url.format(shop=extra_params['shop'])
        
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'state': state,
            'scope': ' '.join(scopes or self.config.get('scopes', [])),
        }
        
        # Add extra params
        if extra_params:
            params.update({k: v for k, v in extra_params.items() if k != 'shop'})
        
        return f"{base_url}?{urlencode(params)}"
    
    async def exchange_code(
        self,
        code: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        extra_params: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for tokens
        
        Args:
            code: Authorization code
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: Callback URL (must match original)
            extra_params: Additional parameters
            
        Returns:
            Token response
        """
        token_url = self.config['token_url']
        
        # Handle Shopify's shop-specific URL
        if self.provider == 'shopify' and extra_params and 'shop' in extra_params:
            token_url = token_url.format(shop=extra_params['shop'])
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
        }
        
        # Some providers expect credentials in body, others in header
        if self.provider in ['quickbooks', 'xero']:
            # Basic auth header
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
            }
            auth = (client_id, client_secret)
        else:
            # Credentials in body
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
            }
            data['client_id'] = client_id
            data['client_secret'] = client_secret
            auth = None
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=data,
                headers=headers,
                auth=auth
            )
            
            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.text}")
                raise Exception(f"Token exchange failed: {response.status_code}")
            
            return response.json()
    
    async def refresh_token(
        self,
        refresh_token: str,
        client_id: str,
        client_secret: str,
        extra_params: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Refresh access token
        
        Args:
            refresh_token: Refresh token
            client_id: OAuth client ID
            client_secret: OAuth client secret
            extra_params: Additional parameters
            
        Returns:
            New token response
        """
        token_url = self.config['token_url']
        
        if self.provider == 'shopify' and extra_params and 'shop' in extra_params:
            token_url = token_url.format(shop=extra_params['shop'])
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }
        
        if self.provider in ['quickbooks', 'xero']:
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
            }
            auth = (client_id, client_secret)
        else:
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
            }
            data['client_id'] = client_id
            data['client_secret'] = client_secret
            auth = None
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=data,
                headers=headers,
                auth=auth
            )
            
            if response.status_code != 200:
                logger.error(f"Token refresh failed: {response.text}")
                raise Exception(f"Token refresh failed: {response.status_code}")
            
            return response.json()


class IntegrationOAuthService:
    """High-level OAuth service for integrations"""
    
    @staticmethod
    def initiate_oauth(
        organization_id: str,
        provider: str,
        user_id: str,
        redirect_uri: str,
        extra_params: Dict[str, str] = None
    ) -> str:
        """
        Initiate OAuth flow
        
        Args:
            organization_id: Organization ID
            provider: Provider name
            user_id: User initiating connection
            redirect_uri: Callback URL
            extra_params: Additional parameters
            
        Returns:
            Authorization URL
        """
        import os
        
        # Create state
        oauth_state = OAuthState.create(
            organization_id=organization_id,
            provider=provider,
            user_id=user_id,
            redirect_uri=redirect_uri,
            additional_data=extra_params
        )
        
        # Get OAuth manager
        oauth_manager = OAuthManager(provider)
        
        # Get client credentials from environment
        client_id = os.getenv(f'{provider.upper()}_CLIENT_ID')
        
        if not client_id:
            raise ValueError(f"Missing {provider.upper()}_CLIENT_ID environment variable")
        
        # Generate authorization URL
        return oauth_manager.get_authorization_url(
            client_id=client_id,
            redirect_uri=redirect_uri,
            state=oauth_state.state,
            extra_params=extra_params
        )
    
    @staticmethod
    async def complete_oauth(
        provider: str,
        code: str,
        state: str,
        redirect_uri: str
    ) -> Integration:
        """
        Complete OAuth flow and create/update integration
        
        Args:
            provider: Provider name
            code: Authorization code
            state: State token
            redirect_uri: Callback URL
            
        Returns:
            Integration instance
        """
        import os
        
        # Validate state
        oauth_state = OAuthState.validate_and_consume(state, provider)
        
        if not oauth_state:
            raise ValueError("Invalid or expired OAuth state")
        
        # Exchange code for tokens
        oauth_manager = OAuthManager(provider)
        
        client_id = os.getenv(f'{provider.upper()}_CLIENT_ID')
        client_secret = os.getenv(f'{provider.upper()}_CLIENT_SECRET')
        
        tokens = await oauth_manager.exchange_code(
            code=code,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            extra_params=oauth_state.additional_data
        )
        
        # Find or create integration
        integration = Integration.query.filter(
            Integration.organization_id == oauth_state.organization_id,
            Integration.provider == provider
        ).first()
        
        if not integration:
            integration = Integration(
                organization_id=oauth_state.organization_id,
                provider=provider,
                category=get_provider_category(provider),
                name=get_provider_label(provider),
            )
            db.session.add(integration)
        
        # Update tokens
        integration.update_tokens(
            access_token=tokens.get('access_token'),
            refresh_token=tokens.get('refresh_token'),
            expires_in=tokens.get('expires_in'),
            scope=tokens.get('scope')
        )
        
        # Store additional config
        if oauth_state.additional_data:
            for key, value in oauth_state.additional_data.items():
                integration.set_config_value(key, value)
        
        # Provider-specific config
        if provider == 'quickbooks' and 'realmId' in tokens:
            integration.set_config_value('realm_id', tokens['realmId'])
        elif provider == 'salesforce' and 'instance_url' in tokens:
            integration.set_config_value('instance_url', tokens['instance_url'])
        
        integration.mark_connected(str(oauth_state.user_id))
        
        db.session.commit()
        
        logger.info(f"OAuth completed for {provider}, integration {integration.id}")
        
        return integration
    
    @staticmethod
    async def refresh_integration_token(integration: Integration) -> bool:
        """
        Refresh token for an integration
        
        Args:
            integration: Integration instance
            
        Returns:
            True if successful
        """
        import os
        
        if not integration.oauth_refresh_token:
            logger.warning(f"No refresh token for integration {integration.id}")
            return False
        
        try:
            oauth_manager = OAuthManager(integration.provider)
            
            client_id = os.getenv(f'{integration.provider.upper()}_CLIENT_ID')
            client_secret = os.getenv(f'{integration.provider.upper()}_CLIENT_SECRET')
            
            tokens = await oauth_manager.refresh_token(
                refresh_token=integration.oauth_refresh_token,
                client_id=client_id,
                client_secret=client_secret,
                extra_params=integration.config
            )
            
            integration.update_tokens(
                access_token=tokens.get('access_token'),
                refresh_token=tokens.get('refresh_token', integration.oauth_refresh_token),
                expires_in=tokens.get('expires_in')
            )
            
            db.session.commit()
            
            logger.info(f"Token refreshed for integration {integration.id}")
            return True
            
        except Exception as e:
            logger.error(f"Token refresh failed for integration {integration.id}: {e}")
            integration.mark_error(str(e))
            db.session.commit()
            return False


def get_provider_category(provider: str) -> str:
    """Get category for a provider"""
    categories = {
        'quickbooks': 'accounting',
        'xero': 'accounting',
        'sage': 'accounting',
        'freshbooks': 'accounting',
        'salesforce': 'crm',
        'hubspot': 'crm',
        'zoho': 'crm',
        'pipedrive': 'crm',
        'shopify': 'ecommerce',
        'woocommerce': 'ecommerce',
        'magento': 'ecommerce',
        'bigcommerce': 'ecommerce',
        'sap': 'erp',
        'netsuite': 'erp',
        'dynamics': 'erp',
        'plaid': 'banking',
        'stripe': 'payments',
        'paypal': 'payments',
        'fedex': 'shipping',
        'ups': 'shipping',
        'dhl': 'shipping',
    }
    return categories.get(provider, 'generic')


def get_provider_label(provider: str) -> str:
    """Get display label for a provider"""
    labels = {
        'quickbooks': 'QuickBooks Online',
        'xero': 'Xero',
        'sage': 'Sage',
        'salesforce': 'Salesforce',
        'hubspot': 'HubSpot',
        'zoho': 'Zoho CRM',
        'shopify': 'Shopify',
        'woocommerce': 'WooCommerce',
        'plaid': 'Plaid',
        'stripe': 'Stripe',
        'fedex': 'FedEx',
        'ups': 'UPS',
        'dhl': 'DHL',
    }
    return labels.get(provider, provider.title())
```

---

## TASK 3: DATA TRANSFORMER

### 3.1 Data Transformer Service

**File:** `backend/app/integrations/core/transformer.py`

```python
"""
Data Transformer
Transforms data between local and remote formats using field mappings
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from decimal import Decimal
import re
import logging

from app.integrations.models.sync_config import FieldMapping

logger = logging.getLogger(__name__)


class DataTransformer:
    """Transforms data between systems using field mappings"""
    
    def __init__(self, field_mappings: List[FieldMapping]):
        self.field_mappings = field_mappings
        self._lookup_tables = {}
    
    def transform_to_remote(self, local_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform local data to remote format
        
        Args:
            local_data: Local record data
            
        Returns:
            Transformed data for remote system
        """
        remote_data = {}
        
        for mapping in self.field_mappings:
            if mapping.direction == 'inbound':
                continue  # Skip inbound-only mappings
            
            local_value = self._get_nested_value(local_data, mapping.local_field)
            
            # Apply transformation
            transformed_value = self._apply_transform(
                value=local_value,
                transform_type=mapping.transform_type,
                transform_config=mapping.transform_config,
                direction='outbound'
            )
            
            # Handle default value
            if transformed_value is None and mapping.default_value is not None:
                transformed_value = mapping.default_value
            
            # Skip if required field is missing
            if mapping.is_required and transformed_value is None:
                raise ValueError(f"Required field missing: {mapping.local_field}")
            
            # Set value in remote data
            if transformed_value is not None:
                self._set_nested_value(remote_data, mapping.remote_field, transformed_value)
        
        return remote_data
    
    def transform_to_local(self, remote_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform remote data to local format
        
        Args:
            remote_data: Remote record data
            
        Returns:
            Transformed data for local system
        """
        local_data = {}
        
        for mapping in self.field_mappings:
            if mapping.direction == 'outbound':
                continue  # Skip outbound-only mappings
            
            remote_value = self._get_nested_value(remote_data, mapping.remote_field)
            
            # Apply transformation (reverse direction)
            transformed_value = self._apply_transform(
                value=remote_value,
                transform_type=mapping.transform_type,
                transform_config=mapping.transform_config,
                direction='inbound'
            )
            
            # Handle default value
            if transformed_value is None and mapping.default_value is not None:
                transformed_value = mapping.default_value
            
            # Set value in local data
            if transformed_value is not None:
                self._set_nested_value(local_data, mapping.local_field, transformed_value)
        
        return local_data
    
    def _apply_transform(
        self,
        value: Any,
        transform_type: str,
        transform_config: Dict[str, Any],
        direction: str
    ) -> Any:
        """
        Apply transformation to a value
        
        Args:
            value: Value to transform
            transform_type: Type of transformation
            transform_config: Transformation configuration
            direction: 'inbound' or 'outbound'
            
        Returns:
            Transformed value
        """
        if value is None:
            return None
        
        transform_config = transform_config or {}
        
        if transform_type == 'direct':
            return value
        
        elif transform_type == 'format':
            return self._transform_format(value, transform_config, direction)
        
        elif transform_type == 'lookup':
            return self._transform_lookup(value, transform_config, direction)
        
        elif transform_type == 'compute':
            return self._transform_compute(value, transform_config, direction)
        
        elif transform_type == 'constant':
            return transform_config.get('value')
        
        elif transform_type == 'concat':
            return self._transform_concat(value, transform_config)
        
        elif transform_type == 'split':
            return self._transform_split(value, transform_config)
        
        elif transform_type == 'cast':
            return self._transform_cast(value, transform_config)
        
        else:
            logger.warning(f"Unknown transform type: {transform_type}")
            return value
    
    def _transform_format(
        self,
        value: Any,
        config: Dict[str, Any],
        direction: str
    ) -> Any:
        """Format transformation (dates, numbers, etc.)"""
        format_type = config.get('type', 'string')
        
        if format_type == 'date':
            input_format = config.get('input_format', '%Y-%m-%d')
            output_format = config.get('output_format', '%Y-%m-%d')
            
            if direction == 'inbound':
                input_format, output_format = output_format, input_format
            
            if isinstance(value, str):
                try:
                    dt = datetime.strptime(value, input_format)
                    return dt.strftime(output_format)
                except ValueError:
                    return value
            elif isinstance(value, (datetime, date)):
                return value.strftime(output_format)
        
        elif format_type == 'number':
            decimals = config.get('decimals', 2)
            if isinstance(value, (int, float, Decimal)):
                return round(float(value), decimals)
            elif isinstance(value, str):
                try:
                    return round(float(value.replace(',', '')), decimals)
                except ValueError:
                    return None
        
        elif format_type == 'currency':
            # Remove currency symbols, convert to cents/pence if needed
            if isinstance(value, str):
                clean = re.sub(r'[^\d.-]', '', value)
                try:
                    return float(clean)
                except ValueError:
                    return None
        
        elif format_type == 'phone':
            # Normalize phone number format
            if isinstance(value, str):
                digits = re.sub(r'\D', '', value)
                return digits
        
        return value
    
    def _transform_lookup(
        self,
        value: Any,
        config: Dict[str, Any],
        direction: str
    ) -> Any:
        """Lookup table transformation"""
        lookup_table = config.get('table', {})
        default = config.get('default')
        
        if direction == 'inbound':
            # Reverse lookup
            lookup_table = {v: k for k, v in lookup_table.items()}
        
        return lookup_table.get(str(value), default)
    
    def _transform_compute(
        self,
        value: Any,
        config: Dict[str, Any],
        direction: str
    ) -> Any:
        """Computed transformation using expression"""
        expression = config.get('expression', 'value')
        
        # Simple expression evaluation (for security, only allow basic operations)
        allowed_operations = {
            'value': value,
            'upper': str(value).upper() if value else None,
            'lower': str(value).lower() if value else None,
            'trim': str(value).strip() if value else None,
            'bool': bool(value),
            'int': int(value) if value else None,
            'float': float(value) if value else None,
            'str': str(value) if value else None,
        }
        
        if expression in allowed_operations:
            return allowed_operations[expression]
        
        # Handle simple math
        if isinstance(value, (int, float)):
            if expression.startswith('multiply:'):
                factor = float(expression.split(':')[1])
                return value * factor
            elif expression.startswith('divide:'):
                divisor = float(expression.split(':')[1])
                return value / divisor if divisor != 0 else None
            elif expression.startswith('add:'):
                addend = float(expression.split(':')[1])
                return value + addend
        
        return value
    
    def _transform_concat(self, value: Any, config: Dict[str, Any]) -> str:
        """Concatenate multiple fields"""
        separator = config.get('separator', ' ')
        fields = config.get('fields', [])
        
        if isinstance(value, dict):
            parts = []
            for field in fields:
                part = self._get_nested_value(value, field)
                if part:
                    parts.append(str(part))
            return separator.join(parts)
        
        return str(value) if value else ''
    
    def _transform_split(self, value: Any, config: Dict[str, Any]) -> Any:
        """Split string and extract part"""
        separator = config.get('separator', ' ')
        index = config.get('index', 0)
        
        if isinstance(value, str):
            parts = value.split(separator)
            if 0 <= index < len(parts):
                return parts[index]
        
        return value
    
    def _transform_cast(self, value: Any, config: Dict[str, Any]) -> Any:
        """Cast value to specified type"""
        target_type = config.get('to', 'string')
        
        try:
            if target_type == 'string':
                return str(value) if value is not None else None
            elif target_type == 'integer':
                return int(float(value)) if value else None
            elif target_type == 'float':
                return float(value) if value else None
            elif target_type == 'boolean':
                if isinstance(value, str):
                    return value.lower() in ('true', 'yes', '1', 'on')
                return bool(value)
            elif target_type == 'array':
                if isinstance(value, list):
                    return value
                return [value] if value else []
        except (ValueError, TypeError):
            return None
        
        return value
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get value from nested dict using dot notation"""
        if not data or not path:
            return None
        
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list) and key.isdigit():
                index = int(key)
                current = current[index] if 0 <= index < len(current) else None
            else:
                return None
            
            if current is None:
                return None
        
        return current
    
    def _set_nested_value(self, data: Dict, path: str, value: Any):
        """Set value in nested dict using dot notation"""
        keys = path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
```

---

## Continue to Part 2 for Accounting & CRM Connectors

---

*Phase 14 Tasks Part 1 - LogiAccounting Pro*
*Core Integration Framework & OAuth Management*
