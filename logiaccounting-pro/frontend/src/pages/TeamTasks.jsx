import { useState, useEffect } from 'react';
import { tasksAPI, commentsAPI } from '../services/api';
import toast from '../utils/toast';

export default function TeamTasks() {
  const [tasks, setTasks] = useState([]);
  const [overdueTasks, setOverdueTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [statuses, setStatuses] = useState([]);
  const [priorities, setPriorities] = useState([]);

  const [formData, setFormData] = useState({
    title: '',
    entity_type: 'project',
    entity_id: '',
    assigned_to: '',
    due_date: '',
    priority: 'medium',
    notes: ''
  });

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    loadTasks();
  }, [statusFilter]);

  const loadInitialData = async () => {
    try {
      const [statusRes, priorityRes, overdueRes] = await Promise.all([
        tasksAPI.getStatuses(),
        tasksAPI.getPriorities(),
        tasksAPI.getOverdue()
      ]);
      setStatuses(statusRes.data.statuses);
      setPriorities(priorityRes.data.priorities);
      setOverdueTasks(overdueRes.data.tasks);
    } catch (err) {
      console.error('Failed to load initial data:', err);
    }
  };

  const loadTasks = async () => {
    setLoading(true);
    try {
      const res = await tasksAPI.getMy(statusFilter || undefined);
      setTasks(res.data.tasks);
    } catch (err) {
      console.error('Failed to load tasks:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    try {
      if (selectedTask) {
        await tasksAPI.update(selectedTask.id, formData);
      } else {
        await tasksAPI.create(formData);
      }
      setShowForm(false);
      setSelectedTask(null);
      resetForm();
      loadTasks();
      loadInitialData();
    } catch (err) {
      toast.error('Failed to save task');
    }
  };

  const handleStatusChange = async (taskId, newStatus) => {
    try {
      await tasksAPI.update(taskId, { status: newStatus });
      loadTasks();
      loadInitialData();
    } catch (err) {
      toast.error('Failed to update status');
    }
  };

  const handleDelete = async (taskId) => {
    if (!confirm('Delete this task?')) return;
    try {
      await tasksAPI.delete(taskId);
      loadTasks();
    } catch (err) {
      toast.error('Failed to delete');
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      entity_type: 'project',
      entity_id: '',
      assigned_to: '',
      due_date: '',
      priority: 'medium',
      notes: ''
    });
  };

  const handleEdit = (task) => {
    setSelectedTask(task);
    setFormData({
      title: task.title,
      entity_type: task.entity_type,
      entity_id: task.entity_id,
      assigned_to: task.assigned_to,
      due_date: task.due_date || '',
      priority: task.priority,
      notes: task.notes || ''
    });
    setShowForm(true);
  };

  const getPriorityBadge = (priority) => {
    const colors = {
      low: 'badge-gray',
      medium: 'badge-info',
      high: 'badge-warning',
      urgent: 'badge-danger'
    };
    return <span className={`badge ${colors[priority]}`}>{priority}</span>;
  };

  const getStatusBadge = (status) => {
    const colors = {
      pending: 'badge-gray',
      in_progress: 'badge-info',
      completed: 'badge-success',
      cancelled: 'badge-danger'
    };
    return <span className={`badge ${colors[status]}`}>{status.replace('_', ' ')}</span>;
  };

  const isOverdue = (dueDate) => {
    if (!dueDate) return false;
    return new Date(dueDate) < new Date() && dueDate !== '';
  };

  return (
    <>
      <div className="info-banner mb-6">
        Manage team tasks, assignments, and deadlines.
      </div>

      {/* Overdue Alert */}
      {overdueTasks.length > 0 && (
        <div className="alert alert-danger mb-6">
          <strong>Overdue Tasks: {overdueTasks.length}</strong>
          <div className="mt-2">
            {overdueTasks.slice(0, 3).map(t => (
              <div key={t.id} className="text-sm">{t.title} - Due: {t.due_date}</div>
            ))}
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex gap-2">
          <button
            className={`btn btn-sm ${statusFilter === '' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setStatusFilter('')}
          >
            All
          </button>
          {statuses.map(s => (
            <button
              key={s}
              className={`btn btn-sm ${statusFilter === s ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setStatusFilter(s)}
            >
              {s.replace('_', ' ')}
            </button>
          ))}
        </div>
        <button className="btn btn-primary" onClick={() => { resetForm(); setShowForm(true); }}>
          + New Task
        </button>
      </div>

      {/* Tasks List */}
      <div className="section">
        {loading ? (
          <div className="text-center p-8">Loading...</div>
        ) : tasks.length === 0 ? (
          <div className="text-center text-muted p-8">No tasks found</div>
        ) : (
          <div className="tasks-list">
            {tasks.map(task => (
              <div
                key={task.id}
                className={`task-card ${task.status === 'completed' ? 'completed' : ''} ${isOverdue(task.due_date) && task.status !== 'completed' ? 'overdue' : ''}`}
              >
                <div className="task-checkbox">
                  <input
                    type="checkbox"
                    checked={task.status === 'completed'}
                    onChange={(e) => handleStatusChange(task.id, e.target.checked ? 'completed' : 'pending')}
                  />
                </div>
                <div className="task-content">
                  <div className="task-title">{task.title}</div>
                  <div className="task-meta">
                    {getPriorityBadge(task.priority)}
                    {getStatusBadge(task.status)}
                    {task.due_date && (
                      <span className={`task-due ${isOverdue(task.due_date) ? 'overdue' : ''}`}>
                        Due: {task.due_date}
                      </span>
                    )}
                    <span className="text-muted">
                      {task.entity_type}/{task.entity_id}
                    </span>
                  </div>
                  {task.notes && <div className="task-notes">{task.notes}</div>}
                </div>
                <div className="task-actions">
                  <select
                    className="form-select form-select-sm"
                    value={task.status}
                    onChange={(e) => handleStatusChange(task.id, e.target.value)}
                  >
                    {statuses.map(s => (
                      <option key={s} value={s}>{s.replace('_', ' ')}</option>
                    ))}
                  </select>
                  <button className="btn btn-sm btn-secondary" onClick={() => handleEdit(task)}>
                    Edit
                  </button>
                  <button className="btn btn-sm btn-danger" onClick={() => handleDelete(task.id)}>
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add/Edit Modal */}
      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{selectedTask ? 'Edit Task' : 'New Task'}</h3>
              <button className="modal-close" onClick={() => setShowForm(false)}>x</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">Title *</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                />
              </div>
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Entity Type</label>
                  <select
                    className="form-select"
                    value={formData.entity_type}
                    onChange={(e) => setFormData({ ...formData, entity_type: e.target.value })}
                  >
                    <option value="project">Project</option>
                    <option value="payment">Payment</option>
                    <option value="transaction">Transaction</option>
                    <option value="material">Material</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Entity ID</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.entity_id}
                    onChange={(e) => setFormData({ ...formData, entity_id: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Assigned To *</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.assigned_to}
                    onChange={(e) => setFormData({ ...formData, assigned_to: e.target.value })}
                    placeholder="User ID or email"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Due Date</label>
                  <input
                    type="date"
                    className="form-input"
                    value={formData.due_date}
                    onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Priority</label>
                  <select
                    className="form-select"
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                  >
                    {priorities.map(p => (
                      <option key={p} value={p}>{p}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Notes</label>
                <textarea
                  className="form-input"
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  rows={3}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
              <button
                className="btn btn-primary"
                onClick={handleSubmit}
                disabled={!formData.title || !formData.assigned_to}
              >
                {selectedTask ? 'Update' : 'Create'} Task
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
