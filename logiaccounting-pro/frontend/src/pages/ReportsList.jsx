/**
 * ReportsList - Reports management page
 */

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Plus,
  Search,
  Star,
  StarOff,
  MoreVertical,
  Play,
  Edit,
  Trash2,
  Clock,
  Share2,
  Copy,
  FileText,
} from 'lucide-react';
import { reportsAPI } from '../services/api/reports';

export default function ReportsList() {
  const navigate = useNavigate();

  const [reports, setReports] = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [categories, setCategories] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [viewMode, setViewMode] = useState('grid');
  const [activeMenu, setActiveMenu] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [reportsRes, favoritesRes, categoriesRes] = await Promise.all([
        reportsAPI.list(),
        reportsAPI.getFavorites(),
        reportsAPI.getCategories(),
      ]);

      setReports(reportsRes.data || []);
      setFavorites(favoritesRes.data?.map(r => r.id) || []);
      setCategories(categoriesRes.data || []);
    } catch (error) {
      console.error('Failed to load reports:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleFavorite = async (reportId) => {
    try {
      await reportsAPI.toggleFavorite(reportId);
      setFavorites(prev =>
        prev.includes(reportId)
          ? prev.filter(id => id !== reportId)
          : [...prev, reportId]
      );
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
    }
  };

  const handleDelete = async (reportId) => {
    if (!window.confirm('Are you sure you want to delete this report?')) return;

    try {
      await reportsAPI.delete(reportId);
      setReports(prev => prev.filter(r => r.id !== reportId));
    } catch (error) {
      console.error('Failed to delete report:', error);
    }
  };

  const handleDuplicate = async (reportId) => {
    try {
      const report = reports.find(r => r.id === reportId);
      const newReport = await reportsAPI.create({
        ...report,
        name: `${report.name} (Copy)`,
      });
      setReports(prev => [newReport.data, ...prev]);
    } catch (error) {
      console.error('Failed to duplicate report:', error);
    }
  };

  const filteredReports = reports.filter(report => {
    const matchesSearch = report.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      report.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || report.category_id === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="reports-list-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1>Reports</h1>
          <p>Create and manage your business reports</p>
        </div>
        <Link to="/reports/new" className="btn-primary">
          <Plus className="w-4 h-4" />
          New Report
        </Link>
      </div>

      {/* Toolbar */}
      <div className="toolbar">
        <div className="search-box">
          <Search className="w-4 h-4" />
          <input
            type="text"
            placeholder="Search reports..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="filters">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            <option value="all">All Categories</option>
            {categories.map(cat => (
              <option key={cat.id} value={cat.id}>
                {cat.icon} {cat.name}
              </option>
            ))}
          </select>

          <div className="view-toggle">
            <button
              className={viewMode === 'grid' ? 'active' : ''}
              onClick={() => setViewMode('grid')}
            >
              Grid
            </button>
            <button
              className={viewMode === 'list' ? 'active' : ''}
              onClick={() => setViewMode('list')}
            >
              List
            </button>
          </div>
        </div>
      </div>

      {/* Quick Access */}
      <div className="quick-access">
        <h3>Quick Access</h3>
        <div className="quick-cards">
          <Link to="/reports/recent" className="quick-card">
            <Clock className="w-5 h-5" />
            <span>Recent</span>
          </Link>
          <Link to="/reports/favorites" className="quick-card">
            <Star className="w-5 h-5" />
            <span>Favorites</span>
          </Link>
          <Link to="/reports/scheduled" className="quick-card">
            <FileText className="w-5 h-5" />
            <span>Scheduled</span>
          </Link>
        </div>
      </div>

      {/* Reports Grid/List */}
      {isLoading ? (
        <div className="loading">Loading reports...</div>
      ) : filteredReports.length === 0 ? (
        <div className="empty-state">
          <FileText className="w-12 h-12" />
          <h3>No reports found</h3>
          <p>Create your first report to get started</p>
          <Link to="/reports/new" className="btn-primary">
            Create Report
          </Link>
        </div>
      ) : (
        <div className={`reports-${viewMode}`}>
          {filteredReports.map(report => (
            <ReportCard
              key={report.id}
              report={report}
              isFavorite={favorites.includes(report.id)}
              viewMode={viewMode}
              activeMenu={activeMenu}
              onToggleFavorite={() => handleToggleFavorite(report.id)}
              onMenuToggle={() => setActiveMenu(activeMenu === report.id ? null : report.id)}
              onEdit={() => navigate(`/reports/${report.id}/edit`)}
              onDelete={() => handleDelete(report.id)}
              onDuplicate={() => handleDuplicate(report.id)}
              onRun={() => navigate(`/reports/${report.id}/preview`)}
            />
          ))}
        </div>
      )}

      <style jsx>{`
        .reports-list-page {
          padding: 24px;
          max-width: 1400px;
          margin: 0 auto;
        }

        .page-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
        }

        .page-header h1 {
          margin: 0;
          font-size: 24px;
        }

        .page-header p {
          margin: 4px 0 0;
          color: var(--text-muted);
        }

        .btn-primary {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 20px;
          background: var(--primary);
          color: white;
          border-radius: 8px;
          font-weight: 500;
        }

        .toolbar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
        }

        .search-box {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 10px 16px;
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          width: 300px;
        }

        .search-box input {
          flex: 1;
          border: none;
          background: transparent;
          outline: none;
        }

        .filters {
          display: flex;
          gap: 12px;
        }

        .filters select {
          padding: 10px 16px;
          border: 1px solid var(--border-color);
          border-radius: 8px;
        }

        .view-toggle {
          display: flex;
          border: 1px solid var(--border-color);
          border-radius: 8px;
          overflow: hidden;
        }

        .view-toggle button {
          padding: 10px 16px;
          border-right: 1px solid var(--border-color);
        }

        .view-toggle button:last-child {
          border-right: none;
        }

        .view-toggle button.active {
          background: var(--primary-light);
          color: var(--primary);
        }

        .quick-access {
          margin-bottom: 24px;
        }

        .quick-access h3 {
          font-size: 14px;
          color: var(--text-muted);
          margin-bottom: 12px;
        }

        .quick-cards {
          display: flex;
          gap: 12px;
        }

        .quick-card {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 20px;
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          color: var(--text-secondary);
          transition: all 0.2s;
        }

        .quick-card:hover {
          border-color: var(--primary);
          color: var(--primary);
        }

        .reports-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 20px;
        }

        .reports-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .loading,
        .empty-state {
          text-align: center;
          padding: 60px;
          color: var(--text-muted);
        }

        .empty-state h3 {
          margin: 16px 0 8px;
        }

        .empty-state .btn-primary {
          margin-top: 16px;
          display: inline-flex;
        }
      `}</style>
    </div>
  );
}

// Report Card Component
function ReportCard({
  report,
  isFavorite,
  viewMode,
  activeMenu,
  onToggleFavorite,
  onMenuToggle,
  onEdit,
  onDelete,
  onDuplicate,
  onRun,
}) {
  return (
    <div className={`report-card ${viewMode}`}>
      <div className="card-header">
        <div className="card-icon">
          <FileText className="w-5 h-5" />
        </div>
        <div className="card-info">
          <h4>{report.name}</h4>
          {report.description && <p>{report.description}</p>}
        </div>
        <button className="favorite-btn" onClick={onToggleFavorite}>
          {isFavorite ? (
            <Star className="w-4 h-4 filled" />
          ) : (
            <StarOff className="w-4 h-4" />
          )}
        </button>
      </div>

      <div className="card-meta">
        <span>Updated {new Date(report.updated_at).toLocaleDateString()}</span>
        {report.is_public && <span className="badge">Public</span>}
      </div>

      <div className="card-actions">
        <button className="action-btn primary" onClick={onRun}>
          <Play className="w-4 h-4" />
          Run
        </button>
        <button className="action-btn" onClick={onEdit}>
          <Edit className="w-4 h-4" />
        </button>
        <div className="menu-wrapper">
          <button className="action-btn" onClick={onMenuToggle}>
            <MoreVertical className="w-4 h-4" />
          </button>
          {activeMenu === report.id && (
            <div className="dropdown-menu">
              <button onClick={onDuplicate}>
                <Copy className="w-4 h-4" />
                Duplicate
              </button>
              <button onClick={() => {}}>
                <Share2 className="w-4 h-4" />
                Share
              </button>
              <button className="danger" onClick={onDelete}>
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
            </div>
          )}
        </div>
      </div>

      <style jsx>{`
        .report-card {
          background: var(--bg-primary);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          padding: 20px;
          transition: all 0.2s;
        }

        .report-card:hover {
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .report-card.list {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .report-card.list .card-header {
          flex: 1;
        }

        .card-header {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          margin-bottom: 12px;
        }

        .card-icon {
          padding: 10px;
          background: var(--primary-light);
          color: var(--primary);
          border-radius: 8px;
        }

        .card-info {
          flex: 1;
        }

        .card-info h4 {
          margin: 0;
          font-size: 15px;
        }

        .card-info p {
          margin: 4px 0 0;
          font-size: 13px;
          color: var(--text-muted);
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }

        .favorite-btn {
          padding: 4px;
          color: var(--text-muted);
        }

        .favorite-btn :global(.filled) {
          color: #f59e0b;
          fill: #f59e0b;
        }

        .card-meta {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 12px;
          color: var(--text-muted);
          margin-bottom: 16px;
        }

        .badge {
          padding: 2px 8px;
          background: var(--primary-light);
          color: var(--primary);
          border-radius: 4px;
          font-size: 11px;
          font-weight: 500;
        }

        .card-actions {
          display: flex;
          gap: 8px;
        }

        .action-btn {
          padding: 8px 12px;
          border: 1px solid var(--border-color);
          border-radius: 6px;
          font-size: 13px;
          display: flex;
          align-items: center;
          gap: 6px;
          transition: all 0.2s;
        }

        .action-btn:hover {
          background: var(--bg-secondary);
        }

        .action-btn.primary {
          background: var(--primary);
          color: white;
          border-color: var(--primary);
        }

        .action-btn.primary:hover {
          background: var(--primary-dark);
        }

        .menu-wrapper {
          position: relative;
        }

        .dropdown-menu {
          position: absolute;
          top: 100%;
          right: 0;
          background: var(--bg-primary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
          min-width: 150px;
          z-index: 100;
        }

        .dropdown-menu button {
          display: flex;
          align-items: center;
          gap: 8px;
          width: 100%;
          padding: 10px 14px;
          font-size: 13px;
          text-align: left;
        }

        .dropdown-menu button:hover {
          background: var(--bg-secondary);
        }

        .dropdown-menu button.danger {
          color: #ef4444;
        }

        .dropdown-menu button.danger:hover {
          background: rgba(239, 68, 68, 0.1);
        }
      `}</style>
    </div>
  );
}
