import { useState, useRef } from 'react';
import { bulkAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import toast from '../utils/toast';

const ENTITIES = [
  { value: 'materials', label: 'Materials', allowDelete: true },
  { value: 'transactions', label: 'Transactions', allowDelete: true },
  { value: 'payments', label: 'Payments', allowDelete: false },
  { value: 'projects', label: 'Projects', allowDelete: false }
];

export default function BulkOperations() {
  const { user } = useAuth();
  const fileInputRef = useRef(null);
  const [activeTab, setActiveTab] = useState('import');
  const [selectedEntity, setSelectedEntity] = useState('materials');
  const [file, setFile] = useState(null);
  const [importing, setImporting] = useState(false);
  const [skipErrors, setSkipErrors] = useState(true);
  const [importResult, setImportResult] = useState(null);

  const handleDownloadTemplate = async () => {
    try {
      const res = await bulkAPI.getTemplate(selectedEntity);
      const blob = new Blob([res.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedEntity}_template.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      toast.error('Failed to download template');
    }
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setImportResult(null);
  };

  const handleImport = async () => {
    if (!file) return;

    setImporting(true);
    setImportResult(null);

    try {
      const res = await bulkAPI.importData(selectedEntity, file, skipErrors);
      setImportResult(res.data);
    } catch (error) {
      setImportResult({
        error: true,
        message: error.response?.data?.detail || 'Import failed'
      });
    } finally {
      setImporting(false);
    }
  };

  const handleExport = async (format) => {
    try {
      const res = await bulkAPI.exportData(selectedEntity, null, format);
      const blob = new Blob([res.data], {
        type: format === 'json' ? 'application/json' : 'text/csv'
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedEntity}_export.${format}`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      toast.error('Export failed');
    }
  };

  return (
    <>
      <div className="info-banner mb-6">
        Import, export, and manage data in bulk. Download templates, upload CSV files, and export data in various formats.
      </div>

      {/* Entity Selection */}
      <div className="section mb-6">
        <div className="form-group" style={{ maxWidth: '300px' }}>
          <label className="form-label">Select Entity</label>
          <select
            className="form-select"
            value={selectedEntity}
            onChange={(e) => setSelectedEntity(e.target.value)}
          >
            {ENTITIES.map(e => (
              <option key={e.value} value={e.value}>{e.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="section mb-6">
        <div className="flex gap-2 mb-4">
          <button
            className={`btn ${activeTab === 'import' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('import')}
          >
            Import
          </button>
          <button
            className={`btn ${activeTab === 'export' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('export')}
          >
            Export
          </button>
        </div>

        {/* Import Tab */}
        {activeTab === 'import' && (
          <div>
            <h4 className="font-bold mb-4">Import {ENTITIES.find(e => e.value === selectedEntity)?.label}</h4>

            {/* Step 1: Download Template */}
            <div className="mb-6">
              <div className="text-muted mb-2">Step 1: Download the CSV template</div>
              <button className="btn btn-secondary" onClick={handleDownloadTemplate}>
                Download Template
              </button>
            </div>

            {/* Step 2: Upload File */}
            <div className="mb-6">
              <div className="text-muted mb-2">Step 2: Fill the template and upload</div>
              <div
                className="upload-zone"
                style={{
                  border: '2px dashed var(--border-color)',
                  borderRadius: '12px',
                  padding: '32px',
                  textAlign: 'center',
                  cursor: 'pointer',
                  background: file ? 'var(--bg-tertiary)' : 'transparent'
                }}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  onChange={handleFileChange}
                  style={{ display: 'none' }}
                />
                {file ? (
                  <div>
                    <div style={{ fontSize: '2rem', marginBottom: '8px' }}>📄</div>
                    <div className="font-bold">{file.name}</div>
                    <div className="text-muted">{(file.size / 1024).toFixed(1)} KB</div>
                  </div>
                ) : (
                  <div>
                    <div style={{ fontSize: '2rem', marginBottom: '8px' }}>📤</div>
                    <div>Click to upload CSV file</div>
                  </div>
                )}
              </div>
            </div>

            {/* Options */}
            <div className="mb-6">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={skipErrors}
                  onChange={(e) => setSkipErrors(e.target.checked)}
                />
                <span>Skip rows with errors and continue import</span>
              </label>
            </div>

            {/* Import Button */}
            <button
              className="btn btn-primary"
              onClick={handleImport}
              disabled={!file || importing}
            >
              {importing ? 'Importing...' : 'Start Import'}
            </button>

            {/* Import Result */}
            {importResult && (
              <div className={`mt-6 p-4 rounded-lg`}
                style={{
                  background: importResult.error ? '#fef2f2' : '#f0fdf4',
                  border: `1px solid ${importResult.error ? '#fecaca' : '#bbf7d0'}`
                }}>
                {importResult.error ? (
                  <div className="text-danger">{importResult.message}</div>
                ) : (
                  <>
                    <div className="font-bold mb-2">Import Complete</div>
                    <div className="grid-2" style={{ maxWidth: '400px' }}>
                      <div>Total Rows: <strong>{importResult.total_rows}</strong></div>
                      <div>Imported: <strong className="text-success">{importResult.imported}</strong></div>
                      <div>Skipped: <strong className="text-warning">{importResult.skipped}</strong></div>
                      <div>Errors: <strong className="text-danger">{importResult.errors?.length || 0}</strong></div>
                    </div>
                    {importResult.errors?.length > 0 && (
                      <div className="mt-4">
                        <div className="font-bold mb-2">Errors:</div>
                        <div style={{ maxHeight: '200px', overflow: 'auto' }}>
                          {importResult.errors.slice(0, 10).map((err, i) => (
                            <div key={i} className="text-sm text-danger mb-1">
                              Row {err.row}: {err.error}
                            </div>
                          ))}
                          {importResult.errors.length > 10 && (
                            <div className="text-muted">...and {importResult.errors.length - 10} more</div>
                          )}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        )}

        {/* Export Tab */}
        {activeTab === 'export' && (
          <div>
            <h4 className="font-bold mb-4">Export {ENTITIES.find(e => e.value === selectedEntity)?.label}</h4>
            <p className="text-muted mb-4">Export all records in your preferred format.</p>

            <div className="flex gap-3">
              <button className="btn btn-primary" onClick={() => handleExport('csv')}>
                Export CSV
              </button>
              <button className="btn btn-secondary" onClick={() => handleExport('json')}>
                Export JSON
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
