import { useState, useEffect, useRef } from 'react';
import { backupAPI } from '../services/api';

const ENTITIES = [
  { value: 'materials', label: 'Materials' },
  { value: 'transactions', label: 'Transactions' },
  { value: 'payments', label: 'Payments' },
  { value: 'projects', label: 'Projects' },
  { value: 'categories', label: 'Categories' },
  { value: 'locations', label: 'Locations' }
];

export default function BackupRestore() {
  const [backups, setBackups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [restoring, setRestoring] = useState(false);
  const [selectedEntities, setSelectedEntities] = useState(ENTITIES.map(e => e.value));
  const [includeUsers, setIncludeUsers] = useState(false);
  const [restoreMode, setRestoreMode] = useState('merge');
  const fileInputRef = useRef(null);

  useEffect(() => {
    loadBackups();
  }, []);

  const loadBackups = async () => {
    try {
      const res = await backupAPI.list();
      setBackups(res.data.backups);
    } catch (err) {
      console.error('Failed to load backups:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBackup = async () => {
    setCreating(true);
    try {
      await backupAPI.create({
        entities: selectedEntities,
        include_users: includeUsers
      });
      loadBackups();
      alert('Backup created successfully!');
    } catch (err) {
      alert('Failed to create backup');
    } finally {
      setCreating(false);
    }
  };

  const handleDownload = async (backup) => {
    try {
      const res = await backupAPI.download(backup.id);
      const blob = new Blob([res.data], { type: 'application/octet-stream' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${backup.id}_${backup.created_at.split('T')[0]}.backup`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Download failed');
    }
  };

  const handleDelete = async (backup) => {
    if (!confirm('Delete this backup?')) return;
    try {
      await backupAPI.delete(backup.id);
      loadBackups();
    } catch (err) {
      alert('Delete failed');
    }
  };

  const handleRestoreFromFile = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!confirm(`Restore from backup? Mode: ${restoreMode}`)) {
      fileInputRef.current.value = '';
      return;
    }

    setRestoring(true);
    try {
      const res = await backupAPI.restoreFromFile(file, restoreMode);
      alert(`Restore complete! Restored: ${JSON.stringify(res.data.restored)}`);
      fileInputRef.current.value = '';
    } catch (err) {
      alert('Restore failed');
    } finally {
      setRestoring(false);
    }
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <>
      <div className="info-banner mb-6">
        Create backups of your data and restore from previous backups.
      </div>

      <div className="section mb-6">
        <h3 className="section-title">Create Backup</h3>

        <div className="mb-4">
          <label className="form-label">Select Entities:</label>
          <div className="checkbox-grid">
            {ENTITIES.map(entity => (
              <label key={entity.value} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={selectedEntities.includes(entity.value)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedEntities([...selectedEntities, entity.value]);
                    } else {
                      setSelectedEntities(selectedEntities.filter(v => v !== entity.value));
                    }
                  }}
                />
                <span>{entity.label}</span>
              </label>
            ))}
          </div>
        </div>

        <label className="checkbox-label mb-4">
          <input
            type="checkbox"
            checked={includeUsers}
            onChange={(e) => setIncludeUsers(e.target.checked)}
          />
          <span>Include Users (without passwords)</span>
        </label>

        <button
          className="btn btn-primary"
          onClick={handleCreateBackup}
          disabled={creating || selectedEntities.length === 0}
        >
          {creating ? 'Creating...' : 'Create Backup'}
        </button>
      </div>

      <div className="section mb-6">
        <h3 className="section-title">Restore from File</h3>

        <div className="form-group mb-4">
          <label className="form-label">Restore Mode:</label>
          <select
            className="form-select"
            value={restoreMode}
            onChange={(e) => setRestoreMode(e.target.value)}
            style={{ maxWidth: '300px' }}
          >
            <option value="merge">Merge (Update existing, add new)</option>
            <option value="replace">Replace (Clear existing first)</option>
          </select>
        </div>

        <div className="upload-zone" onClick={() => fileInputRef.current?.click()}>
          <input
            ref={fileInputRef}
            type="file"
            accept=".backup"
            onChange={handleRestoreFromFile}
            style={{ display: 'none' }}
          />
          {restoring ? (
            <p>Restoring...</p>
          ) : (
            <>
              <div style={{ fontSize: '2rem', marginBottom: '8px' }}>Upload</div>
              <p>Click to upload a .backup file</p>
            </>
          )}
        </div>
      </div>

      <div className="section">
        <h3 className="section-title">Backup History</h3>

        {loading ? (
          <div className="text-center text-muted">Loading...</div>
        ) : backups.length === 0 ? (
          <div className="text-center text-muted">No backups yet</div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Created</th>
                  <th>Entities</th>
                  <th>Size</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {backups.map(backup => (
                  <tr key={backup.id}>
                    <td><code>{backup.id}</code></td>
                    <td>{new Date(backup.created_at).toLocaleString()}</td>
                    <td>{backup.entities.length} entities</td>
                    <td>{formatSize(backup.size_bytes)}</td>
                    <td>
                      <div className="flex gap-2">
                        <button className="btn btn-sm btn-secondary" onClick={() => handleDownload(backup)}>Download</button>
                        <button className="btn btn-sm btn-danger" onClick={() => handleDelete(backup)}>Delete</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
