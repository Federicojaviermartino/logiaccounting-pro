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
