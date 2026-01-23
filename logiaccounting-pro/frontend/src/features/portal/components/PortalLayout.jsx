/**
 * Portal Layout - Main layout for customer portal
 */

import React, { useState } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import {
  LayoutDashboard, HelpCircle, FolderOpen, CreditCard,
  FileText, MessageCircle, User, Settings, LogOut,
  Bell, Menu, X, ChevronDown, Search, Book,
} from 'lucide-react';
import { useAuth } from '../../../hooks/useAuth';

const navigation = [
  { name: 'Dashboard', href: '/portal', icon: LayoutDashboard },
  { name: 'Support', href: '/portal/support', icon: HelpCircle },
  { name: 'Knowledge Base', href: '/portal/kb', icon: Book },
  { name: 'Projects', href: '/portal/projects', icon: FolderOpen },
  { name: 'Quotes', href: '/portal/quotes', icon: FileText },
  { name: 'Payments', href: '/portal/payments', icon: CreditCard },
  { name: 'Messages', href: '/portal/messages', icon: MessageCircle },
];

export default function PortalLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const location = useLocation();
  const { user, logout } = useAuth();

  const isActive = (href) => {
    if (href === '/portal') return location.pathname === '/portal';
    return location.pathname.startsWith(href);
  };

  return (
    <div className="portal-layout">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div className="logo">
            <div className="logo-icon">LP</div>
            <span className="logo-text">Customer Portal</span>
          </div>
          <button className="close-btn md:hidden" onClick={() => setSidebarOpen(false)}>
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="sidebar-nav">
          {navigation.map((item) => (
            <Link
              key={item.name}
              to={item.href}
              className={`nav-item ${isActive(item.href) ? 'active' : ''}`}
              onClick={() => setSidebarOpen(false)}
            >
              <item.icon className="nav-icon" />
              <span>{item.name}</span>
            </Link>
          ))}
        </nav>

        <div className="sidebar-footer">
          <Link to="/portal/account" className="nav-item">
            <Settings className="nav-icon" />
            <span>Account Settings</span>
          </Link>
        </div>
      </aside>

      {/* Main Content */}
      <div className="main-content">
        {/* Top Header */}
        <header className="top-header">
          <div className="header-left">
            <button className="menu-btn md:hidden" onClick={() => setSidebarOpen(true)}>
              <Menu className="w-5 h-5" />
            </button>
            <div className="search-box">
              <Search className="search-icon" />
              <input type="text" placeholder="Search..." />
            </div>
          </div>

          <div className="header-right">
            <button className="notification-btn">
              <Bell className="w-5 h-5" />
              <span className="notification-badge">3</span>
            </button>

            <div className="user-menu">
              <button className="user-btn" onClick={() => setUserMenuOpen(!userMenuOpen)}>
                <div className="user-avatar">
                  {user?.name?.charAt(0) || 'U'}
                </div>
                <span className="user-name">{user?.name || 'User'}</span>
                <ChevronDown className="w-4 h-4" />
              </button>

              {userMenuOpen && (
                <div className="user-dropdown">
                  <div className="dropdown-header">
                    <div className="user-email">{user?.email}</div>
                    <div className="user-company">{user?.company_name}</div>
                  </div>
                  <div className="dropdown-divider" />
                  <Link to="/portal/account" className="dropdown-item" onClick={() => setUserMenuOpen(false)}>
                    <User className="w-4 h-4" />
                    <span>Account</span>
                  </Link>
                  <Link to="/portal/account/preferences" className="dropdown-item" onClick={() => setUserMenuOpen(false)}>
                    <Settings className="w-4 h-4" />
                    <span>Preferences</span>
                  </Link>
                  <div className="dropdown-divider" />
                  <button className="dropdown-item logout" onClick={logout}>
                    <LogOut className="w-4 h-4" />
                    <span>Sign Out</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="page-content">
          <Outlet />
        </main>
      </div>

      <style jsx>{`
        .portal-layout {
          display: flex;
          min-height: 100vh;
          background: var(--bg-secondary, #f8fafc);
        }

        .sidebar {
          width: 260px;
          background: var(--bg-primary, #ffffff);
          border-right: 1px solid var(--border-color, #e2e8f0);
          display: flex;
          flex-direction: column;
          position: fixed;
          top: 0;
          left: 0;
          bottom: 0;
          z-index: 50;
          transform: translateX(-100%);
          transition: transform 0.3s ease;
        }

        @media (min-width: 768px) {
          .sidebar {
            transform: translateX(0);
          }
        }

        .sidebar.open {
          transform: translateX(0);
        }

        .sidebar-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.5);
          z-index: 40;
        }

        @media (min-width: 768px) {
          .sidebar-overlay {
            display: none;
          }
        }

        .sidebar-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 20px;
          border-bottom: 1px solid var(--border-color, #e2e8f0);
        }

        .logo {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .logo-icon {
          width: 40px;
          height: 40px;
          background: linear-gradient(135deg, #3b82f6, #1d4ed8);
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: 700;
          font-size: 14px;
        }

        .logo-text {
          font-weight: 600;
          font-size: 16px;
        }

        .sidebar-nav {
          flex: 1;
          padding: 12px;
          overflow-y: auto;
        }

        .nav-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px 16px;
          border-radius: 10px;
          color: var(--text-secondary, #64748b);
          font-weight: 500;
          transition: all 0.2s;
          margin-bottom: 4px;
          text-decoration: none;
        }

        .nav-item:hover {
          background: var(--bg-secondary, #f8fafc);
          color: var(--text-primary, #1e293b);
        }

        .nav-item.active {
          background: rgba(59, 130, 246, 0.1);
          color: #3b82f6;
        }

        .nav-icon {
          width: 20px;
          height: 20px;
        }

        .sidebar-footer {
          padding: 12px;
          border-top: 1px solid var(--border-color, #e2e8f0);
        }

        .main-content {
          flex: 1;
          margin-left: 0;
          display: flex;
          flex-direction: column;
        }

        @media (min-width: 768px) {
          .main-content {
            margin-left: 260px;
          }
        }

        .top-header {
          background: var(--bg-primary, #ffffff);
          border-bottom: 1px solid var(--border-color, #e2e8f0);
          padding: 16px 24px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          position: sticky;
          top: 0;
          z-index: 30;
        }

        .header-left {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .menu-btn {
          padding: 8px;
          border-radius: 8px;
        }

        .search-box {
          display: flex;
          align-items: center;
          gap: 8px;
          background: var(--bg-secondary, #f8fafc);
          padding: 8px 16px;
          border-radius: 8px;
          width: 300px;
        }

        .search-icon {
          width: 18px;
          height: 18px;
          color: var(--text-muted, #94a3b8);
        }

        .search-box input {
          border: none;
          background: transparent;
          outline: none;
          flex: 1;
        }

        .header-right {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .notification-btn {
          position: relative;
          padding: 8px;
          border-radius: 8px;
        }

        .notification-badge {
          position: absolute;
          top: 2px;
          right: 2px;
          width: 18px;
          height: 18px;
          background: #ef4444;
          color: white;
          font-size: 11px;
          font-weight: 600;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .user-menu {
          position: relative;
        }

        .user-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 6px 12px;
          border-radius: 8px;
        }

        .user-avatar {
          width: 32px;
          height: 32px;
          background: #3b82f6;
          color: white;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 600;
        }

        .user-name {
          font-weight: 500;
        }

        .user-dropdown {
          position: absolute;
          top: 100%;
          right: 0;
          margin-top: 8px;
          background: var(--bg-primary, #ffffff);
          border: 1px solid var(--border-color, #e2e8f0);
          border-radius: 12px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          min-width: 200px;
          z-index: 50;
        }

        .dropdown-header {
          padding: 12px 16px;
        }

        .user-email {
          font-weight: 500;
        }

        .user-company {
          font-size: 13px;
          color: var(--text-muted, #94a3b8);
        }

        .dropdown-divider {
          height: 1px;
          background: var(--border-color, #e2e8f0);
        }

        .dropdown-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px 16px;
          color: var(--text-secondary, #64748b);
          width: 100%;
          text-align: left;
          text-decoration: none;
        }

        .dropdown-item:hover {
          background: var(--bg-secondary, #f8fafc);
          color: var(--text-primary, #1e293b);
        }

        .dropdown-item.logout {
          color: #ef4444;
        }

        .page-content {
          flex: 1;
          padding: 24px;
        }
      `}</style>
    </div>
  );
}
