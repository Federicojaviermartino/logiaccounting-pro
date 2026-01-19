import { useState, useEffect, useRef } from 'react';
import { reconciliationAPI } from '../services/api';

export default function BankReconciliation() {
  const [statements, setStatements] = useState([]);
  const [currentStatement, setCurrentStatement] = useState(null);
  const [unmatchedTxns, setUnmatchedTxns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showImport, setShowImport] = useState(false);
  const [selectedEntry, setSelectedEntry] = useState(null);
  const fileInputRef = useRef(null);

  const [importData, setImportData] = useState({
    bank_name: '',
    account_number: '',
    period_start: '',
    period_end: '',
    entries: []
  });

  useEffect(() => {
    loadStatements();
  }, []);

  useEffect(() => {
    if (currentStatement) {
      loadUnmatchedTransactions();
    }
  }, [currentStatement]);

  const loadStatements = async () => {
    try {
      const res = await reconciliationAPI.list();
      setStatements(res.data.statements || []);
    } catch (err) {
      console.error('Failed to load statements:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadUnmatchedTransactions = async () => {
    try {
      const res = await reconciliationAPI.getUnmatchedTxns(currentStatement.id);
      setUnmatchedTxns(res.data.transactions || []);
    } catch (err) {
      console.error('Failed to load transactions:', err);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target.result;
      const lines = text.split('\n');
      const entries = [];

      // Simple CSV parsing (assume: date,description,amount,reference)
      for (let i = 1; i < lines.length; i++) {
        const cols = lines[i].split(',');
        if (cols.length >= 3) {
          entries.push({
            date: cols[0]?.trim(),
            description: cols[1]?.trim(),
            amount: parseFloat(cols[2]) || 0,
            reference: cols[3]?.trim() || ''
          });
        }
      }

      setImportData({ ...importData, entries });
    };
    reader.readAsText(file);
  };

  const handleImport = async () => {
    try {
      const res = await reconciliationAPI.import(importData);
      setStatements([res.data, ...statements]);
      setCurrentStatement(res.data);
      setShowImport(false);
      setImportData({ bank_name: '', account_number: '', period_start: '', period_end: '', entries: [] });
    } catch (err) {
      alert('Import failed');
    }
  };

  const handleAutoMatch = async () => {
    try {
      const res = await reconciliationAPI.autoMatch(currentStatement.id);
      alert(`Auto-matched: ${res.data.auto_matched}, Suggested: ${res.data.suggested}`);
      const updated = await reconciliationAPI.get(currentStatement.id);
      setCurrentStatement(updated.data);
    } catch (err) {
      alert('Auto-match failed');
    }
  };

  const handleManualMatch = async (txnId) => {
    if (!selectedEntry) return;
    try {
      await reconciliationAPI.manualMatch(currentStatement.id, selectedEntry.entry_id, txnId);
      const updated = await reconciliationAPI.get(currentStatement.id);
      setCurrentStatement(updated.data);
      setSelectedEntry(null);
      loadUnmatchedTransactions();
    } catch (err) {
      alert('Match failed');
    }
  };

  const handleUnmatch = async (entryId) => {
    try {
      await reconciliationAPI.unmatch(currentStatement.id, entryId);
      const updated = await reconciliationAPI.get(currentStatement.id);
      setCurrentStatement(updated.data);
      loadUnmatchedTransactions();
    } catch (err) {
      alert('Unmatch failed');
    }
  };

  const handleComplete = async () => {
    if (currentStatement.unmatched_count > 0) {
      alert('Cannot complete: unmatched entries remain');
      return;
    }
    try {
      await reconciliationAPI.complete(currentStatement.id);
      const updated = await reconciliationAPI.get(currentStatement.id);
      setCurrentStatement(updated.data);
      alert('Reconciliation complete!');
    } catch (err) {
      alert('Failed to complete');
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return '#10b981';
    if (score >= 50) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <>
      <div className="info-banner mb-6">
        Match bank statement entries with system transactions to reconcile accounts.
      </div>

      {/* Statement Selector */}
      <div className="section mb-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="section-title" style={{ margin: 0 }}>Bank Statements</h3>
          <button className="btn btn-primary" onClick={() => setShowImport(true)}>
            Import Statement
          </button>
        </div>

        {loading ? (
          <div className="text-center text-muted">Loading...</div>
        ) : statements.length === 0 ? (
          <div className="text-center text-muted">No statements imported</div>
        ) : (
          <div className="statement-list">
            {statements.map(stmt => (
              <div
                key={stmt.id}
                className={`statement-card ${currentStatement?.id === stmt.id ? 'active' : ''}`}
                onClick={() => setCurrentStatement(stmt)}
              >
                <div className="statement-bank">{stmt.bank_name}</div>
                <div className="statement-period">
                  {stmt.period_start} - {stmt.period_end}
                </div>
                <div className="statement-stats">
                  <span className="matched">Matched: {stmt.matched_count}</span>
                  <span className="unmatched">Unmatched: {stmt.unmatched_count}</span>
                </div>
                {stmt.reconciled && <span className="badge badge-success">Reconciled</span>}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Matching Interface */}
      {currentStatement && (
        <div className="section">
          <div className="flex justify-between items-center mb-4">
            <h3 className="section-title" style={{ margin: 0 }}>
              Reconcile: {currentStatement.bank_name}
            </h3>
            <div className="flex gap-2">
              <button className="btn btn-secondary" onClick={handleAutoMatch}>
                Auto-Match
              </button>
              <button
                className="btn btn-primary"
                onClick={handleComplete}
                disabled={currentStatement.unmatched_count > 0}
              >
                Complete
              </button>
            </div>
          </div>

          <div className="reconciliation-grid">
            {/* Bank Entries */}
            <div className="recon-panel">
              <h4>Bank Entries ({currentStatement.entries?.length || 0})</h4>
              <div className="entries-list">
                {currentStatement.entries?.map(entry => (
                  <div
                    key={entry.entry_id}
                    className={`entry-item ${entry.matched ? 'matched' : ''} ${selectedEntry?.entry_id === entry.entry_id ? 'selected' : ''}`}
                    onClick={() => !entry.matched && setSelectedEntry(entry)}
                  >
                    <div className="entry-date">{entry.date}</div>
                    <div className="entry-desc">{entry.description}</div>
                    <div className={`entry-amount ${entry.amount >= 0 ? 'positive' : 'negative'}`}>
                      ${Math.abs(entry.amount).toLocaleString()}
                    </div>
                    {entry.matched ? (
                      <div className="entry-status">
                        <span className="badge badge-success">Matched</span>
                        <button
                          className="btn btn-sm btn-secondary"
                          onClick={(e) => { e.stopPropagation(); handleUnmatch(entry.entry_id); }}
                        >
                          Unmatch
                        </button>
                      </div>
                    ) : entry.match_score ? (
                      <div className="entry-score" style={{ color: getScoreColor(entry.match_score) }}>
                        {entry.match_score}% match
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            </div>

            {/* System Transactions */}
            <div className="recon-panel">
              <h4>System Transactions ({unmatchedTxns.length})</h4>
              <div className="entries-list">
                {unmatchedTxns.map(txn => (
                  <div
                    key={txn.id}
                    className="entry-item"
                    onClick={() => selectedEntry && handleManualMatch(txn.id)}
                  >
                    <div className="entry-date">{txn.date}</div>
                    <div className="entry-desc">{txn.description}</div>
                    <div className={`entry-amount ${txn.type === 'income' ? 'positive' : 'negative'}`}>
                      ${txn.amount?.toLocaleString()}
                    </div>
                    {selectedEntry && (
                      <button className="btn btn-sm btn-primary">Match</button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Import Modal */}
      {showImport && (
        <div className="modal-overlay" onClick={() => setShowImport(false)}>
          <div className="modal-content modal-lg" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Import Bank Statement</h3>
              <button className="modal-close" onClick={() => setShowImport(false)}>x</button>
            </div>
            <div className="modal-body">
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Bank Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={importData.bank_name}
                    onChange={(e) => setImportData({ ...importData, bank_name: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Account Number</label>
                  <input
                    type="text"
                    className="form-input"
                    value={importData.account_number}
                    onChange={(e) => setImportData({ ...importData, account_number: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Period Start</label>
                  <input
                    type="date"
                    className="form-input"
                    value={importData.period_start}
                    onChange={(e) => setImportData({ ...importData, period_start: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Period End</label>
                  <input
                    type="date"
                    className="form-input"
                    value={importData.period_end}
                    onChange={(e) => setImportData({ ...importData, period_end: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Upload CSV (date,description,amount,reference)</label>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  onChange={handleFileUpload}
                  className="form-input"
                />
              </div>

              {importData.entries.length > 0 && (
                <div className="import-preview">
                  <strong>{importData.entries.length} entries found</strong>
                  <div className="preview-list">
                    {importData.entries.slice(0, 5).map((e, i) => (
                      <div key={i} className="preview-item">
                        {e.date} | {e.description?.substring(0, 30)} | ${e.amount}
                      </div>
                    ))}
                    {importData.entries.length > 5 && (
                      <div className="text-muted">...and {importData.entries.length - 5} more</div>
                    )}
                  </div>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowImport(false)}>Cancel</button>
              <button
                className="btn btn-primary"
                onClick={handleImport}
                disabled={!importData.bank_name || !importData.entries.length}
              >
                Import
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
