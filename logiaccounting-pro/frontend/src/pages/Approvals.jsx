import { useState, useEffect } from 'react';
import { approvalsAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import toast from '../utils/toast';

export default function Approvals() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('pending');
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [myRequests, setMyRequests] = useState([]);
  const [rules, setRules] = useState([]);
  const [showRuleModal, setShowRuleModal] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [comments, setComments] = useState('');

  const [newRule, setNewRule] = useState({
    entity_type: 'transaction',
    min_amount: 1000,
    max_amount: 5000,
    required_roles: ['admin']
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [pendingRes, requestsRes, rulesRes] = await Promise.all([
        approvalsAPI.getPending(),
        approvalsAPI.getMyRequests(),
        approvalsAPI.getRules()
      ]);
      setPendingApprovals(pendingRes.data.approvals || []);
      setMyRequests(requestsRes.data.requests || []);
      setRules(rulesRes.data.rules || []);
    } catch (error) {
      console.error('Failed to load approvals:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (approvalId) => {
    try {
      await approvalsAPI.approve(approvalId, comments);
      setComments('');
      setSelectedItem(null);
      loadData();
    } catch (error) {
      toast.error('Failed to approve: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleReject = async (approvalId) => {
    if (!comments.trim()) {
      toast.warning('Please provide a reason for rejection');
      return;
    }
    try {
      await approvalsAPI.reject(approvalId, comments);
      setComments('');
      setSelectedItem(null);
      loadData();
    } catch (error) {
      toast.error('Failed to reject: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleCreateRule = async () => {
    try {
      await approvalsAPI.createRule(newRule);
      setShowRuleModal(false);
      setNewRule({
        entity_type: 'transaction',
        min_amount: 1000,
        max_amount: 5000,
        required_roles: ['admin']
      });
      loadData();
    } catch (error) {
      toast.error('Failed to create rule: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDeleteRule = async (ruleId) => {
    if (!confirm('Are you sure you want to delete this rule?')) return;
    try {
      await approvalsAPI.deleteRule(ruleId);
      loadData();
    } catch (error) {
      toast.error('Failed to delete rule');
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      pending: 'badge badge-warning',
      approved: 'badge badge-success',
      rejected: 'badge badge-danger'
    };
    return <span className={styles[status] || 'badge'}>{status}</span>;
  };

  const getLevelBadge = (level, required) => {
    return (
      <span className="text-sm text-muted">
        Level {level}/{required}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading approvals...</p>
      </div>
    );
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Approval Workflows</h1>
          <p className="text-muted">Manage approval requests and configure workflow rules</p>
        </div>
        {user?.role === 'admin' && (
          <button className="btn btn-primary" onClick={() => setShowRuleModal(true)}>
            + New Rule
          </button>
        )}
      </div>

      {/* Tab Navigation */}
      <div className="section mb-6">
        <div className="flex gap-2">
          <button
            className={`btn ${activeTab === 'pending' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('pending')}
          >
            Pending Approvals ({pendingApprovals.length})
          </button>
          <button
            className={`btn ${activeTab === 'requests' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('requests')}
          >
            My Requests
          </button>
          {user?.role === 'admin' && (
            <button
              className={`btn ${activeTab === 'rules' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('rules')}
            >
              Workflow Rules
            </button>
          )}
        </div>
      </div>

      {/* Pending Approvals Tab */}
      {activeTab === 'pending' && (
        <div className="section">
          <h3 className="section-title">Pending Approvals</h3>
          {pendingApprovals.length === 0 ? (
            <p className="text-muted text-center py-8">No pending approvals</p>
          ) : (
            <div className="space-y-4">
              {pendingApprovals.map((approval) => (
                <div key={approval.id} className="card p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h4 className="font-bold">{approval.entity_type.toUpperCase()}</h4>
                      <p className="text-muted text-sm">ID: {approval.entity_id}</p>
                    </div>
                    <div className="text-right">
                      {getStatusBadge(approval.status)}
                      <div className="mt-1">
                        {getLevelBadge(approval.current_level, approval.required_levels)}
                      </div>
                    </div>
                  </div>

                  <div className="grid-2 mb-4">
                    <div>
                      <span className="text-muted text-sm">Amount:</span>
                      <p className="font-bold">${approval.amount?.toLocaleString() || 'N/A'}</p>
                    </div>
                    <div>
                      <span className="text-muted text-sm">Requested by:</span>
                      <p>{approval.requested_by || 'Unknown'}</p>
                    </div>
                    <div>
                      <span className="text-muted text-sm">Created:</span>
                      <p>{new Date(approval.created_at).toLocaleDateString()}</p>
                    </div>
                    <div>
                      <span className="text-muted text-sm">Description:</span>
                      <p>{approval.description || '-'}</p>
                    </div>
                  </div>

                  {/* Approval History */}
                  {approval.approvals?.length > 0 && (
                    <div className="mb-4">
                      <span className="text-muted text-sm">Approval History:</span>
                      <div className="mt-2 space-y-1">
                        {approval.approvals.map((a, idx) => (
                          <div key={idx} className="text-sm flex items-center gap-2">
                            <span className={a.action === 'approved' ? 'text-success' : 'text-danger'}>
                              {a.action === 'approved' ? '✓' : '✗'}
                            </span>
                            <span>Level {a.level}: {a.action} by {a.user_id}</span>
                            {a.comments && <span className="text-muted">- {a.comments}</span>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {selectedItem === approval.id ? (
                    <div className="mt-4 p-3 bg-gray-50 rounded">
                      <textarea
                        className="form-input mb-3"
                        placeholder="Comments (required for rejection)"
                        value={comments}
                        onChange={(e) => setComments(e.target.value)}
                        rows={2}
                      />
                      <div className="flex gap-2">
                        <button
                          className="btn btn-success"
                          onClick={() => handleApprove(approval.id)}
                        >
                          Approve
                        </button>
                        <button
                          className="btn btn-danger"
                          onClick={() => handleReject(approval.id)}
                        >
                          Reject
                        </button>
                        <button
                          className="btn btn-secondary"
                          onClick={() => {
                            setSelectedItem(null);
                            setComments('');
                          }}
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      className="btn btn-primary"
                      onClick={() => setSelectedItem(approval.id)}
                    >
                      Review
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* My Requests Tab */}
      {activeTab === 'requests' && (
        <div className="section">
          <h3 className="section-title">My Approval Requests</h3>
          {myRequests.length === 0 ? (
            <p className="text-muted text-center py-8">No approval requests</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Entity ID</th>
                  <th>Amount</th>
                  <th>Status</th>
                  <th>Progress</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {myRequests.map((request) => (
                  <tr key={request.id}>
                    <td>{request.entity_type}</td>
                    <td className="font-mono text-sm">{request.entity_id}</td>
                    <td>${request.amount?.toLocaleString() || 'N/A'}</td>
                    <td>{getStatusBadge(request.status)}</td>
                    <td>{getLevelBadge(request.current_level, request.required_levels)}</td>
                    <td>{new Date(request.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Workflow Rules Tab */}
      {activeTab === 'rules' && user?.role === 'admin' && (
        <div className="section">
          <h3 className="section-title">Workflow Rules</h3>
          {rules.length === 0 ? (
            <p className="text-muted text-center py-8">No workflow rules configured</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Entity Type</th>
                  <th>Amount Range</th>
                  <th>Required Roles</th>
                  <th>Active</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {rules.map((rule) => (
                  <tr key={rule.id}>
                    <td className="font-bold">{rule.entity_type}</td>
                    <td>
                      ${rule.min_amount?.toLocaleString()} - ${rule.max_amount?.toLocaleString() || '∞'}
                    </td>
                    <td>
                      {rule.required_roles?.map((role, idx) => (
                        <span key={idx} className="badge badge-info mr-1">{role}</span>
                      ))}
                    </td>
                    <td>
                      <span className={`badge ${rule.active ? 'badge-success' : 'badge-secondary'}`}>
                        {rule.active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <button
                        className="btn btn-sm btn-danger"
                        onClick={() => handleDeleteRule(rule.id)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* New Rule Modal */}
      {showRuleModal && (
        <div className="modal-overlay" onClick={() => setShowRuleModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Create Approval Rule</h3>
              <button className="modal-close" onClick={() => setShowRuleModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">Entity Type</label>
                <select
                  className="form-select"
                  value={newRule.entity_type}
                  onChange={(e) => setNewRule({ ...newRule, entity_type: e.target.value })}
                >
                  <option value="transaction">Transaction</option>
                  <option value="payment">Payment</option>
                  <option value="project">Project</option>
                </select>
              </div>

              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Min Amount ($)</label>
                  <input
                    type="number"
                    className="form-input"
                    value={newRule.min_amount}
                    onChange={(e) => setNewRule({ ...newRule, min_amount: parseFloat(e.target.value) })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Max Amount ($)</label>
                  <input
                    type="number"
                    className="form-input"
                    value={newRule.max_amount}
                    onChange={(e) => setNewRule({ ...newRule, max_amount: parseFloat(e.target.value) })}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Required Approvers (Roles)</label>
                <div className="space-y-2">
                  {['admin', 'manager', 'accountant'].map((role) => (
                    <label key={role} className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={newRule.required_roles.includes(role)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setNewRule({ ...newRule, required_roles: [...newRule.required_roles, role] });
                          } else {
                            setNewRule({
                              ...newRule,
                              required_roles: newRule.required_roles.filter((r) => r !== role)
                            });
                          }
                        }}
                      />
                      <span className="capitalize">{role}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowRuleModal(false)}>
                Cancel
              </button>
              <button className="btn btn-primary" onClick={handleCreateRule}>
                Create Rule
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
