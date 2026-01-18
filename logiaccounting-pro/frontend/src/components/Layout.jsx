import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

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
  { section: 'Administration', roles: ['admin'] },
  { path: '/users', icon: '👥', label: 'Users', roles: ['admin'] },
  { path: '/reports', icon: '📈', label: 'Reports', roles: ['admin'] }
];

const pageTitles = {
  '/dashboard': 'Dashboard',
  '/inventory': 'Inventory Management',
  '/projects': 'Projects',
  '/movements': 'Stock Movements',
  '/transactions': 'Transactions',
  '/payments': 'Payments',
  '/users': 'User Management',
  '/reports': 'Reports & Analytics'
};

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

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
          <div className="user-info">
            <div className="user-name">{user?.first_name} {user?.last_name}</div>
            <div className="user-role">{user?.role}</div>
          </div>
        </header>
        {children}
      </main>
    </div>
  );
}
