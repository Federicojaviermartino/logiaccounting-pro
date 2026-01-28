import { useState, useEffect } from 'react';
import { importAPI } from '../services/api';
import toast from '../utils/toast';

const STEPS = ['Upload', 'Map Fields', 'Validate', 'Import'];

export default function DataImport() {
  const [step, setStep] = useState(0);
  const [entities, setEntities] = useState([]);
  const [selectedEntity, setSelectedEntity] = useState('');
  const [entityConfig, setEntityConfig] = useState(null);
  const [fileContent, setFileContent] = useState('');
  const [parsedData, setParsedData] = useState({ headers: [], rows: [], total: 0 });
  const [mapping, setMapping] = useState({});
  const [importJob, setImportJob] = useState(null);
  const [imports, setImports] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadEntities();
    loadImports();
  }, []);

  const loadEntities = async () => {
    try {
      const res = await importAPI.getEntities();
      setEntities(res.data.entities);
    } catch (err) {
      console.error('Failed to load entities:', err);
    }
  };

  const loadImports = async () => {
    try {
      const res = await importAPI.list();
      setImports(res.data.imports);
    } catch (err) {
      console.error('Failed to load imports:', err);
    }
  };

  const loadEntityConfig = async (entity) => {
    try {
      const res = await importAPI.getEntityConfig(entity);
      setEntityConfig(res.data);
    } catch (err) {
      console.error('Failed to load config:', err);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      setFileContent(event.target.result);
    };
    reader.readAsText(file);
  };

  const handleParse = async () => {
    setLoading(true);
    try {
      const res = await importAPI.parse(fileContent);
      setParsedData(res.data);

      // Get suggested mappings
      const suggestRes = await importAPI.suggestMapping(selectedEntity, res.data.headers);
      setMapping(suggestRes.data.suggestions);

      setStep(1);
    } catch (err) {
      toast.error('Failed to parse file: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleValidate = async () => {
    setLoading(true);
    try {
      const res = await importAPI.create({
        entity: selectedEntity,
        headers: parsedData.headers,
        rows: parsedData.rows,
        mapping
      });
      setImportJob(res.data);
      setStep(2);
    } catch (err) {
      toast.error('Validation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async () => {
    if (!importJob) return;
    setLoading(true);
    try {
      await importAPI.execute(importJob.id);
      setStep(3);
      loadImports();
    } catch (err) {
      toast.error('Import failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRollback = async (importId) => {
    if (!confirm('Rollback this import? All created records will be deleted.')) return;
    try {
      await importAPI.rollback(importId);
      loadImports();
    } catch (err) {
      toast.error('Rollback failed');
    }
  };

  const resetWizard = () => {
    setStep(0);
    setFileContent('');
    setParsedData({ headers: [], rows: [], total: 0 });
    setMapping({});
    setImportJob(null);
    setEntityConfig(null);
  };

  return (
    <>
      <div className="info-banner mb-6">
        Import data from CSV files with smart column mapping and validation.
      </div>

      {/* Progress Steps */}
      <div className="steps-progress mb-6">
        {STEPS.map((s, i) => (
          <div key={s} className={`step ${i === step ? 'active' : ''} ${i < step ? 'completed' : ''}`}>
            <div className="step-number">{i + 1}</div>
            <div className="step-label">{s}</div>
          </div>
        ))}
      </div>

      {/* Step 0: Upload */}
      {step === 0 && (
        <div className="section">
          <h3 className="section-title">Select Entity & Upload File</h3>

          <div className="form-group">
            <label className="form-label">Entity Type *</label>
            <select
              className="form-select"
              value={selectedEntity}
              onChange={(e) => {
                setSelectedEntity(e.target.value);
                if (e.target.value) loadEntityConfig(e.target.value);
              }}
            >
              <option value="">Select entity...</option>
              {entities.map(e => (
                <option key={e} value={e}>{e.charAt(0).toUpperCase() + e.slice(1)}</option>
              ))}
            </select>
          </div>

          {entityConfig && (
            <div className="info-box mt-4">
              <strong>Required fields:</strong> {entityConfig.required_fields.join(', ')}
              <br />
              <strong>Available fields:</strong> {Object.keys(entityConfig.field_mappings).join(', ')}
            </div>
          )}

          <div className="form-group mt-4">
            <label className="form-label">Upload CSV File</label>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileUpload}
              className="form-input"
            />
          </div>

          {fileContent && (
            <div className="mt-4">
              <strong>Preview (first 500 chars):</strong>
              <pre className="code-preview">{fileContent.slice(0, 500)}</pre>
            </div>
          )}

          <button
            className="btn btn-primary mt-4"
            onClick={handleParse}
            disabled={!selectedEntity || !fileContent || loading}
          >
            {loading ? 'Parsing...' : 'Parse & Continue'}
          </button>
        </div>
      )}

      {/* Step 1: Map Fields */}
      {step === 1 && (
        <div className="section">
          <h3 className="section-title">Map Columns to Fields</h3>
          <p className="text-muted mb-4">
            Found {parsedData.total} rows. Map CSV columns to {selectedEntity} fields.
          </p>

          <div className="mapping-grid">
            {parsedData.headers.map(header => (
              <div key={header} className="mapping-row">
                <div className="mapping-source">
                  <code>{header}</code>
                </div>
                <div className="mapping-arrow">-&gt;</div>
                <div className="mapping-target">
                  <select
                    className="form-select"
                    value={mapping[header] || ''}
                    onChange={(e) => setMapping({ ...mapping, [header]: e.target.value })}
                  >
                    <option value="">Skip this column</option>
                    {entityConfig?.field_mappings && Object.keys(entityConfig.field_mappings).map(f => (
                      <option key={f} value={f}>{f}</option>
                    ))}
                  </select>
                </div>
              </div>
            ))}
          </div>

          <div className="flex gap-4 mt-4">
            <button className="btn btn-secondary" onClick={() => setStep(0)}>Back</button>
            <button className="btn btn-primary" onClick={handleValidate} disabled={loading}>
              {loading ? 'Validating...' : 'Validate'}
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Validate */}
      {step === 2 && importJob && (
        <div className="section">
          <h3 className="section-title">Validation Results</h3>

          <div className="stats-grid mb-4">
            <div className="stat-card">
              <div className="stat-value">{importJob.total_rows}</div>
              <div className="stat-label">Total Rows</div>
            </div>
            <div className="stat-card">
              <div className="stat-value text-success">{importJob.valid_rows}</div>
              <div className="stat-label">Valid</div>
            </div>
            <div className="stat-card">
              <div className="stat-value text-danger">{importJob.error_rows}</div>
              <div className="stat-label">Errors</div>
            </div>
          </div>

          {importJob.errors?.length > 0 && (
            <div className="alert alert-danger mb-4">
              <strong>Validation Errors:</strong>
              <ul className="mt-2">
                {importJob.errors.slice(0, 10).map((e, i) => (
                  <li key={i}>Row {e.row}: {e.field} - {e.error}</li>
                ))}
                {importJob.errors.length > 10 && (
                  <li>...and {importJob.errors.length - 10} more errors</li>
                )}
              </ul>
            </div>
          )}

          {importJob.preview?.length > 0 && (
            <div className="mt-4">
              <strong>Preview (first 5 valid rows):</strong>
              <div className="table-container mt-2">
                <table className="data-table">
                  <thead>
                    <tr>
                      {Object.keys(importJob.preview[0]).map(k => (
                        <th key={k}>{k}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {importJob.preview.slice(0, 5).map((row, i) => (
                      <tr key={i}>
                        {Object.values(row).map((v, j) => (
                          <td key={j}>{String(v)}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <div className="flex gap-4 mt-4">
            <button className="btn btn-secondary" onClick={() => setStep(1)}>Back</button>
            <button
              className="btn btn-primary"
              onClick={handleExecute}
              disabled={importJob.valid_rows === 0 || loading}
            >
              {loading ? 'Importing...' : `Import ${importJob.valid_rows} Records`}
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Complete */}
      {step === 3 && (
        <div className="section text-center">
          <div className="success-icon mb-4">Done!</div>
          <h3>Import Complete</h3>
          <p className="text-muted">Your data has been successfully imported.</p>
          <button className="btn btn-primary mt-4" onClick={resetWizard}>
            Start New Import
          </button>
        </div>
      )}

      {/* Recent Imports */}
      {step === 0 && imports.length > 0 && (
        <div className="section mt-6">
          <h3 className="section-title">Recent Imports</h3>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Entity</th>
                  <th>Status</th>
                  <th>Rows</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {imports.map(imp => (
                  <tr key={imp.id}>
                    <td><code>{imp.id}</code></td>
                    <td>{imp.entity}</td>
                    <td>
                      <span className={`badge ${imp.status === 'completed' ? 'badge-success' : 'badge-warning'}`}>
                        {imp.status}
                      </span>
                    </td>
                    <td>{imp.created_count || imp.valid_rows} / {imp.total_rows}</td>
                    <td>{new Date(imp.created_at).toLocaleString()}</td>
                    <td>
                      {imp.status === 'completed' && (
                        <button
                          className="btn btn-sm btn-danger"
                          onClick={() => handleRollback(imp.id)}
                        >
                          Rollback
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
