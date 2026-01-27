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
