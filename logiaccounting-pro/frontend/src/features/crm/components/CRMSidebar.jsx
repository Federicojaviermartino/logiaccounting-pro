/**
 * CRMSidebar - CRM Module Navigation
 */

import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Building2,
  UserPlus,
  Target,
  Activity,
  FileText,
  Settings,
  TrendingUp,
  Calendar,
} from 'lucide-react';

export default function CRMSidebar() {
  const location = useLocation();

  const navItems = [
    {
      section: 'Overview',
      items: [
        { path: '/crm', icon: LayoutDashboard, label: 'Dashboard', exact: true },
        { path: '/crm/pipeline', icon: Target, label: 'Pipeline' },
      ],
    },
    {
      section: 'Sales',
      items: [
        { path: '/crm/leads', icon: UserPlus, label: 'Leads' },
        { path: '/crm/contacts', icon: Users, label: 'Contacts' },
        { path: '/crm/companies', icon: Building2, label: 'Companies' },
        { path: '/crm/opportunities', icon: TrendingUp, label: 'Opportunities' },
      ],
    },
    {
      section: 'Activities',
      items: [
        { path: '/crm/activities', icon: Activity, label: 'Activities' },
        { path: '/crm/calendar', icon: Calendar, label: 'Calendar' },
      ],
    },
    {
      section: 'Documents',
      items: [
        { path: '/crm/quotes', icon: FileText, label: 'Quotes' },
      ],
    },
    {
      section: 'Settings',
      items: [
        { path: '/crm/settings', icon: Settings, label: 'CRM Settings' },
      ],
    },
  ];

  return (
    <aside className="crm-sidebar">
      <div className="sidebar-header">
        <h2>CRM</h2>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((section) => (
          <div key={section.section} className="nav-section">
            <span className="section-title">{section.section}</span>
            {section.items.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.exact}
                className={({ isActive }) =>
                  `nav-item ${isActive ? 'active' : ''}`
                }
              >
                <item.icon className="nav-icon" />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <style jsx>{`
        .crm-sidebar {
          width: 240px;
          background: var(--bg-primary);
          border-right: 1px solid var(--border-color);
          height: 100%;
          display: flex;
          flex-direction: column;
        }

        .sidebar-header {
          padding: 20px;
          border-bottom: 1px solid var(--border-color);
        }

        .sidebar-header h2 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
        }

        .sidebar-nav {
          flex: 1;
          padding: 16px 12px;
          overflow-y: auto;
        }

        .nav-section {
          margin-bottom: 24px;
        }

        .section-title {
          display: block;
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
          color: var(--text-muted);
          padding: 0 8px;
          margin-bottom: 8px;
        }

        .nav-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 10px 12px;
          border-radius: 8px;
          color: var(--text-secondary);
          font-size: 14px;
          transition: all 0.2s;
          margin-bottom: 2px;
          text-decoration: none;
        }

        .nav-item:hover {
          background: var(--bg-secondary);
          color: var(--text-primary);
        }

        .nav-item.active {
          background: var(--primary-light, rgba(99, 102, 241, 0.1));
          color: var(--primary);
        }

        :global(.nav-icon) {
          width: 18px;
          height: 18px;
        }
      `}</style>
    </aside>
  );
}
