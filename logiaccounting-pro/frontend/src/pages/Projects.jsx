import { useState, useEffect } from 'react';
import { projectsAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import toast from '../utils/toast';

export default function Projects() {
  const { user } = useAuth();
  const [projects, setProjects] = useState([]);
  const [filters, setFilters] = useState({ search: '', status_filter: '' });
  const [modalOpen, setModalOpen] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, [filters]);

  const loadData = async () => {
    try {
      const res = await projectsAPI.getProjects(filters);
      setProjects(res.data.projects || []);
    } catch (error) {
      console.error('Failed to load:', error);
    } finally {
      setLoading(false);
    }
  };

  const openModal = (item = null) => {
    setEditItem(item);
    setFormData(item || { name: '', client: '', description: '', budget: 0, status: 'planning', start_date: '', end_date: '' });
    setModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editItem) {
        await projectsAPI.updateProject(editItem.id, formData);
      } else {
        await projectsAPI.createProject(formData);
      }
      setModalOpen(false);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save project');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this project?')) return;
    try {
      await projectsAPI.deleteProject(id);
      loadData();
    } catch (error) {
      toast.error('Failed to delete project');
    }
  };

  const getStatusBadge = (status) => {
    const colors = { active: 'success', completed: 'primary', planning: 'warning', cancelled: 'danger' };
    return colors[status] || 'gray';
  };

  if (loading) return <div className="text-center text-muted">Loading...</div>;

  return (
    <>
      <div className="toolbar">
        <input
          type="text"
          className="form-input"
          placeholder="Search projects..."
          value={filters.search}
          onChange={(e) => setFilters({ ...filters, search: e.target.value })}
        />
        <select
          className="form-select"
          value={filters.status_filter}
          onChange={(e) => setFilters({ ...filters, status_filter: e.target.value })}
        >
          <option value="">All Status</option>
          <option value="planning">Planning</option>
          <option value="active">Active</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
        {user?.role === 'admin' && (
          <button className="btn btn-primary" onClick={() => openModal()}>+ New Project</button>
        )}
      </div>

      <div className="section">
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Code</th>
                <th>Name</th>
                <th>Client</th>
                <th>Budget</th>
                <th>Status</th>
                <th>Start Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {projects.length === 0 ? (
                <tr className="empty-row"><td colSpan="7">No projects found</td></tr>
              ) : projects.map(p => (
                <tr key={p.id}>
                  <td className="font-mono">{p.code}</td>
                  <td className="font-bold">{p.name}</td>
                  <td>{p.client_name || p.client || '-'}</td>
                  <td className="font-mono">${(p.budget || 0).toLocaleString()}</td>
                  <td><span className={`badge badge-${getStatusBadge(p.status)}`}>{p.status}</span></td>
                  <td>{p.start_date ? new Date(p.start_date).toLocaleDateString() : '-'}</td>
                  <td>
                    {user?.role === 'admin' && (
                      <>
                        <button className="btn btn-secondary btn-sm" onClick={() => openModal(p)}>Edit</button>
                        <button className="btn btn-danger btn-sm ml-2" onClick={() => handleDelete(p.id)}>Delete</button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {modalOpen && (
        <div className="modal-overlay" onClick={() => setModalOpen(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">{editItem ? 'Edit Project' : 'New Project'}</h3>
              <button className="modal-close" onClick={() => setModalOpen(false)}>&times;</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Name *</label>
                  <input className="form-input" value={formData.name || ''} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required />
                </div>
                <div className="form-group">
                  <label className="form-label">Client</label>
                  <input className="form-input" value={formData.client || ''} onChange={(e) => setFormData({ ...formData, client: e.target.value })} />
                </div>
                <div className="form-group">
                  <label className="form-label">Description</label>
                  <textarea className="form-textarea" rows="2" value={formData.description || ''} onChange={(e) => setFormData({ ...formData, description: e.target.value })} />
                </div>
                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label">Budget ($)</label>
                    <input type="number" className="form-input" value={formData.budget || 0} onChange={(e) => setFormData({ ...formData, budget: parseFloat(e.target.value) || 0 })} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Status</label>
                    <select className="form-select" value={formData.status || 'planning'} onChange={(e) => setFormData({ ...formData, status: e.target.value })}>
                      <option value="planning">Planning</option>
                      <option value="active">Active</option>
                      <option value="completed">Completed</option>
                      <option value="cancelled">Cancelled</option>
                    </select>
                  </div>
                </div>
                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label">Start Date</label>
                    <input type="date" className="form-input" value={formData.start_date?.split('T')[0] || ''} onChange={(e) => setFormData({ ...formData, start_date: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">End Date</label>
                    <input type="date" className="form-input" value={formData.end_date?.split('T')[0] || ''} onChange={(e) => setFormData({ ...formData, end_date: e.target.value })} />
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setModalOpen(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
