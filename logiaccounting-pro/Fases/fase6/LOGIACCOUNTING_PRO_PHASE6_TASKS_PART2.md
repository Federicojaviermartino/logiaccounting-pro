# LogiAccounting Pro - Phase 6 Tasks (Part 2/3)

## BANK RECONCILIATION + CLIENT PORTAL + SUPPLIER PORTAL

---

## TASK 4: BANK RECONCILIATION 🏦

### 4.1 Create Reconciliation Service

**File:** `backend/app/services/reconciliation_service.py`

```python
"""
Bank Reconciliation Service
Match bank statements with system transactions
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from app.models.store import db


class ReconciliationService:
    """Manages bank statement reconciliation"""
    
    _instance = None
    _statements: Dict[str, dict] = {}
    _counter = 0
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._statements = {}
            cls._counter = 0
        return cls._instance
    
    def import_statement(
        self,
        bank_name: str,
        account_number: str,
        period_start: str,
        period_end: str,
        entries: List[dict],
        imported_by: str
    ) -> dict:
        """Import a bank statement"""
        self._counter += 1
        statement_id = f"STMT-{self._counter:04d}"
        
        # Process entries
        processed_entries = []
        for i, entry in enumerate(entries):
            processed_entries.append({
                "entry_id": f"E{i+1:04d}",
                "date": entry.get("date"),
                "description": entry.get("description", ""),
                "reference": entry.get("reference", ""),
                "amount": float(entry.get("amount", 0)),
                "balance": float(entry.get("balance", 0)) if entry.get("balance") else None,
                "matched": False,
                "matched_txn_id": None,
                "match_score": None
            })
        
        statement = {
            "id": statement_id,
            "bank_name": bank_name,
            "account_number": account_number[-4:] if len(account_number) > 4 else account_number,
            "period_start": period_start,
            "period_end": period_end,
            "entries": processed_entries,
            "entry_count": len(processed_entries),
            "total_credits": sum(e["amount"] for e in processed_entries if e["amount"] > 0),
            "total_debits": sum(e["amount"] for e in processed_entries if e["amount"] < 0),
            "matched_count": 0,
            "unmatched_count": len(processed_entries),
            "reconciled": False,
            "imported_by": imported_by,
            "imported_at": datetime.utcnow().isoformat()
        }
        
        self._statements[statement_id] = statement
        return statement
    
    def auto_match(self, statement_id: str, tolerance_percent: float = 5, tolerance_days: int = 3) -> dict:
        """Run auto-matching algorithm"""
        statement = self._statements.get(statement_id)
        if not statement:
            return {"error": "Statement not found"}
        
        transactions = db.transactions.find_all()
        
        matches = []
        for entry in statement["entries"]:
            if entry["matched"]:
                continue
            
            best_match = None
            best_score = 0
            
            for txn in transactions:
                if txn.get("reconciled"):
                    continue
                
                score = self._calculate_match_score(entry, txn, tolerance_percent, tolerance_days)
                
                if score > best_score and score >= 50:
                    best_score = score
                    best_match = txn
            
            if best_match and best_score >= 80:
                # Auto-match
                entry["matched"] = True
                entry["matched_txn_id"] = best_match["id"]
                entry["match_score"] = best_score
                matches.append({
                    "entry_id": entry["entry_id"],
                    "txn_id": best_match["id"],
                    "score": best_score,
                    "auto": True
                })
            elif best_match and best_score >= 50:
                # Suggest match
                entry["suggested_txn_id"] = best_match["id"]
                entry["match_score"] = best_score
                matches.append({
                    "entry_id": entry["entry_id"],
                    "txn_id": best_match["id"],
                    "score": best_score,
                    "auto": False,
                    "suggested": True
                })
        
        # Update counts
        statement["matched_count"] = len([e for e in statement["entries"] if e["matched"]])
        statement["unmatched_count"] = len([e for e in statement["entries"] if not e["matched"]])
        
        return {
            "statement_id": statement_id,
            "matches": matches,
            "auto_matched": len([m for m in matches if m.get("auto")]),
            "suggested": len([m for m in matches if m.get("suggested")]),
            "unmatched": statement["unmatched_count"]
        }
    
    def _calculate_match_score(
        self, 
        entry: dict, 
        txn: dict, 
        tolerance_percent: float,
        tolerance_days: int
    ) -> int:
        """Calculate match score between bank entry and transaction"""
        score = 0
        
        # Amount matching (40 points max)
        entry_amount = abs(entry["amount"])
        txn_amount = abs(txn.get("amount", 0))
        
        if entry_amount == txn_amount:
            score += 40
        elif txn_amount > 0:
            diff_percent = abs(entry_amount - txn_amount) / txn_amount * 100
            if diff_percent <= tolerance_percent:
                score += int(40 - diff_percent * 3)
        
        # Date matching (30 points max)
        try:
            entry_date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
            txn_date = datetime.strptime(txn.get("date", ""), "%Y-%m-%d").date()
            
            day_diff = abs((entry_date - txn_date).days)
            
            if day_diff == 0:
                score += 30
            elif day_diff <= tolerance_days:
                score += int(30 - day_diff * 5)
        except (ValueError, TypeError):
            pass
        
        # Reference matching (20 points)
        entry_ref = entry.get("reference", "").lower()
        txn_ref = txn.get("invoice_number", "").lower() or txn.get("reference", "").lower()
        
        if entry_ref and txn_ref and (entry_ref in txn_ref or txn_ref in entry_ref):
            score += 20
        
        # Description matching (10 points)
        entry_desc = entry.get("description", "").lower()
        txn_desc = txn.get("description", "").lower()
        
        if entry_desc and txn_desc:
            words_match = len(set(entry_desc.split()) & set(txn_desc.split()))
            if words_match >= 2:
                score += 10
            elif words_match == 1:
                score += 5
        
        return score
    
    def manual_match(self, statement_id: str, entry_id: str, txn_id: str) -> dict:
        """Manually match an entry to a transaction"""
        statement = self._statements.get(statement_id)
        if not statement:
            return {"error": "Statement not found"}
        
        entry = next((e for e in statement["entries"] if e["entry_id"] == entry_id), None)
        if not entry:
            return {"error": "Entry not found"}
        
        entry["matched"] = True
        entry["matched_txn_id"] = txn_id
        entry["match_score"] = 100  # Manual = 100%
        
        # Update counts
        statement["matched_count"] = len([e for e in statement["entries"] if e["matched"]])
        statement["unmatched_count"] = len([e for e in statement["entries"] if not e["matched"]])
        
        return {"success": True, "entry": entry}
    
    def unmatch(self, statement_id: str, entry_id: str) -> dict:
        """Unmatch an entry"""
        statement = self._statements.get(statement_id)
        if not statement:
            return {"error": "Statement not found"}
        
        entry = next((e for e in statement["entries"] if e["entry_id"] == entry_id), None)
        if not entry:
            return {"error": "Entry not found"}
        
        entry["matched"] = False
        entry["matched_txn_id"] = None
        entry["match_score"] = None
        
        # Update counts
        statement["matched_count"] = len([e for e in statement["entries"] if e["matched"]])
        statement["unmatched_count"] = len([e for e in statement["entries"] if not e["matched"]])
        
        return {"success": True}
    
    def complete_reconciliation(self, statement_id: str) -> dict:
        """Mark statement as reconciled"""
        statement = self._statements.get(statement_id)
        if not statement:
            return {"error": "Statement not found"}
        
        if statement["unmatched_count"] > 0:
            return {"error": f"{statement['unmatched_count']} entries still unmatched"}
        
        statement["reconciled"] = True
        statement["reconciled_at"] = datetime.utcnow().isoformat()
        
        # Mark transactions as reconciled
        for entry in statement["entries"]:
            if entry["matched_txn_id"]:
                txn = db.transactions.find_by_id(entry["matched_txn_id"])
                if txn:
                    db.transactions.update(entry["matched_txn_id"], {"reconciled": True})
        
        return {"success": True, "statement": statement}
    
    def get_statement(self, statement_id: str) -> Optional[dict]:
        """Get a specific statement"""
        return self._statements.get(statement_id)
    
    def list_statements(self) -> List[dict]:
        """List all statements"""
        return sorted(
            self._statements.values(),
            key=lambda s: s["imported_at"],
            reverse=True
        )
    
    def get_unmatched_transactions(self, period_start: str, period_end: str) -> List[dict]:
        """Get unreconciled transactions in a period"""
        transactions = db.transactions.find_all()
        return [
            t for t in transactions
            if not t.get("reconciled")
            and period_start <= t.get("date", "") <= period_end
        ]
    
    def delete_statement(self, statement_id: str) -> bool:
        """Delete a statement"""
        if statement_id in self._statements:
            del self._statements[statement_id]
            return True
        return False


reconciliation_service = ReconciliationService()
```

### 4.2 Create Reconciliation Routes

**File:** `backend/app/routes/reconciliation.py`

```python
"""
Bank Reconciliation routes
"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.reconciliation_service import reconciliation_service
from app.utils.auth import require_roles

router = APIRouter()


class ImportStatementRequest(BaseModel):
    bank_name: str
    account_number: str
    period_start: str
    period_end: str
    entries: List[dict]


class ManualMatchRequest(BaseModel):
    entry_id: str
    txn_id: str


@router.get("")
async def list_statements(current_user: dict = Depends(require_roles("admin"))):
    """List all bank statements"""
    return {"statements": reconciliation_service.list_statements()}


@router.post("/import")
async def import_statement(
    request: ImportStatementRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Import a bank statement"""
    return reconciliation_service.import_statement(
        bank_name=request.bank_name,
        account_number=request.account_number,
        period_start=request.period_start,
        period_end=request.period_end,
        entries=request.entries,
        imported_by=current_user["id"]
    )


@router.get("/{statement_id}")
async def get_statement(
    statement_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get a specific statement"""
    statement = reconciliation_service.get_statement(statement_id)
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")
    return statement


@router.post("/{statement_id}/auto-match")
async def auto_match(
    statement_id: str,
    tolerance_percent: float = 5,
    tolerance_days: int = 3,
    current_user: dict = Depends(require_roles("admin"))
):
    """Run auto-matching"""
    result = reconciliation_service.auto_match(statement_id, tolerance_percent, tolerance_days)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{statement_id}/match")
async def manual_match(
    statement_id: str,
    request: ManualMatchRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Manually match an entry"""
    result = reconciliation_service.manual_match(statement_id, request.entry_id, request.txn_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{statement_id}/unmatch/{entry_id}")
async def unmatch(
    statement_id: str,
    entry_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Unmatch an entry"""
    result = reconciliation_service.unmatch(statement_id, entry_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{statement_id}/complete")
async def complete_reconciliation(
    statement_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Complete reconciliation"""
    result = reconciliation_service.complete_reconciliation(statement_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/{statement_id}/unmatched-transactions")
async def get_unmatched_transactions(
    statement_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get unmatched transactions for a statement period"""
    statement = reconciliation_service.get_statement(statement_id)
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")
    
    transactions = reconciliation_service.get_unmatched_transactions(
        statement["period_start"],
        statement["period_end"]
    )
    return {"transactions": transactions}


@router.delete("/{statement_id}")
async def delete_statement(
    statement_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Delete a statement"""
    if reconciliation_service.delete_statement(statement_id):
        return {"message": "Statement deleted"}
    raise HTTPException(status_code=404, detail="Statement not found")
```

### 4.3 Add Reconciliation API to Frontend

**Add to:** `frontend/src/services/api.js`

```javascript
// Bank Reconciliation API
export const reconciliationAPI = {
  list: () => api.get('/api/v1/reconciliation'),
  import: (data) => api.post('/api/v1/reconciliation/import', data),
  get: (id) => api.get(`/api/v1/reconciliation/${id}`),
  autoMatch: (id, tolerancePercent = 5, toleranceDays = 3) => 
    api.post(`/api/v1/reconciliation/${id}/auto-match`, null, { 
      params: { tolerance_percent: tolerancePercent, tolerance_days: toleranceDays } 
    }),
  manualMatch: (id, entryId, txnId) => api.post(`/api/v1/reconciliation/${id}/match`, { entry_id: entryId, txn_id: txnId }),
  unmatch: (id, entryId) => api.post(`/api/v1/reconciliation/${id}/unmatch/${entryId}`),
  complete: (id) => api.post(`/api/v1/reconciliation/${id}/complete`),
  getUnmatchedTxns: (id) => api.get(`/api/v1/reconciliation/${id}/unmatched-transactions`),
  delete: (id) => api.delete(`/api/v1/reconciliation/${id}`)
};
```

### 4.4 Create Bank Reconciliation Page

**File:** `frontend/src/pages/BankReconciliation.jsx`

```jsx
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
      setStatements(res.data.statements);
    } catch (err) {
      console.error('Failed to load statements:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadUnmatchedTransactions = async () => {
    try {
      const res = await reconciliationAPI.getUnmatchedTxns(currentStatement.id);
      setUnmatchedTxns(res.data.transactions);
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
        🏦 Match bank statement entries with system transactions to reconcile accounts.
      </div>

      {/* Statement Selector */}
      <div className="section mb-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="section-title" style={{ margin: 0 }}>Bank Statements</h3>
          <button className="btn btn-primary" onClick={() => setShowImport(true)}>
            📥 Import Statement
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
                  <span className="matched">✅ {stmt.matched_count}</span>
                  <span className="unmatched">⚪ {stmt.unmatched_count}</span>
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
                🤖 Auto-Match
              </button>
              <button 
                className="btn btn-primary" 
                onClick={handleComplete}
                disabled={currentStatement.unmatched_count > 0}
              >
                ✅ Complete
              </button>
            </div>
          </div>

          <div className="reconciliation-grid">
            {/* Bank Entries */}
            <div className="recon-panel">
              <h4>Bank Entries ({currentStatement.entries.length})</h4>
              <div className="entries-list">
                {currentStatement.entries.map(entry => (
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
              <button className="modal-close" onClick={() => setShowImport(false)}>×</button>
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
```

### 4.5 Add Reconciliation Styles

**Add to:** `frontend/src/index.css`

```css
/* Bank Reconciliation */
.statement-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 16px;
}

.statement-card {
  padding: 16px;
  border: 2px solid var(--border-color);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.statement-card:hover, .statement-card.active {
  border-color: var(--primary);
}

.statement-bank {
  font-weight: 600;
  margin-bottom: 4px;
}

.statement-period {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.statement-stats {
  display: flex;
  gap: 12px;
  font-size: 0.9rem;
}

.statement-stats .matched { color: #10b981; }
.statement-stats .unmatched { color: var(--text-muted); }

.reconciliation-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.recon-panel {
  background: var(--bg-tertiary);
  border-radius: 12px;
  padding: 16px;
}

.recon-panel h4 {
  margin: 0 0 16px 0;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.entries-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 500px;
  overflow-y: auto;
}

.entry-item {
  padding: 12px;
  background: var(--card-bg);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  display: grid;
  grid-template-columns: 80px 1fr auto auto;
  gap: 12px;
  align-items: center;
}

.entry-item:hover {
  transform: translateX(4px);
}

.entry-item.matched {
  opacity: 0.6;
  cursor: default;
}

.entry-item.selected {
  border: 2px solid var(--primary);
  background: rgba(102, 126, 234, 0.1);
}

.entry-date {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.entry-desc {
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.entry-amount {
  font-weight: 600;
}

.entry-amount.positive { color: #10b981; }
.entry-amount.negative { color: #ef4444; }

.entry-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.entry-score {
  font-size: 0.85rem;
  font-weight: 500;
}

.import-preview {
  margin-top: 16px;
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: 8px;
}

.preview-list {
  margin-top: 8px;
  font-size: 0.85rem;
  font-family: monospace;
}

.preview-item {
  padding: 4px 0;
  border-bottom: 1px solid var(--border-color);
}

@media (max-width: 900px) {
  .reconciliation-grid {
    grid-template-columns: 1fr;
  }
}
```

---

## TASK 5: CLIENT PORTAL 👥

### 5.1 Create Portal Routes

**File:** `backend/app/routes/client_portal.py`

```python
"""
Client Portal routes
Limited access for clients to view their data
"""

from fastapi import APIRouter, HTTPException, Depends
from app.models.store import db
from app.utils.auth import get_current_user, require_roles

router = APIRouter()


def get_client_user(current_user: dict = Depends(get_current_user)):
    """Ensure user is a client"""
    if current_user.get("role") not in ["client", "admin"]:
        raise HTTPException(status_code=403, detail="Client access required")
    return current_user


@router.get("/dashboard")
async def client_dashboard(current_user: dict = Depends(get_client_user)):
    """Get client dashboard data"""
    client_email = current_user["email"]
    
    # Get projects where client matches
    projects = [p for p in db.projects.find_all() if p.get("client") == client_email or current_user["role"] == "admin"]
    
    # Get related transactions and payments
    project_ids = [p["id"] for p in projects]
    
    transactions = [t for t in db.transactions.find_all() if t.get("project_id") in project_ids]
    payments = [p for p in db.payments.find_all() if p.get("project_id") in project_ids]
    
    # Stats
    total_invoiced = sum(t.get("amount", 0) for t in transactions if t.get("type") == "income")
    total_paid = sum(p.get("amount", 0) for p in payments if p.get("status") == "paid")
    total_pending = sum(p.get("amount", 0) for p in payments if p.get("status") == "pending")
    
    return {
        "stats": {
            "total_projects": len(projects),
            "active_projects": len([p for p in projects if p.get("status") == "active"]),
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "total_pending": total_pending
        },
        "recent_projects": projects[:5],
        "recent_invoices": transactions[:5],
        "pending_payments": [p for p in payments if p.get("status") == "pending"][:5]
    }


@router.get("/projects")
async def client_projects(current_user: dict = Depends(get_client_user)):
    """Get client's projects"""
    client_email = current_user["email"]
    
    if current_user["role"] == "admin":
        projects = db.projects.find_all()
    else:
        projects = [p for p in db.projects.find_all() if p.get("client") == client_email]
    
    # Remove sensitive fields
    safe_projects = []
    for p in projects:
        safe_projects.append({
            "id": p.get("id"),
            "name": p.get("name"),
            "description": p.get("description"),
            "status": p.get("status"),
            "progress": p.get("progress", 0),
            "start_date": p.get("start_date"),
            "end_date": p.get("end_date")
            # Note: budget/spent not exposed to clients
        })
    
    return {"projects": safe_projects}


@router.get("/projects/{project_id}")
async def client_project_detail(
    project_id: str,
    current_user: dict = Depends(get_client_user)
):
    """Get project details"""
    project = db.projects.find_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify ownership (unless admin)
    if current_user["role"] != "admin" and project.get("client") != current_user["email"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "id": project.get("id"),
        "name": project.get("name"),
        "description": project.get("description"),
        "status": project.get("status"),
        "progress": project.get("progress", 0),
        "start_date": project.get("start_date"),
        "end_date": project.get("end_date")
    }


@router.get("/invoices")
async def client_invoices(current_user: dict = Depends(get_client_user)):
    """Get client's invoices"""
    client_email = current_user["email"]
    
    # Get projects
    if current_user["role"] == "admin":
        projects = db.projects.find_all()
    else:
        projects = [p for p in db.projects.find_all() if p.get("client") == client_email]
    
    project_ids = [p["id"] for p in projects]
    project_names = {p["id"]: p["name"] for p in projects}
    
    # Get income transactions (invoices)
    transactions = [
        t for t in db.transactions.find_all()
        if t.get("project_id") in project_ids and t.get("type") == "income"
    ]
    
    # Add project name
    for t in transactions:
        t["project_name"] = project_names.get(t.get("project_id"), "N/A")
    
    return {"invoices": transactions}


@router.get("/payments")
async def client_payments(current_user: dict = Depends(get_client_user)):
    """Get client's payments"""
    client_email = current_user["email"]
    
    # Get projects
    if current_user["role"] == "admin":
        projects = db.projects.find_all()
    else:
        projects = [p for p in db.projects.find_all() if p.get("client") == client_email]
    
    project_ids = [p["id"] for p in projects]
    project_names = {p["id"]: p["name"] for p in projects}
    
    # Get payments
    payments = [p for p in db.payments.find_all() if p.get("project_id") in project_ids]
    
    for p in payments:
        p["project_name"] = project_names.get(p.get("project_id"), "N/A")
    
    return {"payments": payments}


@router.get("/profile")
async def client_profile(current_user: dict = Depends(get_client_user)):
    """Get client profile"""
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "name": current_user.get("name", ""),
        "company": current_user.get("company", ""),
        "phone": current_user.get("phone", "")
    }
```

### 5.2 Create Client Portal Frontend

**File:** `frontend/src/pages/portal/ClientDashboard.jsx`

```jsx
import { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { Link } from 'react-router-dom';

export default function ClientDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const res = await api.get('/api/v1/portal/client/dashboard');
      setData(res.data);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="text-center p-8">Loading...</div>;

  const { stats, recent_projects, pending_payments } = data || {};

  return (
    <>
      <div className="portal-welcome mb-6">
        <h2>Welcome to Your Portal</h2>
        <p>View your projects, invoices, and payments.</p>
      </div>

      {/* Stats */}
      <div className="stats-grid mb-6">
        <div className="stat-card">
          <div className="stat-icon">📁</div>
          <div className="stat-content">
            <div className="stat-value">{stats?.total_projects || 0}</div>
            <div className="stat-label">Total Projects</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🟢</div>
          <div className="stat-content">
            <div className="stat-value">{stats?.active_projects || 0}</div>
            <div className="stat-label">Active Projects</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">💰</div>
          <div className="stat-content">
            <div className="stat-value">${stats?.total_paid?.toLocaleString() || 0}</div>
            <div className="stat-label">Total Paid</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">⏳</div>
          <div className="stat-content">
            <div className="stat-value">${stats?.total_pending?.toLocaleString() || 0}</div>
            <div className="stat-label">Pending</div>
          </div>
        </div>
      </div>

      <div className="grid-2">
        {/* Recent Projects */}
        <div className="section">
          <h3 className="section-title">Recent Projects</h3>
          {recent_projects?.length === 0 ? (
            <div className="text-muted">No projects yet</div>
          ) : (
            <div className="portal-list">
              {recent_projects?.map(project => (
                <Link key={project.id} to={`/portal/projects/${project.id}`} className="portal-item">
                  <div className="portal-item-name">{project.name}</div>
                  <span className={`badge badge-${project.status === 'active' ? 'success' : 'gray'}`}>
                    {project.status}
                  </span>
                </Link>
              ))}
            </div>
          )}
          <Link to="/portal/projects" className="btn btn-secondary btn-sm mt-4">View All →</Link>
        </div>

        {/* Pending Payments */}
        <div className="section">
          <h3 className="section-title">Pending Payments</h3>
          {pending_payments?.length === 0 ? (
            <div className="text-muted">No pending payments</div>
          ) : (
            <div className="portal-list">
              {pending_payments?.map(payment => (
                <div key={payment.id} className="portal-item">
                  <div>
                    <div className="portal-item-name">${payment.amount?.toLocaleString()}</div>
                    <div className="text-muted text-sm">Due: {payment.due_date}</div>
                  </div>
                  <span className="badge badge-warning">Pending</span>
                </div>
              ))}
            </div>
          )}
          <Link to="/portal/payments" className="btn btn-secondary btn-sm mt-4">View All →</Link>
        </div>
      </div>
    </>
  );
}
```

**File:** `frontend/src/pages/portal/ClientProjects.jsx`

```jsx
import { useState, useEffect } from 'react';
import { api } from '../../services/api';

export default function ClientProjects() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const res = await api.get('/api/v1/portal/client/projects');
      setProjects(res.data.projects);
    } catch (err) {
      console.error('Failed to load projects:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = { active: 'success', completed: 'info', on_hold: 'warning', cancelled: 'danger' };
    return colors[status] || 'gray';
  };

  if (loading) return <div className="text-center p-8">Loading...</div>;

  return (
    <>
      <h2 className="page-title mb-6">My Projects</h2>

      {projects.length === 0 ? (
        <div className="section text-center text-muted">No projects found</div>
      ) : (
        <div className="portal-projects-grid">
          {projects.map(project => (
            <div key={project.id} className="portal-project-card">
              <div className="portal-project-header">
                <h4>{project.name}</h4>
                <span className={`badge badge-${getStatusColor(project.status)}`}>
                  {project.status}
                </span>
              </div>
              <p className="portal-project-desc">{project.description?.substring(0, 100) || 'No description'}</p>
              
              <div className="portal-project-progress">
                <div className="progress-label">
                  <span>Progress</span>
                  <span>{project.progress || 0}%</span>
                </div>
                <div className="progress-bar-container">
                  <div className="progress-bar" style={{ width: `${project.progress || 0}%` }} />
                </div>
              </div>
              
              <div className="portal-project-dates">
                <span>📅 {project.start_date || 'TBD'}</span>
                <span>→</span>
                <span>{project.end_date || 'TBD'}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
```

**File:** `frontend/src/pages/portal/ClientPayments.jsx`

```jsx
import { useState, useEffect } from 'react';
import { api } from '../../services/api';

export default function ClientPayments() {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadPayments();
  }, []);

  const loadPayments = async () => {
    try {
      const res = await api.get('/api/v1/portal/client/payments');
      setPayments(res.data.payments);
    } catch (err) {
      console.error('Failed to load payments:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredPayments = filter === 'all' 
    ? payments 
    : payments.filter(p => p.status === filter);

  const getStatusBadge = (status) => {
    const styles = { paid: 'badge-success', pending: 'badge-warning', overdue: 'badge-danger' };
    return <span className={`badge ${styles[status] || 'badge-gray'}`}>{status}</span>;
  };

  if (loading) return <div className="text-center p-8">Loading...</div>;

  return (
    <>
      <h2 className="page-title mb-6">My Payments</h2>

      <div className="section mb-4">
        <div className="flex gap-2">
          {['all', 'pending', 'paid'].map(f => (
            <button
              key={f}
              className={`btn btn-sm ${filter === f ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setFilter(f)}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="section">
        {filteredPayments.length === 0 ? (
          <div className="text-center text-muted">No payments found</div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Reference</th>
                  <th>Project</th>
                  <th>Amount</th>
                  <th>Due Date</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredPayments.map(payment => (
                  <tr key={payment.id}>
                    <td><code>{payment.reference || payment.id}</code></td>
                    <td>{payment.project_name}</td>
                    <td className="font-bold">${payment.amount?.toLocaleString()}</td>
                    <td>{payment.due_date}</td>
                    <td>{getStatusBadge(payment.status)}</td>
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
```

### 5.3 Add Portal Styles

**Add to:** `frontend/src/index.css`

```css
/* Portal Styles */
.portal-welcome {
  padding: 24px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  border-radius: 12px;
}

.portal-welcome h2 {
  margin: 0 0 8px 0;
}

.portal-welcome p {
  margin: 0;
  color: var(--text-muted);
}

.portal-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.portal-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: 8px;
  text-decoration: none;
  color: var(--text-primary);
  transition: all 0.2s;
}

.portal-item:hover {
  background: var(--bg-hover);
}

.portal-item-name {
  font-weight: 500;
}

.portal-projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.portal-project-card {
  padding: 20px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
}

.portal-project-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.portal-project-header h4 {
  margin: 0;
}

.portal-project-desc {
  font-size: 0.9rem;
  color: var(--text-muted);
  margin-bottom: 16px;
}

.portal-project-progress {
  margin-bottom: 16px;
}

.progress-label {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  margin-bottom: 4px;
}

.progress-bar-container {
  height: 8px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: var(--primary);
  transition: width 0.3s;
}

.portal-project-dates {
  display: flex;
  gap: 8px;
  font-size: 0.85rem;
  color: var(--text-muted);
}
```

---

## TASK 6: SUPPLIER PORTAL 🏭

### 6.1 Create Supplier Portal Routes

**File:** `backend/app/routes/supplier_portal.py`

```python
"""
Supplier Portal routes
Limited access for suppliers to view their data
"""

from fastapi import APIRouter, HTTPException, Depends
from app.models.store import db
from app.utils.auth import get_current_user

router = APIRouter()


def get_supplier_user(current_user: dict = Depends(get_current_user)):
    """Ensure user is a supplier"""
    if current_user.get("role") not in ["supplier", "admin"]:
        raise HTTPException(status_code=403, detail="Supplier access required")
    return current_user


@router.get("/dashboard")
async def supplier_dashboard(current_user: dict = Depends(get_supplier_user)):
    """Get supplier dashboard data"""
    supplier_email = current_user["email"]
    
    # Get transactions where vendor matches (purchases from this supplier)
    if current_user["role"] == "admin":
        transactions = db.transactions.find_all()
        payments = db.payments.find_all()
    else:
        transactions = [
            t for t in db.transactions.find_all() 
            if t.get("vendor_email") == supplier_email or t.get("vendor_name") == supplier_email
        ]
        payments = [
            p for p in db.payments.find_all() 
            if p.get("vendor_email") == supplier_email
        ]
    
    # Stats
    total_orders = len(transactions)
    total_revenue = sum(t.get("amount", 0) for t in transactions)
    total_paid = sum(p.get("amount", 0) for p in payments if p.get("status") == "paid")
    total_pending = sum(p.get("amount", 0) for p in payments if p.get("status") == "pending")
    
    return {
        "stats": {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "total_paid": total_paid,
            "total_pending": total_pending
        },
        "recent_orders": transactions[:10],
        "pending_payments": [p for p in payments if p.get("status") == "pending"][:5]
    }


@router.get("/orders")
async def supplier_orders(current_user: dict = Depends(get_supplier_user)):
    """Get supplier's orders/transactions"""
    supplier_email = current_user["email"]
    
    if current_user["role"] == "admin":
        transactions = [t for t in db.transactions.find_all() if t.get("type") == "expense"]
    else:
        transactions = [
            t for t in db.transactions.find_all() 
            if (t.get("vendor_email") == supplier_email or t.get("vendor_name") == supplier_email)
            and t.get("type") == "expense"
        ]
    
    return {"orders": transactions}


@router.get("/payments")
async def supplier_payments(current_user: dict = Depends(get_supplier_user)):
    """Get supplier's payments"""
    supplier_email = current_user["email"]
    
    if current_user["role"] == "admin":
        payments = [p for p in db.payments.find_all() if p.get("type") == "payable"]
    else:
        payments = [
            p for p in db.payments.find_all() 
            if p.get("vendor_email") == supplier_email and p.get("type") == "payable"
        ]
    
    return {"payments": payments}


@router.get("/catalog")
async def supplier_catalog(current_user: dict = Depends(get_supplier_user)):
    """Get supplier's product catalog"""
    supplier_email = current_user["email"]
    
    # For demo, return materials that could be from this supplier
    if current_user["role"] == "admin":
        materials = db.materials.find_all()
    else:
        materials = [
            m for m in db.materials.find_all() 
            if m.get("supplier_email") == supplier_email
        ]
    
    return {"products": materials}


@router.get("/profile")
async def supplier_profile(current_user: dict = Depends(get_supplier_user)):
    """Get supplier profile"""
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "name": current_user.get("name", ""),
        "company": current_user.get("company", ""),
        "phone": current_user.get("phone", ""),
        "address": current_user.get("address", "")
    }
```

### 6.2 Register Portal Routes

**Update:** `backend/app/main.py`

```python
from app.routes import client_portal, supplier_portal, reconciliation

app.include_router(client_portal.router, prefix="/api/v1/portal/client", tags=["Client Portal"])
app.include_router(supplier_portal.router, prefix="/api/v1/portal/supplier", tags=["Supplier Portal"])
app.include_router(reconciliation.router, prefix="/api/v1/reconciliation", tags=["Reconciliation"])
```

### 6.3 Create Supplier Dashboard

**File:** `frontend/src/pages/portal/SupplierDashboard.jsx`

```jsx
import { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { Link } from 'react-router-dom';

export default function SupplierDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const res = await api.get('/api/v1/portal/supplier/dashboard');
      setData(res.data);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="text-center p-8">Loading...</div>;

  const { stats, recent_orders, pending_payments } = data || {};

  return (
    <>
      <div className="portal-welcome mb-6">
        <h2>Supplier Portal</h2>
        <p>View your orders, payments, and manage your catalog.</p>
      </div>

      {/* Stats */}
      <div className="stats-grid mb-6">
        <div className="stat-card">
          <div className="stat-icon">📦</div>
          <div className="stat-content">
            <div className="stat-value">{stats?.total_orders || 0}</div>
            <div className="stat-label">Total Orders</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">💰</div>
          <div className="stat-content">
            <div className="stat-value">${stats?.total_revenue?.toLocaleString() || 0}</div>
            <div className="stat-label">Total Revenue</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">✅</div>
          <div className="stat-content">
            <div className="stat-value">${stats?.total_paid?.toLocaleString() || 0}</div>
            <div className="stat-label">Paid</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">⏳</div>
          <div className="stat-content">
            <div className="stat-value">${stats?.total_pending?.toLocaleString() || 0}</div>
            <div className="stat-label">Pending</div>
          </div>
        </div>
      </div>

      <div className="grid-2">
        {/* Recent Orders */}
        <div className="section">
          <h3 className="section-title">Recent Orders</h3>
          {recent_orders?.length === 0 ? (
            <div className="text-muted">No orders yet</div>
          ) : (
            <div className="portal-list">
              {recent_orders?.slice(0, 5).map(order => (
                <div key={order.id} className="portal-item">
                  <div>
                    <div className="portal-item-name">{order.description}</div>
                    <div className="text-muted text-sm">{order.date}</div>
                  </div>
                  <strong>${order.amount?.toLocaleString()}</strong>
                </div>
              ))}
            </div>
          )}
          <Link to="/portal/supplier/orders" className="btn btn-secondary btn-sm mt-4">View All →</Link>
        </div>

        {/* Pending Payments */}
        <div className="section">
          <h3 className="section-title">Pending Payments</h3>
          {pending_payments?.length === 0 ? (
            <div className="text-muted">No pending payments</div>
          ) : (
            <div className="portal-list">
              {pending_payments?.map(payment => (
                <div key={payment.id} className="portal-item">
                  <div>
                    <div className="portal-item-name">${payment.amount?.toLocaleString()}</div>
                    <div className="text-muted text-sm">Due: {payment.due_date}</div>
                  </div>
                  <span className="badge badge-warning">Pending</span>
                </div>
              ))}
            </div>
          )}
          <Link to="/portal/supplier/payments" className="btn btn-secondary btn-sm mt-4">View All →</Link>
        </div>
      </div>
    </>
  );
}
```

---

## TASK 7: ADD ALL ROUTES

### 7.1 Update App.jsx

```jsx
// Lazy imports
const BankReconciliation = lazy(() => import('./pages/BankReconciliation'));
const ClientDashboard = lazy(() => import('./pages/portal/ClientDashboard'));
const ClientProjects = lazy(() => import('./pages/portal/ClientProjects'));
const ClientPayments = lazy(() => import('./pages/portal/ClientPayments'));
const SupplierDashboard = lazy(() => import('./pages/portal/SupplierDashboard'));

// Routes
<Route path="/reconciliation" element={
  <PrivateRoute roles={['admin']}>
    <Layout><BankReconciliation /></Layout>
  </PrivateRoute>
} />

{/* Client Portal */}
<Route path="/portal/dashboard" element={
  <PrivateRoute roles={['client', 'admin']}>
    <Layout><ClientDashboard /></Layout>
  </PrivateRoute>
} />
<Route path="/portal/projects" element={
  <PrivateRoute roles={['client', 'admin']}>
    <Layout><ClientProjects /></Layout>
  </PrivateRoute>
} />
<Route path="/portal/payments" element={
  <PrivateRoute roles={['client', 'admin']}>
    <Layout><ClientPayments /></Layout>
  </PrivateRoute>
} />

{/* Supplier Portal */}
<Route path="/portal/supplier/dashboard" element={
  <PrivateRoute roles={['supplier', 'admin']}>
    <Layout><SupplierDashboard /></Layout>
  </PrivateRoute>
} />
```

### 7.2 Update Layout Navigation

```javascript
// Admin routes
{ path: '/reconciliation', icon: '🏦', label: 'Reconciliation', roles: ['admin'] },

// Client routes (show only for clients)
{ path: '/portal/dashboard', icon: '🏠', label: 'Portal Home', roles: ['client'] },
{ path: '/portal/projects', icon: '📁', label: 'My Projects', roles: ['client'] },
{ path: '/portal/payments', icon: '💳', label: 'My Payments', roles: ['client'] },

// Supplier routes
{ path: '/portal/supplier/dashboard', icon: '🏭', label: 'Supplier Portal', roles: ['supplier'] },
```

---

## COMPLETION CHECKLIST - PART 2

### Bank Reconciliation
- [ ] Reconciliation service
- [ ] Import bank statements (CSV)
- [ ] Auto-match algorithm
- [ ] Manual matching interface
- [ ] Match/Unmatch functionality
- [ ] Complete reconciliation
- [ ] Frontend page

### Client Portal
- [ ] Client dashboard
- [ ] View projects
- [ ] View invoices
- [ ] View payments
- [ ] Scoped data access

### Supplier Portal
- [ ] Supplier dashboard
- [ ] View orders
- [ ] View payments
- [ ] Product catalog
- [ ] Scoped data access

---

**Continue to Part 3 for Scheduled Reports, Multi-Currency, Audit Trail, Data Import, and Team Collaboration**
