/**
 * useRoom Hook
 * Manage room subscriptions for collaborative features
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useRealtime } from '../context/RealtimeContext';

export const useRoom = (entityType, entityId) => {
  const { socket, isConnected, emit, on, off } = useRealtime();
  const [roomUsers, setRoomUsers] = useState([]);
  const [isJoined, setIsJoined] = useState(false);
  const joinedRef = useRef(false);

  const roomId = entityType && entityId ? `${entityType}:${entityId}` : null;

  useEffect(() => {
    if (!socket || !isConnected || !roomId || joinedRef.current) return;

    emit('room:join', {
      entity_type: entityType,
      entity_id: entityId,
    });

    joinedRef.current = true;
    setIsJoined(true);

    return () => {
      if (joinedRef.current) {
        emit('room:leave', { room_id: roomId });
        joinedRef.current = false;
        setIsJoined(false);
      }
    };
  }, [socket, isConnected, roomId, entityType, entityId, emit]);

  useEffect(() => {
    if (!socket || !roomId) return;

    const handleRoomUsers = (data) => {
      if (data.room_id === roomId) {
        setRoomUsers(data.users || []);
      }
    };

    const handleUserJoined = (data) => {
      if (data.room_id === roomId) {
        setRoomUsers(prev => {
          const exists = prev.find(u => u.user_id === data.user_id);
          if (exists) return prev;
          return [...prev, data];
        });
      }
    };

    const handleUserLeft = (data) => {
      if (data.room_id === roomId) {
        setRoomUsers(prev =>
          prev.filter(u => u.user_id !== data.user_id)
        );
      }
    };

    socket.on('room:users', handleRoomUsers);
    socket.on('room:user_joined', handleUserJoined);
    socket.on('room:user_left', handleUserLeft);

    return () => {
      socket.off('room:users', handleRoomUsers);
      socket.off('room:user_joined', handleUserJoined);
      socket.off('room:user_left', handleUserLeft);
    };
  }, [socket, roomId]);

  const refreshUsers = useCallback(() => {
    if (roomId) {
      emit('room:users', { room_id: roomId });
    }
  }, [emit, roomId]);

  return {
    roomId,
    roomUsers,
    isJoined,
    userCount: roomUsers.length,
    refreshUsers,
  };
};

export default useRoom;
