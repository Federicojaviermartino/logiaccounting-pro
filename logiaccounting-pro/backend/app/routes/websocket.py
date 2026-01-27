"""
WebSocket routes
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.services.websocket_manager import ws_manager
from app.utils.auth import decode_token
import json

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    """WebSocket connection endpoint"""

    # Validate token
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        role = payload.get("role", "user")
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await ws_manager.connect(websocket, user_id, role)

    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                # Handle ping/pong for keepalive
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)
