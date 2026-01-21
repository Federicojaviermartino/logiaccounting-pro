# LogiAccounting Pro - Phase 18 Tasks Part 3

## FRONTEND COMPONENTS

---

## TASK 10: WEBSOCKET CONTEXT & HOOKS

### 10.1 WebSocket Context

**File:** `frontend/src/features/realtime/context/WebSocketContext.jsx`

```jsx
/**
 * WebSocket Context
 * Provides WebSocket connection to entire app
 */

import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { io } from 'socket.io-client';
import { useAuth } from '../../auth/hooks/useAuth';

const WebSocketContext = createContext(null);

const SOCKET_URL = import.meta.env.VITE_WEBSOCKET_URL || 'http://localhost:5000';

export const WebSocketProvider = ({ children }) => {
  const { user, token, isAuthenticated } = useAuth();
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  
  // Connect to WebSocket server
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
      console.log('WebSocket connected');
      setIsConnected(true);
      setConnectionError(null);
      reconnectAttempts.current = 0;
    });
    
    socketInstance.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      setIsConnected(false);
    });
    
    socketInstance.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      setConnectionError(error.message);
      reconnectAttempts.current += 1;
    });
    
    socketInstance.on('error', (error) => {
      console.error('WebSocket error:', error);
      setConnectionError(error.message);
    });
    
    setSocket(socketInstance);
    
    // Cleanup on unmount
    return () => {
      socketInstance.disconnect();
    };
  }, [isAuthenticated, token]);
  
  // Heartbeat to keep connection alive
  useEffect(() => {
    if (!socket || !isConnected) return;
    
    const interval = setInterval(() => {
      socket.emit('heartbeat');
    }, 30000); // Every 30 seconds
    
    return () => clearInterval(interval);
  }, [socket, isConnected]);
  
  // Emit event helper
  const emit = useCallback((event, data) => {
    if (socket && isConnected) {
      socket.emit(event, data);
    }
  }, [socket, isConnected]);
  
  // Subscribe to event
  const on = useCallback((event, callback) => {
    if (socket) {
      socket.on(event, callback);
      return () => socket.off(event, callback);
    }
    return () => {};
  }, [socket]);
  
  // Unsubscribe from event
  const off = useCallback((event, callback) => {
    if (socket) {
      socket.off(event, callback);
    }
  }, [socket]);
  
  const value = {
    socket,
    isConnected,
    connectionError,
    emit,
    on,
    off,
  };
  
  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within WebSocketProvider');
  }
  return context;
};

export default WebSocketContext;
```

### 10.2 Presence Hook

**File:** `frontend/src/features/realtime/hooks/usePresence.js`

```javascript
/**
 * usePresence Hook
 * Manage user presence
 */

import { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from '../context/WebSocketContext';

export const usePresence = () => {
  const { socket, isConnected, emit, on, off } = useWebSocket();
  const [onlineUsers, setOnlineUsers] = useState([]);
  const [myStatus, setMyStatus] = useState('online');
  
  // Listen for presence events
  useEffect(() => {
    if (!socket) return;
    
    const handlePresenceList = (data) => {
      setOnlineUsers(data.users || []);
    };
    
    const handleUserJoined = (data) => {
      setOnlineUsers(prev => {
        const exists = prev.find(u => u.user_id === data.user_id);
        if (exists) {
          return prev.map(u => 
            u.user_id === data.user_id ? { ...u, ...data } : u
          );
        }
        return [...prev, data];
      });
    };
    
    const handleUserLeft = (data) => {
      setOnlineUsers(prev => 
        prev.filter(u => u.user_id !== data.user_id)
      );
    };
    
    const handlePresenceUpdate = (data) => {
      setOnlineUsers(prev => 
        prev.map(u => 
          u.user_id === data.user_id ? { ...u, ...data } : u
        )
      );
    };
    
    socket.on('presence:list', handlePresenceList);
    socket.on('presence:user_joined', handleUserJoined);
    socket.on('presence:user_left', handleUserLeft);
    socket.on('presence:update', handlePresenceUpdate);
    
    return () => {
      socket.off('presence:list', handlePresenceList);
      socket.off('presence:user_joined', handleUserJoined);
      socket.off('presence:user_left', handleUserLeft);
      socket.off('presence:update', handlePresenceUpdate);
    };
  }, [socket]);
  
  // Update presence when page changes
  const updateLocation = useCallback((page, entityType = null, entityId = null) => {
    emit('presence:update', {
      current_page: page,
      entity_type: entityType,
      entity_id: entityId,
    });
  }, [emit]);
  
  // Set status (online, away, busy)
  const setStatus = useCallback((status) => {
    emit('presence:update', { status });
    setMyStatus(status);
  }, [emit]);
  
  // Request presence list
  const refreshPresence = useCallback(() => {
    emit('presence:list', {});
  }, [emit]);
  
  // Get user by ID
  const getUserById = useCallback((userId) => {
    return onlineUsers.find(u => u.user_id === userId);
  }, [onlineUsers]);
  
  // Check if user is online
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
```

### 10.3 Room Hook

**File:** `frontend/src/features/realtime/hooks/useRoom.js`

```javascript
/**
 * useRoom Hook
 * Manage room subscriptions for collaborative features
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useWebSocket } from '../context/WebSocketContext';

export const useRoom = (entityType, entityId) => {
  const { socket, isConnected, emit } = useWebSocket();
  const [roomUsers, setRoomUsers] = useState([]);
  const [isJoined, setIsJoined] = useState(false);
  const joinedRef = useRef(false);
  
  const roomId = entityType && entityId ? `${entityType}:${entityId}` : null;
  
  // Join room on mount
  useEffect(() => {
    if (!socket || !isConnected || !roomId || joinedRef.current) return;
    
    // Join room
    emit('room:join', {
      entity_type: entityType,
      entity_id: entityId,
    });
    
    joinedRef.current = true;
    setIsJoined(true);
    
    // Leave room on unmount
    return () => {
      if (joinedRef.current) {
        emit('room:leave', { room_id: roomId });
        joinedRef.current = false;
        setIsJoined(false);
      }
    };
  }, [socket, isConnected, roomId, entityType, entityId, emit]);
  
  // Listen for room events
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
  
  // Request room users list
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
```

### 10.4 Notifications Hook

**File:** `frontend/src/features/realtime/hooks/useNotifications.js`

```javascript
/**
 * useNotifications Hook
 * Manage real-time notifications
 */

import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useWebSocket } from '../context/WebSocketContext';
import { notificationApi } from '../api/notificationApi';
import { toast } from 'react-hot-toast';

export const useNotifications = () => {
  const queryClient = useQueryClient();
  const { socket, isConnected, emit } = useWebSocket();
  const [realtimeNotifications, setRealtimeNotifications] = useState([]);
  
  // Fetch notifications
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => notificationApi.getNotifications({ limit: 50 }),
  });
  
  // Fetch unread count
  const { data: countData } = useQuery({
    queryKey: ['notifications-count'],
    queryFn: () => notificationApi.getUnreadCount(),
    refetchInterval: 60000, // Refresh every minute
  });
  
  // Listen for real-time notifications
  useEffect(() => {
    if (!socket) return;
    
    const handleNotification = (notification) => {
      // Add to local state
      setRealtimeNotifications(prev => [notification, ...prev]);
      
      // Show toast notification
      toast.custom((t) => (
        <div
          className={`${t.visible ? 'animate-enter' : 'animate-leave'} 
            max-w-md w-full bg-white shadow-lg rounded-lg pointer-events-auto 
            flex ring-1 ring-black ring-opacity-5`}
        >
          <div className="flex-1 w-0 p-4">
            <div className="flex items-start">
              <div className="ml-3 flex-1">
                <p className="text-sm font-medium text-gray-900">
                  {notification.title}
                </p>
                {notification.message && (
                  <p className="mt-1 text-sm text-gray-500">
                    {notification.message}
                  </p>
                )}
              </div>
            </div>
          </div>
          <div className="flex border-l border-gray-200">
            <button
              onClick={() => toast.dismiss(t.id)}
              className="w-full border border-transparent rounded-none rounded-r-lg p-4 
                flex items-center justify-center text-sm font-medium text-blue-600 
                hover:text-blue-500"
            >
              Close
            </button>
          </div>
        </div>
      ), { duration: 5000 });
      
      // Invalidate queries
      queryClient.invalidateQueries(['notifications']);
      queryClient.invalidateQueries(['notifications-count']);
    };
    
    const handleCountUpdate = (data) => {
      queryClient.setQueryData(['notifications-count'], { count: data.count });
    };
    
    socket.on('notification', handleNotification);
    socket.on('notification:count', handleCountUpdate);
    
    return () => {
      socket.off('notification', handleNotification);
      socket.off('notification:count', handleCountUpdate);
    };
  }, [socket, queryClient]);
  
  // Mark as read mutation
  const markReadMutation = useMutation({
    mutationFn: (id) => notificationApi.markRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['notifications']);
      queryClient.invalidateQueries(['notifications-count']);
    },
  });
  
  // Mark all as read mutation
  const markAllReadMutation = useMutation({
    mutationFn: () => notificationApi.markAllRead(),
    onSuccess: () => {
      queryClient.invalidateQueries(['notifications']);
      queryClient.invalidateQueries(['notifications-count']);
    },
  });
  
  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id) => notificationApi.deleteNotification(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['notifications']);
    },
  });
  
  // Combine stored and realtime notifications
  const allNotifications = [
    ...realtimeNotifications,
    ...(data?.notifications || []),
  ].reduce((acc, notif) => {
    // Dedupe by ID
    if (!acc.find(n => n.id === notif.id)) {
      acc.push(notif);
    }
    return acc;
  }, []);
  
  return {
    notifications: allNotifications,
    unreadCount: countData?.count || 0,
    isLoading,
    refetch,
    markRead: markReadMutation.mutate,
    markAllRead: markAllReadMutation.mutate,
    deleteNotification: deleteMutation.mutate,
  };
};

export default useNotifications;
```

---

## TASK 11: PRESENCE COMPONENTS

### 11.1 Presence Indicator

**File:** `frontend/src/features/realtime/components/PresenceIndicator.jsx`

```jsx
/**
 * Presence Indicator
 * Shows user online status dot
 */

import React from 'react';
import { motion } from 'framer-motion';

const statusColors = {
  online: 'bg-green-500',
  away: 'bg-yellow-500',
  busy: 'bg-red-500',
  offline: 'bg-gray-400',
};

const PresenceIndicator = ({ 
  status = 'offline', 
  size = 'sm',
  showPulse = true,
  className = '',
}) => {
  const sizeClasses = {
    xs: 'w-2 h-2',
    sm: 'w-2.5 h-2.5',
    md: 'w-3 h-3',
    lg: 'w-4 h-4',
  };
  
  const colorClass = statusColors[status] || statusColors.offline;
  const sizeClass = sizeClasses[size] || sizeClasses.sm;
  
  return (
    <span className={`relative inline-flex ${className}`}>
      <span className={`${sizeClass} ${colorClass} rounded-full`} />
      {showPulse && status === 'online' && (
        <motion.span
          className={`absolute inset-0 ${sizeClass} ${colorClass} rounded-full`}
          animate={{
            scale: [1, 1.5, 1.5],
            opacity: [1, 0.5, 0],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'easeOut',
          }}
        />
      )}
    </span>
  );
};

export default PresenceIndicator;
```

### 11.2 User Avatar with Presence

**File:** `frontend/src/features/realtime/components/UserAvatar.jsx`

```jsx
/**
 * User Avatar with Presence
 */

import React from 'react';
import PresenceIndicator from './PresenceIndicator';

const UserAvatar = ({
  name,
  imageUrl,
  status = 'offline',
  size = 'md',
  showPresence = true,
  className = '',
}) => {
  const sizeClasses = {
    xs: 'w-6 h-6 text-xs',
    sm: 'w-8 h-8 text-sm',
    md: 'w-10 h-10 text-base',
    lg: 'w-12 h-12 text-lg',
    xl: 'w-16 h-16 text-xl',
  };
  
  const presenceSizes = {
    xs: 'xs',
    sm: 'xs',
    md: 'sm',
    lg: 'md',
    xl: 'lg',
  };
  
  const presencePositions = {
    xs: 'bottom-0 right-0',
    sm: 'bottom-0 right-0',
    md: '-bottom-0.5 -right-0.5',
    lg: '-bottom-0.5 -right-0.5',
    xl: 'bottom-0 right-0',
  };
  
  const getInitials = (name) => {
    if (!name) return '?';
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };
  
  const sizeClass = sizeClasses[size] || sizeClasses.md;
  
  return (
    <div className={`relative inline-flex ${className}`}>
      {imageUrl ? (
        <img
          src={imageUrl}
          alt={name}
          className={`${sizeClass} rounded-full object-cover`}
        />
      ) : (
        <div
          className={`${sizeClass} rounded-full bg-blue-500 text-white 
            flex items-center justify-center font-medium`}
        >
          {getInitials(name)}
        </div>
      )}
      
      {showPresence && (
        <span className={`absolute ${presencePositions[size]} ring-2 ring-white rounded-full`}>
          <PresenceIndicator status={status} size={presenceSizes[size]} />
        </span>
      )}
    </div>
  );
};

export default UserAvatar;
```

### 11.3 Online Users List

**File:** `frontend/src/features/realtime/components/OnlineUsersList.jsx`

```jsx
/**
 * Online Users List
 * Shows list of currently online users
 */

import React from 'react';
import { usePresence } from '../hooks/usePresence';
import UserAvatar from './UserAvatar';
import PresenceIndicator from './PresenceIndicator';

const OnlineUsersList = ({ maxDisplay = 5, compact = false }) => {
  const { onlineUsers, onlineCount } = usePresence();
  
  const displayUsers = onlineUsers.slice(0, maxDisplay);
  const remainingCount = Math.max(0, onlineCount - maxDisplay);
  
  if (compact) {
    return (
      <div className="flex items-center">
        <div className="flex -space-x-2">
          {displayUsers.map((user) => (
            <UserAvatar
              key={user.user_id}
              name={user.user_name}
              status={user.status}
              size="sm"
              className="ring-2 ring-white"
            />
          ))}
          {remainingCount > 0 && (
            <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center 
              justify-center text-xs font-medium text-gray-600 ring-2 ring-white">
              +{remainingCount}
            </div>
          )}
        </div>
        <span className="ml-2 text-sm text-gray-500">
          {onlineCount} online
        </span>
      </div>
    );
  }
  
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-900">Team Online</h3>
        <span className="text-xs text-gray-500">{onlineCount} members</span>
      </div>
      
      <div className="space-y-2">
        {onlineUsers.map((user) => (
          <div
            key={user.user_id}
            className="flex items-center justify-between py-1"
          >
            <div className="flex items-center">
              <UserAvatar
                name={user.user_name}
                status={user.status}
                size="sm"
              />
              <div className="ml-2">
                <p className="text-sm font-medium text-gray-900">
                  {user.user_name}
                </p>
                {user.current_page && (
                  <p className="text-xs text-gray-500 truncate max-w-[150px]">
                    {user.current_page}
                  </p>
                )}
              </div>
            </div>
            <PresenceIndicator status={user.status} size="sm" />
          </div>
        ))}
        
        {onlineUsers.length === 0 && (
          <p className="text-sm text-gray-500 text-center py-4">
            No one else online
          </p>
        )}
      </div>
    </div>
  );
};

export default OnlineUsersList;
```

---

## TASK 12: NOTIFICATION COMPONENTS

### 12.1 Notification Center

**File:** `frontend/src/features/realtime/components/NotificationCenter.jsx`

```jsx
/**
 * Notification Center
 * Dropdown with all notifications
 */

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNotifications } from '../hooks/useNotifications';
import { formatDistanceToNow } from 'date-fns';

const NotificationCenter = () => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);
  
  const {
    notifications,
    unreadCount,
    isLoading,
    markRead,
    markAllRead,
    deleteNotification,
  } = useNotifications();
  
  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);
  
  const handleNotificationClick = (notification) => {
    if (!notification.is_read) {
      markRead(notification.id);
    }
    
    if (notification.action_url) {
      window.location.href = notification.action_url;
    }
    
    setIsOpen(false);
  };
  
  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'urgent': return 'border-l-red-500';
      case 'high': return 'border-l-orange-500';
      case 'normal': return 'border-l-blue-500';
      default: return 'border-l-gray-300';
    }
  };
  
  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" 
          />
        </svg>
        
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 w-5 h-5 bg-red-500 text-white 
            text-xs font-medium rounded-full flex items-center justify-center">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>
      
      {/* Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-lg 
              border border-gray-200 z-50 overflow-hidden"
          >
            {/* Header */}
            <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">Notifications</h3>
              {unreadCount > 0 && (
                <button
                  onClick={markAllRead}
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  Mark all read
                </button>
              )}
            </div>
            
            {/* Notifications List */}
            <div className="max-h-96 overflow-y-auto">
              {isLoading ? (
                <div className="p-4 text-center text-gray-500">
                  Loading...
                </div>
              ) : notifications.length === 0 ? (
                <div className="p-8 text-center">
                  <svg className="w-12 h-12 mx-auto text-gray-300 mb-3" fill="none" 
                    stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                      d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" 
                    />
                  </svg>
                  <p className="text-gray-500">No notifications</p>
                </div>
              ) : (
                notifications.map((notification) => (
                  <div
                    key={notification.id}
                    onClick={() => handleNotificationClick(notification)}
                    className={`px-4 py-3 border-l-4 ${getPriorityColor(notification.priority)} 
                      hover:bg-gray-50 cursor-pointer transition-colors
                      ${!notification.is_read ? 'bg-blue-50' : ''}`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <p className={`text-sm ${!notification.is_read ? 'font-semibold' : 'font-medium'} text-gray-900`}>
                          {notification.title}
                        </p>
                        {notification.message && (
                          <p className="text-sm text-gray-500 mt-0.5 line-clamp-2">
                            {notification.message}
                          </p>
                        )}
                        <p className="text-xs text-gray-400 mt-1">
                          {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
                        </p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteNotification(notification.id);
                        }}
                        className="ml-2 text-gray-400 hover:text-gray-600"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
            
            {/* Footer */}
            <div className="px-4 py-3 border-t border-gray-200 text-center">
              <a href="/notifications" className="text-sm text-blue-600 hover:text-blue-700">
                View all notifications
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default NotificationCenter;
```

---

## TASK 13: COLLABORATION COMPONENTS

### 13.1 Collaborator Cursors

**File:** `frontend/src/features/realtime/components/CollaboratorCursors.jsx`

```jsx
/**
 * Collaborator Cursors
 * Shows other users' cursor positions
 */

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const CollaboratorCursors = ({ cursors = [], containerRef }) => {
  return (
    <AnimatePresence>
      {cursors.map((cursor) => (
        <motion.div
          key={cursor.user_id}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.8 }}
          style={{
            position: 'absolute',
            left: `${cursor.column * 8}px`,
            top: `${cursor.line * 20}px`,
            pointerEvents: 'none',
            zIndex: 50,
          }}
        >
          {/* Cursor */}
          <svg
            width="20"
            height="20"
            viewBox="0 0 20 20"
            fill={cursor.color}
            style={{ transform: 'rotate(-45deg)' }}
          >
            <path d="M0 0L0 16L4 12L8 20L10 19L6 11L12 11L0 0Z" />
          </svg>
          
          {/* Name Label */}
          <div
            className="absolute left-5 top-0 px-2 py-0.5 rounded text-xs text-white whitespace-nowrap"
            style={{ backgroundColor: cursor.color }}
          >
            {cursor.user_name}
          </div>
        </motion.div>
      ))}
    </AnimatePresence>
  );
};

export default CollaboratorCursors;
```

### 13.2 Editing Indicator

**File:** `frontend/src/features/realtime/components/EditingIndicator.jsx`

```jsx
/**
 * Editing Indicator
 * Shows who is currently editing a document
 */

import React from 'react';
import { useRoom } from '../hooks/useRoom';
import UserAvatar from './UserAvatar';
import { useAuth } from '../../auth/hooks/useAuth';

const EditingIndicator = ({ entityType, entityId }) => {
  const { user } = useAuth();
  const { roomUsers, userCount } = useRoom(entityType, entityId);
  
  // Filter out current user
  const otherUsers = roomUsers.filter(u => u.user_id !== user?.id);
  
  if (otherUsers.length === 0) {
    return null;
  }
  
  return (
    <div className="flex items-center bg-yellow-50 border border-yellow-200 
      rounded-lg px-3 py-2 text-sm">
      <div className="flex -space-x-2 mr-2">
        {otherUsers.slice(0, 3).map((u) => (
          <UserAvatar
            key={u.user_id}
            name={u.user_name}
            status="online"
            size="xs"
            showPresence={false}
            className="ring-2 ring-white"
          />
        ))}
      </div>
      
      <span className="text-yellow-800">
        {otherUsers.length === 1 ? (
          <>{otherUsers[0].user_name} is viewing</>
        ) : otherUsers.length === 2 ? (
          <>{otherUsers[0].user_name} and {otherUsers[1].user_name} are viewing</>
        ) : (
          <>{otherUsers[0].user_name} and {otherUsers.length - 1} others are viewing</>
        )}
      </span>
    </div>
  );
};

export default EditingIndicator;
```

### 13.3 Activity Feed Widget

**File:** `frontend/src/features/realtime/components/ActivityFeed.jsx`

```jsx
/**
 * Activity Feed Widget
 * Real-time activity stream
 */

import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../context/WebSocketContext';
import { useQuery } from '@tanstack/react-query';
import { activityApi } from '../api/activityApi';
import { formatDistanceToNow } from 'date-fns';
import UserAvatar from './UserAvatar';

const ActivityFeed = ({ entityType, entityId, limit = 20 }) => {
  const { socket } = useWebSocket();
  const [realtimeActivities, setRealtimeActivities] = useState([]);
  
  // Fetch initial activities
  const { data, isLoading } = useQuery({
    queryKey: ['activity', entityType, entityId],
    queryFn: () => entityType && entityId
      ? activityApi.getEntityActivity(entityType, entityId, limit)
      : activityApi.getFeed({ limit }),
  });
  
  // Listen for real-time activities
  useEffect(() => {
    if (!socket) return;
    
    const handleActivity = (activity) => {
      // Filter by entity if specified
      if (entityType && entityId) {
        if (activity.entity_type !== entityType || activity.entity_id !== entityId) {
          return;
        }
      }
      
      setRealtimeActivities(prev => [activity, ...prev]);
    };
    
    socket.on('activity', handleActivity);
    
    return () => socket.off('activity', handleActivity);
  }, [socket, entityType, entityId]);
  
  // Combine activities
  const allActivities = [
    ...realtimeActivities,
    ...(data?.activities || []),
  ].slice(0, limit);
  
  const getActionIcon = (action) => {
    switch (action) {
      case 'created':
        return (
          <span className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
            <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
          </span>
        );
      case 'updated':
        return (
          <span className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
            <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </span>
        );
      case 'deleted':
        return (
          <span className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center">
            <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </span>
        );
      case 'completed':
        return (
          <span className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
            <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </span>
        );
      default:
        return (
          <span className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
            <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </span>
        );
    }
  };
  
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-start space-x-3">
              <div className="w-8 h-8 bg-gray-200 rounded-full" />
              <div className="flex-1">
                <div className="h-4 bg-gray-200 rounded w-3/4" />
                <div className="h-3 bg-gray-200 rounded w-1/2 mt-2" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }
  
  return (
    <div className="bg-white rounded-lg border border-gray-200">
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900">Activity</h3>
      </div>
      
      <div className="divide-y divide-gray-100 max-h-96 overflow-y-auto">
        {allActivities.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            No activity yet
          </div>
        ) : (
          allActivities.map((activity) => (
            <div key={activity.id} className="px-4 py-3 hover:bg-gray-50">
              <div className="flex items-start space-x-3">
                {getActionIcon(activity.action)}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900">
                    <span className="font-medium">{activity.user_name}</span>
                    {' '}{activity.action_label}{' '}
                    <span className="font-medium">{activity.entity_name}</span>
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {formatDistanceToNow(new Date(activity.created_at), { addSuffix: true })}
                  </p>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ActivityFeed;
```

---

## SUMMARY

### Phase 18 Complete Implementation

| Part | Content | Size |
|------|---------|------|
| **Part 1** | WebSocket server, Connection manager, Presence manager, Room manager | ~55KB |
| **Part 2** | Cursor tracking, Notification service, Activity service, API routes | ~50KB |
| **Part 3** | Frontend context, hooks, presence components, notification center, activity feed | ~45KB |

### Key Features Implemented

| Feature | Backend | Frontend |
|---------|---------|----------|
| **WebSocket Server** | Socket.IO with Redis adapter | WebSocket context & hooks |
| **User Presence** | Online/away/busy tracking | Presence indicators, online list |
| **Collaboration Rooms** | Room join/leave, user tracking | Room hook, editing indicator |
| **Cursor Sync** | Real-time cursor positions | Cursor overlay component |
| **Notifications** | Push + WebSocket delivery | Notification center, toasts |
| **Activity Feed** | Real-time activity logging | Activity feed widget |

### WebSocket Events

| Event | Direction | Purpose |
|-------|-----------|---------|
| `connect` | C→S | Authenticate & connect |
| `presence:update` | Both | Status/location changes |
| `room:join/leave` | C→S | Enter/exit collaboration |
| `cursor:move` | C→S | Cursor position update |
| `notification` | S→C | Push notification |
| `activity` | S→C | Activity feed item |

### Estimated Time: ~160 hours (15 weeks)

---

*Phase 18 Tasks Part 3 - LogiAccounting Pro*
*Frontend Components*
