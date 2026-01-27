"""
WebSocket Server
Socket.IO server with Redis adapter for horizontal scaling
"""

import os
import logging
from typing import Optional
import socketio

logger = logging.getLogger(__name__)

sio: Optional[socketio.AsyncServer] = None


def create_socketio() -> socketio.AsyncServer:
    """Create Socket.IO async server instance"""
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    cors_origins = os.getenv('CORS_ORIGINS', '*').split(',')

    mgr = socketio.AsyncRedisManager(redis_url) if redis_url else None

    server = socketio.AsyncServer(
        async_mode='asgi',
        cors_allowed_origins=cors_origins,
        client_manager=mgr,
        logger=True,
        engineio_logger=True,
        ping_timeout=30,
        ping_interval=25,
        max_http_buffer_size=1024 * 1024,
    )

    return server


def init_socketio(app) -> socketio.ASGIApp:
    """Initialize Socket.IO with ASGI app"""
    global sio

    sio = create_socketio()

    from app.realtime.handlers import register_handlers
    register_handlers(sio)

    socket_app = socketio.ASGIApp(sio, app)

    logger.info("Socket.IO server initialized")

    return socket_app


def get_socketio() -> Optional[socketio.AsyncServer]:
    """Get Socket.IO instance"""
    return sio


socketio_server = sio
