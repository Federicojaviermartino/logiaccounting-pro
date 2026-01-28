import { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { useAuth } from './AuthContext';

const WebSocketContext = createContext(null);

export function WebSocketProvider({ children }) {
  const { token, isAuthenticated } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    if (!token || wsRef.current?.readyState === WebSocket.OPEN) return;

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws`;

    try {
      wsRef.current = new WebSocket(wsUrl, [token]);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);

        // Start ping interval
        const pingInterval = setInterval(() => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);

        wsRef.current.pingInterval = pingInterval;
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          if (message.type === 'notification') {
            const notification = {
              id: Date.now(),
              event: message.event,
              data: message.data,
              timestamp: message.timestamp,
              read: false
            };

            setNotifications(prev => [notification, ...prev].slice(0, 50));

            // Show toast
            showToast(notification);

            // Request desktop notification permission
            if (Notification.permission === 'granted') {
              new Notification('LogiAccounting Pro', {
                body: getNotificationMessage(notification),
                icon: '/logo192.png'
              });
            }
          }
        } catch (e) {
          console.error('WebSocket message error:', e);
        }
      };

      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);

        if (wsRef.current?.pingInterval) {
          clearInterval(wsRef.current.pingInterval);
        }

        // Reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(connect, 3000);
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (err) {
      console.error('WebSocket connection failed:', err);
    }
  }, [token]);

  useEffect(() => {
    if (isAuthenticated && token) {
      connect();
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [isAuthenticated, token, connect]);

  const showToast = (notification) => {
    // Dispatch custom event for toast
    window.dispatchEvent(new CustomEvent('show-toast', {
      detail: notification
    }));
  };

  const getNotificationMessage = (notification) => {
    const messages = {
      'transaction.created': 'New transaction created',
      'payment.due_soon': 'Payment due soon',
      'payment.overdue': 'Payment overdue',
      'inventory.low_stock': 'Low stock alert',
      'approval.required': 'Approval required',
      'approval.completed': 'Approval completed',
      'budget.threshold_reached': 'Budget threshold reached',
      'anomaly.detected': 'Anomaly detected'
    };
    return messages[notification.event] || 'New notification';
  };

  const markAsRead = (notificationId) => {
    setNotifications(prev =>
      prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  const clearNotifications = () => {
    setNotifications([]);
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <WebSocketContext.Provider value={{
      isConnected,
      notifications,
      unreadCount,
      markAsRead,
      markAllAsRead,
      clearNotifications
    }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export const useWebSocket = () => useContext(WebSocketContext);
