import { useState, useEffect } from 'react';
import { authAPI } from '../services/api';

export default function Users() {
  const [users, setUsers] = useState([]);
  const [filters, setFilters] = useState({ role: '', status: '' });
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const res = await authAPI.getUsers();
      setUsers(res.data || []);
    } catch (error) {
      console.error('Failed to load users:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = async (userId, newStatus) => {
    if (!window.confirm(`Change user status to ${newStatus}?`)) return;
    try {
      await authAPI.updateUserStatus(userId, newStatus);
      loadData();
    } catch (error) {
      alert('Failed to update status');
    }
  };

  const filteredUsers = users.filter(u => {
    if (filters.role && u.role !== filters.role) return false;
    if (filters.status && u.status !== filters.status) return false;
    return true;
  });

  const getRoleBadge = (role) => {
    const colors = { admin: 'primary', client: 'success', supplier: 'warning' };
    return colors[role] || 'gray';
  };

  const getStatusBadge = (status) => {
    const colors = { active: 'success', inactive: 'gray', suspended: 'danger' };
    return colors[status] || 'gray';
  };

  if (loading) return <div className="text-center text-muted">Loading...</div>;

  return (
    <>
      <div className="stats-grid mb-6">
        <div className="stat-card">
          <span className="stat-icon">👥</span>
          <div className="stat-content">
            <div className="stat-label">Total Users</div>
            <div className="stat-value">{users.length}</div>
          </div>
        </div>
        <div className="stat-card">
          <span className="stat-icon">✅</span>
          <div className="stat-content">
            <div className="stat-label">Active</div>
            <div className="stat-value success">{users.filter(u => u.status === 'active').length}</div>
          </div>
        </div>
        <div className="stat-card">
          <span className="stat-icon">🧑‍💼</span>
          <div className="stat-content">
            <div className="stat-label">Clients</div>
            <div className="stat-value">{users.filter(u => u.role === 'client').length}</div>
          </div>
        </div>
        <div className="stat-card">
          <span className="stat-icon">🏭</span>
          <div className="stat-content">
            <div className="stat-label">Suppliers</div>
            <div className="stat-value">{users.filter(u => u.role === 'supplier').length}</div>
          </div>
        </div>
      </div>

      <div className="toolbar">
        <select className="form-select" value={filters.role} onChange={(e) => setFilters({ ...filters, role: e.target.value })}>
          <option value="">All Roles</option>
          <option value="admin">Admin</option>
          <option value="client">Client</option>
          <option value="supplier">Supplier</option>
        </select>
        <select className="form-select" value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="suspended">Suspended</option>
        </select>
      </div>

      <div className="section">
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Company</th>
                <th>Role</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.length === 0 ? (
                <tr className="empty-row"><td colSpan="7">No users found</td></tr>
              ) : filteredUsers.map(u => (
                <tr key={u.id}>
                  <td className="font-bold">{u.first_name} {u.last_name}</td>
                  <td className="font-mono">{u.email}</td>
                  <td>{u.company_name || '-'}</td>
                  <td>
                    <span className={`badge badge-${getRoleBadge(u.role)}`}>
                      {u.role}
                    </span>
                  </td>
                  <td>
                    <span className={`badge badge-${getStatusBadge(u.status)}`}>
                      {u.status}
                    </span>
                  </td>
                  <td>{new Date(u.created_at).toLocaleDateString()}</td>
                  <td>
                    {u.status === 'active' ? (
                      <>
                        <button className="btn btn-secondary btn-sm" onClick={() => updateStatus(u.id, 'inactive')}>Deactivate</button>
                        <button className="btn btn-danger btn-sm ml-2" onClick={() => updateStatus(u.id, 'suspended')}>Suspend</button>
                      </>
                    ) : (
                      <button className="btn btn-success btn-sm" onClick={() => updateStatus(u.id, 'active')}>Activate</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="info-banner mt-4">
        <strong>Note:</strong> Users can self-register as clients or suppliers. Only admins can manage user status.
        New users are automatically set to "active" status.
      </div>
    </>
  );
}
