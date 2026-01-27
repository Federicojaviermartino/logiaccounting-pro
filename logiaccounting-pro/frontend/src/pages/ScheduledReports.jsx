import { useState, useEffect } from 'react';
import { scheduledReportsAPI } from '../services/api';

const DAYS_OF_WEEK = [
  { value: 0, label: 'Monday' },
  { value: 1, label: 'Tuesday' },
  { value: 2, label: 'Wednesday' },
  { value: 3, label: 'Thursday' },
  { value: 4, label: 'Friday' },
  { value: 5, label: 'Saturday' },
  { value: 6, label: 'Sunday' }
];

const REPORT_TYPES = [
  { value: 'financial', label: 'Financial Summary' },
  { value: 'inventory', label: 'Inventory Report' },
  { value: 'payments', label: 'Payments Report' },
  { value: 'projects', label: 'Projects Report' }
];

export default function ScheduledReports() {
  const [schedules, setSchedules] = useState([]);
  const [frequencies, setFrequencies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [selectedSchedule, setSelectedSchedule] = useState(null);
  const [historyData, setHistoryData] = useState([]);

  const [formData, setFormData] = useState({
    name: '',
    report_type: 'financial',
    report_config: { columns: [], filters: {} },
    frequency: 'weekly',
    time_of_day: '09:00',
    day_of_week: 0,
    day_of_month: 1,
    recipients: '',
    format: 'pdf'
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [schedulesRes, freqRes] = await Promise.all([
        scheduledReportsAPI.list(),
        scheduledReportsAPI.getFrequencies()
      ]);
      setSchedules(schedulesRes.data.schedules || []);
      setFrequencies(freqRes.data.frequencies || []);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    try {
      const data = {
        ...formData,
        recipients: formData.recipients.split(',').map(r => r.trim()).filter(Boolean)
      };
      await scheduledReportsAPI.create(data);
      setShowForm(false);
      resetForm();
      loadData();
    } catch (err) {
      alert('Failed to create schedule');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      report_type: 'financial',
      report_config: { columns: [], filters: {} },
      frequency: 'weekly',
      time_of_day: '09:00',
      day_of_week: 0,
      day_of_month: 1,
      recipients: '',
      format: 'pdf'
    });
  };

  const handleToggle = async (schedule) => {
    try {
      await scheduledReportsAPI.toggle(schedule.id);
      loadData();
    } catch (err) {
      alert('Failed to toggle');
    }
  };

  const handleRunNow = async (schedule) => {
    try {
      const res = await scheduledReportsAPI.runNow(schedule.id);
      alert(`Report generated! ${res.data.run_record.row_count} rows`);
      loadData();
    } catch (err) {
      alert('Failed to run');
    }
  };

  const handleDelete = async (schedule) => {
    if (!confirm('Delete this schedule?')) return;
    try {
      await scheduledReportsAPI.delete(schedule.id);
      loadData();
    } catch (err) {
      alert('Failed to delete');
    }
  };

  const handleViewHistory = async (schedule) => {
    try {
      const res = await scheduledReportsAPI.getHistory(schedule.id);
      setHistoryData(res.data.history || []);
      setSelectedSchedule(schedule);
    } catch (err) {
      alert('Failed to load history');
    }
  };

  const getFrequencyLabel = (freq, dayOfWeek, dayOfMonth) => {
    if (freq === 'daily') return 'Daily';
    if (freq === 'weekly') return `Weekly (${DAYS_OF_WEEK.find(d => d.value === dayOfWeek)?.label || ''})`;
    if (freq === 'monthly') return `Monthly (Day ${dayOfMonth})`;
    return freq;
  };

  return (
    <>
      <div className="info-banner mb-6">
        Schedule automatic report generation and delivery.
      </div>

      <div className="section">
        <div className="flex justify-between items-center mb-4">
          <h3 className="section-title" style={{ margin: 0 }}>Report Schedules</h3>
          <button className="btn btn-primary" onClick={() => setShowForm(true)}>
            + New Schedule
          </button>
        </div>

        {loading ? (
          <div className="text-center text-muted">Loading...</div>
        ) : schedules.length === 0 ? (
          <div className="text-center text-muted">No scheduled reports</div>
        ) : (
          <div className="schedules-list">
            {schedules.map(schedule => (
              <div key={schedule.id} className={`schedule-card ${!schedule.active ? 'inactive' : ''}`}>
                <div className="schedule-header">
                  <div>
                    <h4>{schedule.name}</h4>
                    <span className={`badge ${schedule.active ? 'badge-success' : 'badge-gray'}`}>
                      {schedule.active ? 'Active' : 'Paused'}
                    </span>
                    <span className="badge badge-info">{schedule.report_type}</span>
                  </div>
                  <div className="schedule-format">
                    {schedule.format?.toUpperCase()}
                  </div>
                </div>

                <div className="schedule-details">
                  <div>{getFrequencyLabel(schedule.frequency, schedule.day_of_week, schedule.day_of_month)}</div>
                  <div>@ {schedule.time_of_day}</div>
                  <div>{schedule.recipients?.length || 0} recipients</div>
                  <div>Run {schedule.run_count} times</div>
                </div>

                <div className="schedule-next">
                  <strong>Next run:</strong> {schedule.next_run ? new Date(schedule.next_run).toLocaleString() : 'N/A'}
                </div>

                <div className="schedule-actions">
                  <button className="btn btn-sm btn-secondary" onClick={() => handleViewHistory(schedule)}>
                    History
                  </button>
                  <button className="btn btn-sm btn-primary" onClick={() => handleRunNow(schedule)}>
                    Run Now
                  </button>
                  <button className="btn btn-sm btn-secondary" onClick={() => handleToggle(schedule)}>
                    {schedule.active ? 'Pause' : 'Resume'}
                  </button>
                  <button className="btn btn-sm btn-danger" onClick={() => handleDelete(schedule)}>
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* History Modal */}
      {selectedSchedule && (
        <div className="modal-overlay" onClick={() => setSelectedSchedule(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Run History: {selectedSchedule.name}</h3>
              <button className="modal-close" onClick={() => setSelectedSchedule(null)}>x</button>
            </div>
            <div className="modal-body">
              {historyData.length === 0 ? (
                <div className="text-muted text-center">No history yet</div>
              ) : (
                <div className="history-list">
                  {historyData.map((h, i) => (
                    <div key={i} className="history-item">
                      <div className="history-date">{new Date(h.run_at).toLocaleString()}</div>
                      <div className="history-stats">
                        <span className={`badge badge-${h.status === 'success' ? 'success' : 'danger'}`}>
                          {h.status}
                        </span>
                        <span>{h.row_count} rows</span>
                        <span>{h.format?.toUpperCase()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Create Form Modal */}
      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-content modal-lg" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Create Schedule</h3>
              <button className="modal-close" onClick={() => setShowForm(false)}>x</button>
            </div>
            <div className="modal-body">
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Schedule Name *</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Weekly Sales Report"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Report Type</label>
                  <select
                    className="form-select"
                    value={formData.report_type}
                    onChange={(e) => setFormData({ ...formData, report_type: e.target.value })}
                  >
                    {REPORT_TYPES.map(t => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Frequency</label>
                  <select
                    className="form-select"
                    value={formData.frequency}
                    onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                  >
                    {frequencies.map(f => (
                      <option key={f.value} value={f.value}>{f.label}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Time</label>
                  <input
                    type="time"
                    className="form-input"
                    value={formData.time_of_day}
                    onChange={(e) => setFormData({ ...formData, time_of_day: e.target.value })}
                  />
                </div>

                {formData.frequency === 'weekly' && (
                  <div className="form-group">
                    <label className="form-label">Day of Week</label>
                    <select
                      className="form-select"
                      value={formData.day_of_week}
                      onChange={(e) => setFormData({ ...formData, day_of_week: parseInt(e.target.value) })}
                    >
                      {DAYS_OF_WEEK.map(d => (
                        <option key={d.value} value={d.value}>{d.label}</option>
                      ))}
                    </select>
                  </div>
                )}

                {formData.frequency === 'monthly' && (
                  <div className="form-group">
                    <label className="form-label">Day of Month</label>
                    <select
                      className="form-select"
                      value={formData.day_of_month}
                      onChange={(e) => setFormData({ ...formData, day_of_month: parseInt(e.target.value) })}
                    >
                      {[...Array(28)].map((_, i) => (
                        <option key={i + 1} value={i + 1}>{i + 1}</option>
                      ))}
                    </select>
                  </div>
                )}

                <div className="form-group">
                  <label className="form-label">Format</label>
                  <select
                    className="form-select"
                    value={formData.format}
                    onChange={(e) => setFormData({ ...formData, format: e.target.value })}
                  >
                    <option value="pdf">PDF</option>
                    <option value="csv">CSV</option>
                    <option value="excel">Excel</option>
                  </select>
                </div>

                <div className="form-group full-width">
                  <label className="form-label">Recipients (comma separated)</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.recipients}
                    onChange={(e) => setFormData({ ...formData, recipients: e.target.value })}
                    placeholder="cfo@company.com, accounting@company.com"
                  />
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
              <button
                className="btn btn-primary"
                onClick={handleSubmit}
                disabled={!formData.name}
              >
                Create Schedule
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
