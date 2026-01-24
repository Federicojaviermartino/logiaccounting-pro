/**
 * Mobile Layout - Responsive layout for mobile devices
 */

import React, { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import MobileHeader from '../components/mobile/MobileHeader';
import BottomNav from '../components/mobile/BottomNav';
import FAB from '../components/mobile/FAB';
import { useAuth } from '../hooks/useAuth';
import { mobileAPI } from '../services/mobileAPI';

export default function MobileLayout() {
  const location = useLocation();
  const { user } = useAuth();
  const [notifications, setNotifications] = useState(0);
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  const pageTitles = {
    '/portal': 'Dashboard',
    '/portal/projects': 'Projects',
    '/portal/payments': 'Payments',
    '/portal/support': 'Support',
    '/portal/support/new': 'New Ticket',
    '/portal/messages': 'Messages',
    '/portal/documents': 'Documents',
    '/portal/account': 'Account',
    '/portal/kb': 'Help Center',
    '/portal/more': 'More',
  };

  const showBack = location.pathname !== '/portal' &&
    !location.pathname.match(/^\/portal\/(projects|payments|support|more)$/);

  const getTitle = () => {
    for (const [path, title] of Object.entries(pageTitles)) {
      if (location.pathname === path) return title;
    }
    if (location.pathname.startsWith('/portal/projects/')) return 'Project Details';
    if (location.pathname.startsWith('/portal/support/')) return 'Ticket Details';
    if (location.pathname.startsWith('/portal/payments/')) return 'Invoice Details';
    return 'LogiAccounting';
  };

  useEffect(() => {
    const loadNotifications = async () => {
      try {
        const response = await mobileAPI.getUnreadCount();
        setNotifications(response.data.count || 0);
      } catch (error) {
        console.error('Failed to load notifications:', error);
      }
    };

    loadNotifications();
    const interval = setInterval(loadNotifications, 60000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const badges = {
    '/portal/payments': 3,
    '/portal/support': 1,
  };

  return (
    <div className="mobile-layout">
      {!isOnline && (
        <div className="offline-banner">
          <span>You're offline. Some features may be unavailable.</span>
        </div>
      )}

      <MobileHeader
        title={getTitle()}
        showBack={showBack}
        showSearch={location.pathname === '/portal'}
        notifications={notifications}
        user={user}
      />

      <main className="mobile-content">
        <Outlet />
      </main>

      {['/portal', '/portal/projects', '/portal/payments'].includes(location.pathname) && (
        <FAB />
      )}

      <BottomNav badges={badges} />

      <style jsx>{`
        .mobile-layout {
          display: flex;
          flex-direction: column;
          min-height: 100vh;
          min-height: 100dvh;
          background: var(--bg-secondary);
        }

        .offline-banner {
          background: var(--warning);
          color: white;
          text-align: center;
          padding: 8px 16px;
          font-size: 13px;
          font-weight: 500;
        }

        .mobile-content {
          flex: 1;
          padding: 16px;
          padding-bottom: calc(80px + env(safe-area-inset-bottom));
          overflow-y: auto;
          -webkit-overflow-scrolling: touch;
        }

        @media (min-width: 769px) {
          .mobile-layout {
            display: none;
          }
        }
      `}</style>
    </div>
  );
}
