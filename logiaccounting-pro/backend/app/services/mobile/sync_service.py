"""
Offline Sync Service
Handles synchronization of offline data and actions
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import uuid4
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SyncActionType(str, Enum):
    CREATE_TICKET = "create_ticket"
    REPLY_TICKET = "reply_ticket"
    CLOSE_TICKET = "close_ticket"
    ADD_NOTE = "add_note"
    UPDATE_PREFERENCES = "update_preferences"
    MARK_NOTIFICATION_READ = "mark_notification_read"


class SyncAction:
    """Represents an offline action to be synced."""

    def __init__(self, offline_id: str, action_type: str, data: Dict, created_at: str):
        self.offline_id = offline_id
        self.action_type = action_type
        self.data = data
        self.created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        self.server_id = None
        self.status = "pending"
        self.error = None
        self.processed_at = None


class SyncResult:
    """Result of processing a sync action."""

    def __init__(self, offline_id: str, status: str, server_id: str = None, error: str = None):
        self.offline_id = offline_id
        self.status = status
        self.server_id = server_id
        self.error = error


class OfflineSyncService:
    """Manages offline data synchronization."""

    def __init__(self):
        self._sync_tokens: Dict[str, Dict] = {}
        self._processed_actions: List[SyncAction] = []

    def process_sync(self, contact_id: str, customer_id: str, last_sync: Optional[str], pending_actions: List[Dict]) -> Dict[str, Any]:
        """Process sync request from mobile client."""
        sync_token = f"sync_{uuid4().hex[:16]}"
        server_time = datetime.utcnow()

        # Process pending offline actions
        results = []
        for action_data in pending_actions:
            action = SyncAction(
                offline_id=action_data["id"],
                action_type=action_data["type"],
                data=action_data.get("data", {}),
                created_at=action_data["created_at"],
            )

            result = self._process_action(action, contact_id, customer_id)
            results.append({
                "offline_id": result.offline_id,
                "server_id": result.server_id,
                "status": result.status,
                "error": result.error,
            })

        # Get updates since last sync
        updates = self._get_updates_since(customer_id, contact_id, last_sync)

        # Store sync state
        self._sync_tokens[contact_id] = {
            "token": sync_token,
            "timestamp": server_time,
        }

        return {
            "sync_token": sync_token,
            "server_time": server_time.isoformat() + "Z",
            "processed": results,
            "updates": updates,
            "conflicts": [],
        }

    def _process_action(self, action: SyncAction, contact_id: str, customer_id: str) -> SyncResult:
        """Process a single offline action."""
        try:
            handler = self._get_action_handler(action.action_type)
            if not handler:
                return SyncResult(
                    offline_id=action.offline_id,
                    status="error",
                    error=f"Unknown action type: {action.action_type}",
                )

            server_id = handler(action, contact_id, customer_id)

            action.server_id = server_id
            action.status = "success"
            action.processed_at = datetime.utcnow()
            self._processed_actions.append(action)

            return SyncResult(
                offline_id=action.offline_id,
                status="success",
                server_id=server_id,
            )

        except Exception as e:
            logger.error(f"Failed to process action {action.offline_id}: {e}")
            return SyncResult(
                offline_id=action.offline_id,
                status="error",
                error=str(e),
            )

    def _get_action_handler(self, action_type: str):
        """Get handler for action type."""
        handlers = {
            SyncActionType.CREATE_TICKET.value: self._handle_create_ticket,
            SyncActionType.REPLY_TICKET.value: self._handle_reply_ticket,
            SyncActionType.CLOSE_TICKET.value: self._handle_close_ticket,
            SyncActionType.ADD_NOTE.value: self._handle_add_note,
            SyncActionType.UPDATE_PREFERENCES.value: self._handle_update_preferences,
            SyncActionType.MARK_NOTIFICATION_READ.value: self._handle_mark_notification_read,
        }
        return handlers.get(action_type)

    def _handle_create_ticket(self, action: SyncAction, contact_id: str, customer_id: str) -> str:
        server_id = f"tkt_{uuid4().hex[:12]}"
        logger.info(f"Created ticket {server_id} from offline action {action.offline_id}")
        return server_id

    def _handle_reply_ticket(self, action: SyncAction, contact_id: str, customer_id: str) -> str:
        server_id = f"msg_{uuid4().hex[:12]}"
        logger.info(f"Added reply {server_id} from offline action {action.offline_id}")
        return server_id

    def _handle_close_ticket(self, action: SyncAction, contact_id: str, customer_id: str) -> str:
        ticket_id = action.data.get("ticket_id")
        logger.info(f"Closed ticket {ticket_id} from offline action {action.offline_id}")
        return ticket_id

    def _handle_add_note(self, action: SyncAction, contact_id: str, customer_id: str) -> str:
        server_id = f"note_{uuid4().hex[:12]}"
        logger.info(f"Added note {server_id} from offline action {action.offline_id}")
        return server_id

    def _handle_update_preferences(self, action: SyncAction, contact_id: str, customer_id: str) -> str:
        logger.info(f"Updated preferences from offline action {action.offline_id}")
        return "preferences_updated"

    def _handle_mark_notification_read(self, action: SyncAction, contact_id: str, customer_id: str) -> str:
        notification_id = action.data.get("notification_id")
        logger.info(f"Marked notification {notification_id} as read")
        return notification_id

    def _get_updates_since(self, customer_id: str, contact_id: str, last_sync: Optional[str]) -> Dict[str, List]:
        """Get data updates since last sync."""
        if not last_sync:
            return {
                "invoices": self._get_invoice_updates(customer_id, None),
                "projects": self._get_project_updates(customer_id, None),
                "tickets": self._get_ticket_updates(customer_id, None),
                "notifications": self._get_notification_updates(contact_id, None),
            }

        sync_time = datetime.fromisoformat(last_sync.replace("Z", "+00:00"))

        return {
            "invoices": self._get_invoice_updates(customer_id, sync_time),
            "projects": self._get_project_updates(customer_id, sync_time),
            "tickets": self._get_ticket_updates(customer_id, sync_time),
            "notifications": self._get_notification_updates(contact_id, sync_time),
        }

    def _get_invoice_updates(self, customer_id: str, since: Optional[datetime]) -> List[Dict]:
        return [
            {"id": "inv_001", "number": "INV-2024-0042", "amount": 5250.00, "status": "pending", "due_date": "2024-02-15", "_action": "update"},
        ]

    def _get_project_updates(self, customer_id: str, since: Optional[datetime]) -> List[Dict]:
        return [
            {"id": "proj_001", "name": "Website Redesign", "progress": 68, "status": "active", "_action": "update"},
        ]

    def _get_ticket_updates(self, customer_id: str, since: Optional[datetime]) -> List[Dict]:
        return []

    def _get_notification_updates(self, contact_id: str, since: Optional[datetime]) -> List[Dict]:
        return []

    def get_sync_status(self, contact_id: str) -> Dict:
        """Get current sync status for a contact."""
        sync_state = self._sync_tokens.get(contact_id)

        if not sync_state:
            return {"status": "never_synced", "last_sync": None}

        return {
            "status": "synced",
            "last_sync": sync_state["timestamp"].isoformat() + "Z",
            "sync_token": sync_state["token"],
        }


# Service instance
sync_service = OfflineSyncService()
