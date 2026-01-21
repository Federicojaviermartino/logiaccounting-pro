# LogiAccounting Pro - Phase 3 Tasks (Part 2/3)

## ENTERPRISE FEATURES: Activity Log + Bulk Operations + Email Notifications

---

## TASK 5: ACTIVITY LOG SYSTEM

### 5.1 Create Activity Logger Utility

**File:** `backend/app/utils/activity_logger.py`

```python
"""
Activity Logger - Tracks all user actions for audit trail
"""

from datetime import datetime
from typing import Optional, Dict, Any
from functools import wraps


class ActivityLogger:
    """Centralized activity logging service"""
    
    _instance = None
    _activities = []
    _counter = 0
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def log(
        self,
        user_id: str,
        user_email: str,
        user_role: str,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        entity_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict:
        """Log an activity"""
        self._counter += 1
        activity = {
            "id": f"ACT-{self._counter:06d}",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "user_email": user_email,
            "user_role": user_role,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "entity_name": entity_name,
            "details": details or {},
            "ip_address": ip_address,
            "user_agent": user_agent
        }
        self._activities.insert(0, activity)  # Most recent first
        
        # Keep last 10000 activities in memory
        if len(self._activities) > 10000:
            self._activities = self._activities[:10000]
        
        return activity
    
    def get_activities(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple:
        """Get filtered activities with pagination"""
        filtered = self._activities.copy()
        
        if user_id:
            filtered = [a for a in filtered if a["user_id"] == user_id]
        
        if action:
            filtered = [a for a in filtered if a["action"] == action]
        
        if entity_type:
            filtered = [a for a in filtered if a["entity_type"] == entity_type]
        
        if date_from:
            filtered = [a for a in filtered if a["timestamp"] >= date_from]
        
        if date_to:
            filtered = [a for a in filtered if a["timestamp"] <= date_to]
        
        total = len(filtered)
        paginated = filtered[offset:offset + limit]
        
        return paginated, total
    
    def get_stats(self, days: int = 30) -> Dict:
        """Get activity statistics"""
        from datetime import timedelta
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        recent = [a for a in self._activities if a["timestamp"] >= cutoff]
        
        # Count by action
        by_action = {}
        for a in recent:
            by_action[a["action"]] = by_action.get(a["action"], 0) + 1
        
        # Count by entity
        by_entity = {}
        for a in recent:
            by_entity[a["entity_type"]] = by_entity.get(a["entity_type"], 0) + 1
        
        # Count by user
        by_user = {}
        for a in recent:
            key = a["user_email"]
            by_user[key] = by_user.get(key, 0) + 1
        
        # Top 5 active users
        top_users = sorted(by_user.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "period_days": days,
            "total_activities": len(recent),
            "by_action": by_action,
            "by_entity": by_entity,
            "top_users": [{"email": u[0], "count": u[1]} for u in top_users],
            "daily_average": round(len(recent) / days, 1) if days > 0 else 0
        }
    
    def clear(self):
        """Clear all activities (for testing)"""
        self._activities = []
        self._counter = 0


# Global instance
activity_logger = ActivityLogger()


def log_activity(action: str, entity_type: str):
    """Decorator to automatically log endpoint activities"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Execute the function first
            result = await func(*args, **kwargs)
            
            # Try to log the activity
            try:
                current_user = kwargs.get("current_user")
                if current_user:
                    # Extract entity info from result if possible
                    entity_id = None
                    entity_name = None
                    
                    if isinstance(result, dict):
                        for key in ["material", "transaction", "payment", "project", "user"]:
                            if key in result:
                                entity_id = result[key].get("id")
                                entity_name = result[key].get("name") or result[key].get("reference")
                                break
                    
                    activity_logger.log(
                        user_id=current_user["id"],
                        user_email=current_user["email"],
                        user_role=current_user["role"],
                        action=action,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        entity_name=entity_name
                    )
            except Exception as e:
                print(f"Activity logging failed: {e}")
            
            return result
        return wrapper
    return decorator
```

### 5.2 Create Activity Routes

**File:** `backend/app/routes/activity.py`

```python
"""
Activity Log routes
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from app.utils.auth import require_roles
from app.utils.activity_logger import activity_logger
import csv
import io

router = APIRouter()


@router.get("")
async def get_activities(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(require_roles("admin"))
):
    """Get activity log with filters (admin only)"""
    activities, total = activity_logger.get_activities(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset
    )
    
    return {
        "activities": activities,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }


@router.get("/stats")
async def get_activity_stats(
    days: int = Query(default=30, le=365),
    current_user: dict = Depends(require_roles("admin"))
):
    """Get activity statistics (admin only)"""
    return activity_logger.get_stats(days)


@router.get("/actions")
async def get_available_actions(
    current_user: dict = Depends(require_roles("admin"))
):
    """Get list of available action types"""
    return {
        "actions": [
            {"code": "LOGIN", "label": "User Login"},
            {"code": "LOGOUT", "label": "User Logout"},
            {"code": "CREATE", "label": "Create"},
            {"code": "UPDATE", "label": "Update"},
            {"code": "DELETE", "label": "Delete"},
            {"code": "EXPORT", "label": "Export Data"},
            {"code": "IMPORT", "label": "Import Data"},
            {"code": "STATUS_CHANGE", "label": "Status Change"},
            {"code": "AI_OCR", "label": "AI: OCR Process"},
            {"code": "AI_PREDICT", "label": "AI: Prediction"},
            {"code": "AI_ANOMALY", "label": "AI: Anomaly Scan"},
            {"code": "AI_ASSISTANT", "label": "AI: Assistant Query"}
        ],
        "entities": [
            {"code": "user", "label": "Users"},
            {"code": "material", "label": "Materials"},
            {"code": "project", "label": "Projects"},
            {"code": "transaction", "label": "Transactions"},
            {"code": "payment", "label": "Payments"},
            {"code": "movement", "label": "Movements"},
            {"code": "report", "label": "Reports"},
            {"code": "settings", "label": "Settings"}
        ]
    }


@router.get("/export")
async def export_activities(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(require_roles("admin"))
):
    """Export activity log to CSV (admin only)"""
    activities, _ = activity_logger.get_activities(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        date_from=date_from,
        date_to=date_to,
        limit=10000,
        offset=0
    )
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "Timestamp", "User Email", "User Role", "Action", 
        "Entity Type", "Entity ID", "Entity Name", "Details"
    ])
    
    # Data
    for a in activities:
        writer.writerow([
            a["timestamp"],
            a["user_email"],
            a["user_role"],
            a["action"],
            a["entity_type"],
            a["entity_id"] or "",
            a["entity_name"] or "",
            str(a["details"])
        ])
    
    output.seek(0)
    
    # Log this export
    activity_logger.log(
        user_id=current_user["id"],
        user_email=current_user["email"],
        user_role=current_user["role"],
        action="EXPORT",
        entity_type="activity_log",
        details={"format": "csv", "record_count": len(activities)}
    )
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=activity_log.csv"}
    )
```

### 5.3 Register Activity Routes

**Update:** `backend/app/main.py`

**Add import:**
```python
from app.routes import activity
```

**Add router:**
```python
app.include_router(activity.router, prefix="/api/v1/activity", tags=["Activity"])
```

### 5.4 Add Activity Logging to Auth Routes

**Update:** `backend/app/routes/auth.py`

**Add import:**
```python
from app.utils.activity_logger import activity_logger
```

**In login endpoint, after successful login:**
```python
# Log login activity
activity_logger.log(
    user_id=user["id"],
    user_email=user["email"],
    user_role=user["role"],
    action="LOGIN",
    entity_type="user",
    entity_id=user["id"],
    entity_name=f"{user['first_name']} {user['last_name']}"
)
```

### 5.5 Add Activity API to Frontend

**Add to:** `frontend/src/services/api.js`

```javascript
// Activity Log API
export const activityAPI = {
  getActivities: (params) => api.get('/api/v1/activity', { params }),
  getStats: (days = 30) => api.get('/api/v1/activity/stats', { params: { days } }),
  getAvailableActions: () => api.get('/api/v1/activity/actions'),
  exportCSV: (params) => api.get('/api/v1/activity/export', { 
    params, 
    responseType: 'blob' 
  })
};
```

### 5.6 Create ActivityLog Page

**File:** `frontend/src/pages/ActivityLog.jsx`

```jsx
import { useState, useEffect } from 'react';
import { activityAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

export default function ActivityLog() {
  const { user } = useAuth();
  const [activities, setActivities] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [options, setOptions] = useState({ actions: [], entities: [] });
  const [filters, setFilters] = useState({
    action: '',
    entity_type: '',
    date_from: '',
    date_to: ''
  });
  const [pagination, setPagination] = useState({
    limit: 50,
    offset: 0,
    total: 0,
    hasMore: false
  });

  useEffect(() => {
    loadOptions();
    loadStats();
  }, []);

  useEffect(() => {
    loadActivities();
  }, [filters, pagination.offset]);

  const loadOptions = async () => {
    try {
      const res = await activityAPI.getAvailableActions();
      setOptions(res.data);
    } catch (error) {
      console.error('Failed to load options:', error);
    }
  };

  const loadStats = async () => {
    try {
      const res = await activityAPI.getStats(30);
      setStats(res.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const loadActivities = async () => {
    setLoading(true);
    try {
      const params = {
        ...filters,
        limit: pagination.limit,
        offset: pagination.offset
      };
      // Remove empty filters
      Object.keys(params).forEach(key => {
        if (!params[key]) delete params[key];
      });
      
      const res = await activityAPI.getActivities(params);
      setActivities(res.data.activities);
      setPagination(prev => ({
        ...prev,
        total: res.data.total,
        hasMore: res.data.has_more
      }));
    } catch (error) {
      console.error('Failed to load activities:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, offset: 0 }));
  };

  const handleExport = async () => {
    try {
      const res = await activityAPI.exportCSV(filters);
      const blob = new Blob([res.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `activity_log_${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      alert('Export failed');
    }
  };

  const getActionBadgeColor = (action) => {
    const colors = {
      LOGIN: 'primary',
      LOGOUT: 'gray',
      CREATE: 'success',
      UPDATE: 'warning',
      DELETE: 'danger',
      EXPORT: 'primary',
      IMPORT: 'primary',
      STATUS_CHANGE: 'warning'
    };
    return colors[action] || 'gray';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <>
      {/* Stats Overview */}
      {stats && (
        <div className="stats-grid mb-6">
          <div className="stat-card">
            <span className="stat-icon">📊</span>
            <div className="stat-content">
              <div className="stat-label">Total (30 days)</div>
              <div className="stat-value">{stats.total_activities}</div>
            </div>
          </div>
          <div className="stat-card">
            <span className="stat-icon">📈</span>
            <div className="stat-content">
              <div className="stat-label">Daily Average</div>
              <div className="stat-value">{stats.daily_average}</div>
            </div>
          </div>
          <div className="stat-card">
            <span className="stat-icon">✏️</span>
            <div className="stat-content">
              <div className="stat-label">Updates</div>
              <div className="stat-value">{stats.by_action?.UPDATE || 0}</div>
            </div>
          </div>
          <div className="stat-card">
            <span className="stat-icon">🔐</span>
            <div className="stat-content">
              <div className="stat-label">Logins</div>
              <div className="stat-value">{stats.by_action?.LOGIN || 0}</div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="section mb-6">
        <div className="toolbar">
          <div className="flex gap-3 flex-wrap">
            <select
              className="form-select"
              value={filters.action}
              onChange={(e) => handleFilterChange('action', e.target.value)}
            >
              <option value="">All Actions</option>
              {options.actions.map(a => (
                <option key={a.code} value={a.code}>{a.label}</option>
              ))}
            </select>
            
            <select
              className="form-select"
              value={filters.entity_type}
              onChange={(e) => handleFilterChange('entity_type', e.target.value)}
            >
              <option value="">All Entities</option>
              {options.entities.map(e => (
                <option key={e.code} value={e.code}>{e.label}</option>
              ))}
            </select>
            
            <input
              type="date"
              className="form-input"
              value={filters.date_from}
              onChange={(e) => handleFilterChange('date_from', e.target.value)}
              placeholder="From date"
            />
            
            <input
              type="date"
              className="form-input"
              value={filters.date_to}
              onChange={(e) => handleFilterChange('date_to', e.target.value)}
              placeholder="To date"
            />
          </div>
          
          <button className="btn btn-secondary" onClick={handleExport}>
            📥 Export CSV
          </button>
        </div>
      </div>

      {/* Activity Table */}
      <div className="section">
        <h3 className="section-title">Activity Log</h3>
        
        {loading ? (
          <div className="text-center text-muted">Loading...</div>
        ) : activities.length === 0 ? (
          <div className="text-center text-muted">No activities found</div>
        ) : (
          <>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>User</th>
                    <th>Action</th>
                    <th>Entity</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {activities.map(activity => (
                    <tr key={activity.id}>
                      <td className="text-muted" style={{ whiteSpace: 'nowrap' }}>
                        {formatDate(activity.timestamp)}
                      </td>
                      <td>
                        <div>{activity.user_email}</div>
                        <div className="text-muted text-sm">{activity.user_role}</div>
                      </td>
                      <td>
                        <span className={`badge badge-${getActionBadgeColor(activity.action)}`}>
                          {activity.action}
                        </span>
                      </td>
                      <td>
                        <div>{activity.entity_type}</div>
                        {activity.entity_name && (
                          <div className="text-muted text-sm">{activity.entity_name}</div>
                        )}
                      </td>
                      <td className="text-muted text-sm">
                        {Object.keys(activity.details).length > 0 ? (
                          <code>{JSON.stringify(activity.details)}</code>
                        ) : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex justify-between items-center mt-4">
              <div className="text-muted">
                Showing {pagination.offset + 1} - {Math.min(pagination.offset + pagination.limit, pagination.total)} of {pagination.total}
              </div>
              <div className="flex gap-2">
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => setPagination(prev => ({ ...prev, offset: Math.max(0, prev.offset - prev.limit) }))}
                  disabled={pagination.offset === 0}
                >
                  ← Previous
                </button>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => setPagination(prev => ({ ...prev, offset: prev.offset + prev.limit }))}
                  disabled={!pagination.hasMore}
                >
                  Next →
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </>
  );
}
```

### 5.7 Add ActivityLog Route

**Update:** `frontend/src/App.jsx`

**Add import:**
```jsx
import ActivityLog from './pages/ActivityLog';
```

**Add route:**
```jsx
<Route path="/activity-log" element={
  <PrivateRoute roles={['admin']}>
    <Layout><ActivityLog /></Layout>
  </PrivateRoute>
} />
```

### 5.8 Update Navigation

**Update navItems in:** `frontend/src/components/Layout.jsx`

Add to Administration section:
```javascript
{ path: '/activity-log', icon: '📋', label: 'Activity Log', roles: ['admin'] },
```

Add to pageTitles:
```javascript
'/activity-log': 'Activity Log'
```

---

## TASK 6: BULK OPERATIONS

### 6.1 Create Bulk Routes

**File:** `backend/app/routes/bulk.py`

```python
"""
Bulk operations routes - Import, Export, Mass Update, Mass Delete
"""

import csv
import io
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.models.store import db
from app.utils.auth import require_roles
from app.utils.activity_logger import activity_logger

router = APIRouter()


class BulkDeleteRequest(BaseModel):
    ids: List[str]


class BulkUpdateRequest(BaseModel):
    ids: List[str]
    updates: dict


# Supported entities and their configurations
ENTITY_CONFIG = {
    "materials": {
        "store": lambda: db.materials,
        "fields": ["reference", "name", "description", "category_id", "unit", "quantity", "min_stock", "unit_cost", "state"],
        "required": ["name", "quantity"],
        "searchable": ["name", "reference"]
    },
    "transactions": {
        "store": lambda: db.transactions,
        "fields": ["type", "amount", "description", "category_id", "date", "vendor_name", "invoice_number"],
        "required": ["type", "amount"],
        "searchable": ["description", "vendor_name"]
    },
    "payments": {
        "store": lambda: db.payments,
        "fields": ["type", "amount", "due_date", "description", "reference", "status"],
        "required": ["type", "amount", "due_date"],
        "searchable": ["description", "reference"]
    },
    "projects": {
        "store": lambda: db.projects,
        "fields": ["name", "client", "description", "budget", "status", "start_date", "end_date"],
        "required": ["name"],
        "searchable": ["name", "client"]
    }
}


@router.get("/template/{entity}")
async def get_import_template(
    entity: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Download CSV template for import"""
    if entity not in ENTITY_CONFIG:
        raise HTTPException(status_code=400, detail=f"Unsupported entity: {entity}")
    
    config = ENTITY_CONFIG[entity]
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(config["fields"])
    
    # Write example row
    example_row = []
    for field in config["fields"]:
        if field == "type":
            example_row.append("expense")
        elif field == "amount" or field == "budget" or field == "unit_cost":
            example_row.append("1000.00")
        elif field == "quantity" or field == "min_stock":
            example_row.append("100")
        elif "date" in field:
            example_row.append("2024-01-15")
        elif field == "status":
            example_row.append("active")
        elif field == "state":
            example_row.append("available")
        else:
            example_row.append(f"Example {field}")
    writer.writerow(example_row)
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={entity}_template.csv"}
    )


@router.post("/import/{entity}")
async def import_data(
    entity: str,
    file: UploadFile = File(...),
    skip_errors: bool = Query(default=False),
    current_user: dict = Depends(require_roles("admin"))
):
    """Import data from CSV file"""
    if entity not in ENTITY_CONFIG:
        raise HTTPException(status_code=400, detail=f"Unsupported entity: {entity}")
    
    config = ENTITY_CONFIG[entity]
    store = config["store"]()
    
    # Read file
    content = await file.read()
    try:
        text = content.decode('utf-8')
    except UnicodeDecodeError:
        text = content.decode('latin-1')
    
    reader = csv.DictReader(io.StringIO(text))
    
    results = {
        "total_rows": 0,
        "imported": 0,
        "skipped": 0,
        "errors": [],
        "imported_ids": []
    }
    
    for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
        results["total_rows"] += 1
        
        try:
            # Validate required fields
            for field in config["required"]:
                if not row.get(field):
                    raise ValueError(f"Missing required field: {field}")
            
            # Clean and convert data
            clean_row = {}
            for field in config["fields"]:
                value = row.get(field, "").strip()
                if value:
                    # Convert numeric fields
                    if field in ["amount", "budget", "unit_cost", "quantity", "min_stock"]:
                        try:
                            value = float(value)
                        except ValueError:
                            raise ValueError(f"Invalid number in field: {field}")
                    clean_row[field] = value
            
            # Create record
            clean_row["created_by"] = current_user["id"]
            record = store.create(clean_row)
            results["imported"] += 1
            results["imported_ids"].append(record["id"])
            
        except Exception as e:
            if skip_errors:
                results["skipped"] += 1
                results["errors"].append({
                    "row": row_num,
                    "error": str(e),
                    "data": dict(row)
                })
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Error at row {row_num}: {str(e)}"
                )
    
    # Log activity
    activity_logger.log(
        user_id=current_user["id"],
        user_email=current_user["email"],
        user_role=current_user["role"],
        action="IMPORT",
        entity_type=entity,
        details={
            "total_rows": results["total_rows"],
            "imported": results["imported"],
            "skipped": results["skipped"]
        }
    )
    
    return results


@router.post("/export/{entity}")
async def export_data(
    entity: str,
    ids: Optional[List[str]] = None,
    format: str = Query(default="csv"),
    current_user: dict = Depends(require_roles("admin"))
):
    """Export data to CSV or JSON"""
    if entity not in ENTITY_CONFIG:
        raise HTTPException(status_code=400, detail=f"Unsupported entity: {entity}")
    
    config = ENTITY_CONFIG[entity]
    store = config["store"]()
    
    # Get data
    if ids:
        data = [store.find_by_id(id) for id in ids if store.find_by_id(id)]
    else:
        data = store.find_all()
    
    # Log activity
    activity_logger.log(
        user_id=current_user["id"],
        user_email=current_user["email"],
        user_role=current_user["role"],
        action="EXPORT",
        entity_type=entity,
        details={"format": format, "record_count": len(data)}
    )
    
    if format == "json":
        return StreamingResponse(
            iter([json.dumps(data, indent=2)]),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={entity}_export.json"}
        )
    
    # CSV format
    output = io.StringIO()
    if data:
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={entity}_export.csv"}
    )


@router.post("/delete/{entity}")
async def bulk_delete(
    entity: str,
    request: BulkDeleteRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Bulk delete records"""
    if entity not in ENTITY_CONFIG:
        raise HTTPException(status_code=400, detail=f"Unsupported entity: {entity}")
    
    if entity in ["payments", "projects"]:
        raise HTTPException(status_code=403, detail=f"Bulk delete not allowed for {entity}")
    
    store = ENTITY_CONFIG[entity]["store"]()
    
    deleted = 0
    failed = []
    
    for id in request.ids:
        if store.delete(id):
            deleted += 1
        else:
            failed.append(id)
    
    # Log activity
    activity_logger.log(
        user_id=current_user["id"],
        user_email=current_user["email"],
        user_role=current_user["role"],
        action="DELETE",
        entity_type=entity,
        details={"deleted_count": deleted, "failed_count": len(failed)}
    )
    
    return {
        "deleted": deleted,
        "failed": len(failed),
        "failed_ids": failed
    }


@router.post("/update/{entity}")
async def bulk_update(
    entity: str,
    request: BulkUpdateRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Bulk update records"""
    if entity not in ENTITY_CONFIG:
        raise HTTPException(status_code=400, detail=f"Unsupported entity: {entity}")
    
    store = ENTITY_CONFIG[entity]["store"]()
    
    updated = 0
    failed = []
    
    for id in request.ids:
        if store.update(id, request.updates):
            updated += 1
        else:
            failed.append(id)
    
    # Log activity
    activity_logger.log(
        user_id=current_user["id"],
        user_email=current_user["email"],
        user_role=current_user["role"],
        action="UPDATE",
        entity_type=entity,
        details={
            "updated_count": updated,
            "failed_count": len(failed),
            "fields_updated": list(request.updates.keys())
        }
    )
    
    return {
        "updated": updated,
        "failed": len(failed),
        "failed_ids": failed
    }
```

### 6.2 Register Bulk Routes

**Update:** `backend/app/main.py`

**Add import:**
```python
from app.routes import bulk
```

**Add router:**
```python
app.include_router(bulk.router, prefix="/api/v1/bulk", tags=["Bulk Operations"])
```

### 6.3 Add Bulk API to Frontend

**Add to:** `frontend/src/services/api.js`

```javascript
// Bulk Operations API
export const bulkAPI = {
  getTemplate: (entity) => api.get(`/api/v1/bulk/template/${entity}`, { responseType: 'blob' }),
  importData: (entity, file, skipErrors = false) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/api/v1/bulk/import/${entity}?skip_errors=${skipErrors}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  exportData: (entity, ids = null, format = 'csv') => {
    const params = { format };
    if (ids) params.ids = ids;
    return api.post(`/api/v1/bulk/export/${entity}`, ids ? { ids } : null, { 
      params, 
      responseType: 'blob' 
    });
  },
  bulkDelete: (entity, ids) => api.post(`/api/v1/bulk/delete/${entity}`, { ids }),
  bulkUpdate: (entity, ids, updates) => api.post(`/api/v1/bulk/update/${entity}`, { ids, updates })
};
```

### 6.4 Create BulkOperations Page

**File:** `frontend/src/pages/BulkOperations.jsx`

```jsx
import { useState, useRef } from 'react';
import { bulkAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

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
      alert('Failed to download template');
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
      alert('Export failed');
    }
  };

  return (
    <>
      <div className="info-banner mb-6">
        📦 Import, export, and manage data in bulk. Download templates, upload CSV files, and export data in various formats.
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
            📥 Import
          </button>
          <button
            className={`btn ${activeTab === 'export' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('export')}
          >
            📤 Export
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
                📄 Download Template
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
              {importing ? 'Importing...' : '🚀 Start Import'}
            </button>

            {/* Import Result */}
            {importResult && (
              <div className={`mt-6 p-4 rounded-lg ${importResult.error ? 'bg-danger-light' : 'bg-success-light'}`}
                   style={{ 
                     background: importResult.error ? '#fef2f2' : '#f0fdf4',
                     border: `1px solid ${importResult.error ? '#fecaca' : '#bbf7d0'}`
                   }}>
                {importResult.error ? (
                  <div className="text-danger">❌ {importResult.message}</div>
                ) : (
                  <>
                    <div className="font-bold mb-2">✅ Import Complete</div>
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
                📄 Export CSV
              </button>
              <button className="btn btn-secondary" onClick={() => handleExport('json')}>
                📋 Export JSON
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
```

### 6.5 Add BulkOperations Route and Navigation

**Update:** `frontend/src/App.jsx`

**Add import:**
```jsx
import BulkOperations from './pages/BulkOperations';
```

**Add route:**
```jsx
<Route path="/bulk-operations" element={
  <PrivateRoute roles={['admin']}>
    <Layout><BulkOperations /></Layout>
  </PrivateRoute>
} />
```

**Update Layout.jsx navItems:**
```javascript
{ path: '/bulk-operations', icon: '📦', label: 'Bulk Operations', roles: ['admin'] },
```

**Update pageTitles:**
```javascript
'/bulk-operations': 'Bulk Operations'
```

---

## TASK 7: EMAIL NOTIFICATIONS (SIMULATED)

### 7.1 Create Email Service

**File:** `backend/app/services/email_service.py`

```python
"""
Email Notification Service (Simulated)
In production, integrate with SendGrid, AWS SES, or SMTP
"""

from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict


@dataclass
class EmailLog:
    id: str
    to: str
    subject: str
    template: str
    data: dict
    status: str  # sent, failed, pending
    sent_at: str
    error: Optional[str] = None


class EmailService:
    """Simulated email service for demo purposes"""
    
    _instance = None
    _logs: List[EmailLog] = []
    _counter = 0
    
    TEMPLATES = {
        "payment_reminder": {
            "subject": "Payment Reminder: {reference}",
            "body": """
Hi {user_name},

This is a reminder that payment {reference} for ${amount:.2f} is due on {due_date}.

Please ensure timely payment to avoid late fees.

Best regards,
LogiAccounting Pro
            """
        },
        "payment_overdue": {
            "subject": "OVERDUE: Payment {reference}",
            "body": """
Hi {user_name},

Payment {reference} for ${amount:.2f} was due on {due_date} and is now overdue.

Please process this payment immediately.

Best regards,
LogiAccounting Pro
            """
        },
        "low_stock_alert": {
            "subject": "Low Stock Alert: {material_name}",
            "body": """
Hi {user_name},

Material "{material_name}" (Ref: {reference}) is running low.

Current quantity: {quantity}
Minimum stock: {min_stock}

Please reorder soon.

Best regards,
LogiAccounting Pro
            """
        },
        "anomaly_detected": {
            "subject": "Anomaly Detected: {anomaly_type}",
            "body": """
Hi {user_name},

Our system has detected an anomaly that requires your attention.

Type: {anomaly_type}
Severity: {severity}
Description: {description}

Please review this in the AI Dashboard.

Best regards,
LogiAccounting Pro
            """
        },
        "welcome": {
            "subject": "Welcome to LogiAccounting Pro",
            "body": """
Hi {user_name},

Welcome to LogiAccounting Pro! Your account has been created.

Email: {email}
Role: {role}

You can login at: {login_url}

Best regards,
LogiAccounting Pro Team
            """
        }
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._logs = []
            cls._counter = 0
        return cls._instance
    
    def send(
        self,
        to: str,
        template: str,
        data: Dict,
        subject_override: Optional[str] = None
    ) -> EmailLog:
        """Send an email (simulated - logs to memory)"""
        self._counter += 1
        
        if template not in self.TEMPLATES:
            raise ValueError(f"Unknown template: {template}")
        
        tmpl = self.TEMPLATES[template]
        
        try:
            subject = subject_override or tmpl["subject"].format(**data)
            body = tmpl["body"].format(**data)
            
            log = EmailLog(
                id=f"EMAIL-{self._counter:06d}",
                to=to,
                subject=subject,
                template=template,
                data=data,
                status="sent",
                sent_at=datetime.utcnow().isoformat()
            )
            
            # In production: Actually send email here
            # For demo: Just log it
            print(f"[EMAIL] To: {to}, Subject: {subject}")
            
        except Exception as e:
            log = EmailLog(
                id=f"EMAIL-{self._counter:06d}",
                to=to,
                subject=f"[{template}]",
                template=template,
                data=data,
                status="failed",
                sent_at=datetime.utcnow().isoformat(),
                error=str(e)
            )
        
        self._logs.insert(0, log)
        
        # Keep last 1000 logs
        if len(self._logs) > 1000:
            self._logs = self._logs[:1000]
        
        return log
    
    def get_logs(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        template: Optional[str] = None
    ) -> tuple:
        """Get email logs with optional filters"""
        filtered = self._logs.copy()
        
        if status:
            filtered = [l for l in filtered if l.status == status]
        
        if template:
            filtered = [l for l in filtered if l.template == template]
        
        total = len(filtered)
        paginated = filtered[offset:offset + limit]
        
        return [asdict(l) for l in paginated], total
    
    def get_templates(self) -> Dict:
        """Get available email templates"""
        return {
            name: {
                "subject": tmpl["subject"],
                "preview": tmpl["body"][:200] + "..."
            }
            for name, tmpl in self.TEMPLATES.items()
        }


# Global instance
email_service = EmailService()
```

### 7.2 Create Email Routes

**File:** `backend/app/routes/email.py`

```python
"""
Email notification routes
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from app.services.email_service import email_service
from app.utils.auth import require_roles

router = APIRouter()


class TestEmailRequest(BaseModel):
    to: str
    template: str
    data: dict = {}


@router.get("/logs")
async def get_email_logs(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
    template: Optional[str] = None,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get email logs (admin only)"""
    logs, total = email_service.get_logs(
        limit=limit,
        offset=offset,
        status=status,
        template=template
    )
    
    return {
        "logs": logs,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/templates")
async def get_email_templates(
    current_user: dict = Depends(require_roles("admin"))
):
    """Get available email templates (admin only)"""
    return {"templates": email_service.get_templates()}


@router.post("/test")
async def send_test_email(
    request: TestEmailRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Send a test email (admin only)"""
    # Add default data
    data = {
        "user_name": current_user["first_name"],
        "login_url": "https://logiaccounting-pro.onrender.com/login",
        **request.data
    }
    
    log = email_service.send(
        to=request.to,
        template=request.template,
        data=data
    )
    
    return {
        "success": log.status == "sent",
        "log": {
            "id": log.id,
            "to": log.to,
            "subject": log.subject,
            "status": log.status,
            "sent_at": log.sent_at,
            "error": log.error
        }
    }
```

### 7.3 Register Email Routes

**Update:** `backend/app/main.py`

**Add import:**
```python
from app.routes import email
```

**Add router:**
```python
app.include_router(email.router, prefix="/api/v1/email", tags=["Email"])
```

### 7.4 Add Email API to Frontend

**Add to:** `frontend/src/services/api.js`

```javascript
// Email API
export const emailAPI = {
  getLogs: (params) => api.get('/api/v1/email/logs', { params }),
  getTemplates: () => api.get('/api/v1/email/templates'),
  sendTest: (data) => api.post('/api/v1/email/test', data)
};
```

---

## TASK 8: BUILD AND TEST PART 2

```bash
# Run backend tests
cd backend
pytest -v

# Start development servers
cd backend && uvicorn app.main:app --reload --port 5000
cd frontend && npm run dev

# Test:
# 1. Activity Log - Navigate to /activity-log
# 2. Bulk Operations - Navigate to /bulk-operations
# 3. Download template, fill it, import
# 4. Export data in CSV/JSON

# Build and deploy
cd frontend && npm run build
git add .
git commit -m "feat: Phase 3.2 - Activity Log, Bulk Operations, Email Service"
git push origin main
```

---

## COMPLETION CHECKLIST - PART 2

### Activity Log
- [ ] Activity logger utility created
- [ ] Activity routes created
- [ ] Logging on login/auth events
- [ ] ActivityLog page created
- [ ] Filters working (action, entity, date)
- [ ] Export to CSV working
- [ ] Statistics displayed

### Bulk Operations
- [ ] Bulk routes created (import/export/delete/update)
- [ ] BulkOperations page created
- [ ] Template download working
- [ ] CSV import with validation
- [ ] Export to CSV/JSON working
- [ ] Error handling and reporting

### Email Notifications
- [ ] Email service created (simulated)
- [ ] Email templates defined
- [ ] Email routes created
- [ ] Logs viewable in admin

---

**Continue to Part 3 for i18n, PWA, and Performance Optimization**
