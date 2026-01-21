# LogiAccounting Pro - Phase 7 Tasks (Part 1/3)

## ADVANCED AUDIT TRAIL + DATA IMPORT WIZARD

---

## TASK 1: ADVANCED AUDIT TRAIL 📜

### 1.1 Create Audit Service

**File:** `backend/app/services/audit_service.py`

```python
"""
Advanced Audit Trail Service
Complete action logging for compliance
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import hashlib
import json


class AuditService:
    """Immutable audit logging system"""
    
    _instance = None
    _logs: List[dict] = []
    _counter = 0
    
    ACTION_TYPES = [
        "CREATE", "READ", "UPDATE", "DELETE",
        "LOGIN", "LOGOUT", "LOGIN_FAILED",
        "EXPORT", "IMPORT", "BULK_ACTION",
        "APPROVE", "REJECT",
        "SETTINGS_CHANGE", "PASSWORD_CHANGE",
        "API_CALL", "WEBHOOK_TRIGGER"
    ]
    
    ENTITY_TYPES = [
        "user", "material", "transaction", "payment",
        "project", "category", "location", "document",
        "approval", "budget", "recurring", "report",
        "settings", "api_key", "webhook"
    ]
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._logs = []
            cls._counter = 0
        return cls._instance
    
    def log(
        self,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        user_role: Optional[str] = None,
        before: Optional[dict] = None,
        after: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        duration_ms: Optional[int] = None
    ) -> dict:
        """Create an immutable audit log entry"""
        self._counter += 1
        
        # Calculate changes if before/after provided
        changes = None
        if before and after:
            changes = self._calculate_changes(before, after)
        
        # Generate unique ID with hash for integrity
        timestamp = datetime.utcnow().isoformat()
        entry_data = f"{self._counter}{timestamp}{action}{entity_type}{entity_id}{user_id}"
        integrity_hash = hashlib.sha256(entry_data.encode()).hexdigest()[:16]
        
        log_entry = {
            "id": f"AUD-{self._counter:06d}",
            "hash": integrity_hash,
            "timestamp": timestamp,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "user_id": user_id,
            "user_email": user_email,
            "user_role": user_role,
            "changes": changes,
            "before": before,
            "after": after,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "session_id": session_id,
            "metadata": metadata or {},
            "duration_ms": duration_ms
        }
        
        # Append-only (immutable)
        self._logs.append(log_entry)
        
        return log_entry
    
    def _calculate_changes(self, before: dict, after: dict) -> dict:
        """Calculate diff between before and after states"""
        changes = {}
        
        all_keys = set(before.keys()) | set(after.keys())
        
        for key in all_keys:
            old_val = before.get(key)
            new_val = after.get(key)
            
            if old_val != new_val:
                changes[key] = {
                    "before": old_val,
                    "after": new_val
                }
        
        return changes if changes else None
    
    def get_log(self, log_id: str) -> Optional[dict]:
        """Get a specific log entry"""
        for log in self._logs:
            if log["id"] == log_id:
                return log
        return None
    
    def search(
        self,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> dict:
        """Search audit logs with filters"""
        results = self._logs.copy()
        
        # Apply filters
        if action:
            results = [l for l in results if l["action"] == action]
        if entity_type:
            results = [l for l in results if l["entity_type"] == entity_type]
        if entity_id:
            results = [l for l in results if l["entity_id"] == entity_id]
        if user_id:
            results = [l for l in results if l["user_id"] == user_id]
        if user_email:
            results = [l for l in results if l["user_email"] == user_email]
        if ip_address:
            results = [l for l in results if l["ip_address"] == ip_address]
        if date_from:
            results = [l for l in results if l["timestamp"] >= date_from]
        if date_to:
            results = [l for l in results if l["timestamp"] <= date_to]
        
        # Sort by timestamp descending (newest first)
        results = sorted(results, key=lambda x: x["timestamp"], reverse=True)
        
        total = len(results)
        paginated = results[offset:offset + limit]
        
        return {
            "logs": paginated,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
    
    def get_entity_history(self, entity_type: str, entity_id: str) -> List[dict]:
        """Get complete history for an entity"""
        return sorted(
            [l for l in self._logs if l["entity_type"] == entity_type and l["entity_id"] == entity_id],
            key=lambda x: x["timestamp"],
            reverse=True
        )
    
    def get_user_activity(self, user_id: str, days: int = 30) -> List[dict]:
        """Get user activity for last N days"""
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        return sorted(
            [l for l in self._logs if l["user_id"] == user_id and l["timestamp"] >= cutoff],
            key=lambda x: x["timestamp"],
            reverse=True
        )
    
    def get_statistics(self, days: int = 30) -> dict:
        """Get audit statistics"""
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        recent = [l for l in self._logs if l["timestamp"] >= cutoff]
        
        # Count by action
        by_action = {}
        for log in recent:
            action = log["action"]
            by_action[action] = by_action.get(action, 0) + 1
        
        # Count by entity
        by_entity = {}
        for log in recent:
            entity = log["entity_type"]
            by_entity[entity] = by_entity.get(entity, 0) + 1
        
        # Count by user
        by_user = {}
        for log in recent:
            user = log["user_email"] or "system"
            by_user[user] = by_user.get(user, 0) + 1
        
        # Failed logins
        failed_logins = len([l for l in recent if l["action"] == "LOGIN_FAILED"])
        
        # Activity by hour
        by_hour = {str(i).zfill(2): 0 for i in range(24)}
        for log in recent:
            hour = log["timestamp"][11:13]
            by_hour[hour] = by_hour.get(hour, 0) + 1
        
        return {
            "total_logs": len(recent),
            "period_days": days,
            "by_action": by_action,
            "by_entity": by_entity,
            "by_user": dict(sorted(by_user.items(), key=lambda x: x[1], reverse=True)[:10]),
            "failed_logins": failed_logins,
            "by_hour": by_hour
        }
    
    def export(
        self,
        format: str = "json",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Any:
        """Export audit logs for compliance"""
        results = self._logs.copy()
        
        if date_from:
            results = [l for l in results if l["timestamp"] >= date_from]
        if date_to:
            results = [l for l in results if l["timestamp"] <= date_to]
        
        results = sorted(results, key=lambda x: x["timestamp"])
        
        if format == "json":
            return json.dumps(results, indent=2)
        
        if format == "csv":
            if not results:
                return "id,timestamp,action,entity_type,entity_id,user_email,ip_address\n"
            
            lines = ["id,timestamp,action,entity_type,entity_id,user_email,ip_address"]
            for log in results:
                lines.append(
                    f"{log['id']},{log['timestamp']},{log['action']},"
                    f"{log['entity_type']},{log['entity_id'] or ''},"
                    f"{log['user_email'] or ''},{log['ip_address'] or ''}"
                )
            return "\n".join(lines)
        
        return results
    
    def detect_anomalies(self) -> List[dict]:
        """Detect suspicious activity patterns"""
        anomalies = []
        now = datetime.utcnow()
        hour_ago = (now - timedelta(hours=1)).isoformat()
        recent = [l for l in self._logs if l["timestamp"] >= hour_ago]
        
        # Multiple failed logins from same IP
        failed_by_ip = {}
        for log in recent:
            if log["action"] == "LOGIN_FAILED" and log["ip_address"]:
                ip = log["ip_address"]
                failed_by_ip[ip] = failed_by_ip.get(ip, 0) + 1
        
        for ip, count in failed_by_ip.items():
            if count >= 5:
                anomalies.append({
                    "type": "brute_force_attempt",
                    "severity": "high",
                    "description": f"{count} failed logins from IP {ip} in last hour",
                    "ip_address": ip
                })
        
        # Unusual bulk operations
        bulk_by_user = {}
        for log in recent:
            if log["action"] in ["DELETE", "BULK_ACTION"]:
                user = log["user_id"]
                bulk_by_user[user] = bulk_by_user.get(user, 0) + 1
        
        for user, count in bulk_by_user.items():
            if count >= 20:
                anomalies.append({
                    "type": "bulk_deletion",
                    "severity": "medium",
                    "description": f"User performed {count} delete/bulk operations in last hour",
                    "user_id": user
                })
        
        # Off-hours activity
        for log in recent:
            try:
                hour = int(log["timestamp"][11:13])
                if hour < 6 or hour > 22:  # Outside 6am-10pm
                    if log["action"] in ["SETTINGS_CHANGE", "DELETE", "EXPORT"]:
                        anomalies.append({
                            "type": "off_hours_sensitive",
                            "severity": "low",
                            "description": f"Sensitive action at {hour}:00",
                            "user_id": log["user_id"],
                            "action": log["action"]
                        })
            except:
                pass
        
        return anomalies


audit_service = AuditService()


# Helper function for route handlers
def log_action(
    action: str,
    entity_type: str,
    entity_id: str = None,
    before: dict = None,
    after: dict = None,
    request = None,
    current_user: dict = None
):
    """Helper to log actions from routes"""
    return audit_service.log(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=current_user.get("id") if current_user else None,
        user_email=current_user.get("email") if current_user else None,
        user_role=current_user.get("role") if current_user else None,
        before=before,
        after=after,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
```

### 1.2 Create Audit Routes

**File:** `backend/app/routes/audit.py`

```python
"""
Audit Trail routes
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from app.services.audit_service import audit_service
from app.utils.auth import require_roles

router = APIRouter()


@router.get("/actions")
async def get_action_types():
    """Get available action types"""
    return {"actions": audit_service.ACTION_TYPES}


@router.get("/entities")
async def get_entity_types():
    """Get available entity types"""
    return {"entities": audit_service.ENTITY_TYPES}


@router.get("")
async def search_logs(
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    ip_address: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    current_user: dict = Depends(require_roles("admin"))
):
    """Search audit logs"""
    return audit_service.search(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        user_email=user_email,
        ip_address=ip_address,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset
    )


@router.get("/statistics")
async def get_statistics(
    days: int = 30,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get audit statistics"""
    return audit_service.get_statistics(days)


@router.get("/anomalies")
async def get_anomalies(
    current_user: dict = Depends(require_roles("admin"))
):
    """Detect security anomalies"""
    return {"anomalies": audit_service.detect_anomalies()}


@router.get("/entity/{entity_type}/{entity_id}")
async def get_entity_history(
    entity_type: str,
    entity_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get complete history for an entity"""
    return {"history": audit_service.get_entity_history(entity_type, entity_id)}


@router.get("/user/{user_id}")
async def get_user_activity(
    user_id: str,
    days: int = 30,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get user activity"""
    return {"activity": audit_service.get_user_activity(user_id, days)}


@router.get("/export")
async def export_logs(
    format: str = "json",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(require_roles("admin"))
):
    """Export audit logs"""
    data = audit_service.export(format, date_from, date_to)
    
    if format == "csv":
        return {
            "content": data,
            "filename": f"audit_logs_{date_from or 'all'}_{date_to or 'now'}.csv",
            "content_type": "text/csv"
        }
    
    return {"data": data if isinstance(data, list) else None, "content": data if isinstance(data, str) else None}


@router.get("/{log_id}")
async def get_log(
    log_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get a specific log entry"""
    log = audit_service.get_log(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return log
```

### 1.3 Add Audit API to Frontend

**Add to:** `frontend/src/services/api.js`

```javascript
// Audit Trail API
export const auditAPI = {
  getActions: () => api.get('/api/v1/audit/actions'),
  getEntities: () => api.get('/api/v1/audit/entities'),
  search: (params) => api.get('/api/v1/audit', { params }),
  getStatistics: (days = 30) => api.get('/api/v1/audit/statistics', { params: { days } }),
  getAnomalies: () => api.get('/api/v1/audit/anomalies'),
  getEntityHistory: (entityType, entityId) => api.get(`/api/v1/audit/entity/${entityType}/${entityId}`),
  getUserActivity: (userId, days = 30) => api.get(`/api/v1/audit/user/${userId}`, { params: { days } }),
  export: (format, dateFrom, dateTo) => api.get('/api/v1/audit/export', { params: { format, date_from: dateFrom, date_to: dateTo } }),
  get: (logId) => api.get(`/api/v1/audit/${logId}`)
};
```

### 1.4 Create Audit Trail Page

**File:** `frontend/src/pages/AuditTrail.jsx`

```jsx
import { useState, useEffect } from 'react';
import { auditAPI } from '../services/api';

export default function AuditTrail() {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [statistics, setStatistics] = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [actions, setActions] = useState([]);
  const [entities, setEntities] = useState([]);
  const [selectedLog, setSelectedLog] = useState(null);
  
  // Filters
  const [filters, setFilters] = useState({
    action: '',
    entity_type: '',
    user_email: '',
    date_from: '',
    date_to: '',
    limit: 50,
    offset: 0
  });

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    searchLogs();
  }, [filters]);

  const loadInitialData = async () => {
    try {
      const [actionsRes, entitiesRes, statsRes, anomaliesRes] = await Promise.all([
        auditAPI.getActions(),
        auditAPI.getEntities(),
        auditAPI.getStatistics(30),
        auditAPI.getAnomalies()
      ]);
      setActions(actionsRes.data.actions);
      setEntities(entitiesRes.data.entities);
      setStatistics(statsRes.data);
      setAnomalies(anomaliesRes.data.anomalies);
    } catch (err) {
      console.error('Failed to load initial data:', err);
    }
  };

  const searchLogs = async () => {
    setLoading(true);
    try {
      const params = Object.fromEntries(
        Object.entries(filters).filter(([_, v]) => v !== '')
      );
      const res = await auditAPI.search(params);
      setLogs(res.data.logs);
      setTotal(res.data.total);
    } catch (err) {
      console.error('Failed to search logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    try {
      const res = await auditAPI.export(format, filters.date_from, filters.date_to);
      const content = format === 'csv' ? res.data.content : JSON.stringify(res.data.data, null, 2);
      const blob = new Blob([content], { type: format === 'csv' ? 'text/csv' : 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit_logs.${format}`;
      a.click();
    } catch (err) {
      alert('Export failed');
    }
  };

  const getActionIcon = (action) => {
    const icons = {
      CREATE: '➕', READ: '👁️', UPDATE: '✏️', DELETE: '🗑️',
      LOGIN: '🔑', LOGOUT: '🚪', LOGIN_FAILED: '❌',
      EXPORT: '📤', IMPORT: '📥', BULK_ACTION: '📦',
      APPROVE: '✅', REJECT: '❌',
      SETTINGS_CHANGE: '⚙️', PASSWORD_CHANGE: '🔒'
    };
    return icons[action] || '📋';
  };

  const getActionColor = (action) => {
    if (['DELETE', 'LOGIN_FAILED', 'REJECT'].includes(action)) return 'danger';
    if (['CREATE', 'APPROVE', 'LOGIN'].includes(action)) return 'success';
    if (['UPDATE', 'SETTINGS_CHANGE'].includes(action)) return 'warning';
    return 'info';
  };

  const formatTimestamp = (ts) => {
    return new Date(ts).toLocaleString();
  };

  return (
    <>
      <div className="info-banner mb-6">
        📜 Complete audit trail for compliance and security monitoring.
      </div>

      {/* Anomalies Alert */}
      {anomalies.length > 0 && (
        <div className="alert alert-danger mb-6">
          <strong>⚠️ Security Anomalies Detected:</strong>
          <ul className="mt-2">
            {anomalies.slice(0, 3).map((a, i) => (
              <li key={i}>{a.description}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Statistics Cards */}
      {statistics && (
        <div className="stats-grid mb-6">
          <div className="stat-card">
            <div className="stat-icon">📊</div>
            <div className="stat-content">
              <div className="stat-value">{statistics.total_logs.toLocaleString()}</div>
              <div className="stat-label">Total Logs (30d)</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">❌</div>
            <div className="stat-content">
              <div className="stat-value">{statistics.failed_logins}</div>
              <div className="stat-label">Failed Logins</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">👥</div>
            <div className="stat-content">
              <div className="stat-value">{Object.keys(statistics.by_user).length}</div>
              <div className="stat-label">Active Users</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">⚠️</div>
            <div className="stat-content">
              <div className="stat-value">{anomalies.length}</div>
              <div className="stat-label">Anomalies</div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="section mb-6">
        <h3 className="section-title">Filters</h3>
        <div className="filters-grid">
          <div className="form-group">
            <label className="form-label">Action</label>
            <select
              className="form-select"
              value={filters.action}
              onChange={(e) => setFilters({ ...filters, action: e.target.value, offset: 0 })}
            >
              <option value="">All Actions</option>
              {actions.map(a => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Entity Type</label>
            <select
              className="form-select"
              value={filters.entity_type}
              onChange={(e) => setFilters({ ...filters, entity_type: e.target.value, offset: 0 })}
            >
              <option value="">All Entities</option>
              {entities.map(e => (
                <option key={e} value={e}>{e}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">User Email</label>
            <input
              type="text"
              className="form-input"
              value={filters.user_email}
              onChange={(e) => setFilters({ ...filters, user_email: e.target.value, offset: 0 })}
              placeholder="user@example.com"
            />
          </div>
          <div className="form-group">
            <label className="form-label">From Date</label>
            <input
              type="date"
              className="form-input"
              value={filters.date_from}
              onChange={(e) => setFilters({ ...filters, date_from: e.target.value, offset: 0 })}
            />
          </div>
          <div className="form-group">
            <label className="form-label">To Date</label>
            <input
              type="date"
              className="form-input"
              value={filters.date_to}
              onChange={(e) => setFilters({ ...filters, date_to: e.target.value, offset: 0 })}
            />
          </div>
          <div className="form-group">
            <label className="form-label">&nbsp;</label>
            <div className="flex gap-2">
              <button className="btn btn-secondary" onClick={() => handleExport('csv')}>
                📤 CSV
              </button>
              <button className="btn btn-secondary" onClick={() => handleExport('json')}>
                📤 JSON
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Logs Table */}
      <div className="section">
        <div className="flex justify-between items-center mb-4">
          <h3 className="section-title" style={{ margin: 0 }}>
            Audit Logs ({total.toLocaleString()} total)
          </h3>
        </div>

        {loading ? (
          <div className="text-center text-muted">Loading...</div>
        ) : logs.length === 0 ? (
          <div className="text-center text-muted">No logs found</div>
        ) : (
          <>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Action</th>
                    <th>Entity</th>
                    <th>User</th>
                    <th>IP Address</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map(log => (
                    <tr key={log.id}>
                      <td>
                        <div className="text-sm">{formatTimestamp(log.timestamp)}</div>
                        <div className="text-muted text-xs">{log.id}</div>
                      </td>
                      <td>
                        <span className={`badge badge-${getActionColor(log.action)}`}>
                          {getActionIcon(log.action)} {log.action}
                        </span>
                      </td>
                      <td>
                        <div>{log.entity_type}</div>
                        {log.entity_id && (
                          <div className="text-muted text-sm">{log.entity_id}</div>
                        )}
                      </td>
                      <td>
                        <div>{log.user_email || 'System'}</div>
                        <div className="text-muted text-sm">{log.user_role}</div>
                      </td>
                      <td>
                        <code className="text-sm">{log.ip_address || '-'}</code>
                      </td>
                      <td>
                        <button 
                          className="btn btn-sm btn-secondary"
                          onClick={() => setSelectedLog(log)}
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="pagination mt-4">
              <button
                className="btn btn-sm btn-secondary"
                disabled={filters.offset === 0}
                onClick={() => setFilters({ ...filters, offset: Math.max(0, filters.offset - filters.limit) })}
              >
                ← Previous
              </button>
              <span className="px-4">
                Page {Math.floor(filters.offset / filters.limit) + 1} of {Math.ceil(total / filters.limit)}
              </span>
              <button
                className="btn btn-sm btn-secondary"
                disabled={filters.offset + filters.limit >= total}
                onClick={() => setFilters({ ...filters, offset: filters.offset + filters.limit })}
              >
                Next →
              </button>
            </div>
          </>
        )}
      </div>

      {/* Log Detail Modal */}
      {selectedLog && (
        <div className="modal-overlay" onClick={() => setSelectedLog(null)}>
          <div className="modal-content modal-lg" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Audit Log Details</h3>
              <button className="modal-close" onClick={() => setSelectedLog(null)}>×</button>
            </div>
            <div className="modal-body">
              <div className="audit-detail-grid">
                <div className="detail-item">
                  <label>ID</label>
                  <code>{selectedLog.id}</code>
                </div>
                <div className="detail-item">
                  <label>Timestamp</label>
                  <span>{formatTimestamp(selectedLog.timestamp)}</span>
                </div>
                <div className="detail-item">
                  <label>Action</label>
                  <span className={`badge badge-${getActionColor(selectedLog.action)}`}>
                    {selectedLog.action}
                  </span>
                </div>
                <div className="detail-item">
                  <label>Entity</label>
                  <span>{selectedLog.entity_type} / {selectedLog.entity_id || 'N/A'}</span>
                </div>
                <div className="detail-item">
                  <label>User</label>
                  <span>{selectedLog.user_email} ({selectedLog.user_role})</span>
                </div>
                <div className="detail-item">
                  <label>IP Address</label>
                  <code>{selectedLog.ip_address || 'N/A'}</code>
                </div>
                <div className="detail-item">
                  <label>Session</label>
                  <code>{selectedLog.session_id || 'N/A'}</code>
                </div>
                <div className="detail-item">
                  <label>Hash</label>
                  <code>{selectedLog.hash}</code>
                </div>
              </div>

              {selectedLog.changes && (
                <div className="changes-section mt-4">
                  <h4>Changes</h4>
                  <div className="changes-diff">
                    {Object.entries(selectedLog.changes).map(([key, value]) => (
                      <div key={key} className="change-item">
                        <div className="change-field">{key}</div>
                        <div className="change-before">
                          <span className="label">Before:</span>
                          <code>{JSON.stringify(value.before)}</code>
                        </div>
                        <div className="change-after">
                          <span className="label">After:</span>
                          <code>{JSON.stringify(value.after)}</code>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selectedLog.user_agent && (
                <div className="mt-4">
                  <label className="form-label">User Agent</label>
                  <code className="text-sm" style={{ wordBreak: 'break-all' }}>
                    {selectedLog.user_agent}
                  </code>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
```

### 1.5 Add Audit Trail Styles

**Add to:** `frontend/src/index.css`

```css
/* Audit Trail */
.filters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

.audit-detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-item label {
  font-size: 0.85rem;
  color: var(--text-muted);
  font-weight: 500;
}

.changes-section h4 {
  margin: 0 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
}

.changes-diff {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.change-item {
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: 8px;
}

.change-field {
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--primary);
}

.change-before, .change-after {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  margin-top: 4px;
}

.change-before .label {
  color: #ef4444;
  font-size: 0.85rem;
  min-width: 50px;
}

.change-after .label {
  color: #10b981;
  font-size: 0.85rem;
  min-width: 50px;
}

.change-before code, .change-after code {
  font-size: 0.85rem;
  word-break: break-all;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
}

.alert {
  padding: 16px;
  border-radius: 8px;
}

.alert-danger {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

.alert ul {
  margin: 0;
  padding-left: 20px;
}
```

---

## TASK 2: DATA IMPORT WIZARD 📥

### 2.1 Create Import Service

**File:** `backend/app/services/import_service.py`

```python
"""
Data Import Service
CSV/Excel import with validation
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import csv
import io
from app.models.store import db


class ImportService:
    """Handles data import with validation"""
    
    _instance = None
    _imports: Dict[str, dict] = {}
    _templates: Dict[str, dict] = {}
    _counter = 0
    
    ENTITY_CONFIGS = {
        "materials": {
            "collection": "materials",
            "required_fields": ["name"],
            "field_mappings": {
                "name": {"type": "string", "required": True},
                "sku": {"type": "string", "required": False},
                "description": {"type": "string", "required": False},
                "quantity": {"type": "number", "required": False, "default": 0},
                "unit_cost": {"type": "number", "required": False, "default": 0},
                "category_id": {"type": "string", "required": False},
                "location_id": {"type": "string", "required": False},
                "min_stock": {"type": "number", "required": False, "default": 0},
                "max_stock": {"type": "number", "required": False}
            }
        },
        "transactions": {
            "collection": "transactions",
            "required_fields": ["description", "amount", "type"],
            "field_mappings": {
                "description": {"type": "string", "required": True},
                "amount": {"type": "number", "required": True},
                "type": {"type": "enum", "values": ["income", "expense"], "required": True},
                "date": {"type": "date", "required": False},
                "category_id": {"type": "string", "required": False},
                "project_id": {"type": "string", "required": False},
                "invoice_number": {"type": "string", "required": False}
            }
        },
        "payments": {
            "collection": "payments",
            "required_fields": ["amount", "type"],
            "field_mappings": {
                "amount": {"type": "number", "required": True},
                "type": {"type": "enum", "values": ["receivable", "payable"], "required": True},
                "status": {"type": "enum", "values": ["pending", "paid", "overdue"], "default": "pending"},
                "due_date": {"type": "date", "required": False},
                "description": {"type": "string", "required": False},
                "project_id": {"type": "string", "required": False}
            }
        },
        "categories": {
            "collection": "categories",
            "required_fields": ["name"],
            "field_mappings": {
                "name": {"type": "string", "required": True},
                "type": {"type": "enum", "values": ["income", "expense", "inventory"], "required": False},
                "description": {"type": "string", "required": False},
                "color": {"type": "string", "required": False}
            }
        }
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._imports = {}
            cls._templates = {}
            cls._counter = 0
        return cls._instance
    
    def get_entity_config(self, entity: str) -> Optional[dict]:
        """Get configuration for an entity type"""
        return self.ENTITY_CONFIGS.get(entity)
    
    def get_supported_entities(self) -> List[str]:
        """Get list of supported entity types"""
        return list(self.ENTITY_CONFIGS.keys())
    
    def parse_csv(self, content: str, delimiter: str = ",") -> Tuple[List[str], List[dict]]:
        """Parse CSV content"""
        reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
        headers = reader.fieldnames or []
        rows = list(reader)
        return headers, rows
    
    def suggest_mappings(self, headers: List[str], entity: str) -> Dict[str, str]:
        """Suggest column mappings based on header names"""
        config = self.ENTITY_CONFIGS.get(entity, {})
        field_mappings = config.get("field_mappings", {})
        
        suggestions = {}
        
        for header in headers:
            header_lower = header.lower().strip()
            
            # Direct match
            if header_lower in field_mappings:
                suggestions[header] = header_lower
                continue
            
            # Common variations
            variations = {
                "product": "name",
                "product_name": "name",
                "item": "name",
                "item_name": "name",
                "material": "name",
                "price": "unit_cost",
                "cost": "unit_cost",
                "unit_price": "unit_cost",
                "qty": "quantity",
                "stock": "quantity",
                "on_hand": "quantity",
                "category": "category_id",
                "location": "location_id",
                "desc": "description",
                "notes": "description",
                "min": "min_stock",
                "minimum": "min_stock",
                "max": "max_stock",
                "maximum": "max_stock",
                "invoice": "invoice_number",
                "inv_no": "invoice_number",
                "due": "due_date",
                "payment_date": "due_date"
            }
            
            if header_lower in variations and variations[header_lower] in field_mappings:
                suggestions[header] = variations[header_lower]
        
        return suggestions
    
    def validate_row(self, row: dict, mapping: dict, entity: str, row_index: int) -> Tuple[dict, List[dict]]:
        """Validate and transform a single row"""
        config = self.ENTITY_CONFIGS.get(entity, {})
        field_mappings = config.get("field_mappings", {})
        required_fields = config.get("required_fields", [])
        
        errors = []
        validated = {}
        
        for source_col, target_field in mapping.items():
            if target_field not in field_mappings:
                continue
            
            field_config = field_mappings[target_field]
            value = row.get(source_col, "").strip()
            
            # Handle empty values
            if not value:
                if field_config.get("required"):
                    errors.append({
                        "row": row_index,
                        "field": target_field,
                        "error": f"Required field '{target_field}' is empty"
                    })
                elif "default" in field_config:
                    validated[target_field] = field_config["default"]
                continue
            
            # Type validation
            field_type = field_config.get("type")
            
            if field_type == "number":
                try:
                    validated[target_field] = float(value.replace(",", ""))
                except ValueError:
                    errors.append({
                        "row": row_index,
                        "field": target_field,
                        "error": f"Invalid number: {value}"
                    })
            
            elif field_type == "date":
                # Try common date formats
                parsed = None
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]:
                    try:
                        parsed = datetime.strptime(value, fmt).strftime("%Y-%m-%d")
                        break
                    except ValueError:
                        continue
                
                if parsed:
                    validated[target_field] = parsed
                else:
                    errors.append({
                        "row": row_index,
                        "field": target_field,
                        "error": f"Invalid date format: {value}"
                    })
            
            elif field_type == "enum":
                allowed = field_config.get("values", [])
                if value.lower() in [v.lower() for v in allowed]:
                    validated[target_field] = value.lower()
                else:
                    errors.append({
                        "row": row_index,
                        "field": target_field,
                        "error": f"Invalid value: {value}. Allowed: {', '.join(allowed)}"
                    })
            
            else:  # string
                validated[target_field] = value
        
        # Check required fields
        for req in required_fields:
            if req not in validated:
                errors.append({
                    "row": row_index,
                    "field": req,
                    "error": f"Required field '{req}' not mapped or empty"
                })
        
        return validated, errors
    
    def create_import(
        self,
        entity: str,
        headers: List[str],
        rows: List[dict],
        mapping: Dict[str, str],
        created_by: str
    ) -> dict:
        """Create an import job with validation"""
        self._counter += 1
        import_id = f"IMP-{self._counter:04d}"
        
        # Validate all rows
        valid_rows = []
        all_errors = []
        
        for i, row in enumerate(rows):
            validated, errors = self.validate_row(row, mapping, entity, i + 1)
            if errors:
                all_errors.extend(errors)
            else:
                valid_rows.append(validated)
        
        import_job = {
            "id": import_id,
            "entity": entity,
            "headers": headers,
            "mapping": mapping,
            "total_rows": len(rows),
            "valid_rows": len(valid_rows),
            "error_rows": len(all_errors),
            "errors": all_errors[:100],  # Limit errors returned
            "preview": valid_rows[:10],
            "status": "pending",
            "created_by": created_by,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Store validated data for execution
        import_job["_valid_data"] = valid_rows
        
        self._imports[import_id] = import_job
        
        return {
            k: v for k, v in import_job.items() if not k.startswith("_")
        }
    
    def execute_import(self, import_id: str) -> dict:
        """Execute the import and create records"""
        import_job = self._imports.get(import_id)
        if not import_job:
            return {"error": "Import not found"}
        
        if import_job["status"] != "pending":
            return {"error": f"Import already {import_job['status']}"}
        
        entity = import_job["entity"]
        config = self.ENTITY_CONFIGS.get(entity)
        collection_name = config["collection"]
        
        # Get the collection
        collection = getattr(db, collection_name, None)
        if not collection:
            return {"error": f"Collection {collection_name} not found"}
        
        # Insert records
        created = 0
        valid_data = import_job.get("_valid_data", [])
        created_ids = []
        
        for data in valid_data:
            try:
                record = collection.create(data)
                created += 1
                created_ids.append(record.get("id"))
            except Exception as e:
                pass  # Continue on individual failures
        
        import_job["status"] = "completed"
        import_job["completed_at"] = datetime.utcnow().isoformat()
        import_job["created_count"] = created
        import_job["created_ids"] = created_ids
        
        return {
            "success": True,
            "import_id": import_id,
            "created_count": created,
            "total_rows": import_job["total_rows"]
        }
    
    def rollback_import(self, import_id: str) -> dict:
        """Rollback an executed import"""
        import_job = self._imports.get(import_id)
        if not import_job:
            return {"error": "Import not found"}
        
        if import_job["status"] != "completed":
            return {"error": "Can only rollback completed imports"}
        
        entity = import_job["entity"]
        config = self.ENTITY_CONFIGS.get(entity)
        collection_name = config["collection"]
        collection = getattr(db, collection_name, None)
        
        if not collection:
            return {"error": f"Collection {collection_name} not found"}
        
        # Delete created records
        deleted = 0
        for record_id in import_job.get("created_ids", []):
            try:
                if collection.delete(record_id):
                    deleted += 1
            except:
                pass
        
        import_job["status"] = "rolled_back"
        import_job["rolled_back_at"] = datetime.utcnow().isoformat()
        import_job["deleted_count"] = deleted
        
        return {
            "success": True,
            "deleted_count": deleted
        }
    
    def get_import(self, import_id: str) -> Optional[dict]:
        """Get import job details"""
        job = self._imports.get(import_id)
        if job:
            return {k: v for k, v in job.items() if not k.startswith("_")}
        return None
    
    def list_imports(self, limit: int = 20) -> List[dict]:
        """List recent imports"""
        imports = list(self._imports.values())
        imports = sorted(imports, key=lambda x: x["created_at"], reverse=True)[:limit]
        return [{k: v for k, v in i.items() if not k.startswith("_")} for i in imports]


import_service = ImportService()
```

### 2.2 Create Import Routes

**File:** `backend/app/routes/data_import.py`

```python
"""
Data Import Wizard routes
"""

from typing import Dict, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.import_service import import_service
from app.utils.auth import require_roles

router = APIRouter()


class ParseRequest(BaseModel):
    content: str
    delimiter: str = ","


class CreateImportRequest(BaseModel):
    entity: str
    headers: List[str]
    rows: List[dict]
    mapping: Dict[str, str]


@router.get("/entities")
async def get_supported_entities():
    """Get supported entity types for import"""
    return {"entities": import_service.get_supported_entities()}


@router.get("/entities/{entity}/config")
async def get_entity_config(entity: str):
    """Get import configuration for an entity"""
    config = import_service.get_entity_config(entity)
    if not config:
        raise HTTPException(status_code=404, detail="Entity not supported")
    return config


@router.post("/parse")
async def parse_csv(
    request: ParseRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Parse CSV content"""
    try:
        headers, rows = import_service.parse_csv(request.content, request.delimiter)
        return {
            "headers": headers,
            "rows": rows[:100],  # Limit preview
            "total_rows": len(rows)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {str(e)}")


@router.post("/suggest-mapping")
async def suggest_mapping(
    entity: str,
    headers: List[str],
    current_user: dict = Depends(require_roles("admin"))
):
    """Get suggested column mappings"""
    return {"suggestions": import_service.suggest_mappings(headers, entity)}


@router.post("")
async def create_import(
    request: CreateImportRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Create and validate an import job"""
    return import_service.create_import(
        entity=request.entity,
        headers=request.headers,
        rows=request.rows,
        mapping=request.mapping,
        created_by=current_user["id"]
    )


@router.get("")
async def list_imports(
    limit: int = 20,
    current_user: dict = Depends(require_roles("admin"))
):
    """List recent imports"""
    return {"imports": import_service.list_imports(limit)}


@router.get("/{import_id}")
async def get_import(
    import_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get import details"""
    import_job = import_service.get_import(import_id)
    if not import_job:
        raise HTTPException(status_code=404, detail="Import not found")
    return import_job


@router.post("/{import_id}/execute")
async def execute_import(
    import_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Execute the import"""
    result = import_service.execute_import(import_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{import_id}/rollback")
async def rollback_import(
    import_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Rollback a completed import"""
    result = import_service.rollback_import(import_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
```

### 2.3 Add Import API to Frontend

**Add to:** `frontend/src/services/api.js`

```javascript
// Data Import API
export const importAPI = {
  getEntities: () => api.get('/api/v1/import/entities'),
  getEntityConfig: (entity) => api.get(`/api/v1/import/entities/${entity}/config`),
  parse: (content, delimiter = ',') => api.post('/api/v1/import/parse', { content, delimiter }),
  suggestMapping: (entity, headers) => api.post('/api/v1/import/suggest-mapping', headers, { params: { entity } }),
  create: (data) => api.post('/api/v1/import', data),
  list: (limit = 20) => api.get('/api/v1/import', { params: { limit } }),
  get: (importId) => api.get(`/api/v1/import/${importId}`),
  execute: (importId) => api.post(`/api/v1/import/${importId}/execute`),
  rollback: (importId) => api.post(`/api/v1/import/${importId}/rollback`)
};
```

### 2.4 Create Data Import Page

**File:** `frontend/src/pages/DataImport.jsx`

```jsx
import { useState, useEffect, useRef } from 'react';
import { importAPI } from '../services/api';

const STEPS = ['upload', 'entity', 'mapping', 'preview', 'complete'];

export default function DataImport() {
  const [step, setStep] = useState(0);
  const [entities, setEntities] = useState([]);
  const [entityConfig, setEntityConfig] = useState(null);
  const [fileContent, setFileContent] = useState('');
  const [headers, setHeaders] = useState([]);
  const [rows, setRows] = useState([]);
  const [totalRows, setTotalRows] = useState(0);
  const [selectedEntity, setSelectedEntity] = useState('');
  const [mapping, setMapping] = useState({});
  const [importJob, setImportJob] = useState(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const fileInputRef = useRef(null);

  useEffect(() => {
    loadEntities();
    loadHistory();
  }, []);

  const loadEntities = async () => {
    try {
      const res = await importAPI.getEntities();
      setEntities(res.data.entities);
    } catch (err) {
      console.error('Failed to load entities:', err);
    }
  };

  const loadHistory = async () => {
    try {
      const res = await importAPI.list(10);
      setHistory(res.data.imports);
    } catch (err) {
      console.error('Failed to load history:', err);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (event) => {
      const content = event.target.result;
      setFileContent(content);
      
      try {
        setLoading(true);
        const res = await importAPI.parse(content);
        setHeaders(res.data.headers);
        setRows(res.data.rows);
        setTotalRows(res.data.total_rows);
        setStep(1);
      } catch (err) {
        alert('Failed to parse file: ' + (err.response?.data?.detail || err.message));
      } finally {
        setLoading(false);
      }
    };
    reader.readAsText(file);
  };

  const handleEntitySelect = async (entity) => {
    setSelectedEntity(entity);
    
    try {
      setLoading(true);
      const [configRes, suggestRes] = await Promise.all([
        importAPI.getEntityConfig(entity),
        importAPI.suggestMapping(entity, headers)
      ]);
      setEntityConfig(configRes.data);
      setMapping(suggestRes.data.suggestions);
      setStep(2);
    } catch (err) {
      alert('Failed to load entity config');
    } finally {
      setLoading(false);
    }
  };

  const handleMappingChange = (header, field) => {
    setMapping(prev => {
      if (!field) {
        const { [header]: _, ...rest } = prev;
        return rest;
      }
      return { ...prev, [header]: field };
    });
  };

  const handleValidate = async () => {
    try {
      setLoading(true);
      const res = await importAPI.create({
        entity: selectedEntity,
        headers,
        rows,
        mapping
      });
      setImportJob(res.data);
      setStep(3);
    } catch (err) {
      alert('Validation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async () => {
    if (!importJob) return;
    
    try {
      setLoading(true);
      const res = await importAPI.execute(importJob.id);
      alert(`Success! Created ${res.data.created_count} records.`);
      setStep(4);
      loadHistory();
    } catch (err) {
      alert('Import failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleRollback = async (importId) => {
    if (!confirm('Rollback this import? This will delete all created records.')) return;
    
    try {
      const res = await importAPI.rollback(importId);
      alert(`Rolled back: ${res.data.deleted_count} records deleted`);
      loadHistory();
    } catch (err) {
      alert('Rollback failed');
    }
  };

  const resetWizard = () => {
    setStep(0);
    setFileContent('');
    setHeaders([]);
    setRows([]);
    setSelectedEntity('');
    setMapping({});
    setImportJob(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <>
      <div className="info-banner mb-6">
        📥 Import data from CSV or Excel files with intelligent mapping.
      </div>

      {/* Progress Steps */}
      <div className="import-steps mb-6">
        {STEPS.map((s, i) => (
          <div key={s} className={`import-step ${i <= step ? 'active' : ''} ${i === step ? 'current' : ''}`}>
            <div className="step-number">{i + 1}</div>
            <div className="step-label">{s.charAt(0).toUpperCase() + s.slice(1)}</div>
          </div>
        ))}
      </div>

      {/* Step Content */}
      <div className="section">
        {/* Step 1: Upload */}
        {step === 0 && (
          <div className="import-upload">
            <h3>Upload File</h3>
            <p className="text-muted mb-4">Select a CSV file to import</p>
            <div className="upload-zone" onClick={() => fileInputRef.current?.click()}>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.txt"
                onChange={handleFileUpload}
                style={{ display: 'none' }}
              />
              <div className="upload-icon">📁</div>
              <div className="upload-text">
                Click or drag file here
              </div>
              <div className="upload-hint">Supports CSV files</div>
            </div>
          </div>
        )}

        {/* Step 2: Select Entity */}
        {step === 1 && (
          <div className="import-entity">
            <h3>Select Data Type</h3>
            <p className="text-muted mb-4">
              Found {totalRows} rows with {headers.length} columns
            </p>
            <div className="entity-grid">
              {entities.map(entity => (
                <div
                  key={entity}
                  className={`entity-card ${selectedEntity === entity ? 'selected' : ''}`}
                  onClick={() => handleEntitySelect(entity)}
                >
                  <div className="entity-icon">
                    {entity === 'materials' && '📦'}
                    {entity === 'transactions' && '💰'}
                    {entity === 'payments' && '💳'}
                    {entity === 'categories' && '🏷️'}
                  </div>
                  <div className="entity-name">{entity}</div>
                </div>
              ))}
            </div>
            <button className="btn btn-secondary mt-4" onClick={() => setStep(0)}>
              ← Back
            </button>
          </div>
        )}

        {/* Step 3: Mapping */}
        {step === 2 && entityConfig && (
          <div className="import-mapping">
            <h3>Map Columns</h3>
            <p className="text-muted mb-4">
              Match your file columns to {selectedEntity} fields
            </p>
            <div className="mapping-table">
              <div className="mapping-header">
                <div>File Column</div>
                <div></div>
                <div>System Field</div>
              </div>
              {headers.map(header => (
                <div key={header} className="mapping-row">
                  <div className="mapping-source">
                    <code>{header}</code>
                    <div className="sample-data">
                      {rows[0]?.[header]?.substring(0, 30) || '-'}
                    </div>
                  </div>
                  <div className="mapping-arrow">→</div>
                  <div className="mapping-target">
                    <select
                      className="form-select"
                      value={mapping[header] || ''}
                      onChange={(e) => handleMappingChange(header, e.target.value)}
                    >
                      <option value="">-- Skip --</option>
                      {Object.entries(entityConfig.field_mappings).map(([field, config]) => (
                        <option key={field} value={field}>
                          {field} {config.required ? '*' : ''}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              ))}
            </div>
            <div className="flex gap-2 mt-4">
              <button className="btn btn-secondary" onClick={() => setStep(1)}>
                ← Back
              </button>
              <button className="btn btn-primary" onClick={handleValidate} disabled={loading}>
                {loading ? 'Validating...' : 'Validate & Preview'}
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Preview */}
        {step === 3 && importJob && (
          <div className="import-preview">
            <h3>Validation Results</h3>
            
            <div className="validation-summary">
              <div className="valid-count">
                ✅ {importJob.valid_rows} valid rows
              </div>
              <div className="error-count">
                ❌ {importJob.error_rows} errors
              </div>
            </div>

            {importJob.errors?.length > 0 && (
              <div className="errors-section mt-4">
                <h4>Errors (first 10)</h4>
                <div className="errors-list">
                  {importJob.errors.slice(0, 10).map((err, i) => (
                    <div key={i} className="error-item">
                      Row {err.row}: <strong>{err.field}</strong> - {err.error}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {importJob.preview?.length > 0 && (
              <div className="preview-section mt-4">
                <h4>Preview (first 5 rows)</h4>
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        {Object.keys(importJob.preview[0]).map(key => (
                          <th key={key}>{key}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {importJob.preview.slice(0, 5).map((row, i) => (
                        <tr key={i}>
                          {Object.values(row).map((val, j) => (
                            <td key={j}>{String(val)}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            <div className="flex gap-2 mt-4">
              <button className="btn btn-secondary" onClick={() => setStep(2)}>
                ← Back to Mapping
              </button>
              <button 
                className="btn btn-primary" 
                onClick={handleExecute} 
                disabled={loading || importJob.valid_rows === 0}
              >
                {loading ? 'Importing...' : `Import ${importJob.valid_rows} Records`}
              </button>
            </div>
          </div>
        )}

        {/* Step 5: Complete */}
        {step === 4 && (
          <div className="import-complete text-center">
            <div className="complete-icon">🎉</div>
            <h3>Import Complete!</h3>
            <p className="text-muted">Your data has been imported successfully.</p>
            <button className="btn btn-primary mt-4" onClick={resetWizard}>
              Start New Import
            </button>
          </div>
        )}
      </div>

      {/* Import History */}
      <div className="section mt-6">
        <h3 className="section-title">Recent Imports</h3>
        {history.length === 0 ? (
          <div className="text-muted">No imports yet</div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Entity</th>
                  <th>Rows</th>
                  <th>Status</th>
                  <th>Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {history.map(imp => (
                  <tr key={imp.id}>
                    <td><code>{imp.id}</code></td>
                    <td>{imp.entity}</td>
                    <td>{imp.created_count || imp.valid_rows} / {imp.total_rows}</td>
                    <td>
                      <span className={`badge badge-${imp.status === 'completed' ? 'success' : imp.status === 'rolled_back' ? 'danger' : 'warning'}`}>
                        {imp.status}
                      </span>
                    </td>
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
        )}
      </div>
    </>
  );
}
```

### 2.5 Add Import Styles

**Add to:** `frontend/src/index.css`

```css
/* Data Import Wizard */
.import-steps {
  display: flex;
  justify-content: center;
  gap: 32px;
}

.import-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  opacity: 0.5;
}

.import-step.active {
  opacity: 1;
}

.import-step.current .step-number {
  background: var(--primary);
  color: white;
}

.step-number {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.step-label {
  font-size: 0.85rem;
  text-transform: capitalize;
}

.upload-zone {
  border: 2px dashed var(--border-color);
  border-radius: 12px;
  padding: 48px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-zone:hover {
  border-color: var(--primary);
  background: rgba(102, 126, 234, 0.05);
}

.upload-icon {
  font-size: 3rem;
  margin-bottom: 16px;
}

.upload-text {
  font-size: 1.1rem;
  font-weight: 500;
}

.upload-hint {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-top: 8px;
}

.entity-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 16px;
}

.entity-card {
  padding: 24px;
  border: 2px solid var(--border-color);
  border-radius: 12px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.entity-card:hover, .entity-card.selected {
  border-color: var(--primary);
}

.entity-card.selected {
  background: rgba(102, 126, 234, 0.1);
}

.entity-icon {
  font-size: 2rem;
  margin-bottom: 8px;
}

.entity-name {
  font-weight: 500;
  text-transform: capitalize;
}

.mapping-table {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mapping-header, .mapping-row {
  display: grid;
  grid-template-columns: 1fr 40px 1fr;
  gap: 16px;
  align-items: center;
}

.mapping-header {
  font-weight: 600;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
}

.mapping-row {
  padding: 8px 0;
}

.mapping-source code {
  display: block;
  font-size: 0.9rem;
}

.sample-data {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-top: 4px;
}

.mapping-arrow {
  text-align: center;
  color: var(--text-muted);
}

.validation-summary {
  display: flex;
  gap: 24px;
  padding: 16px;
  background: var(--bg-tertiary);
  border-radius: 8px;
}

.valid-count {
  color: #10b981;
  font-weight: 600;
}

.error-count {
  color: #ef4444;
  font-weight: 600;
}

.errors-list {
  max-height: 200px;
  overflow-y: auto;
}

.error-item {
  padding: 8px 12px;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 4px;
  margin-bottom: 4px;
  font-size: 0.9rem;
}

.import-complete {
  padding: 48px;
}

.complete-icon {
  font-size: 4rem;
  margin-bottom: 16px;
}
```

---

## TASK 3: REGISTER ROUTES

### 3.1 Update Backend main.py

```python
from app.routes import audit, data_import

app.include_router(audit.router, prefix="/api/v1/audit", tags=["Audit"])
app.include_router(data_import.router, prefix="/api/v1/import", tags=["Import"])
```

### 3.2 Update Frontend App.jsx

```jsx
// Lazy imports
const AuditTrail = lazy(() => import('./pages/AuditTrail'));
const DataImport = lazy(() => import('./pages/DataImport'));

// Routes
<Route path="/audit" element={
  <PrivateRoute roles={['admin']}>
    <Layout><AuditTrail /></Layout>
  </PrivateRoute>
} />
<Route path="/import" element={
  <PrivateRoute roles={['admin']}>
    <Layout><DataImport /></Layout>
  </PrivateRoute>
} />
```

### 3.3 Update Layout Navigation

```javascript
{ path: '/audit', icon: '📜', label: 'Audit Trail', roles: ['admin'] },
{ path: '/import', icon: '📥', label: 'Data Import', roles: ['admin'] },
```

---

## COMPLETION CHECKLIST - PART 1

### Advanced Audit Trail
- [ ] Audit service with immutable logging
- [ ] Before/After diff calculation
- [ ] IP/User Agent tracking
- [ ] Search and filters
- [ ] Statistics and analytics
- [ ] Anomaly detection
- [ ] Export (CSV/JSON)
- [ ] Frontend page

### Data Import Wizard
- [ ] CSV parsing
- [ ] Entity configuration
- [ ] Smart column mapping suggestions
- [ ] Validation with error details
- [ ] Preview before import
- [ ] Execute import
- [ ] Rollback capability
- [ ] Import history

---

**Continue to Part 2 for Team Collaboration, Tax Management, and Custom Fields**
