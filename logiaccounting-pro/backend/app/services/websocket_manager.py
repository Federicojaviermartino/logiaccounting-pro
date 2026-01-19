"""
WebSocket Connection Manager
Real-time notifications
"""

from typing import Dict, List, Set
from fastapi import WebSocket
import json
from datetime import datetime


class WebSocketManager:
    """Manages WebSocket connections and broadcasting"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}  # user_id -> websocket
        self.user_roles: Dict[str, str] = {}  # user_id -> role

    async def connect(self, websocket: WebSocket, user_id: str, role: str):
        """Accept and store connection"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_roles[user_id] = role
        print(f"WebSocket connected: {user_id} ({role})")

    def disconnect(self, user_id: str):
        """Remove connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_roles:
            del self.user_roles[user_id]
        print(f"WebSocket disconnected: {user_id}")

    async def send_to_user(self, user_id: str, message: dict):
        """Send message to specific user"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                print(f"Error sending to {user_id}: {e}")
                self.disconnect(user_id)

    async def send_to_role(self, role: str, message: dict):
        """Send message to all users with specific role"""
        for user_id, user_role in self.user_roles.items():
            if user_role == role:
                await self.send_to_user(user_id, message)

    async def broadcast(self, message: dict):
        """Send message to all connected users"""
        for user_id in list(self.active_connections.keys()):
            await self.send_to_user(user_id, message)

    async def notify(
        self,
        event_type: str,
        data: dict,
        target_users: List[str] = None,
        target_roles: List[str] = None
    ):
        """Send notification to targeted users/roles"""
        message = {
            "type": "notification",
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }

        if target_users:
            for user_id in target_users:
                await self.send_to_user(user_id, message)
        elif target_roles:
            for role in target_roles:
                await self.send_to_role(role, message)
        else:
            await self.broadcast(message)

    def get_connected_users(self) -> List[str]:
        """Get list of connected user IDs"""
        return list(self.active_connections.keys())


ws_manager = WebSocketManager()


# Notification event types and helpers
async def notify_transaction_created(transaction: dict, user_id: str):
    await ws_manager.notify(
        "transaction.created",
        {"transaction": transaction},
        target_roles=["admin"]
    )

async def notify_payment_due(payment: dict):
    await ws_manager.notify(
        "payment.due_soon",
        {"payment": payment},
        target_roles=["admin"]
    )

async def notify_low_stock(material: dict):
    await ws_manager.notify(
        "inventory.low_stock",
        {"material": material},
        target_roles=["admin"]
    )

async def notify_approval_required(approval: dict, approver_ids: List[str]):
    await ws_manager.notify(
        "approval.required",
        {"approval": approval},
        target_users=approver_ids
    )

async def notify_budget_threshold(budget: dict, threshold: int):
    await ws_manager.notify(
        "budget.threshold_reached",
        {"budget": budget, "threshold": threshold},
        target_roles=["admin"]
    )
