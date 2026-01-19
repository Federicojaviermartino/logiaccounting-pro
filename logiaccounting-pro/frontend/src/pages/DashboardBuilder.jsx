import { useState, useEffect, useCallback } from 'react';
import { dashboardAPI } from '../services/api';

// Widget Components
import KPIWidget from '../components/dashboard/widgets/KPIWidget';
import ChartWidget from '../components/dashboard/widgets/ChartWidget';
import DonutWidget from '../components/dashboard/widgets/DonutWidget';
import GaugeWidget from '../components/dashboard/widgets/GaugeWidget';
import AlertsWidget from '../components/dashboard/widgets/AlertsWidget';

const WIDGET_COMPONENTS = {
  kpi: KPIWidget,
  line_chart: ChartWidget,
  bar_chart: ChartWidget,
  area_chart: ChartWidget,
  donut_chart: DonutWidget,
  gauge: GaugeWidget,
  alerts_feed: AlertsWidget
};

export default function DashboardBuilder() {
  const [dashboards, setDashboards] = useState([]);
  const [currentDashboard, setCurrentDashboard] = useState(null);
  const [widgetTypes, setWidgetTypes] = useState({});
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editMode, setEditMode] = useState(false);
  const [showNewDashboard, setShowNewDashboard] = useState(false);
  const [showAddWidget, setShowAddWidget] = useState(false);
  const [newDashboardName, setNewDashboardName] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [dashboardsRes, typesRes, templatesRes] = await Promise.all([
        dashboardAPI.list(),
        dashboardAPI.getWidgetTypes(),
        dashboardAPI.getTemplates()
      ]);
      setDashboards(dashboardsRes.data.dashboards || []);
      setWidgetTypes(typesRes.data.types || {});
      setTemplates(templatesRes.data.templates || []);

      // Load default or first dashboard
      const defaultDash = dashboardsRes.data.dashboards?.find(d => d.is_default)
                          || dashboardsRes.data.dashboards?.[0];
      if (defaultDash) {
        setCurrentDashboard(defaultDash);
      }
    } catch (err) {
      console.error('Failed to load dashboards:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDashboard = async () => {
    try {
      const res = await dashboardAPI.create({
        name: newDashboardName,
        from_template: selectedTemplate || null,
        is_default: dashboards.length === 0
      });
      setDashboards([...dashboards, res.data]);
      setCurrentDashboard(res.data);
      setShowNewDashboard(false);
      setNewDashboardName('');
      setSelectedTemplate('');
    } catch (err) {
      alert('Failed to create dashboard');
    }
  };

  const handleLayoutChange = useCallback(async (widgetId, newPosition) => {
    if (!currentDashboard || !editMode) return;

    const updatedLayout = currentDashboard.layout.map(widget => {
      if (widget.widget_id === widgetId) {
        return { ...widget, ...newPosition };
      }
      return widget;
    });

    try {
      await dashboardAPI.updateLayout(currentDashboard.id, updatedLayout);
      setCurrentDashboard({ ...currentDashboard, layout: updatedLayout });
    } catch (err) {
      console.error('Failed to update layout:', err);
    }
  }, [currentDashboard, editMode]);

  const handleAddWidget = async (widgetType) => {
    try {
      const typeConfig = widgetTypes[widgetType];
      const res = await dashboardAPI.addWidget(currentDashboard.id, {
        type: widgetType,
        x: 0,
        y: 0,
        w: typeConfig?.min_w || 3,
        h: typeConfig?.min_h || 2,
        config: {}
      });
      setCurrentDashboard(res.data);
      setShowAddWidget(false);
    } catch (err) {
      alert('Failed to add widget');
    }
  };

  const handleRemoveWidget = async (widgetId) => {
    if (!confirm('Remove this widget?')) return;
    try {
      const res = await dashboardAPI.removeWidget(currentDashboard.id, widgetId);
      setCurrentDashboard(res.data);
    } catch (err) {
      alert('Failed to remove widget');
    }
  };

  const handleShare = async () => {
    try {
      const res = await dashboardAPI.share(currentDashboard.id);
      const shareUrl = `${window.location.origin}/dashboard/shared/${res.data.share_token}`;
      navigator.clipboard.writeText(shareUrl);
      alert('Share link copied to clipboard!');
    } catch (err) {
      alert('Failed to share');
    }
  };

  const handleDeleteDashboard = async () => {
    if (!confirm('Delete this dashboard?')) return;
    try {
      await dashboardAPI.delete(currentDashboard.id);
      const remaining = dashboards.filter(d => d.id !== currentDashboard.id);
      setDashboards(remaining);
      setCurrentDashboard(remaining[0] || null);
    } catch (err) {
      alert('Failed to delete');
    }
  };

  const renderWidget = (widget) => {
    const WidgetComponent = WIDGET_COMPONENTS[widget.type];
    if (!WidgetComponent) {
      return <div className="widget-placeholder">Unknown widget: {widget.type}</div>;
    }
    return (
      <WidgetComponent
        widget={widget}
        dashboardId={currentDashboard.id}
        onRemove={editMode ? () => handleRemoveWidget(widget.widget_id) : null}
      />
    );
  };

  const getWidgetIcon = (type) => {
    const icons = {
      kpi: '#',
      line_chart: '~',
      bar_chart: '|',
      donut_chart: 'O',
      area_chart: '^',
      gauge: '%',
      data_table: '=',
      alerts_feed: '!'
    };
    return icons[type] || '?';
  };

  if (loading) {
    return <div className="text-center p-8">Loading dashboards...</div>;
  }

  return (
    <div className="dashboard-builder">
      {/* Header */}
      <div className="dashboard-header">
        <div className="dashboard-tabs">
          {dashboards.map(dash => (
            <button
              key={dash.id}
              className={`dashboard-tab ${currentDashboard?.id === dash.id ? 'active' : ''}`}
              onClick={() => setCurrentDashboard(dash)}
            >
              {dash.name}
            </button>
          ))}
          <button
            className="dashboard-tab add"
            onClick={() => setShowNewDashboard(true)}
          >
            + New
          </button>
        </div>

        <div className="dashboard-actions">
          <button
            className={`btn btn-sm ${editMode ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setEditMode(!editMode)}
          >
            {editMode ? 'Done Editing' : 'Edit'}
          </button>
          {editMode && (
            <button className="btn btn-sm btn-secondary" onClick={() => setShowAddWidget(true)}>
              + Add Widget
            </button>
          )}
          <button className="btn btn-sm btn-secondary" onClick={handleShare}>
            Share
          </button>
          {editMode && (
            <button className="btn btn-sm btn-danger" onClick={handleDeleteDashboard}>
              Delete
            </button>
          )}
        </div>
      </div>

      {/* Dashboard Grid */}
      {currentDashboard ? (
        <div className="dashboard-grid">
          {currentDashboard.layout?.map(widget => (
            <div
              key={widget.widget_id}
              className="widget-container"
              style={{
                gridColumn: `span ${widget.w || 3}`,
                gridRow: `span ${widget.h || 2}`
              }}
            >
              {renderWidget(widget)}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center p-8">
          <h3>No dashboards yet</h3>
          <p className="text-muted">Create your first dashboard to get started</p>
          <button className="btn btn-primary mt-4" onClick={() => setShowNewDashboard(true)}>
            Create Dashboard
          </button>
        </div>
      )}

      {/* New Dashboard Modal */}
      {showNewDashboard && (
        <div className="modal-overlay" onClick={() => setShowNewDashboard(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Create Dashboard</h3>
              <button className="modal-close" onClick={() => setShowNewDashboard(false)}>x</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">Dashboard Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={newDashboardName}
                  onChange={(e) => setNewDashboardName(e.target.value)}
                  placeholder="My Dashboard"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Start from Template (optional)</label>
                <select
                  className="form-select"
                  value={selectedTemplate}
                  onChange={(e) => setSelectedTemplate(e.target.value)}
                >
                  <option value="">Blank Dashboard</option>
                  {templates.map(t => (
                    <option key={t.name} value={t.name}>{t.name}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowNewDashboard(false)}>Cancel</button>
              <button
                className="btn btn-primary"
                onClick={handleCreateDashboard}
                disabled={!newDashboardName.trim()}
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Widget Modal */}
      {showAddWidget && (
        <div className="modal-overlay" onClick={() => setShowAddWidget(false)}>
          <div className="modal-content modal-lg" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add Widget</h3>
              <button className="modal-close" onClick={() => setShowAddWidget(false)}>x</button>
            </div>
            <div className="modal-body">
              <div className="widget-palette">
                {Object.entries(widgetTypes).map(([type, config]) => (
                  <div
                    key={type}
                    className="widget-type-card"
                    onClick={() => handleAddWidget(type)}
                  >
                    <div className="widget-type-icon">
                      {getWidgetIcon(type)}
                    </div>
                    <div className="widget-type-name">{type.replace(/_/g, ' ')}</div>
                    <div className="widget-type-size">
                      {config.min_w}x{config.min_h} min
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
