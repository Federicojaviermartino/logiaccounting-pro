/**
 * usePresence Hook
 * Manage user presence
 */

import { useState, useEffect, useCallback } from 'react';
import { useRealtime } from '../context/RealtimeContext';

export const usePresence = () => {
  const { socket, isConnected, onlineUsers, emit, on } = useRealtime();
  const [myStatus, setMyStatus] = useState('online');

  const updateLocation = useCallback((page, entityType = null, entityId = null) => {
    emit('presence:update', {
      current_page: page,
      entity_type: entityType,
      entity_id: entityId,
    });
  }, [emit]);

  const setStatus = useCallback((status) => {
    emit('presence:update', { status });
    setMyStatus(status);
  }, [emit]);

  const refreshPresence = useCallback(() => {
    emit('presence:list', {});
  }, [emit]);

  const getUserById = useCallback((userId) => {
    return onlineUsers.find(u => u.user_id === userId);
  }, [onlineUsers]);

  const isUserOnline = useCallback((userId) => {
    const user = onlineUsers.find(u => u.user_id === userId);
    return user && user.status !== 'offline';
  }, [onlineUsers]);

  return {
    onlineUsers,
    myStatus,
    isConnected,
    updateLocation,
    setStatus,
    refreshPresence,
    getUserById,
    isUserOnline,
    onlineCount: onlineUsers.length,
  };
};

export default usePresence;
