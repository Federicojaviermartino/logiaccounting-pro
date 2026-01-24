# Phase 29: Integration Hub - Part 1: Integration Core

## Overview
This part covers the core integration infrastructure including base classes, registry, connection manager, and credential handling.

---

## File 1: Base Integration Class
**Path:** `backend/app/integrations/base.py`

```python
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
            "errors": self.errors[:10],  # Limit errors in response
            "error_count": len(self.errors),
        }
```

---

## File 2: Integration Registry
**Path:** `backend/app/integrations/registry.py`

```python
"""
Integration Registry
Central catalog of available integrations
"""

from typing import Dict, Type, List, Optional
from app.integrations.base import BaseIntegration, IntegrationCategory
import logging

logger = logging.getLogger(__name__)


class IntegrationRegistry:
    """Manages registration and discovery of integrations."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._integrations: Dict[str, Type[BaseIntegration]] = {}
            cls._instance._initialized = False
        return cls._instance
    
    def register(self, integration_class: Type[BaseIntegration]):
        """Register an integration provider."""
        provider_id = integration_class.PROVIDER_ID
        
        if not provider_id:
            raise ValueError("Integration must have a PROVIDER_ID")
        
        if provider_id in self._integrations:
            logger.warning(f"Overwriting existing integration: {provider_id}")
        
        self._integrations[provider_id] = integration_class
        logger.info(f"Registered integration: {provider_id}")
    
    def get(self, provider_id: str) -> Optional[Type[BaseIntegration]]:
        """Get integration class by provider ID."""
        return self._integrations.get(provider_id)
    
    def create_instance(self, provider_id: str, credentials: Dict = None) -> Optional[BaseIntegration]:
        """Create an instance of an integration."""
        integration_class = self.get(provider_id)
        if integration_class:
            return integration_class(credentials=credentials)
        return None
    
    def list_all(self) -> List[Dict]:
        """List all registered integrations."""
        return [
            cls(credentials={}).get_metadata()
            for cls in self._integrations.values()
        ]
    
    def list_by_category(self, category: IntegrationCategory) -> List[Dict]:
        """List integrations by category."""
        return [
            cls(credentials={}).get_metadata()
            for cls in self._integrations.values()
            if cls.CATEGORY == category
        ]
    
    def get_categories(self) -> List[Dict]:
        """Get all categories with their integrations."""
        categories = {}
        
        for cls in self._integrations.values():
            cat = cls.CATEGORY.value
            if cat not in categories:
                categories[cat] = {
                    "id": cat,
                    "name": cat.replace("_", " ").title(),
                    "integrations": [],
                }
            categories[cat]["integrations"].append(cls(credentials={}).get_metadata())
        
        return list(categories.values())
    
    @property
    def provider_ids(self) -> List[str]:
        """Get list of registered provider IDs."""
        return list(self._integrations.keys())


# Global registry instance
registry = IntegrationRegistry()


def register_integration(cls: Type[BaseIntegration]) -> Type[BaseIntegration]:
    """Decorator to register an integration."""
    registry.register(cls)
    return cls
```

---

## File 3: Connection Manager
**Path:** `backend/app/integrations/connection.py`

```python
"""
Connection Manager
Manages integration connections and credentials
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import uuid4
import json
import logging
from cryptography.fernet import Fernet

from app.integrations.base import BaseIntegration, IntegrationStatus
from app.integrations.registry import registry

logger = logging.getLogger(__name__)


class Connection:
    """Represents a connection to an integration provider."""
    
    def __init__(self, customer_id: str, provider_id: str):
        self.id = f"conn_{uuid4().hex[:12]}"
        self.customer_id = customer_id
        self.provider_id = provider_id
        self.status = IntegrationStatus.DISCONNECTED
        self.credentials: Dict[str, Any] = {}
        self.settings: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.connected_at: Optional[datetime] = None
        self.last_sync_at: Optional[datetime] = None
        self.last_error: Optional[str] = None
        self.sync_enabled = True


class ConnectionManager:
    """Manages integration connections."""
    
    def __init__(self, encryption_key: str = None):
        self._connections: Dict[str, Connection] = {}
        self._instances: Dict[str, BaseIntegration] = {}
        
        # Initialize encryption for credentials
        if encryption_key:
            self._cipher = Fernet(encryption_key.encode())
        else:
            # Generate key for demo (should be from env in production)
            self._cipher = Fernet(Fernet.generate_key())
    
    def _encrypt(self, data: str) -> str:
        """Encrypt sensitive data."""
        return self._cipher.encrypt(data.encode()).decode()
    
    def _decrypt(self, data: str) -> str:
        """Decrypt sensitive data."""
        return self._cipher.decrypt(data.encode()).decode()
    
    def _encrypt_credentials(self, credentials: Dict) -> Dict:
        """Encrypt credential values."""
        encrypted = {}
        sensitive_keys = ["access_token", "refresh_token", "api_key", "secret", "password"]
        
        for key, value in credentials.items():
            if key in sensitive_keys and value:
                encrypted[key] = self._encrypt(str(value))
            else:
                encrypted[key] = value
        
        return encrypted
    
    def _decrypt_credentials(self, credentials: Dict) -> Dict:
        """Decrypt credential values."""
        decrypted = {}
        sensitive_keys = ["access_token", "refresh_token", "api_key", "secret", "password"]
        
        for key, value in credentials.items():
            if key in sensitive_keys and value:
                try:
                    decrypted[key] = self._decrypt(str(value))
                except Exception:
                    decrypted[key] = value
            else:
                decrypted[key] = value
        
        return decrypted
    
    async def create_connection(self, customer_id: str, provider_id: str, credentials: Dict = None, settings: Dict = None) -> Connection:
        """Create a new connection."""
        # Check if provider exists
        if not registry.get(provider_id):
            raise ValueError(f"Unknown provider: {provider_id}")
        
        # Check for existing connection
        existing = self.get_connection(customer_id, provider_id)
        if existing:
            # Update existing connection
            return await self.update_connection(existing.id, credentials, settings)
        
        # Create new connection
        connection = Connection(customer_id, provider_id)
        
        if credentials:
            connection.credentials = self._encrypt_credentials(credentials)
        
        if settings:
            connection.settings = settings
        
        self._connections[connection.id] = connection
        logger.info(f"Created connection {connection.id} for {provider_id}")
        
        return connection
    
    async def update_connection(self, connection_id: str, credentials: Dict = None, settings: Dict = None) -> Optional[Connection]:
        """Update connection credentials or settings."""
        connection = self._connections.get(connection_id)
        if not connection:
            return None
        
        if credentials:
            connection.credentials = self._encrypt_credentials(credentials)
        
        if settings:
            connection.settings.update(settings)
        
        connection.updated_at = datetime.utcnow()
        
        # Invalidate cached instance
        if connection_id in self._instances:
            del self._instances[connection_id]
        
        return connection
    
    async def connect(self, connection_id: str) -> bool:
        """Establish connection to provider."""
        connection = self._connections.get(connection_id)
        if not connection:
            return False
        
        try:
            connection.status = IntegrationStatus.CONNECTING
            
            # Get integration instance
            instance = self.get_instance(connection_id)
            if not instance:
                raise ValueError("Failed to create integration instance")
            
            # Attempt connection
            decrypted_creds = self._decrypt_credentials(connection.credentials)
            success = await instance.connect(decrypted_creds)
            
            if success:
                connection.status = IntegrationStatus.CONNECTED
                connection.connected_at = datetime.utcnow()
                connection.last_error = None
                logger.info(f"Connection {connection_id} established")
            else:
                connection.status = IntegrationStatus.ERROR
                connection.last_error = "Connection failed"
            
            return success
            
        except Exception as e:
            connection.status = IntegrationStatus.ERROR
            connection.last_error = str(e)
            logger.error(f"Connection {connection_id} failed: {e}")
            return False
    
    async def disconnect(self, connection_id: str) -> bool:
        """Disconnect from provider."""
        connection = self._connections.get(connection_id)
        if not connection:
            return False
        
        try:
            instance = self._instances.get(connection_id)
            if instance:
                await instance.disconnect()
                del self._instances[connection_id]
            
            connection.status = IntegrationStatus.DISCONNECTED
            connection.credentials = {}
            connection.updated_at = datetime.utcnow()
            
            logger.info(f"Connection {connection_id} disconnected")
            return True
            
        except Exception as e:
            logger.error(f"Disconnect failed for {connection_id}: {e}")
            return False
    
    async def test_connection(self, connection_id: str) -> Dict[str, Any]:
        """Test if connection is valid."""
        connection = self._connections.get(connection_id)
        if not connection:
            return {"success": False, "error": "Connection not found"}
        
        try:
            instance = self.get_instance(connection_id)
            if not instance:
                return {"success": False, "error": "Failed to create instance"}
            
            success = await instance.test_connection()
            
            return {
                "success": success,
                "status": connection.status.value,
                "tested_at": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def refresh_tokens(self, connection_id: str) -> bool:
        """Refresh OAuth tokens if needed."""
        connection = self._connections.get(connection_id)
        if not connection:
            return False
        
        try:
            instance = self.get_instance(connection_id)
            if not instance:
                return False
            
            new_credentials = await instance.refresh_credentials()
            
            if new_credentials:
                connection.credentials = self._encrypt_credentials(new_credentials)
                connection.updated_at = datetime.utcnow()
                logger.info(f"Tokens refreshed for connection {connection_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Token refresh failed for {connection_id}: {e}")
            return False
    
    def get_connection(self, customer_id: str, provider_id: str) -> Optional[Connection]:
        """Get connection by customer and provider."""
        for conn in self._connections.values():
            if conn.customer_id == customer_id and conn.provider_id == provider_id:
                return conn
        return None
    
    def get_connection_by_id(self, connection_id: str) -> Optional[Connection]:
        """Get connection by ID."""
        return self._connections.get(connection_id)
    
    def get_customer_connections(self, customer_id: str) -> List[Connection]:
        """Get all connections for a customer."""
        return [
            conn for conn in self._connections.values()
            if conn.customer_id == customer_id
        ]
    
    def get_instance(self, connection_id: str) -> Optional[BaseIntegration]:
        """Get or create integration instance for connection."""
        if connection_id in self._instances:
            return self._instances[connection_id]
        
        connection = self._connections.get(connection_id)
        if not connection:
            return None
        
        instance = registry.create_instance(
            connection.provider_id,
            self._decrypt_credentials(connection.credentials),
        )
        
        if instance:
            self._instances[connection_id] = instance
        
        return instance
    
    def connection_to_dict(self, connection: Connection, include_credentials: bool = False) -> Dict:
        """Convert connection to dictionary."""
        data = {
            "id": connection.id,
            "customer_id": connection.customer_id,
            "provider_id": connection.provider_id,
            "status": connection.status.value,
            "settings": connection.settings,
            "metadata": connection.metadata,
            "sync_enabled": connection.sync_enabled,
            "created_at": connection.created_at.isoformat(),
            "updated_at": connection.updated_at.isoformat(),
            "connected_at": connection.connected_at.isoformat() if connection.connected_at else None,
            "last_sync_at": connection.last_sync_at.isoformat() if connection.last_sync_at else None,
            "last_error": connection.last_error,
        }
        
        if include_credentials:
            # Only include non-sensitive credential info
            data["has_credentials"] = bool(connection.credentials)
        
        return data


# Global connection manager instance
connection_manager = ConnectionManager()
```

---

## File 4: Webhook Service
**Path:** `backend/app/services/integrations/webhook_service.py`

```python
"""
Webhook Service
Handles incoming and outgoing webhooks
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from uuid import uuid4
import hmac
import hashlib
import logging
import asyncio

logger = logging.getLogger(__name__)


class WebhookSubscription:
    """Represents a webhook subscription."""
    
    def __init__(self, customer_id: str, url: str, events: List[str]):
        self.id = f"whsub_{uuid4().hex[:12]}"
        self.customer_id = customer_id
        self.url = url
        self.events = events
        self.secret = uuid4().hex
        self.is_active = True
        self.created_at = datetime.utcnow()
        self.last_triggered_at: Optional[datetime] = None
        self.failure_count = 0


class WebhookDelivery:
    """Represents a webhook delivery attempt."""
    
    def __init__(self, subscription_id: str, event_type: str, payload: Dict):
        self.id = f"whdel_{uuid4().hex[:12]}"
        self.subscription_id = subscription_id
        self.event_type = event_type
        self.payload = payload
        self.status = "pending"
        self.attempts = 0
        self.response_code: Optional[int] = None
        self.response_body: Optional[str] = None
        self.created_at = datetime.utcnow()
        self.delivered_at: Optional[datetime] = None
        self.next_retry_at: Optional[datetime] = None


class WebhookService:
    """Manages webhooks for the platform."""
    
    # Event types we can emit
    EVENT_TYPES = [
        "invoice.created",
        "invoice.updated",
        "invoice.paid",
        "invoice.overdue",
        "invoice.cancelled",
        "payment.received",
        "payment.failed",
        "payment.refunded",
        "customer.created",
        "customer.updated",
        "customer.deleted",
        "project.created",
        "project.updated",
        "project.completed",
        "ticket.created",
        "ticket.updated",
        "ticket.resolved",
        "quote.created",
        "quote.accepted",
        "quote.rejected",
        "quote.expired",
    ]
    
    def __init__(self):
        self._subscriptions: Dict[str, WebhookSubscription] = {}
        self._deliveries: List[WebhookDelivery] = []
        self._event_handlers: Dict[str, List[Callable]] = {}
    
    # ==================== Subscriptions ====================
    
    def create_subscription(self, customer_id: str, url: str, events: List[str]) -> WebhookSubscription:
        """Create a new webhook subscription."""
        # Validate events
        invalid_events = [e for e in events if e not in self.EVENT_TYPES and e != "*"]
        if invalid_events:
            raise ValueError(f"Invalid event types: {invalid_events}")
        
        subscription = WebhookSubscription(customer_id, url, events)
        self._subscriptions[subscription.id] = subscription
        
        logger.info(f"Created webhook subscription {subscription.id} for {customer_id}")
        return subscription
    
    def get_subscription(self, subscription_id: str) -> Optional[WebhookSubscription]:
        """Get subscription by ID."""
        return self._subscriptions.get(subscription_id)
    
    def get_customer_subscriptions(self, customer_id: str) -> List[WebhookSubscription]:
        """Get all subscriptions for a customer."""
        return [
            s for s in self._subscriptions.values()
            if s.customer_id == customer_id and s.is_active
        ]
    
    def update_subscription(self, subscription_id: str, url: str = None, events: List[str] = None) -> Optional[WebhookSubscription]:
        """Update a subscription."""
        subscription = self._subscriptions.get(subscription_id)
        if not subscription:
            return None
        
        if url:
            subscription.url = url
        if events:
            subscription.events = events
        
        return subscription
    
    def delete_subscription(self, subscription_id: str) -> bool:
        """Delete (deactivate) a subscription."""
        subscription = self._subscriptions.get(subscription_id)
        if subscription:
            subscription.is_active = False
            return True
        return False
    
    def regenerate_secret(self, subscription_id: str) -> Optional[str]:
        """Regenerate webhook secret."""
        subscription = self._subscriptions.get(subscription_id)
        if subscription:
            subscription.secret = uuid4().hex
            return subscription.secret
        return None
    
    # ==================== Event Emission ====================
    
    async def emit(self, event_type: str, customer_id: str, payload: Dict):
        """Emit an event to all subscribed webhooks."""
        if event_type not in self.EVENT_TYPES:
            logger.warning(f"Unknown event type: {event_type}")
            return
        
        # Find matching subscriptions
        subscriptions = [
            s for s in self._subscriptions.values()
            if s.customer_id == customer_id
            and s.is_active
            and (event_type in s.events or "*" in s.events)
        ]
        
        # Create deliveries
        for subscription in subscriptions:
            delivery = WebhookDelivery(subscription.id, event_type, payload)
            self._deliveries.append(delivery)
            
            # Attempt delivery asynchronously
            asyncio.create_task(self._deliver(delivery, subscription))
        
        # Call internal handlers
        await self._call_handlers(event_type, payload)
        
        logger.info(f"Emitted {event_type} to {len(subscriptions)} subscribers")
    
    async def _deliver(self, delivery: WebhookDelivery, subscription: WebhookSubscription):
        """Deliver webhook to subscriber."""
        import aiohttp
        
        max_retries = 3
        retry_delays = [60, 300, 900]  # 1min, 5min, 15min
        
        while delivery.attempts < max_retries:
            delivery.attempts += 1
            
            try:
                # Prepare payload
                webhook_payload = {
                    "id": delivery.id,
                    "event": delivery.event_type,
                    "created_at": delivery.created_at.isoformat(),
                    "data": delivery.payload,
                }
                
                # Generate signature
                signature = self._generate_signature(
                    subscription.secret,
                    webhook_payload,
                )
                
                # Send request
                headers = {
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": signature,
                    "X-Webhook-ID": delivery.id,
                    "X-Webhook-Event": delivery.event_type,
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        subscription.url,
                        json=webhook_payload,
                        headers=headers,
                        timeout=30,
                    ) as response:
                        delivery.response_code = response.status
                        delivery.response_body = await response.text()
                        
                        if response.status < 300:
                            delivery.status = "delivered"
                            delivery.delivered_at = datetime.utcnow()
                            subscription.last_triggered_at = datetime.utcnow()
                            subscription.failure_count = 0
                            logger.info(f"Webhook {delivery.id} delivered successfully")
                            return
                        else:
                            logger.warning(f"Webhook {delivery.id} returned {response.status}")
                
            except Exception as e:
                logger.error(f"Webhook delivery failed: {e}")
                delivery.response_body = str(e)
            
            # Retry logic
            if delivery.attempts < max_retries:
                delay = retry_delays[delivery.attempts - 1]
                delivery.next_retry_at = datetime.utcnow()
                await asyncio.sleep(delay)
        
        # Mark as failed after all retries
        delivery.status = "failed"
        subscription.failure_count += 1
        
        # Disable subscription after too many failures
        if subscription.failure_count >= 10:
            subscription.is_active = False
            logger.warning(f"Subscription {subscription.id} disabled due to failures")
    
    def _generate_signature(self, secret: str, payload: Dict) -> str:
        """Generate HMAC signature for webhook payload."""
        import json
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={signature}"
    
    def verify_signature(self, secret: str, payload: Dict, signature: str) -> bool:
        """Verify webhook signature."""
        expected = self._generate_signature(secret, payload)
        return hmac.compare_digest(expected, signature)
    
    # ==================== Internal Handlers ====================
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register internal event handler."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    async def _call_handlers(self, event_type: str, payload: Dict):
        """Call internal handlers for event."""
        handlers = self._event_handlers.get(event_type, [])
        handlers.extend(self._event_handlers.get("*", []))
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_type, payload)
                else:
                    handler(event_type, payload)
            except Exception as e:
                logger.error(f"Event handler error: {e}")
    
    # ==================== Delivery History ====================
    
    def get_deliveries(self, subscription_id: str = None, limit: int = 50) -> List[Dict]:
        """Get webhook delivery history."""
        deliveries = self._deliveries
        
        if subscription_id:
            deliveries = [d for d in deliveries if d.subscription_id == subscription_id]
        
        deliveries = sorted(deliveries, key=lambda d: d.created_at, reverse=True)
        
        return [
            {
                "id": d.id,
                "subscription_id": d.subscription_id,
                "event_type": d.event_type,
                "status": d.status,
                "attempts": d.attempts,
                "response_code": d.response_code,
                "created_at": d.created_at.isoformat(),
                "delivered_at": d.delivered_at.isoformat() if d.delivered_at else None,
            }
            for d in deliveries[:limit]
        ]
    
    def subscription_to_dict(self, subscription: WebhookSubscription) -> Dict:
        """Convert subscription to dictionary."""
        return {
            "id": subscription.id,
            "url": subscription.url,
            "events": subscription.events,
            "is_active": subscription.is_active,
            "created_at": subscription.created_at.isoformat(),
            "last_triggered_at": subscription.last_triggered_at.isoformat() if subscription.last_triggered_at else None,
        }


# Service instance
webhook_service = WebhookService()
```

---

## File 5: Sync Service
**Path:** `backend/app/services/integrations/sync_service.py`

```python
"""
Sync Service
Handles data synchronization between LogiAccounting and integrations
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4
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
        job.started_at = datetime.utcnow()
        
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
            config.last_sync_at = datetime.utcnow()
            connection.last_sync_at = datetime.utcnow()
            
            logger.info(f"Sync job {job.id} completed successfully")
            
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            logger.error(f"Sync job {job.id} failed: {e}")
        
        finally:
            job.completed_at = datetime.utcnow()
            
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
            job.completed_at = datetime.utcnow()
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
```

---

## File 6: Integrations Init
**Path:** `backend/app/integrations/__init__.py`

```python
"""
Integrations Module
Central hub for all integration providers
"""

from app.integrations.base import (
    BaseIntegration,
    IntegrationStatus,
    IntegrationCategory,
    IntegrationCapability,
    IntegrationError,
    WebhookEvent,
    SyncResult,
)
from app.integrations.registry import registry, register_integration
from app.integrations.connection import connection_manager, Connection


__all__ = [
    # Base classes
    'BaseIntegration',
    'IntegrationStatus',
    'IntegrationCategory',
    'IntegrationCapability',
    'IntegrationError',
    'WebhookEvent',
    'SyncResult',
    
    # Registry
    'registry',
    'register_integration',
    
    # Connection
    'connection_manager',
    'Connection',
]


def init_integrations():
    """Initialize all integration providers."""
    # Import providers to register them
    from app.integrations.providers import stripe, paypal, quickbooks, xero, zapier, slack
    
    print(f"[Integrations] Registered {len(registry.provider_ids)} providers:")
    for provider_id in registry.provider_ids:
        print(f"  - {provider_id}")
```

---

## Summary Part 1

| File | Description | Lines |
|------|-------------|-------|
| `base.py` | Base integration class & utilities | ~280 |
| `registry.py` | Integration registry | ~100 |
| `connection.py` | Connection manager | ~300 |
| `webhook_service.py` | Webhook handling | ~320 |
| `sync_service.py` | Sync service | ~280 |
| `__init__.py` | Module initialization | ~50 |
| **Total** | | **~1,330 lines** |
