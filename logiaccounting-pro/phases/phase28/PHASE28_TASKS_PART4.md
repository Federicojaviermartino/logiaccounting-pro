# Phase 28: Mobile API & PWA - Part 4: Frontend Mobile Components

## Overview
This part covers the frontend mobile components including layout, navigation, and PWA UI components.

---

## File 1: IndexedDB Offline Storage
**Path:** `frontend/src/pwa/offlineStorage.js`

```javascript
/**
 * Offline Storage Manager
 * IndexedDB wrapper for offline data persistence
 */

const DB_NAME = 'logiaccounting-offline';
const DB_VERSION = 1;

// Store names
const STORES = {
  OFFLINE_ACTIONS: 'offline-actions',
  CACHED_DATA: 'cached-data',
  USER_PREFERENCES: 'user-preferences',
  SYNC_STATE: 'sync-state',
};

class OfflineStorage {
  constructor() {
    this.db = null;
    this.isReady = false;
  }

  /**
   * Initialize the database
   */
  async init() {
    if (this.db) {
      return this.db;
    }

    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => {
        console.error('[Offline] Database failed to open');
        reject(request.error);
      };

      request.onsuccess = () => {
        this.db = request.result;
        this.isReady = true;
        console.log('[Offline] Database ready');
        resolve(this.db);
      };

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        // Offline actions store
        if (!db.objectStoreNames.contains(STORES.OFFLINE_ACTIONS)) {
          const actionStore = db.createObjectStore(STORES.OFFLINE_ACTIONS, {
            keyPath: 'id',
          });
          actionStore.createIndex('type', 'type', { unique: false });
          actionStore.createIndex('created_at', 'created_at', { unique: false });
        }

        // Cached data store
        if (!db.objectStoreNames.contains(STORES.CACHED_DATA)) {
          const dataStore = db.createObjectStore(STORES.CACHED_DATA, {
            keyPath: 'key',
          });
          dataStore.createIndex('type', 'type', { unique: false });
          dataStore.createIndex('expires_at', 'expires_at', { unique: false });
        }

        // User preferences store
        if (!db.objectStoreNames.contains(STORES.USER_PREFERENCES)) {
          db.createObjectStore(STORES.USER_PREFERENCES, { keyPath: 'key' });
        }

        // Sync state store
        if (!db.objectStoreNames.contains(STORES.SYNC_STATE)) {
          db.createObjectStore(STORES.SYNC_STATE, { keyPath: 'key' });
        }

        console.log('[Offline] Database schema created');
      };
    });
  }

  /**
   * Ensure database is ready
   */
  async ensureReady() {
    if (!this.db) {
      await this.init();
    }
  }

  // ==================== Offline Actions ====================

  /**
   * Queue an offline action
   */
  async queueAction(type, data) {
    await this.ensureReady();

    const action = {
      id: `offline_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type,
      data,
      created_at: new Date().toISOString(),
      status: 'pending',
    };

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(STORES.OFFLINE_ACTIONS, 'readwrite');
      const store = tx.objectStore(STORES.OFFLINE_ACTIONS);
      const request = store.add(action);

      request.onsuccess = () => {
        console.log('[Offline] Action queued:', action.id);
        resolve(action);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * Get all pending actions
   */
  async getPendingActions() {
    await this.ensureReady();

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(STORES.OFFLINE_ACTIONS, 'readonly');
      const store = tx.objectStore(STORES.OFFLINE_ACTIONS);
      const request = store.getAll();

      request.onsuccess = () => {
        const actions = request.result.filter((a) => a.status === 'pending');
        resolve(actions);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * Mark action as synced
   */
  async markActionSynced(actionId, serverId) {
    await this.ensureReady();

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(STORES.OFFLINE_ACTIONS, 'readwrite');
      const store = tx.objectStore(STORES.OFFLINE_ACTIONS);
      const getRequest = store.get(actionId);

      getRequest.onsuccess = () => {
        const action = getRequest.result;
        if (action) {
          action.status = 'synced';
          action.server_id = serverId;
          action.synced_at = new Date().toISOString();
          store.put(action);
        }
        resolve();
      };

      getRequest.onerror = () => {
        reject(getRequest.error);
      };
    });
  }

  /**
   * Clear synced actions
   */
  async clearSyncedActions() {
    await this.ensureReady();

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(STORES.OFFLINE_ACTIONS, 'readwrite');
      const store = tx.objectStore(STORES.OFFLINE_ACTIONS);
      const request = store.getAll();

      request.onsuccess = () => {
        const actions = request.result;
        actions.forEach((action) => {
          if (action.status === 'synced') {
            store.delete(action.id);
          }
        });
        resolve();
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  // ==================== Cached Data ====================

  /**
   * Cache data with optional TTL
   */
  async cacheData(key, type, data, ttlMinutes = 60) {
    await this.ensureReady();

    const item = {
      key,
      type,
      data,
      cached_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + ttlMinutes * 60 * 1000).toISOString(),
    };

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(STORES.CACHED_DATA, 'readwrite');
      const store = tx.objectStore(STORES.CACHED_DATA);
      const request = store.put(item);

      request.onsuccess = () => {
        resolve(item);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * Get cached data
   */
  async getCachedData(key) {
    await this.ensureReady();

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(STORES.CACHED_DATA, 'readonly');
      const store = tx.objectStore(STORES.CACHED_DATA);
      const request = store.get(key);

      request.onsuccess = () => {
        const item = request.result;
        if (item && new Date(item.expires_at) > new Date()) {
          resolve(item.data);
        } else {
          resolve(null);
        }
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * Clear expired cache
   */
  async clearExpiredCache() {
    await this.ensureReady();

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(STORES.CACHED_DATA, 'readwrite');
      const store = tx.objectStore(STORES.CACHED_DATA);
      const request = store.getAll();

      request.onsuccess = () => {
        const now = new Date();
        request.result.forEach((item) => {
          if (new Date(item.expires_at) <= now) {
            store.delete(item.key);
          }
        });
        resolve();
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  // ==================== Sync State ====================

  /**
   * Save sync state
   */
  async setSyncState(key, value) {
    await this.ensureReady();

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(STORES.SYNC_STATE, 'readwrite');
      const store = tx.objectStore(STORES.SYNC_STATE);
      const request = store.put({ key, value, updated_at: new Date().toISOString() });

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Get sync state
   */
  async getSyncState(key) {
    await this.ensureReady();

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(STORES.SYNC_STATE, 'readonly');
      const store = tx.objectStore(STORES.SYNC_STATE);
      const request = store.get(key);

      request.onsuccess = () => {
        resolve(request.result?.value || null);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  // ==================== Utilities ====================

  /**
   * Clear all offline data
   */
  async clearAll() {
    await this.ensureReady();

    const stores = Object.values(STORES);
    const tx = this.db.transaction(stores, 'readwrite');

    stores.forEach((storeName) => {
      tx.objectStore(storeName).clear();
    });

    return new Promise((resolve, reject) => {
      tx.oncomplete = () => {
        console.log('[Offline] All data cleared');
        resolve();
      };
      tx.onerror = () => reject(tx.error);
    });
  }

  /**
   * Get storage info
   */
  async getStorageInfo() {
    const pendingActions = await this.getPendingActions();

    return {
      pendingActionsCount: pendingActions.length,
      isReady: this.isReady,
    };
  }
}

// Export singleton instance
export const offlineStorage = new OfflineStorage();

// Initialize on import
offlineStorage.init().catch(console.error);

export default offlineStorage;
```

---

## File 2: Bottom Navigation
**Path:** `frontend/src/components/mobile/BottomNav.jsx`

```jsx
/**
 * Bottom Navigation - Mobile navigation bar
 */

import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  TicketIcon,
  CreditCard,
  FolderKanban,
  Menu,
} from 'lucide-react';

const navItems = [
  { path: '/portal', icon: LayoutDashboard, label: 'Home', exact: true },
  { path: '/portal/projects', icon: FolderKanban, label: 'Projects' },
  { path: '/portal/payments', icon: CreditCard, label: 'Payments' },
  { path: '/portal/support', icon: TicketIcon, label: 'Support' },
  { path: '/portal/more', icon: Menu, label: 'More' },
];

export default function BottomNav({ badges = {} }) {
  const location = useLocation();

  const isActive = (path, exact = false) => {
    if (exact) return location.pathname === path;
    return location.pathname.startsWith(path);
  };

  return (
    <nav className="bottom-nav">
      {navItems.map((item) => (
        <NavLink
          key={item.path}
          to={item.path}
          className={`nav-item ${isActive(item.path, item.exact) ? 'active' : ''}`}
        >
          <div className="icon-wrapper">
            <item.icon className="icon" />
            {badges[item.path] > 0 && (
              <span className="badge">{badges[item.path]}</span>
            )}
          </div>
          <span className="label">{item.label}</span>
        </NavLink>
      ))}

      <style jsx>{`
        .bottom-nav {
          position: fixed;
          bottom: 0;
          left: 0;
          right: 0;
          display: flex;
          justify-content: space-around;
          background: var(--bg-primary);
          border-top: 1px solid var(--border-color);
          padding: 8px 0;
          padding-bottom: calc(8px + env(safe-area-inset-bottom));
          z-index: 100;
        }

        .nav-item {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
          padding: 8px 16px;
          color: var(--text-muted);
          text-decoration: none;
          transition: color 0.2s;
          min-width: 64px;
        }

        .nav-item.active {
          color: var(--primary);
        }

        .icon-wrapper {
          position: relative;
        }

        .icon {
          width: 24px;
          height: 24px;
        }

        .badge {
          position: absolute;
          top: -4px;
          right: -8px;
          min-width: 18px;
          height: 18px;
          background: var(--danger);
          color: white;
          font-size: 11px;
          font-weight: 600;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 0 4px;
        }

        .label {
          font-size: 11px;
          font-weight: 500;
        }

        @media (min-width: 769px) {
          .bottom-nav {
            display: none;
          }
        }
      `}</style>
    </nav>
  );
}
```

---

## File 3: Floating Action Button (FAB)
**Path:** `frontend/src/components/mobile/FAB.jsx`

```jsx
/**
 * Floating Action Button (FAB) - Quick actions menu
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  X,
  CreditCard,
  TicketIcon,
  MessageCircle,
  FileText,
} from 'lucide-react';

const defaultActions = [
  { id: 'pay', label: 'Pay Invoice', icon: CreditCard, color: '#10b981', path: '/portal/payments' },
  { id: 'ticket', label: 'New Ticket', icon: TicketIcon, color: '#3b82f6', path: '/portal/support/new' },
  { id: 'message', label: 'Message', icon: MessageCircle, color: '#8b5cf6', path: '/portal/messages/new' },
  { id: 'quote', label: 'View Quotes', icon: FileText, color: '#f59e0b', path: '/portal/quotes' },
];

export default function FAB({ actions = defaultActions, onAction }) {
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();

  const handleAction = (action) => {
    setIsOpen(false);
    if (onAction) {
      onAction(action);
    } else if (action.path) {
      navigate(action.path);
    }
  };

  return (
    <div className="fab-container">
      {/* Backdrop */}
      {isOpen && (
        <div className="fab-backdrop" onClick={() => setIsOpen(false)} />
      )}

      {/* Action items */}
      <div className={`fab-actions ${isOpen ? 'open' : ''}`}>
        {actions.map((action, index) => (
          <button
            key={action.id}
            className="fab-action"
            style={{
              '--action-color': action.color,
              '--delay': `${index * 50}ms`,
            }}
            onClick={() => handleAction(action)}
          >
            <span className="action-label">{action.label}</span>
            <span className="action-icon" style={{ background: action.color }}>
              <action.icon className="icon" />
            </span>
          </button>
        ))}
      </div>

      {/* Main FAB button */}
      <button
        className={`fab-main ${isOpen ? 'open' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        aria-label={isOpen ? 'Close menu' : 'Open quick actions'}
      >
        {isOpen ? <X className="icon" /> : <Plus className="icon" />}
      </button>

      <style jsx>{`
        .fab-container {
          position: fixed;
          bottom: calc(80px + env(safe-area-inset-bottom));
          right: 16px;
          z-index: 90;
        }

        @media (min-width: 769px) {
          .fab-container {
            bottom: 24px;
            right: 24px;
          }
        }

        .fab-backdrop {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.3);
          z-index: -1;
        }

        .fab-main {
          width: 56px;
          height: 56px;
          border-radius: 16px;
          background: linear-gradient(135deg, var(--primary), var(--primary-dark));
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4);
          transition: transform 0.3s, box-shadow 0.3s;
        }

        .fab-main:hover {
          transform: scale(1.05);
          box-shadow: 0 6px 24px rgba(59, 130, 246, 0.5);
        }

        .fab-main.open {
          transform: rotate(45deg);
          background: var(--text-secondary);
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        }

        .fab-main .icon {
          width: 24px;
          height: 24px;
          transition: transform 0.3s;
        }

        .fab-actions {
          position: absolute;
          bottom: 70px;
          right: 0;
          display: flex;
          flex-direction: column;
          gap: 12px;
          opacity: 0;
          pointer-events: none;
          transform: translateY(20px);
          transition: opacity 0.3s, transform 0.3s;
        }

        .fab-actions.open {
          opacity: 1;
          pointer-events: all;
          transform: translateY(0);
        }

        .fab-action {
          display: flex;
          align-items: center;
          gap: 12px;
          opacity: 0;
          transform: translateY(10px) scale(0.9);
          transition: opacity 0.2s var(--delay), transform 0.2s var(--delay);
        }

        .fab-actions.open .fab-action {
          opacity: 1;
          transform: translateY(0) scale(1);
        }

        .action-label {
          padding: 8px 16px;
          background: var(--bg-primary);
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          white-space: nowrap;
          box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
        }

        .action-icon {
          width: 44px;
          height: 44px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
        }

        .action-icon .icon {
          width: 20px;
          height: 20px;
        }
      `}</style>
    </div>
  );
}
```

---

## File 4: Pull to Refresh
**Path:** `frontend/src/components/mobile/PullToRefresh.jsx`

```jsx
/**
 * Pull to Refresh - Touch gesture refresh component
 */

import React, { useState, useRef, useCallback } from 'react';
import { RefreshCw } from 'lucide-react';

const THRESHOLD = 80;
const RESISTANCE = 2.5;

export default function PullToRefresh({ onRefresh, children, disabled = false }) {
  const [pullDistance, setPullDistance] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const containerRef = useRef(null);
  const startY = useRef(0);
  const isPulling = useRef(false);

  const handleTouchStart = useCallback((e) => {
    if (disabled || isRefreshing) return;
    
    const container = containerRef.current;
    if (container && container.scrollTop === 0) {
      startY.current = e.touches[0].clientY;
      isPulling.current = true;
    }
  }, [disabled, isRefreshing]);

  const handleTouchMove = useCallback((e) => {
    if (!isPulling.current || disabled || isRefreshing) return;

    const currentY = e.touches[0].clientY;
    const diff = currentY - startY.current;

    if (diff > 0) {
      // Apply resistance
      const distance = Math.min(diff / RESISTANCE, 120);
      setPullDistance(distance);

      // Prevent scroll while pulling
      if (distance > 10) {
        e.preventDefault();
      }
    }
  }, [disabled, isRefreshing]);

  const handleTouchEnd = useCallback(async () => {
    if (!isPulling.current || disabled) return;

    isPulling.current = false;

    if (pullDistance >= THRESHOLD && onRefresh) {
      setIsRefreshing(true);
      
      try {
        await onRefresh();
      } finally {
        setIsRefreshing(false);
      }
    }

    setPullDistance(0);
  }, [pullDistance, onRefresh, disabled]);

  const progress = Math.min(pullDistance / THRESHOLD, 1);
  const shouldTrigger = pullDistance >= THRESHOLD;

  return (
    <div
      ref={containerRef}
      className="pull-to-refresh-container"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {/* Pull indicator */}
      <div
        className={`pull-indicator ${isRefreshing ? 'refreshing' : ''} ${shouldTrigger ? 'ready' : ''}`}
        style={{
          transform: `translateY(${pullDistance - 60}px)`,
          opacity: progress,
        }}
      >
        <div
          className="indicator-content"
          style={{
            transform: `rotate(${progress * 180}deg)`,
          }}
        >
          <RefreshCw className={`icon ${isRefreshing ? 'spinning' : ''}`} />
        </div>
        <span className="indicator-text">
          {isRefreshing ? 'Refreshing...' : shouldTrigger ? 'Release to refresh' : 'Pull to refresh'}
        </span>
      </div>

      {/* Content */}
      <div
        className="pull-content"
        style={{
          transform: pullDistance > 0 ? `translateY(${pullDistance}px)` : undefined,
        }}
      >
        {children}
      </div>

      <style jsx>{`
        .pull-to-refresh-container {
          position: relative;
          overflow-y: auto;
          overflow-x: hidden;
          height: 100%;
          -webkit-overflow-scrolling: touch;
        }

        .pull-indicator {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 60px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 8px;
          z-index: 10;
          pointer-events: none;
        }

        .indicator-content {
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .icon {
          width: 24px;
          height: 24px;
          color: var(--primary);
          transition: color 0.2s;
        }

        .pull-indicator.ready .icon {
          color: var(--success);
        }

        .icon.spinning {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .indicator-text {
          font-size: 12px;
          color: var(--text-muted);
          font-weight: 500;
        }

        .pull-indicator.ready .indicator-text {
          color: var(--success);
        }

        .pull-content {
          transition: transform 0.2s ease-out;
          min-height: 100%;
        }

        @media (min-width: 769px) {
          .pull-indicator {
            display: none;
          }
        }
      `}</style>
    </div>
  );
}
```

---

## File 5: Mobile Header
**Path:** `frontend/src/components/mobile/MobileHeader.jsx`

```jsx
/**
 * Mobile Header - Compact header for mobile views
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Bell, User, ArrowLeft, Search, X } from 'lucide-react';

export default function MobileHeader({
  title,
  showBack = false,
  backPath,
  showSearch = false,
  onSearch,
  notifications = 0,
  user,
}) {
  const navigate = useNavigate();
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const handleBack = () => {
    if (backPath) {
      navigate(backPath);
    } else {
      navigate(-1);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (onSearch && searchQuery.trim()) {
      onSearch(searchQuery);
    }
  };

  return (
    <header className="mobile-header">
      {/* Search mode */}
      {searchOpen ? (
        <div className="search-bar">
          <form onSubmit={handleSearch}>
            <Search className="search-icon" />
            <input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              autoFocus
            />
          </form>
          <button className="close-btn" onClick={() => { setSearchOpen(false); setSearchQuery(''); }}>
            <X className="w-5 h-5" />
          </button>
        </div>
      ) : (
        <>
          {/* Left section */}
          <div className="header-left">
            {showBack ? (
              <button className="back-btn" onClick={handleBack}>
                <ArrowLeft className="w-5 h-5" />
              </button>
            ) : (
              <Link to="/portal" className="logo">
                <span className="logo-icon">L</span>
              </Link>
            )}
          </div>

          {/* Title */}
          <div className="header-center">
            <h1 className="title">{title || 'LogiAccounting'}</h1>
          </div>

          {/* Right section */}
          <div className="header-right">
            {showSearch && (
              <button className="icon-btn" onClick={() => setSearchOpen(true)}>
                <Search className="w-5 h-5" />
              </button>
            )}
            
            <Link to="/portal/notifications" className="icon-btn notification-btn">
              <Bell className="w-5 h-5" />
              {notifications > 0 && (
                <span className="badge">{notifications > 9 ? '9+' : notifications}</span>
              )}
            </Link>
            
            <Link to="/portal/account" className="avatar-btn">
              {user?.avatar ? (
                <img src={user.avatar} alt={user.name} />
              ) : (
                <User className="w-5 h-5" />
              )}
            </Link>
          </div>
        </>
      )}

      <style jsx>{`
        .mobile-header {
          position: sticky;
          top: 0;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 16px;
          background: var(--bg-primary);
          border-bottom: 1px solid var(--border-color);
          z-index: 50;
        }

        .header-left, .header-right {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .back-btn, .icon-btn {
          width: 40px;
          height: 40px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 10px;
          color: var(--text-secondary);
        }

        .back-btn:hover, .icon-btn:hover {
          background: var(--bg-secondary);
        }

        .logo-icon {
          width: 36px;
          height: 36px;
          background: linear-gradient(135deg, var(--primary), var(--primary-dark));
          color: white;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 18px;
          font-weight: 700;
        }

        .header-center {
          flex: 1;
          text-align: center;
          padding: 0 8px;
        }

        .title {
          font-size: 17px;
          font-weight: 600;
          margin: 0;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .notification-btn {
          position: relative;
        }

        .badge {
          position: absolute;
          top: 4px;
          right: 4px;
          min-width: 18px;
          height: 18px;
          background: var(--danger);
          color: white;
          font-size: 11px;
          font-weight: 600;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .avatar-btn {
          width: 36px;
          height: 36px;
          background: var(--bg-secondary);
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          overflow: hidden;
          color: var(--text-muted);
        }

        .search-bar {
          flex: 1;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .search-bar form {
          flex: 1;
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          background: var(--bg-secondary);
          border-radius: 10px;
        }

        .search-bar input {
          flex: 1;
          border: none;
          background: transparent;
          outline: none;
          font-size: 16px;
        }

        @media (min-width: 769px) {
          .mobile-header {
            display: none;
          }
        }
      `}</style>
    </header>
  );
}
```

---

## File 6: Install Prompt
**Path:** `frontend/src/components/mobile/InstallPrompt.jsx`

```jsx
/**
 * PWA Install Prompt - Handles app installation
 */

import React, { useState, useEffect } from 'react';
import { Download, X, Smartphone } from 'lucide-react';

let deferredPrompt = null;

// Capture the install prompt event globally
if (typeof window !== 'undefined') {
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    window.dispatchEvent(new CustomEvent('pwainstallready'));
  });
}

export default function InstallPrompt({ onDismiss }) {
  const [showPrompt, setShowPrompt] = useState(false);
  const [isInstalled, setIsInstalled] = useState(false);
  const [isIOS, setIsIOS] = useState(false);

  useEffect(() => {
    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      setIsInstalled(true);
      return;
    }

    // Check if iOS
    const isIOSDevice = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    setIsIOS(isIOSDevice);

    // Check if prompt is available
    if (deferredPrompt) {
      setShowPrompt(true);
    }

    // Listen for install ready event
    const handleInstallReady = () => {
      setShowPrompt(true);
    };

    window.addEventListener('pwainstallready', handleInstallReady);

    // Listen for app installed event
    window.addEventListener('appinstalled', () => {
      setIsInstalled(true);
      setShowPrompt(false);
      deferredPrompt = null;
    });

    return () => {
      window.removeEventListener('pwainstallready', handleInstallReady);
    };
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;

    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    
    if (outcome === 'accepted') {
      console.log('[PWA] User accepted install');
    }

    deferredPrompt = null;
    setShowPrompt(false);
  };

  const handleDismiss = () => {
    setShowPrompt(false);
    localStorage.setItem('pwa_prompt_dismissed', Date.now().toString());
    if (onDismiss) onDismiss();
  };

  if (isInstalled) return null;
  
  const dismissedAt = localStorage.getItem('pwa_prompt_dismissed');
  if (dismissedAt && Date.now() - parseInt(dismissedAt) < 7 * 24 * 60 * 60 * 1000) {
    return null;
  }

  if (!showPrompt && !isIOS) return null;

  return (
    <div className="install-prompt">
      <div className="prompt-content">
        <div className="prompt-icon">
          <Smartphone className="w-8 h-8" />
        </div>
        
        <div className="prompt-text">
          <h3>Install LogiAccounting</h3>
          <p>
            {isIOS
              ? 'Tap the share button and "Add to Home Screen"'
              : 'Install our app for a better experience'}
          </p>
        </div>

        <div className="prompt-actions">
          {!isIOS && (
            <button className="install-btn" onClick={handleInstall}>
              <Download className="w-4 h-4" />
              Install
            </button>
          )}
          <button className="dismiss-btn" onClick={handleDismiss}>
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      <style jsx>{`
        .install-prompt {
          position: fixed;
          bottom: calc(90px + env(safe-area-inset-bottom));
          left: 16px;
          right: 16px;
          z-index: 200;
          animation: slideUp 0.3s ease-out;
        }

        @keyframes slideUp {
          from { transform: translateY(100%); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }

        .prompt-content {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 16px;
          background: var(--bg-primary);
          border: 1px solid var(--border-color);
          border-radius: 16px;
          box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
        }

        .prompt-icon {
          width: 48px;
          height: 48px;
          background: linear-gradient(135deg, var(--primary), var(--primary-dark));
          color: white;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .prompt-text { flex: 1; }
        .prompt-text h3 { font-size: 15px; font-weight: 600; margin: 0 0 4px; }
        .prompt-text p { font-size: 13px; color: var(--text-muted); margin: 0; }

        .prompt-actions { display: flex; align-items: center; gap: 8px; }

        .install-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 10px 16px;
          background: var(--primary);
          color: white;
          border-radius: 10px;
          font-size: 14px;
          font-weight: 500;
        }

        .dismiss-btn {
          width: 36px;
          height: 36px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--text-muted);
          border-radius: 8px;
        }
      `}</style>
    </div>
  );
}
```

---

## File 7: Update Available
**Path:** `frontend/src/components/mobile/UpdateAvailable.jsx`

```jsx
/**
 * Update Available - Notification for PWA updates
 */

import React, { useState, useEffect } from 'react';
import { RefreshCw, X } from 'lucide-react';
import { swManager } from '../pwa/serviceWorker';

export default function UpdateAvailable() {
  const [showUpdate, setShowUpdate] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);

  useEffect(() => {
    swManager.onUpdateAvailable = () => {
      setShowUpdate(true);
    };

    if (swManager.updateAvailable) {
      setShowUpdate(true);
    }
  }, []);

  const handleUpdate = () => {
    setIsUpdating(true);
    swManager.applyUpdate();
  };

  if (!showUpdate) return null;

  return (
    <div className="update-banner">
      <div className="update-content">
        <RefreshCw className={`update-icon ${isUpdating ? 'spinning' : ''}`} />
        <span className="update-text">
          {isUpdating ? 'Updating...' : 'A new version is available'}
        </span>
      </div>
      
      <div className="update-actions">
        {!isUpdating && (
          <>
            <button className="update-btn" onClick={handleUpdate}>
              Update Now
            </button>
            <button className="dismiss-btn" onClick={() => setShowUpdate(false)}>
              <X className="w-4 h-4" />
            </button>
          </>
        )}
      </div>

      <style jsx>{`
        .update-banner {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 16px;
          background: linear-gradient(135deg, var(--primary), var(--primary-dark));
          color: white;
          z-index: 1000;
          animation: slideDown 0.3s ease-out;
        }

        @keyframes slideDown {
          from { transform: translateY(-100%); }
          to { transform: translateY(0); }
        }

        .update-content { display: flex; align-items: center; gap: 12px; }
        .update-icon { width: 20px; height: 20px; }
        .update-icon.spinning { animation: spin 1s linear infinite; }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .update-text { font-size: 14px; font-weight: 500; }
        .update-actions { display: flex; align-items: center; gap: 8px; }

        .update-btn {
          padding: 8px 16px;
          background: white;
          color: var(--primary);
          border-radius: 8px;
          font-size: 13px;
          font-weight: 600;
        }

        .dismiss-btn {
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          opacity: 0.8;
        }
      `}</style>
    </div>
  );
}
```

---

## File 8: Mobile Layout
**Path:** `frontend/src/layouts/MobileLayout.jsx`

```jsx
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
```

---

## File 9: Mobile API Service
**Path:** `frontend/src/services/mobileAPI.js`

```javascript
/**
 * Mobile API Service
 * Handles all mobile-specific API calls
 */

import axios from 'axios';
import { offlineStorage } from '../pwa/offlineStorage';

const API_BASE = '/api/mobile/v1';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('portal_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle errors and offline fallback
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (!navigator.onLine && error.config.method === 'get') {
      const cachedData = await offlineStorage.getCachedData(error.config.url);
      if (cachedData) {
        return { data: cachedData, cached: true };
      }
    }

    if (error.response?.status === 401) {
      localStorage.removeItem('portal_token');
      window.location.href = '/portal/login';
    }

    return Promise.reject(error);
  }
);

// Cache successful GET responses
api.interceptors.response.use(
  async (response) => {
    if (response.config.method === 'get' && response.data) {
      await offlineStorage.cacheData(response.config.url, 'api', response.data, 30);
    }
    return response;
  }
);

export const mobileAPI = {
  // Home
  getHome: () => api.get('/home'),
  getQuickStats: () => api.get('/quick-stats'),
  getActivity: (limit = 10) => api.get('/activity', { params: { limit } }),
  getQuickActions: () => api.get('/quick-actions'),
  getOfflineData: () => api.get('/offline-data'),
  getAlerts: () => api.get('/alerts'),

  // Notifications
  getVapidKey: () => api.get('/notifications/vapid-key'),
  getNotifications: (params) => api.get('/notifications', { params }),
  getUnreadCount: () => api.get('/notifications/unread-count'),
  markRead: (notificationId) => api.post(`/notifications/${notificationId}/read`),
  markAllRead: () => api.post('/notifications/read-all'),
  getSubscriptions: () => api.get('/notifications/subscriptions'),
  subscribePush: (data) => api.post('/notifications/subscribe', data),
  unsubscribePush: (subscriptionId) => api.delete(`/notifications/subscriptions/${subscriptionId}`),
  updateNotificationPreferences: (subscriptionId, preferences) =>
    api.put(`/notifications/subscriptions/${subscriptionId}/preferences`, preferences),

  // Devices
  getDevices: () => api.get('/devices'),
  registerDevice: (data) => api.post('/devices', data),
  updateDevice: (deviceId, data) => api.put(`/devices/${deviceId}`, data),
  unregisterDevice: (deviceId) => api.delete(`/devices/${deviceId}`),
  pingDevice: (deviceId) => api.post(`/devices/${deviceId}/ping`),

  // Sync
  sync: async (data) => {
    const pendingActions = await offlineStorage.getPendingActions();
    
    const response = await api.post('/sync', {
      last_sync: data?.last_sync,
      pending_actions: pendingActions,
    });

    if (response.data.processed) {
      for (const result of response.data.processed) {
        if (result.status === 'success') {
          await offlineStorage.markActionSynced(result.offline_id, result.server_id);
        }
      }
    }

    await offlineStorage.setSyncState('last_sync', response.data.server_time);
    await offlineStorage.clearSyncedActions();

    return response;
  },
  getSyncStatus: () => api.get('/sync/status'),
  fullSync: () => api.post('/sync/full'),

  // Offline Actions
  queueOfflineAction: async (type, data) => {
    const action = await offlineStorage.queueAction(type, data);
    
    if (navigator.onLine) {
      try {
        await mobileAPI.sync();
      } catch (error) {
        console.log('[Mobile API] Will sync later');
      }
    } else {
      if ('serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype) {
        const registration = await navigator.serviceWorker.ready;
        await registration.sync.register('sync-offline-actions');
      }
    }
    
    return action;
  },

  getPendingActionsCount: async () => {
    const actions = await offlineStorage.getPendingActions();
    return actions.length;
  },
};

export default mobileAPI;
```

---

## File 10: Components Index
**Path:** `frontend/src/components/mobile/index.js`

```javascript
/**
 * Mobile Components Index
 */

export { default as BottomNav } from './BottomNav';
export { default as FAB } from './FAB';
export { default as MobileHeader } from './MobileHeader';
export { default as PullToRefresh } from './PullToRefresh';
export { default as InstallPrompt } from './InstallPrompt';
export { default as UpdateAvailable } from './UpdateAvailable';
```

---

## Summary Part 4

| File | Description | Lines |
|------|-------------|-------|
| `offlineStorage.js` | IndexedDB wrapper | ~280 |
| `BottomNav.jsx` | Bottom navigation | ~100 |
| `FAB.jsx` | Floating action button | ~180 |
| `PullToRefresh.jsx` | Pull to refresh | ~150 |
| `MobileHeader.jsx` | Mobile header | ~200 |
| `InstallPrompt.jsx` | PWA install prompt | ~160 |
| `UpdateAvailable.jsx` | Update notification | ~90 |
| `MobileLayout.jsx` | Mobile layout | ~150 |
| `mobileAPI.js` | Mobile API service | ~150 |
| `index.js` | Components export | ~10 |
| **Total** | | **~1,470 lines** |

---

## Phase 28 Complete Summary

| Part | Description | Files | Lines |
|------|-------------|-------|-------|
| Part 1 | Backend Services | 5 | ~925 |
| Part 2 | Backend Routes | 5 | ~390 |
| Part 3 | PWA Core | 6 | ~880 |
| Part 4 | Frontend Components | 10 | ~1,470 |
| **Total** | | **26** | **~3,665** |
