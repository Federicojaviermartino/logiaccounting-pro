import { useState, useEffect } from 'react';
import { teamAPI, invitationsAPI, quotaAPI } from '../services/tenantApi';

const ROLES = [
  { value: 'admin', label: 'Admin', description: 'Full access to all features' },
  { value: 'manager', label: 'Manager', description: 'Can manage team and most settings' },
  { value: 'member', label: 'Member', description: 'Standard user access' },
  { value: 'viewer', label: 'Viewer', description: 'Read-only access' }
];

export default function TeamManagement() {
  const [members, setMembers] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [quota, setQuota] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [activeTab, setActiveTab] = useState('members');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [membersRes, invitationsRes, quotaRes] = await Promise.all([
        teamAPI.list(),
        invitationsAPI.list(),
        quotaAPI.get()
      ]);
      setMembers(membersRes.data.members);
      setInvitations(invitationsRes.data.invitations);
      setQuota(quotaRes.data.quota);
    } catch (err) {
      setError('Failed to load team data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleInvite = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
      email: formData.get('email'),
      role: formData.get('role')
    };

    try {
      await invitationsAPI.create(data);
      setShowInviteModal(false);
      setSuccess('Invitation sent successfully');
      loadData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send invitation');
    }
  };

  const handleUpdateRole = async (userId, newRole) => {
    try {
      await teamAPI.updateRole(userId, { role: newRole });
      setSuccess('Role updated successfully');
      loadData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update role');
    }
  };

  const handleRemoveMember = async (userId) => {
    if (!window.confirm('Are you sure you want to remove this team member?')) return;
    try {
      await teamAPI.remove(userId);
      setSuccess('Team member removed');
      loadData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to remove member');
    }
  };

  const handleRevokeInvitation = async (invitationId) => {
    if (!window.confirm('Are you sure you want to revoke this invitation?')) return;
    try {
      await invitationsAPI.revoke(invitationId);
      setSuccess('Invitation revoked');
      loadData();
    } catch (err) {
      setError('Failed to revoke invitation');
    }
  };

  const canAddUsers = () => {
    if (!quota) return false;
    if (quota.max_users === -1) return true;
    return quota.current_users < quota.max_users;
  };

  const getRoleBadge = (role) => {
    const colors = {
      owner: 'badge-primary',
      admin: 'badge-danger',
      manager: 'badge-warning',
      member: 'badge-info',
      viewer: 'badge-secondary'
    };
    return <span className={`badge ${colors[role] || 'badge-secondary'}`}>{role}</span>;
  };

  const getStatusBadge = (status) => {
    const colors = {
      pending: 'badge-warning',
      accepted: 'badge-success',
      expired: 'badge-secondary',
      revoked: 'badge-danger'
    };
    return <span className={`badge ${colors[status] || 'badge-secondary'}`}>{status}</span>;
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner">Loading team...</div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>Team Management</h1>
          <p className="page-subtitle">Manage team members and invitations</p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => setShowInviteModal(true)}
          disabled={!canAddUsers()}
        >
          + Invite Member
        </button>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
          <button className="alert-close" onClick={() => setError(null)}>×</button>
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          {success}
          <button className="alert-close" onClick={() => setSuccess(null)}>×</button>
        </div>
      )}

      {/* Quota Info */}
      {quota && (
        <div className="info-card">
          <div className="quota-display">
            <div className="quota-item">
              <span className="quota-label">Team Members</span>
              <span className="quota-value">
                {quota.current_users} / {quota.max_users === -1 ? '∞' : quota.max_users}
              </span>
            </div>
            {quota.max_users !== -1 && (
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${(quota.current_users / quota.max_users) * 100}%` }}
                />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="tabs">
        <button
          className={`tab ${activeTab === 'members' ? 'active' : ''}`}
          onClick={() => setActiveTab('members')}
        >
          Members ({members.length})
        </button>
        <button
          className={`tab ${activeTab === 'invitations' ? 'active' : ''}`}
          onClick={() => setActiveTab('invitations')}
        >
          Pending Invitations ({invitations.filter(i => i.status === 'pending').length})
        </button>
      </div>

      {/* Members Tab */}
      {activeTab === 'members' && (
        <div className="card">
          <div className="card-body">
            {members.length === 0 ? (
              <div className="empty-state">
                <p>No team members yet</p>
              </div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Joined</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {members.map(member => (
                    <tr key={member.id}>
                      <td>
                        <div className="user-cell">
                          <div className="user-avatar">
                            {(member.user_name || member.user_email)?.[0]?.toUpperCase() || '?'}
                          </div>
                          <span>{member.user_name || 'Unknown'}</span>
                          {member.is_owner && (
                            <span className="badge badge-primary ml-2">Owner</span>
                          )}
                        </div>
                      </td>
                      <td>{member.user_email}</td>
                      <td>
                        {member.is_owner ? (
                          getRoleBadge('owner')
                        ) : (
                          <select
                            value={member.role}
                            onChange={(e) => handleUpdateRole(member.user_id, e.target.value)}
                            className="form-control form-control-sm"
                          >
                            {ROLES.map(role => (
                              <option key={role.value} value={role.value}>
                                {role.label}
                              </option>
                            ))}
                          </select>
                        )}
                      </td>
                      <td>{new Date(member.joined_at).toLocaleDateString()}</td>
                      <td>
                        {!member.is_owner && (
                          <button
                            className="btn btn-sm btn-danger"
                            onClick={() => handleRemoveMember(member.user_id)}
                          >
                            Remove
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* Invitations Tab */}
      {activeTab === 'invitations' && (
        <div className="card">
          <div className="card-body">
            {invitations.length === 0 ? (
              <div className="empty-state">
                <p>No pending invitations</p>
              </div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Sent</th>
                    <th>Expires</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {invitations.map(invitation => (
                    <tr key={invitation.id}>
                      <td>{invitation.email}</td>
                      <td>{getRoleBadge(invitation.role)}</td>
                      <td>{getStatusBadge(invitation.status)}</td>
                      <td>{new Date(invitation.created_at).toLocaleDateString()}</td>
                      <td>{new Date(invitation.expires_at).toLocaleDateString()}</td>
                      <td>
                        {invitation.status === 'pending' && (
                          <button
                            className="btn btn-sm btn-danger"
                            onClick={() => handleRevokeInvitation(invitation.id)}
                          >
                            Revoke
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* Invite Modal */}
      {showInviteModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Invite Team Member</h3>
              <button className="modal-close" onClick={() => setShowInviteModal(false)}>×</button>
            </div>
            <form onSubmit={handleInvite}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Email Address</label>
                  <input
                    type="email"
                    name="email"
                    className="form-control"
                    placeholder="colleague@company.com"
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Role</label>
                  <select name="role" className="form-control" defaultValue="member">
                    {ROLES.map(role => (
                      <option key={role.value} value={role.value}>
                        {role.label} - {role.description}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="info-box">
                  <p>An invitation email will be sent with a link to join your organization.</p>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowInviteModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">Send Invitation</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
