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
from app.utils.datetime_utils import utc_now

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
        self.created_at = utc_now()
        self.updated_at = utc_now()
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

        connection.updated_at = utc_now()

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
                connection.connected_at = utc_now()
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
            connection.updated_at = utc_now()

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
                "tested_at": utc_now().isoformat(),
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
                connection.updated_at = utc_now()
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
