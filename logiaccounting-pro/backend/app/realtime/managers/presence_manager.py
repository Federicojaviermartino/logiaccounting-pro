"""
Presence Manager
Manages user presence state
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta

from app.realtime.models.presence import PresenceData, PresenceStatus

logger = logging.getLogger(__name__)


class PresenceManager:
    """Manages user presence state"""

    AWAY_TIMEOUT_SECONDS = 300
    OFFLINE_TIMEOUT_SECONDS = 60

    def __init__(self):
        self.presence_data: Dict[str, Dict[str, PresenceData]] = {}

    def set_online(
        self,
        user_id: str,
        tenant_id: str,
        user_name: str,
        device_type: str = 'desktop',
        current_page: str = None
    ) -> PresenceData:
        """Set user as online"""
        presence = PresenceData(
            user_id=user_id,
            user_name=user_name,
            tenant_id=tenant_id,
            status=PresenceStatus.ONLINE,
            last_active_at=datetime.utcnow(),
            current_page=current_page,
            device_type=device_type,
        )

        if tenant_id not in self.presence_data:
            self.presence_data[tenant_id] = {}

        self.presence_data[tenant_id][user_id] = presence

        logger.debug(f"User {user_id} is now online")

        return presence

    def set_away(self, user_id: str, tenant_id: str) -> Optional[PresenceData]:
        """Set user as away"""
        presence = self.get_presence(user_id, tenant_id)

        if presence and presence.status == PresenceStatus.ONLINE:
            presence.set_away()
            logger.debug(f"User {user_id} is now away")
            return presence

        return presence

    def set_busy(self, user_id: str, tenant_id: str) -> Optional[PresenceData]:
        """Set user as busy (Do Not Disturb)"""
        presence = self.get_presence(user_id, tenant_id)

        if presence:
            presence.set_busy()
            logger.debug(f"User {user_id} is now busy")
            return presence

        return presence

    def set_offline(self, user_id: str, tenant_id: str) -> Optional[PresenceData]:
        """Set user as offline"""
        if tenant_id in self.presence_data and user_id in self.presence_data[tenant_id]:
            presence = self.presence_data[tenant_id].pop(user_id)
            presence.set_offline()
            logger.debug(f"User {user_id} is now offline")
            return presence

        return None

    def update_activity(
        self,
        user_id: str,
        tenant_id: str,
        current_page: str = None,
        current_entity_type: str = None,
        current_entity_id: str = None
    ) -> Optional[PresenceData]:
        """Update user's last activity and location"""
        presence = self.get_presence(user_id, tenant_id)

        if presence:
            presence.update_activity(current_page, current_entity_type, current_entity_id)
            return presence

        return None

    def get_presence(self, user_id: str, tenant_id: str) -> Optional[PresenceData]:
        """Get user's presence data"""
        if tenant_id not in self.presence_data:
            return None

        return self.presence_data[tenant_id].get(user_id)

    def get_online_users(self, tenant_id: str) -> List[Dict]:
        """Get all online users for a tenant"""
        if tenant_id not in self.presence_data:
            return []

        users = []
        for user_id, presence in self.presence_data[tenant_id].items():
            if presence.status != PresenceStatus.OFFLINE:
                users.append(presence.to_dict())

        return users

    def get_users_viewing_entity(
        self,
        tenant_id: str,
        entity_type: str,
        entity_id: str
    ) -> List[Dict]:
        """Get users currently viewing a specific entity"""
        online_users = self.get_online_users(tenant_id)

        return [
            user for user in online_users
            if user.get('current_entity_type') == entity_type and user.get('current_entity_id') == entity_id
        ]

    def check_inactive_users(self, tenant_id: str) -> List[str]:
        """Check for users that should be marked as away"""
        cutoff = datetime.utcnow() - timedelta(seconds=self.AWAY_TIMEOUT_SECONDS)

        away_users = []

        if tenant_id not in self.presence_data:
            return away_users

        for user_id, presence in self.presence_data[tenant_id].items():
            if presence.status == PresenceStatus.ONLINE:
                if presence.last_active_at < cutoff:
                    presence.set_away()
                    away_users.append(user_id)

        return away_users

    def get_online_count(self, tenant_id: str) -> int:
        """Get count of online users"""
        return len(self.get_online_users(tenant_id))


_presence_manager: Optional[PresenceManager] = None


def get_presence_manager() -> PresenceManager:
    """Get presence manager singleton"""
    global _presence_manager
    if _presence_manager is None:
        _presence_manager = PresenceManager()
    return _presence_manager
