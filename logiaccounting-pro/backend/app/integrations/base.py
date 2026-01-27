"""
Base Integration Class
Foundation for all integration providers
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class IntegrationStatus(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    SYNCING = "syncing"


class IntegrationCategory(str, Enum):
    PAYMENTS = "payments"
    ACCOUNTING = "accounting"
    AUTOMATION = "automation"
    COMMUNICATION = "communication"
    STORAGE = "storage"
    CRM = "crm"


class IntegrationCapability(str, Enum):
    OAUTH = "oauth"
    API_KEY = "api_key"
    WEBHOOKS = "webhooks"
    SYNC = "sync"
    REALTIME = "realtime"


class IntegrationError(Exception):
    """Base exception for integration errors."""

    def __init__(self, message: str, provider: str, code: str = None, details: Dict = None):
        self.message = message
        self.provider = provider
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class BaseIntegration(ABC):
    """Abstract base class for all integrations."""

    # Integration metadata (override in subclasses)
    PROVIDER_ID: str = ""
    PROVIDER_NAME: str = ""
    DESCRIPTION: str = ""
    CATEGORY: IntegrationCategory = IntegrationCategory.AUTOMATION
    ICON_URL: str = ""
    DOCS_URL: str = ""

    # Capabilities
    CAPABILITIES: List[IntegrationCapability] = []

    # OAuth settings (if applicable)
    OAUTH_AUTHORIZE_URL: str = ""
    OAUTH_TOKEN_URL: str = ""
    OAUTH_SCOPES: List[str] = []

    def __init__(self, credentials: Dict[str, Any] = None):
        self.credentials = credentials or {}
        self._client = None
        self._status = IntegrationStatus.DISCONNECTED
        self._last_sync = None
        self._error = None

    @property
    def status(self) -> IntegrationStatus:
        return self._status

    @property
    def is_connected(self) -> bool:
        return self._status == IntegrationStatus.CONNECTED

    @property
    def last_sync(self) -> Optional[datetime]:
        return self._last_sync

    def get_metadata(self) -> Dict[str, Any]:
        """Get integration metadata."""
        return {
            "id": self.PROVIDER_ID,
            "name": self.PROVIDER_NAME,
            "description": self.DESCRIPTION,
            "category": self.CATEGORY.value,
            "icon_url": self.ICON_URL,
            "docs_url": self.DOCS_URL,
            "capabilities": [c.value for c in self.CAPABILITIES],
            "requires_oauth": IntegrationCapability.OAUTH in self.CAPABILITIES,
            "supports_webhooks": IntegrationCapability.WEBHOOKS in self.CAPABILITIES,
            "supports_sync": IntegrationCapability.SYNC in self.CAPABILITIES,
        }

    def get_status_info(self) -> Dict[str, Any]:
        """Get current status information."""
        return {
            "status": self._status.value,
            "is_connected": self.is_connected,
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "error": self._error,
        }

    # ==================== Abstract Methods ====================

    @abstractmethod
    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """Establish connection with the provider."""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from the provider."""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if connection is valid."""
        pass

    @abstractmethod
    async def refresh_credentials(self) -> Dict[str, Any]:
        """Refresh OAuth tokens if needed."""
        pass

    # ==================== Optional Methods ====================

    def get_oauth_url(self, redirect_uri: str, state: str) -> str:
        """Generate OAuth authorization URL."""
        raise NotImplementedError("OAuth not supported")

    async def handle_oauth_callback(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Handle OAuth callback and exchange code for tokens."""
        raise NotImplementedError("OAuth not supported")

    async def handle_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """Process incoming webhook."""
        raise NotImplementedError("Webhooks not supported")

    async def sync(self, entity_type: str, direction: str = "pull") -> Dict[str, Any]:
        """Synchronize data with provider."""
        raise NotImplementedError("Sync not supported")

    # ==================== Helper Methods ====================

    def _set_status(self, status: IntegrationStatus, error: str = None):
        """Update integration status."""
        self._status = status
        self._error = error
        logger.info(f"[{self.PROVIDER_ID}] Status changed to: {status.value}")

    def _update_last_sync(self):
        """Update last sync timestamp."""
        self._last_sync = datetime.utcnow()

    def _log_error(self, message: str, exc: Exception = None):
        """Log integration error."""
        logger.error(f"[{self.PROVIDER_ID}] {message}", exc_info=exc)
        self._error = message

    def _validate_credentials(self, required_fields: List[str]) -> bool:
        """Validate that required credentials are present."""
        for field in required_fields:
            if not self.credentials.get(field):
                raise IntegrationError(
                    message=f"Missing required credential: {field}",
                    provider=self.PROVIDER_ID,
                    code="MISSING_CREDENTIAL",
                )
        return True


class WebhookEvent:
    """Represents an incoming webhook event."""

    def __init__(self, provider: str, event_type: str, payload: Dict, raw_payload: bytes = None):
        self.id = f"wh_{datetime.utcnow().timestamp()}"
        self.provider = provider
        self.event_type = event_type
        self.payload = payload
        self.raw_payload = raw_payload
        self.received_at = datetime.utcnow()
        self.processed = False
        self.error = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "provider": self.provider,
            "event_type": self.event_type,
            "payload": self.payload,
            "received_at": self.received_at.isoformat(),
            "processed": self.processed,
            "error": self.error,
        }


class SyncResult:
    """Result of a sync operation."""

    def __init__(self, entity_type: str, direction: str):
        self.entity_type = entity_type
        self.direction = direction
        self.started_at = datetime.utcnow()
        self.completed_at = None
        self.created = 0
        self.updated = 0
        self.deleted = 0
        self.skipped = 0
        self.errors = []

    def complete(self):
        self.completed_at = datetime.utcnow()

    @property
    def total_processed(self) -> int:
        return self.created + self.updated + self.deleted

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def to_dict(self) -> Dict:
        return {
            "entity_type": self.entity_type,
            "direction": self.direction,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created": self.created,
            "updated": self.updated,
            "deleted": self.deleted,
            "skipped": self.skipped,
            "total_processed": self.total_processed,
            "errors": self.errors[:10],
            "error_count": len(self.errors),
        }
