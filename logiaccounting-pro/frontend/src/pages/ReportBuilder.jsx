import { useState, useEffect } from 'react';
import { reportBuilderAPI } from '../services/api';
import toast from '../utils/toast';

const REPORT_TYPES = [
  { value: 'financial', label: 'Financial Report', icon: '💰' },
  { value: 'inventory', label: 'Inventory Report', icon: '📦' },
  { value: 'projects', label: 'Projects Report', icon: '📁' },
  { value: 'payments', label: 'Payments Report', icon: '💳' }
];

export default function ReportBuilder() {
  const [step, setStep] = useState(1);
  const [reportType, setReportType] = useState('');
  const [availableColumns, setAvailableColumns] = useState([]);
  const [selectedColumns, setSelectedColumns] = useState([]);
  const [filters, setFilters] = useState({});
  const [grouping, setGrouping] = useState('');
  const [sortBy, setSortBy] = useState('');
  const [sortOrder, setSortOrder] = useState('desc');
  const [previewData, setPreviewData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [templateName, setTemplateName] = useState('');

  useEffect(() => {
    loadTemplates();
  }, []);

  useEffect(() => {
    if (reportType) {
      loadColumns();
    }
  }, [reportType]);

  const loadTemplates = async () => {
    try {
      const res = await reportBuilderAPI.getTemplates();
      setTemplates(res.data.templates);
    } catch (err) {
      console.error('Failed to load templates:', err);
    }
  };

  const loadColumns = async () => {
    try {
      const res = await reportBuilderAPI.getColumns(reportType);
      setAvailableColumns(res.data);
      setSelectedColumns(res.data.required);
    } catch (err) {
      console.error('Failed to load columns:', err);
    }
  };

  const toggleColumn = (column) => {
    const required = availableColumns.required || [];
    if (required.includes(column)) return;

    if (selectedColumns.includes(column)) {
      setSelectedColumns(selectedColumns.filter(c => c !== column));
    } else {
      setSelectedColumns([...selectedColumns, column]);
    }
  };

  const handlePreview = async () => {
    setLoading(true);
    try {
      const config = {
        name: 'Preview',
        type: reportType,
        columns: selectedColumns,
        filters,
        grouping: grouping || null,
        sort_by: sortBy || null,
        sort_order: sortOrder
      };

      const res = await reportBuilderAPI.preview(config, 20);
      setPreviewData(res.data);
      setStep(4);
    } catch (err) {
      toast.error('Preview failed');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async (format) => {
    setLoading(true);
    try {
      const config = {
        name: templateName || `${reportType}_report`,
        type: reportType,
        columns: selectedColumns,
        filters,
        grouping: grouping || null,
        sort_by: sortBy || null,
        sort_order: sortOrder
      };

      if (format === 'csv') {
        const res = await reportBuilderAPI.generate(config, 'csv');
        const blob = new Blob([res.data], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${config.name}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
      } else {
        const res = await reportBuilderAPI.generate(config, 'json');
        const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${config.name}.json`;
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (err) {
      toast.error('Generation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveTemplate = async () => {
    if (!templateName.trim()) {
      toast.warning('Please enter a template name');
      return;
    }

    try {
      const template = {
        name: templateName,
        config: {
          name: templateName,
          type: reportType,
          columns: selectedColumns,
          filters,
          grouping: grouping || null,
          sort_by: sortBy || null,
          sort_order: sortOrder
        }
      };

      await reportBuilderAPI.saveTemplate(template);
      loadTemplates();
      toast.success('Template saved!');
    } catch (err) {
      toast.error('Failed to save template');
    }
  };

  const loadTemplate = (template) => {
    const config = template.config;
    setReportType(config.type);
    setSelectedColumns(config.columns);
    setFilters(config.filters || {});
    setGrouping(config.grouping || '');
    setSortBy(config.sort_by || '');
    setSortOrder(config.sort_order || 'desc');
    setTemplateName(template.name);
    setStep(2);
  };

  return (
    <>
      <div className="section mb-6">
        <div className="steps-indicator">
          {['Report Type', 'Columns', 'Filters', 'Preview & Export'].map((label, i) => (
            <div
              key={i}
              className={`step ${step > i ? 'completed' : ''} ${step === i + 1 ? 'active' : ''}`}
              onClick={() => i < step && setStep(i + 1)}
            >
              <div className="step-number">{i + 1}</div>
              <div className="step-label">{label}</div>
            </div>
          ))}
        </div>
      </div>

      {templates.length > 0 && step === 1 && (
        <div className="section mb-6">
          <h4 className="font-bold mb-3">Saved Templates</h4>
          <div className="templates-grid">
            {templates.map(t => (
              <div
                key={t.id}
                className="template-card"
                onClick={() => loadTemplate(t)}
              >
                <div className="template-name">{t.name}</div>
                <div className="template-type">{t.config.type}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {step === 1 && (
        <div className="section">
          <h3 className="section-title">Select Report Type</h3>
          <div className="report-type-grid">
            {REPORT_TYPES.map(type => (
              <div
                key={type.value}
                className={`report-type-card ${reportType === type.value ? 'selected' : ''}`}
                onClick={() => {
                  setReportType(type.value);
                  setStep(2);
                }}
              >
                <span className="report-type-icon">{type.icon}</span>
                <span className="report-type-label">{type.label}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="section">
          <h3 className="section-title">Select Columns</h3>
          <p className="text-muted mb-4">Choose which columns to include in your report:</p>

          <div className="columns-grid">
            {availableColumns.available?.map(col => (
              <label
                key={col}
                className={`column-option ${availableColumns.required?.includes(col) ? 'required' : ''}`}
              >
                <input
                  type="checkbox"
                  checked={selectedColumns.includes(col)}
                  onChange={() => toggleColumn(col)}
                  disabled={availableColumns.required?.includes(col)}
                />
                <span>{col.replace(/_/g, ' ')}</span>
                {availableColumns.required?.includes(col) && (
                  <span className="required-badge">Required</span>
                )}
              </label>
            ))}
          </div>

          <div className="flex gap-3 mt-6">
            <button className="btn btn-secondary" onClick={() => setStep(1)}>Back</button>
            <button className="btn btn-primary" onClick={() => setStep(3)}>Continue</button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="section">
          <h3 className="section-title">Configure Filters</h3>

          <div className="grid-2 mb-6">
            <div className="form-group">
              <label className="form-label">Date From</label>
              <input
                type="date"
                className="form-input"
                value={filters.date_from || ''}
                onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Date To</label>
              <input
                type="date"
                className="form-input"
                value={filters.date_to || ''}
                onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Min Amount</label>
              <input
                type="number"
                className="form-input"
                value={filters.min_amount || ''}
                onChange={(e) => setFilters({ ...filters, min_amount: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Max Amount</label>
              <input
                type="number"
                className="form-input"
                value={filters.max_amount || ''}
                onChange={(e) => setFilters({ ...filters, max_amount: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Group By</label>
              <select
                className="form-select"
                value={grouping}
                onChange={(e) => setGrouping(e.target.value)}
              >
                <option value="">No Grouping</option>
                {availableColumns.grouping?.map(g => (
                  <option key={g} value={g}>{g}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Sort By</label>
              <div className="flex gap-2">
                <select
                  className="form-select"
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                >
                  <option value="">Default</option>
                  {selectedColumns.map(c => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
                <select
                  className="form-select"
                  value={sortOrder}
                  onChange={(e) => setSortOrder(e.target.value)}
                  style={{ width: '100px' }}
                >
                  <option value="asc">Asc</option>
                  <option value="desc">Desc</option>
                </select>
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <button className="btn btn-secondary" onClick={() => setStep(2)}>Back</button>
            <button className="btn btn-primary" onClick={handlePreview} disabled={loading}>
              {loading ? 'Loading...' : 'Preview Report'}
            </button>
          </div>
        </div>
      )}

      {step === 4 && previewData && (
        <div className="section">
          <h3 className="section-title">Report Preview</h3>
          <p className="text-muted mb-4">
            Showing {previewData.data.length} of {previewData.total_rows} rows
          </p>

          <div className="table-container mb-6">
            <table className="data-table">
              <thead>
                <tr>
                  {previewData.columns.map(col => (
                    <th key={col}>{col.replace(/_/g, ' ')}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {previewData.data.map((row, i) => (
                  <tr key={i}>
                    {previewData.columns.map(col => (
                      <td key={col}>
                        {typeof row[col] === 'number'
                          ? row[col].toLocaleString()
                          : row[col] || '-'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="form-group mb-6" style={{ maxWidth: '400px' }}>
            <label className="form-label">Save as Template</label>
            <div className="flex gap-2">
              <input
                type="text"
                className="form-input"
                value={templateName}
                onChange={(e) => setTemplateName(e.target.value)}
                placeholder="Template name"
              />
              <button className="btn btn-secondary" onClick={handleSaveTemplate}>Save</button>
            </div>
          </div>

          <div className="flex gap-3">
            <button className="btn btn-secondary" onClick={() => setStep(3)}>Back</button>
            <button className="btn btn-primary" onClick={() => handleGenerate('csv')} disabled={loading}>
              Export CSV
            </button>
            <button className="btn btn-secondary" onClick={() => handleGenerate('json')} disabled={loading}>
              Export JSON
            </button>
          </div>
        </div>
      )}
    </>
  );
}
