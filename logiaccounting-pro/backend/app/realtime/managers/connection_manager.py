"""
Connection Manager
Manages WebSocket connections and authentication
"""

import logging
import os
from typing import Dict, Optional, List, Set
from datetime import datetime
from jose import jwt, JWTError

from app.utils.datetime_utils import utc_now
from app.realtime.models.connection import Connection

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages all WebSocket connections"""

    def __init__(self):
        self.connections: Dict[str, Connection] = {}
        self.user_connections: Dict[str, Set[str]] = {}
        self.tenant_connections: Dict[str, Set[str]] = {}

    def authenticate(self, token: str) -> Optional[dict]:
        """
        Authenticate WebSocket connection using JWT token

        Args:
            token: JWT token from client

        Returns:
            User data if valid, None otherwise
        """
        try:
            if not token:
                return None

            if token.startswith('Bearer '):
                token = token[7:]

            secret_key = os.getenv('JWT_SECRET_KEY', 'super-secret-key-change-in-production')
            algorithm = os.getenv('JWT_ALGORITHM', 'HS256')

            decoded = jwt.decode(token, secret_key, algorithms=[algorithm])

            return {
                'user_id': decoded.get('sub'),
                'tenant_id': decoded.get('tenant_id', 'default'),
                'user_name': decoded.get('name', 'Unknown'),
                'user_email': decoded.get('email', ''),
                'role': decoded.get('role', 'user'),
            }

        except JWTError as e:
            logger.warning(f"WebSocket auth failed: {e}")
            return None

    def add_connection(
        self,
        sid: str,
        user_data: dict,
        device_type: str = 'desktop',
        browser: str = 'unknown',
        ip_address: str = ''
    ) -> Connection:
        """Add a new connection"""
        connection = Connection(
            sid=sid,
            user_id=user_data['user_id'],
            tenant_id=user_data['tenant_id'],
            user_name=user_data['user_name'],
            user_email=user_data.get('user_email', ''),
            connected_at=utc_now(),
            device_type=device_type,
            browser=browser,
            ip_address=ip_address,
        )

        self.connections[sid] = connection

        user_id = user_data['user_id']
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(sid)

        tenant_id = user_data['tenant_id']
        if tenant_id not in self.tenant_connections:
            self.tenant_connections[tenant_id] = set()
        self.tenant_connections[tenant_id].add(sid)

        logger.info(f"Connection added: {sid} for user {connection.user_id}")

        return connection

    def remove_connection(self, sid: str) -> Optional[Connection]:
        """Remove a connection"""
        connection = self.connections.pop(sid, None)

        if connection:
            user_id = connection.user_id
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(sid)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]

            tenant_id = connection.tenant_id
            if tenant_id in self.tenant_connections:
                self.tenant_connections[tenant_id].discard(sid)
                if not self.tenant_connections[tenant_id]:
                    del self.tenant_connections[tenant_id]

            logger.info(f"Connection removed: {sid}")

        return connection

    def get_connection(self, sid: str) -> Optional[Connection]:
        """Get connection by SID"""
        return self.connections.get(sid)

    def get_user_connections(self, user_id: str) -> List[Connection]:
        """Get all connections for a user"""
        sids = self.user_connections.get(user_id, set())
        return [self.connections[sid] for sid in sids if sid in self.connections]

    def get_user_sids(self, user_id: str) -> List[str]:
        """Get all SIDs for a user"""
        return list(self.user_connections.get(user_id, set()))

    def get_tenant_connections(self, tenant_id: str) -> List[Connection]:
        """Get all connections for a tenant"""
        sids = self.tenant_connections.get(tenant_id, set())
        return [self.connections[sid] for sid in sids if sid in self.connections]

    def get_tenant_sids(self, tenant_id: str) -> List[str]:
        """Get all SIDs for a tenant"""
        return list(self.tenant_connections.get(tenant_id, set()))

    def get_online_user_ids(self, tenant_id: str) -> Set[str]:
        """Get unique online user IDs for a tenant"""
        connections = self.get_tenant_connections(tenant_id)
        return {conn.user_id for conn in connections}

    def add_to_room(self, sid: str, room: str):
        """Add connection to a room"""
        connection = self.connections.get(sid)
        if connection:
            connection.add_room(room)

    def remove_from_room(self, sid: str, room: str):
        """Remove connection from a room"""
        connection = self.connections.get(sid)
        if connection:
            connection.remove_room(room)

    def get_connection_count(self) -> int:
        """Get total connection count"""
        return len(self.connections)

    def is_user_online(self, user_id: str) -> bool:
        """Check if user has any active connections"""
        return user_id in self.user_connections and len(self.user_connections[user_id]) > 0


_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Get connection manager singleton"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager
