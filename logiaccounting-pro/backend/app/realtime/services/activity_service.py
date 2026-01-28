"""
Activity Service
Create and retrieve activity feed items
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from app.utils.datetime_utils import utc_now
from app.realtime.server import get_socketio
from app.realtime.utils.message_types import MessageType

logger = logging.getLogger(__name__)

activities_db: Dict[str, List[Dict]] = {}


ACTION_LABELS = {
    'created': 'created',
    'updated': 'updated',
    'deleted': 'deleted',
    'commented': 'commented on',
    'assigned': 'assigned',
    'completed': 'completed',
    'sent': 'sent',
    'paid': 'marked as paid',
    'uploaded': 'uploaded',
    'shared': 'shared',
}


class ActivityService:
    """Service for activity feed operations"""

    @staticmethod
    async def log_activity(
        tenant_id: str,
        user_id: str,
        user_name: str,
        action: str,
        entity_type: str,
        entity_id: str,
        entity_name: str = None,
        details: Dict[str, Any] = None,
        visibility: str = 'team',
        visible_to: List[str] = None,
        broadcast: bool = True,
    ) -> Dict[str, Any]:
        """Log an activity and optionally broadcast it"""
        activity = {
            'id': str(uuid.uuid4()),
            'tenant_id': tenant_id,
            'user_id': user_id,
            'user_name': user_name,
            'action': action,
            'action_label': ACTION_LABELS.get(action, action),
            'entity_type': entity_type,
            'entity_id': entity_id,
            'entity_name': entity_name,
            'details': details,
            'visibility': visibility,
            'visible_to': visible_to,
            'created_at': utc_now().isoformat(),
        }

        if tenant_id not in activities_db:
            activities_db[tenant_id] = []

        activities_db[tenant_id].insert(0, activity)

        if len(activities_db[tenant_id]) > 1000:
            activities_db[tenant_id] = activities_db[tenant_id][:1000]

        if broadcast:
            await ActivityService._broadcast_activity(activity)

        logger.debug(f"Activity logged: {user_name} {action} {entity_type} {entity_id}")

        return activity

    @staticmethod
    async def _broadcast_activity(activity: Dict[str, Any]):
        """Broadcast activity to relevant users"""
        try:
            sio = get_socketio()
            if not sio:
                logger.warning("Socket.IO not initialized")
                return

            tenant_room = f"tenant:{activity['tenant_id']}"

            await sio.emit(
                MessageType.ACTIVITY.value,
                activity,
                room=tenant_room,
            )

        except Exception as e:
            logger.error(f"Activity broadcast failed: {e}")

    @staticmethod
    def get_feed(
        tenant_id: str,
        user_id: str = None,
        entity_type: str = None,
        entity_id: str = None,
        limit: int = 50,
        offset: int = 0,
        since: datetime = None,
    ) -> List[Dict[str, Any]]:
        """Get activity feed"""
        if tenant_id not in activities_db:
            return []

        activities = activities_db[tenant_id]

        if user_id:
            activities = [
                a for a in activities
                if a.get('visibility') in ['team', 'public']
                or a.get('user_id') == user_id
                or (a.get('visible_to') and user_id in a.get('visible_to', []))
            ]

        if entity_type:
            activities = [a for a in activities if a.get('entity_type') == entity_type]

        if entity_id:
            activities = [a for a in activities if a.get('entity_id') == entity_id]

        if since:
            since_str = since.isoformat()
            activities = [a for a in activities if a.get('created_at', '') > since_str]

        return activities[offset:offset + limit]

    @staticmethod
    def get_entity_activity(
        tenant_id: str,
        entity_type: str,
        entity_id: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get activity for a specific entity"""
        if tenant_id not in activities_db:
            return []

        activities = [
            a for a in activities_db[tenant_id]
            if a.get('entity_type') == entity_type and a.get('entity_id') == entity_id
        ]

        return activities[:limit]

    @staticmethod
    def get_user_activity(
        tenant_id: str,
        user_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get activity by a specific user"""
        if tenant_id not in activities_db:
            return []

        activities = [
            a for a in activities_db[tenant_id]
            if a.get('user_id') == user_id
        ]

        return activities[:limit]


async def log_invoice_created(tenant_id: str, user_id: str, user_name: str, invoice_id: str, invoice_number: str):
    """Log invoice creation activity"""
    return await ActivityService.log_activity(
        tenant_id=tenant_id,
        user_id=user_id,
        user_name=user_name,
        action='created',
        entity_type='invoice',
        entity_id=invoice_id,
        entity_name=f'Invoice #{invoice_number}',
    )


async def log_payment_received(tenant_id: str, user_id: str, user_name: str, payment_id: str, amount: float, invoice_number: str):
    """Log payment received activity"""
    return await ActivityService.log_activity(
        tenant_id=tenant_id,
        user_id=user_id,
        user_name=user_name,
        action='paid',
        entity_type='payment',
        entity_id=payment_id,
        entity_name=f'Payment ${amount:,.2f}',
        details={
            'amount': amount,
            'invoice_number': invoice_number,
        },
    )


async def log_project_completed(tenant_id: str, user_id: str, user_name: str, project_id: str, project_name: str):
    """Log project completion activity"""
    return await ActivityService.log_activity(
        tenant_id=tenant_id,
        user_id=user_id,
        user_name=user_name,
        action='completed',
        entity_type='project',
        entity_id=project_id,
        entity_name=project_name,
    )
