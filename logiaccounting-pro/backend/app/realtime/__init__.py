"""
Real-Time Collaboration Module
WebSocket-based features for collaborative work
"""

from .server import socketio, init_socketio, get_socketio

__all__ = ['socketio', 'init_socketio', 'get_socketio']
