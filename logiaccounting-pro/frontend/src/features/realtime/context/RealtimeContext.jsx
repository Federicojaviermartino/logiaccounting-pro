/**
 * Realtime Context
 * Provides Socket.IO connection and real-time features to entire app
 */

import { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { io } from 'socket.io-client';
import { useAuth } from '../../../contexts/AuthContext';

const RealtimeContext = createContext(null);

const SOCKET_URL = import.meta.env.VITE_WEBSOCKET_URL || window.location.origin;

export function RealtimeProvider({ children }) {
  const { token, isAuthenticated } = useAuth();
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  const [onlineUsers, setOnlineUsers] = useState([]);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  useEffect(() => {
    if (!isAuthenticated || !token) {
      return;
    }

    const socketInstance = io(SOCKET_URL, {
      auth: { token },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: maxReconnectAttempts,
    });

    socketInstance.on('connect', () => {
      console.log('Realtime connected');
      setIsConnected(true);
      setConnectionError(null);
      reconnectAttempts.current = 0;
    });

    socketInstance.on('disconnect', (reason) => {
      console.log('Realtime disconnected:', reason);
      setIsConnected(false);
    });

    socketInstance.on('connect_error', (error) => {
      console.error('Realtime connection error:', error);
      setConnectionError(error.message);
      reconnectAttempts.current += 1;
    });

    socketInstance.on('error', (error) => {
      console.error('Realtime error:', error);
      setConnectionError(error.message);
    });

    socketInstance.on('presence:list', (data) => {
      setOnlineUsers(data.users || []);
    });

    socketInstance.on('presence:user_joined', (data) => {
      setOnlineUsers(prev => {
        const exists = prev.find(u => u.user_id === data.user_id);
        if (exists) {
          return prev.map(u =>
            u.user_id === data.user_id ? { ...u, ...data } : u
          );
        }
        return [...prev, data];
      });
    });

    socketInstance.on('presence:user_left', (data) => {
      setOnlineUsers(prev =>
        prev.filter(u => u.user_id !== data.user_id)
      );
    });

    socketInstance.on('presence:update', (data) => {
      setOnlineUsers(prev =>
        prev.map(u =>
          u.user_id === data.user_id ? { ...u, ...data } : u
        )
      );
    });

    setSocket(socketInstance);

    return () => {
      socketInstance.disconnect();
    };
  }, [isAuthenticated, token]);

  useEffect(() => {
    if (!socket || !isConnected) return;

    const interval = setInterval(() => {
      socket.emit('heartbeat');
    }, 30000);

    return () => clearInterval(interval);
  }, [socket, isConnected]);

  const emit = useCallback((event, data) => {
    if (socket && isConnected) {
      socket.emit(event, data);
    }
  }, [socket, isConnected]);

  const on = useCallback((event, callback) => {
    if (socket) {
      socket.on(event, callback);
      return () => socket.off(event, callback);
    }
    return () => {};
  }, [socket]);

  const off = useCallback((event, callback) => {
    if (socket) {
      socket.off(event, callback);
    }
  }, [socket]);

  const updatePresence = useCallback((page, entityType = null, entityId = null) => {
    emit('presence:update', {
      current_page: page,
      entity_type: entityType,
      entity_id: entityId,
    });
  }, [emit]);

  const setStatus = useCallback((status) => {
    emit('presence:update', { status });
  }, [emit]);

  const joinRoom = useCallback((entityType, entityId) => {
    emit('room:join', {
      entity_type: entityType,
      entity_id: entityId,
    });
  }, [emit]);

  const leaveRoom = useCallback((roomId) => {
    emit('room:leave', { room_id: roomId });
  }, [emit]);

  const value = {
    socket,
    isConnected,
    connectionError,
    onlineUsers,
    emit,
    on,
    off,
    updatePresence,
    setStatus,
    joinRoom,
    leaveRoom,
    onlineCount: onlineUsers.length,
  };

  return (
    <RealtimeContext.Provider value={value}>
      {children}
    </RealtimeContext.Provider>
  );
}

export const useRealtime = () => {
  const context = useContext(RealtimeContext);
  if (!context) {
    throw new Error('useRealtime must be used within RealtimeProvider');
  }
  return context;
};

export default RealtimeContext;
