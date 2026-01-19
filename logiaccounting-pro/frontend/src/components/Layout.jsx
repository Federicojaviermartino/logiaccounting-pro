import { useState } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import NotificationBell from './NotificationBell';
import ThemeToggle from './ThemeToggle';
import LanguageSelector from './LanguageSelector';
import CommandPalette from './CommandPalette';
import ShortcutsHelp from './ShortcutsHelp';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';

const navItems = [
  { path: '/dashboard', icon: '📊', label: 'Dashboard', roles: ['admin', 'client', 'supplier'] },

  { section: 'Logistics', roles: ['admin', 'supplier'] },
  { path: '/inventory', icon: '📦', label: 'Inventory', roles: ['admin', 'supplier'] },
  { path: '/movements', icon: '🔄', label: 'Movements', roles: ['admin', 'supplier'] },

  { section: 'Projects', roles: ['admin', 'client'] },
  { path: '/projects', icon: '📁', label: 'Projects', roles: ['admin', 'client'] },

  { section: 'Finance', roles: ['admin', 'client', 'supplier'] },
  { path: '/transactions', icon: '💰', label: 'Transactions', roles: ['admin', 'client', 'supplier'] },
  { path: '/payments', icon: '💳', label: 'Payments', roles: ['admin', 'client', 'supplier'] },
  { path: '/budgets', icon: '💵', label: 'Budgets', roles: ['admin'] },
  { path: '/recurring', icon: '🔁', label: 'Recurring', roles: ['admin'] },
  { path: '/reconciliation', icon: '🏦', label: 'Reconciliation', roles: ['admin'] },
  { path: '/currencies', icon: '💱', label: 'Currencies', roles: ['admin'] },

  { section: 'AI Tools', roles: ['admin'] },
  { path: '/ai-dashboard', icon: '🤖', label: 'AI Dashboard', roles: ['admin'] },
  { path: '/invoice-ocr', icon: '📄', label: 'Invoice OCR', roles: ['admin', 'supplier'] },
  { path: '/assistant', icon: '💬', label: 'Assistant', roles: ['admin'] },

  { section: 'Administration', roles: ['admin'] },
  { path: '/users', icon: '👥', label: 'Users', roles: ['admin'] },
  { path: '/approvals', icon: '✅', label: 'Approvals', roles: ['admin', 'manager'] },
  { path: '/reports', icon: '📈', label: 'Reports', roles: ['admin'] },
  { path: '/report-builder', icon: '📊', label: 'Report Builder', roles: ['admin'] },
  { path: '/dashboard-builder', icon: '🎛️', label: 'Dashboard Builder', roles: ['admin'] },
  { path: '/scheduled-reports', icon: '📅', label: 'Scheduled Reports', roles: ['admin'] },
  { path: '/activity-log', icon: '📋', label: 'Activity Log', roles: ['admin'] },
  { path: '/bulk-operations', icon: '📥', label: 'Bulk Operations', roles: ['admin'] },
  { path: '/backup', icon: '💾', label: 'Backup', roles: ['admin'] },
  { path: '/webhooks', icon: '🔗', label: 'Webhooks', roles: ['admin'] },
  { path: '/api-keys', icon: '🔑', label: 'API Keys', roles: ['admin'] },

  { section: 'Client Portal', roles: ['client'] },
  { path: '/portal/client', icon: '🏠', label: 'My Dashboard', roles: ['client'] },
  { path: '/portal/client/projects', icon: '📁', label: 'My Projects', roles: ['client'] },
  { path: '/portal/client/payments', icon: '💳', label: 'My Payments', roles: ['client'] },

  { section: 'Supplier Portal', roles: ['supplier'] },
  { path: '/portal/supplier', icon: '🏠', label: 'My Dashboard', roles: ['supplier'] },
  { path: '/portal/supplier/orders', icon: '📦', label: 'My Orders', roles: ['supplier'] },
  { path: '/portal/supplier/payments', icon: '💰', label: 'My Payments', roles: ['supplier'] },

  { section: 'Settings', roles: ['admin', 'client', 'supplier'] },
  { path: '/settings', icon: '⚙️', label: 'Settings', roles: ['admin', 'client', 'supplier'] },
  { path: '/help', icon: '❓', label: 'Help', roles: ['admin', 'client', 'supplier'] }
];

const pageTitles = {
  '/dashboard': 'Dashboard',
  '/inventory': 'Inventory Management',
  '/projects': 'Projects',
  '/movements': 'Stock Movements',
  '/transactions': 'Transactions',
  '/payments': 'Payments',
  '/budgets': 'Budget Management',
  '/recurring': 'Recurring Transactions',
  '/reconciliation': 'Bank Reconciliation',
  '/currencies': 'Currency Management',
  '/users': 'User Management',
  '/approvals': 'Approval Workflows',
  '/reports': 'Reports & Analytics',
  '/report-builder': 'Report Builder',
  '/dashboard-builder': 'Dashboard Builder',
  '/scheduled-reports': 'Scheduled Reports',
  '/ai-dashboard': 'AI Analytics Dashboard',
  '/invoice-ocr': 'Smart Invoice Processing',
  '/assistant': 'Profitability Assistant',
  '/activity-log': 'Activity Log',
  '/bulk-operations': 'Bulk Operations',
  '/backup': 'Backup & Restore',
  '/webhooks': 'Webhooks',
  '/api-keys': 'API Keys Management',
  '/portal/client': 'Client Portal',
  '/portal/client/projects': 'My Projects',
  '/portal/client/payments': 'My Payments',
  '/portal/supplier': 'Supplier Portal',
  '/portal/supplier/orders': 'My Orders',
  '/portal/supplier/payments': 'My Payments',
  '/settings': 'Settings',
  '/help': 'Help Center'
};

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);

  useKeyboardShortcuts({
    onCommandPalette: () => setShowCommandPalette(true),
    onShowShortcuts: () => setShowShortcuts(true),
    onCloseModal: () => {
      setShowCommandPalette(false);
      setShowShortcuts(false);
    }
  });

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-header">
          <span className="sidebar-logo">📦</span>
          <span className="sidebar-title">LogiAccounting</span>
        </div>
        
        <nav className="sidebar-nav">
          {navItems.map((item, index) => {
            if (!item.roles.includes(user?.role)) return null;
            
            if (item.section) {
              return (
                <div key={`section-${index}`} className="nav-section">
                  <div className="nav-section-title">{item.section}</div>
                </div>
              );
            }
            
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              >
                <span className="nav-icon">{item.icon}</span>
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
        
        <div className="sidebar-footer">
          <button className="logout-btn" onClick={handleLogout}>
            <span>🚪</span>
            <span>Logout</span>
          </button>
        </div>
      </aside>
      
      <main className="main-content">
        <header className="page-header">
          <h1 className="page-title">{pageTitles[location.pathname] || 'Dashboard'}</h1>
          <div className="header-right">
            <LanguageSelector />
            <ThemeToggle />
            <NotificationBell />
            <div className="user-info">
              <div className="user-name">{user?.first_name} {user?.last_name}</div>
              <div className="user-role">{user?.role}</div>
            </div>
          </div>
        </header>
        {children}
      </main>

      <CommandPalette
        isOpen={showCommandPalette}
        onClose={() => setShowCommandPalette(false)}
        onShowShortcuts={() => { setShowCommandPalette(false); setShowShortcuts(true); }}
      />
      <ShortcutsHelp isOpen={showShortcuts} onClose={() => setShowShortcuts(false)} />
    </div>
  );
}
