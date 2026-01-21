/**
 * useNotifications Hook
 * Manage real-time notifications
 */

import { useState, useEffect, useCallback } from 'react';
import { useRealtime } from '../context/RealtimeContext';
import axios from 'axios';

export const useNotifications = () => {
  const { socket, isConnected, on } = useRealtime();
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  const fetchNotifications = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await axios.get('/api/v1/notifications', {
        params: { limit: 50 }
      });
      if (response.data.success) {
        setNotifications(response.data.notifications);
      }
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchUnreadCount = useCallback(async () => {
    try {
      const response = await axios.get('/api/v1/notifications/unread/count');
      if (response.data.success) {
        setUnreadCount(response.data.count);
      }
    } catch (error) {
      console.error('Failed to fetch unread count:', error);
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
    fetchUnreadCount();
  }, [fetchNotifications, fetchUnreadCount]);

  useEffect(() => {
    if (!socket) return;

    const handleNotification = (notification) => {
      setNotifications(prev => [notification, ...prev].slice(0, 50));
      setUnreadCount(prev => prev + 1);

      window.dispatchEvent(new CustomEvent('show-toast', {
        detail: {
          type: 'info',
          title: notification.title,
          message: notification.message,
        }
      }));
    };

    const handleCountUpdate = (data) => {
      setUnreadCount(data.count);
    };

    socket.on('notification', handleNotification);
    socket.on('notification:count', handleCountUpdate);

    return () => {
      socket.off('notification', handleNotification);
      socket.off('notification:count', handleCountUpdate);
    };
  }, [socket]);

  const markRead = useCallback(async (notificationId) => {
    try {
      await axios.put(`/api/v1/notifications/${notificationId}/read`);
      setNotifications(prev =>
        prev.map(n =>
          n.id === notificationId ? { ...n, is_read: true } : n
        )
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  }, []);

  const markAllRead = useCallback(async () => {
    try {
      await axios.put('/api/v1/notifications/read-all');
      setNotifications(prev =>
        prev.map(n => ({ ...n, is_read: true }))
      );
      setUnreadCount(0);
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    }
  }, []);

  const deleteNotification = useCallback(async (notificationId) => {
    try {
      await axios.delete(`/api/v1/notifications/${notificationId}`);
      setNotifications(prev =>
        prev.filter(n => n.id !== notificationId)
      );
    } catch (error) {
      console.error('Failed to delete notification:', error);
    }
  }, []);

  return {
    notifications,
    unreadCount,
    isLoading,
    refetch: fetchNotifications,
    markRead,
    markAllRead,
    deleteNotification,
  };
};

export default useNotifications;
