# LogiAccounting Pro - Phase 5 Tasks (Part 2/3)

## RECURRING TRANSACTIONS + BUDGET MANAGEMENT + DOCUMENT MANAGEMENT

---

## TASK 4: RECURRING TRANSACTIONS 🔄

### 4.1 Create Recurring Service

**File:** `backend/app/services/recurring_service.py`

```python
"""
Recurring Transactions Service
Automate periodic transactions and payments
"""

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Dict, List, Optional
from app.models.store import db


class RecurringService:
    """Manages recurring transaction templates"""
    
    _instance = None
    _templates: Dict[str, dict] = {}
    _counter = 0
    
    FREQUENCIES = {
        "daily": {"days": 1},
        "weekly": {"weeks": 1},
        "biweekly": {"weeks": 2},
        "monthly": {"months": 1},
        "quarterly": {"months": 3},
        "yearly": {"years": 1}
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._templates = {}
            cls._counter = 0
        return cls._instance
    
    def create_template(
        self,
        name: str,
        entity_type: str,  # transaction or payment
        template_data: dict,
        frequency: str,
        start_date: str,
        end_date: Optional[str] = None,
        day_of_month: Optional[int] = None,
        day_of_week: Optional[int] = None,
        auto_create: bool = False,
        created_by: str = None
    ) -> dict:
        """Create a recurring template"""
        self._counter += 1
        template_id = f"REC-{self._counter:04d}"
        
        # Calculate next occurrence
        next_occurrence = self._calculate_next_occurrence(
            start_date, frequency, day_of_month, day_of_week
        )
        
        template = {
            "id": template_id,
            "name": name,
            "entity_type": entity_type,
            "template_data": template_data,
            "frequency": frequency,
            "start_date": start_date,
            "end_date": end_date,
            "day_of_month": day_of_month,
            "day_of_week": day_of_week,
            "next_occurrence": next_occurrence,
            "last_generated": None,
            "auto_create": auto_create,
            "active": True,
            "created_by": created_by,
            "created_at": datetime.utcnow().isoformat(),
            "generation_count": 0
        }
        
        self._templates[template_id] = template
        return template
    
    def _calculate_next_occurrence(
        self,
        from_date: str,
        frequency: str,
        day_of_month: Optional[int] = None,
        day_of_week: Optional[int] = None
    ) -> str:
        """Calculate next occurrence date"""
        base_date = datetime.fromisoformat(from_date.replace('Z', '+00:00')).date() \
                    if 'T' in from_date else datetime.strptime(from_date, '%Y-%m-%d').date()
        today = datetime.utcnow().date()
        
        if base_date > today:
            return base_date.isoformat()
        
        # Calculate based on frequency
        freq_delta = self.FREQUENCIES.get(frequency, {"days": 1})
        
        next_date = base_date
        while next_date <= today:
            if "days" in freq_delta:
                next_date += timedelta(days=freq_delta["days"])
            elif "weeks" in freq_delta:
                next_date += timedelta(weeks=freq_delta["weeks"])
            elif "months" in freq_delta:
                next_date += relativedelta(months=freq_delta["months"])
            elif "years" in freq_delta:
                next_date += relativedelta(years=freq_delta["years"])
        
        # Adjust for specific day of month
        if day_of_month and frequency in ["monthly", "quarterly", "yearly"]:
            try:
                next_date = next_date.replace(day=min(day_of_month, 28))
            except ValueError:
                pass
        
        # Adjust for specific day of week
        if day_of_week is not None and frequency == "weekly":
            days_ahead = day_of_week - next_date.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_date += timedelta(days=days_ahead)
        
        return next_date.isoformat()
    
    def update_template(self, template_id: str, updates: dict) -> Optional[dict]:
        """Update a recurring template"""
        if template_id not in self._templates:
            return None
        
        template = self._templates[template_id]
        
        for key, value in updates.items():
            if key in template and key not in ["id", "created_at", "created_by"]:
                template[key] = value
        
        # Recalculate next occurrence if frequency changed
        if "frequency" in updates or "start_date" in updates:
            template["next_occurrence"] = self._calculate_next_occurrence(
                template["start_date"],
                template["frequency"],
                template.get("day_of_month"),
                template.get("day_of_week")
            )
        
        return template
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a recurring template"""
        if template_id in self._templates:
            del self._templates[template_id]
            return True
        return False
    
    def toggle_active(self, template_id: str) -> Optional[dict]:
        """Toggle template active status"""
        if template_id not in self._templates:
            return None
        
        template = self._templates[template_id]
        template["active"] = not template["active"]
        return template
    
    def get_template(self, template_id: str) -> Optional[dict]:
        """Get a specific template"""
        return self._templates.get(template_id)
    
    def list_templates(self, user_id: Optional[str] = None, active_only: bool = False) -> List[dict]:
        """List all templates"""
        templates = list(self._templates.values())
        
        if user_id:
            templates = [t for t in templates if t["created_by"] == user_id]
        
        if active_only:
            templates = [t for t in templates if t["active"]]
        
        return sorted(templates, key=lambda t: t["next_occurrence"])
    
    def get_due_templates(self) -> List[dict]:
        """Get templates due for generation"""
        today = datetime.utcnow().date().isoformat()
        return [
            t for t in self._templates.values()
            if t["active"] and t["next_occurrence"] <= today
            and (not t["end_date"] or t["end_date"] >= today)
        ]
    
    def generate_from_template(self, template_id: str) -> Optional[dict]:
        """Generate entity from template"""
        template = self._templates.get(template_id)
        if not template:
            return None
        
        entity_type = template["entity_type"]
        data = template["template_data"].copy()
        
        # Set current date
        data["date"] = datetime.utcnow().date().isoformat()
        data["created_at"] = datetime.utcnow().isoformat()
        data["recurring_template_id"] = template_id
        
        # Create entity
        if entity_type == "transaction":
            created = db.transactions.create(data)
        elif entity_type == "payment":
            created = db.payments.create(data)
        else:
            return None
        
        # Update template
        template["last_generated"] = datetime.utcnow().isoformat()
        template["generation_count"] += 1
        template["next_occurrence"] = self._calculate_next_occurrence(
            template["next_occurrence"],
            template["frequency"],
            template.get("day_of_month"),
            template.get("day_of_week")
        )
        
        return created
    
    def preview_occurrences(self, template_id: str, count: int = 5) -> List[str]:
        """Preview next N occurrences"""
        template = self._templates.get(template_id)
        if not template:
            return []
        
        occurrences = []
        current = template["next_occurrence"]
        
        for _ in range(count):
            occurrences.append(current)
            current = self._calculate_next_occurrence(
                current,
                template["frequency"],
                template.get("day_of_month"),
                template.get("day_of_week")
            )
            
            # Stop if past end date
            if template["end_date"] and current > template["end_date"]:
                break
        
        return occurrences


recurring_service = RecurringService()
```

### 4.2 Create Recurring Routes

**File:** `backend/app/routes/recurring.py`

```python
"""
Recurring Transactions routes
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.recurring_service import recurring_service
from app.utils.auth import get_current_user, require_roles

router = APIRouter()


class CreateTemplateRequest(BaseModel):
    name: str
    entity_type: str
    template_data: dict
    frequency: str
    start_date: str
    end_date: Optional[str] = None
    day_of_month: Optional[int] = None
    day_of_week: Optional[int] = None
    auto_create: bool = False


class UpdateTemplateRequest(BaseModel):
    name: Optional[str] = None
    template_data: Optional[dict] = None
    frequency: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    day_of_month: Optional[int] = None
    day_of_week: Optional[int] = None
    auto_create: Optional[bool] = None


@router.get("/frequencies")
async def get_frequencies():
    """Get available frequencies"""
    return {
        "frequencies": [
            {"value": "daily", "label": "Daily"},
            {"value": "weekly", "label": "Weekly"},
            {"value": "biweekly", "label": "Bi-weekly"},
            {"value": "monthly", "label": "Monthly"},
            {"value": "quarterly", "label": "Quarterly"},
            {"value": "yearly", "label": "Yearly"}
        ]
    }


@router.get("")
async def list_templates(
    active_only: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """List recurring templates"""
    return {"templates": recurring_service.list_templates(active_only=active_only)}


@router.post("")
async def create_template(
    request: CreateTemplateRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Create a recurring template"""
    if request.frequency not in recurring_service.FREQUENCIES:
        raise HTTPException(status_code=400, detail="Invalid frequency")
    
    return recurring_service.create_template(
        name=request.name,
        entity_type=request.entity_type,
        template_data=request.template_data,
        frequency=request.frequency,
        start_date=request.start_date,
        end_date=request.end_date,
        day_of_month=request.day_of_month,
        day_of_week=request.day_of_week,
        auto_create=request.auto_create,
        created_by=current_user["id"]
    )


@router.get("/{template_id}")
async def get_template(
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific template"""
    template = recurring_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.put("/{template_id}")
async def update_template(
    template_id: str,
    request: UpdateTemplateRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update a template"""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    template = recurring_service.update_template(template_id, updates)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Delete a template"""
    if recurring_service.delete_template(template_id):
        return {"message": "Template deleted"}
    raise HTTPException(status_code=404, detail="Template not found")


@router.post("/{template_id}/toggle")
async def toggle_template(
    template_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Toggle template active status"""
    template = recurring_service.toggle_active(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.post("/{template_id}/generate")
async def generate_now(
    template_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Manually generate from template"""
    result = recurring_service.generate_from_template(template_id)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to generate")
    return {"generated": result}


@router.get("/{template_id}/preview")
async def preview_occurrences(
    template_id: str,
    count: int = 5,
    current_user: dict = Depends(get_current_user)
):
    """Preview next occurrences"""
    occurrences = recurring_service.preview_occurrences(template_id, count)
    return {"occurrences": occurrences}


@router.get("/due/list")
async def get_due(current_user: dict = Depends(require_roles("admin"))):
    """Get templates due for generation"""
    return {"templates": recurring_service.get_due_templates()}
```

### 4.3 Register Routes

**Update:** `backend/app/main.py`

```python
from app.routes import recurring

app.include_router(recurring.router, prefix="/api/v1/recurring", tags=["Recurring"])
```

### 4.4 Add Recurring API to Frontend

**Add to:** `frontend/src/services/api.js`

```javascript
// Recurring API
export const recurringAPI = {
  getFrequencies: () => api.get('/api/v1/recurring/frequencies'),
  list: (activeOnly = false) => api.get('/api/v1/recurring', { params: { active_only: activeOnly } }),
  get: (id) => api.get(`/api/v1/recurring/${id}`),
  create: (data) => api.post('/api/v1/recurring', data),
  update: (id, data) => api.put(`/api/v1/recurring/${id}`, data),
  delete: (id) => api.delete(`/api/v1/recurring/${id}`),
  toggle: (id) => api.post(`/api/v1/recurring/${id}/toggle`),
  generate: (id) => api.post(`/api/v1/recurring/${id}/generate`),
  preview: (id, count = 5) => api.get(`/api/v1/recurring/${id}/preview`, { params: { count } }),
  getDue: () => api.get('/api/v1/recurring/due/list')
};
```

### 4.5 Create Recurring Page

**File:** `frontend/src/pages/RecurringItems.jsx`

```jsx
import { useState, useEffect } from 'react';
import { recurringAPI, categoriesAPI } from '../services/api';

const FREQUENCIES = [
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'biweekly', label: 'Bi-weekly' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'quarterly', label: 'Quarterly' },
  { value: 'yearly', label: 'Yearly' }
];

const DAYS_OF_WEEK = [
  { value: 0, label: 'Monday' },
  { value: 1, label: 'Tuesday' },
  { value: 2, label: 'Wednesday' },
  { value: 3, label: 'Thursday' },
  { value: 4, label: 'Friday' },
  { value: 5, label: 'Saturday' },
  { value: 6, label: 'Sunday' }
];

export default function RecurringItems() {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [categories, setCategories] = useState([]);
  const [previewOccurrences, setPreviewOccurrences] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  
  const [formData, setFormData] = useState({
    name: '',
    entity_type: 'transaction',
    frequency: 'monthly',
    start_date: new Date().toISOString().split('T')[0],
    end_date: '',
    day_of_month: 1,
    day_of_week: null,
    auto_create: false,
    template_data: {
      type: 'expense',
      amount: 0,
      description: '',
      category_id: ''
    }
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [templatesRes, categoriesRes] = await Promise.all([
        recurringAPI.list(),
        categoriesAPI.getAll()
      ]);
      setTemplates(templatesRes.data.templates);
      setCategories(categoriesRes.data.categories || []);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    try {
      await recurringAPI.create(formData);
      setShowForm(false);
      resetForm();
      loadData();
    } catch (err) {
      alert('Failed to create template');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      entity_type: 'transaction',
      frequency: 'monthly',
      start_date: new Date().toISOString().split('T')[0],
      end_date: '',
      day_of_month: 1,
      day_of_week: null,
      auto_create: false,
      template_data: {
        type: 'expense',
        amount: 0,
        description: '',
        category_id: ''
      }
    });
  };

  const handleToggle = async (template) => {
    try {
      await recurringAPI.toggle(template.id);
      loadData();
    } catch (err) {
      alert('Failed to toggle');
    }
  };

  const handleDelete = async (template) => {
    if (!confirm('Delete this recurring template?')) return;
    try {
      await recurringAPI.delete(template.id);
      loadData();
    } catch (err) {
      alert('Failed to delete');
    }
  };

  const handleGenerateNow = async (template) => {
    try {
      const res = await recurringAPI.generate(template.id);
      alert('Generated successfully!');
      loadData();
    } catch (err) {
      alert('Failed to generate');
    }
  };

  const handlePreview = async (template) => {
    try {
      const res = await recurringAPI.preview(template.id, 5);
      setPreviewOccurrences(res.data.occurrences);
      setSelectedTemplate(template);
    } catch (err) {
      alert('Failed to load preview');
    }
  };

  return (
    <>
      <div className="info-banner mb-6">
        🔄 Create recurring templates for automated transaction and payment generation.
      </div>

      <div className="section mb-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="section-title" style={{ margin: 0 }}>Recurring Templates</h3>
          <button className="btn btn-primary" onClick={() => setShowForm(true)}>
            ➕ New Template
          </button>
        </div>

        {loading ? (
          <div className="text-center text-muted">Loading...</div>
        ) : templates.length === 0 ? (
          <div className="text-center text-muted">No recurring templates</div>
        ) : (
          <div className="recurring-list">
            {templates.map(template => (
              <div key={template.id} className={`recurring-card ${!template.active ? 'inactive' : ''}`}>
                <div className="recurring-header">
                  <div>
                    <h4>{template.name}</h4>
                    <span className={`badge ${template.active ? 'badge-success' : 'badge-gray'}`}>
                      {template.active ? 'Active' : 'Paused'}
                    </span>
                    <span className="badge badge-info">{template.entity_type}</span>
                  </div>
                  <div className="recurring-amount">
                    ${template.template_data.amount?.toLocaleString() || 0}
                  </div>
                </div>
                
                <div className="recurring-details">
                  <div>📅 <strong>Frequency:</strong> {template.frequency}</div>
                  <div>⏭️ <strong>Next:</strong> {template.next_occurrence}</div>
                  <div>📊 <strong>Generated:</strong> {template.generation_count} times</div>
                </div>

                <div className="recurring-actions">
                  <button className="btn btn-sm btn-secondary" onClick={() => handlePreview(template)}>
                    👁️ Preview
                  </button>
                  <button className="btn btn-sm btn-primary" onClick={() => handleGenerateNow(template)}>
                    ▶️ Generate Now
                  </button>
                  <button className="btn btn-sm btn-secondary" onClick={() => handleToggle(template)}>
                    {template.active ? '⏸️ Pause' : '▶️ Resume'}
                  </button>
                  <button className="btn btn-sm btn-danger" onClick={() => handleDelete(template)}>
                    🗑️
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Preview Modal */}
      {selectedTemplate && (
        <div className="modal-overlay" onClick={() => setSelectedTemplate(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Next Occurrences: {selectedTemplate.name}</h3>
              <button className="modal-close" onClick={() => setSelectedTemplate(null)}>×</button>
            </div>
            <div className="modal-body">
              <ul className="occurrence-list">
                {previewOccurrences.map((date, i) => (
                  <li key={i}>
                    <span className="occurrence-num">#{i + 1}</span>
                    <span className="occurrence-date">{new Date(date).toLocaleDateString()}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Create Form Modal */}
      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-content modal-lg" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Create Recurring Template</h3>
              <button className="modal-close" onClick={() => setShowForm(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Template Name *</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Monthly Rent"
                  />
                </div>
                
                <div className="form-group">
                  <label className="form-label">Entity Type</label>
                  <select
                    className="form-select"
                    value={formData.entity_type}
                    onChange={(e) => setFormData({ ...formData, entity_type: e.target.value })}
                  >
                    <option value="transaction">Transaction</option>
                    <option value="payment">Payment</option>
                  </select>
                </div>
                
                <div className="form-group">
                  <label className="form-label">Frequency</label>
                  <select
                    className="form-select"
                    value={formData.frequency}
                    onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                  >
                    {FREQUENCIES.map(f => (
                      <option key={f.value} value={f.value}>{f.label}</option>
                    ))}
                  </select>
                </div>
                
                <div className="form-group">
                  <label className="form-label">Start Date</label>
                  <input
                    type="date"
                    className="form-input"
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  />
                </div>
                
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
                
                {formData.frequency === 'weekly' && (
                  <div className="form-group">
                    <label className="form-label">Day of Week</label>
                    <select
                      className="form-select"
                      value={formData.day_of_week || 0}
                      onChange={(e) => setFormData({ ...formData, day_of_week: parseInt(e.target.value) })}
                    >
                      {DAYS_OF_WEEK.map(d => (
                        <option key={d.value} value={d.value}>{d.label}</option>
                      ))}
                    </select>
                  </div>
                )}
              </div>

              <hr className="my-6" />
              <h4 className="mb-4">Template Data</h4>

              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Type</label>
                  <select
                    className="form-select"
                    value={formData.template_data.type}
                    onChange={(e) => setFormData({
                      ...formData,
                      template_data: { ...formData.template_data, type: e.target.value }
                    })}
                  >
                    <option value="expense">Expense</option>
                    <option value="income">Income</option>
                  </select>
                </div>
                
                <div className="form-group">
                  <label className="form-label">Amount *</label>
                  <input
                    type="number"
                    className="form-input"
                    value={formData.template_data.amount}
                    onChange={(e) => setFormData({
                      ...formData,
                      template_data: { ...formData.template_data, amount: parseFloat(e.target.value) }
                    })}
                  />
                </div>
                
                <div className="form-group full-width">
                  <label className="form-label">Description</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.template_data.description}
                    onChange={(e) => setFormData({
                      ...formData,
                      template_data: { ...formData.template_data, description: e.target.value }
                    })}
                  />
                </div>
                
                <div className="form-group">
                  <label className="form-label">Category</label>
                  <select
                    className="form-select"
                    value={formData.template_data.category_id}
                    onChange={(e) => setFormData({
                      ...formData,
                      template_data: { ...formData.template_data, category_id: e.target.value }
                    })}
                  >
                    <option value="">Select category</option>
                    {categories.map(c => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <label className="checkbox-label mt-4">
                <input
                  type="checkbox"
                  checked={formData.auto_create}
                  onChange={(e) => setFormData({ ...formData, auto_create: e.target.checked })}
                />
                <span>Auto-create when due (otherwise notify only)</span>
              </label>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
              <button 
                className="btn btn-primary" 
                onClick={handleSubmit}
                disabled={!formData.name || !formData.template_data.amount}
              >
                Create Template
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
```

### 4.6 Add Recurring Styles

**Add to:** `frontend/src/index.css`

```css
/* Recurring Items */
.recurring-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.recurring-card {
  padding: 20px;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background: var(--card-bg);
  transition: opacity 0.3s;
}

.recurring-card.inactive {
  opacity: 0.6;
}

.recurring-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.recurring-header h4 {
  margin: 0 0 8px 0;
}

.recurring-amount {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--primary);
}

.recurring-details {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 16px;
  font-size: 0.9rem;
}

.recurring-actions {
  display: flex;
  gap: 8px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.occurrence-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.occurrence-list li {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-color);
}

.occurrence-num {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  font-weight: 600;
}
```

---

## TASK 5: BUDGET MANAGEMENT 💰

### 5.1 Create Budget Service

**File:** `backend/app/services/budget_service.py`

```python
"""
Budget Management Service
Track and manage budgets by category, project, or department
"""

from datetime import datetime
from typing import Dict, List, Optional
from app.models.store import db


class BudgetService:
    """Manages budgets and spending tracking"""
    
    _instance = None
    _budgets: Dict[str, dict] = {}
    _counter = 0
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._budgets = {}
            cls._counter = 0
        return cls._instance
    
    def create_budget(
        self,
        name: str,
        amount: float,
        period: str,  # monthly, quarterly, yearly
        start_date: str,
        category_id: Optional[str] = None,
        project_id: Optional[str] = None,
        alerts: List[dict] = None,
        created_by: str = None
    ) -> dict:
        """Create a new budget"""
        self._counter += 1
        budget_id = f"BUD-{self._counter:04d}"
        
        budget = {
            "id": budget_id,
            "name": name,
            "amount": amount,
            "spent": 0,
            "period": period,
            "start_date": start_date,
            "category_id": category_id,
            "project_id": project_id,
            "alerts": alerts or [
                {"threshold": 50, "notified": False},
                {"threshold": 80, "notified": False},
                {"threshold": 100, "notified": False}
            ],
            "active": True,
            "created_by": created_by,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Calculate current spending
        budget["spent"] = self._calculate_spent(budget)
        
        self._budgets[budget_id] = budget
        return budget
    
    def _calculate_spent(self, budget: dict) -> float:
        """Calculate total spent against a budget"""
        transactions = db.transactions.find_all()
        
        # Filter by date range
        start = budget["start_date"]
        period_end = self._get_period_end(budget["start_date"], budget["period"])
        
        filtered = [
            t for t in transactions
            if t.get("type") == "expense"
            and start <= t.get("date", "") <= period_end
        ]
        
        # Filter by category or project
        if budget["category_id"]:
            filtered = [t for t in filtered if t.get("category_id") == budget["category_id"]]
        
        if budget["project_id"]:
            filtered = [t for t in filtered if t.get("project_id") == budget["project_id"]]
        
        return sum(t.get("amount", 0) for t in filtered)
    
    def _get_period_end(self, start_date: str, period: str) -> str:
        """Get the end date for a budget period"""
        from dateutil.relativedelta import relativedelta
        
        start = datetime.fromisoformat(start_date)
        
        if period == "monthly":
            end = start + relativedelta(months=1) - relativedelta(days=1)
        elif period == "quarterly":
            end = start + relativedelta(months=3) - relativedelta(days=1)
        elif period == "yearly":
            end = start + relativedelta(years=1) - relativedelta(days=1)
        else:
            end = start + relativedelta(months=1) - relativedelta(days=1)
        
        return end.strftime("%Y-%m-%d")
    
    def update_budget(self, budget_id: str, updates: dict) -> Optional[dict]:
        """Update a budget"""
        if budget_id not in self._budgets:
            return None
        
        budget = self._budgets[budget_id]
        
        for key, value in updates.items():
            if key in budget and key not in ["id", "created_at", "created_by", "spent"]:
                budget[key] = value
        
        # Recalculate spent
        budget["spent"] = self._calculate_spent(budget)
        
        return budget
    
    def delete_budget(self, budget_id: str) -> bool:
        """Delete a budget"""
        if budget_id in self._budgets:
            del self._budgets[budget_id]
            return True
        return False
    
    def get_budget(self, budget_id: str) -> Optional[dict]:
        """Get a specific budget with updated spending"""
        budget = self._budgets.get(budget_id)
        if budget:
            budget["spent"] = self._calculate_spent(budget)
            self._check_alerts(budget)
        return budget
    
    def list_budgets(self, active_only: bool = True) -> List[dict]:
        """List all budgets with updated spending"""
        budgets = list(self._budgets.values())
        
        if active_only:
            budgets = [b for b in budgets if b["active"]]
        
        # Update spending for all
        for budget in budgets:
            budget["spent"] = self._calculate_spent(budget)
            budget["remaining"] = max(0, budget["amount"] - budget["spent"])
            budget["percentage"] = min(100, (budget["spent"] / budget["amount"]) * 100) if budget["amount"] > 0 else 0
            self._check_alerts(budget)
        
        return sorted(budgets, key=lambda b: b["percentage"], reverse=True)
    
    def _check_alerts(self, budget: dict) -> List[dict]:
        """Check and return triggered alerts"""
        triggered = []
        percentage = (budget["spent"] / budget["amount"]) * 100 if budget["amount"] > 0 else 0
        
        for alert in budget.get("alerts", []):
            if percentage >= alert["threshold"] and not alert["notified"]:
                alert["notified"] = True
                triggered.append({
                    "budget_id": budget["id"],
                    "budget_name": budget["name"],
                    "threshold": alert["threshold"],
                    "current_percentage": percentage,
                    "spent": budget["spent"],
                    "amount": budget["amount"]
                })
        
        return triggered
    
    def get_budget_summary(self) -> dict:
        """Get summary of all budgets"""
        budgets = self.list_budgets()
        
        total_budgeted = sum(b["amount"] for b in budgets)
        total_spent = sum(b["spent"] for b in budgets)
        
        over_budget = [b for b in budgets if b["spent"] > b["amount"]]
        at_risk = [b for b in budgets if 80 <= b["percentage"] < 100]
        on_track = [b for b in budgets if b["percentage"] < 80]
        
        return {
            "total_budgeted": total_budgeted,
            "total_spent": total_spent,
            "total_remaining": max(0, total_budgeted - total_spent),
            "budget_count": len(budgets),
            "over_budget_count": len(over_budget),
            "at_risk_count": len(at_risk),
            "on_track_count": len(on_track),
            "over_budget": over_budget,
            "at_risk": at_risk
        }
    
    def get_variance_report(self, budget_id: str) -> dict:
        """Get variance analysis for a budget"""
        budget = self.get_budget(budget_id)
        if not budget:
            return {"error": "Budget not found"}
        
        variance = budget["amount"] - budget["spent"]
        variance_percentage = (variance / budget["amount"]) * 100 if budget["amount"] > 0 else 0
        
        # Get breakdown by category or period
        transactions = db.transactions.find_all()
        start = budget["start_date"]
        period_end = self._get_period_end(budget["start_date"], budget["period"])
        
        filtered = [
            t for t in transactions
            if t.get("type") == "expense"
            and start <= t.get("date", "") <= period_end
        ]
        
        if budget["category_id"]:
            filtered = [t for t in filtered if t.get("category_id") == budget["category_id"]]
        
        # Group by week/month
        by_period = {}
        for t in filtered:
            period_key = t.get("date", "")[:7]  # YYYY-MM
            by_period[period_key] = by_period.get(period_key, 0) + t.get("amount", 0)
        
        return {
            "budget": budget,
            "variance": variance,
            "variance_percentage": variance_percentage,
            "status": "over" if variance < 0 else "under",
            "spending_by_period": by_period,
            "period_end": period_end
        }


budget_service = BudgetService()
```

### 5.2 Create Budget Routes

**File:** `backend/app/routes/budgets.py`

```python
"""
Budget Management routes
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.budget_service import budget_service
from app.utils.auth import get_current_user, require_roles

router = APIRouter()


class CreateBudgetRequest(BaseModel):
    name: str
    amount: float
    period: str
    start_date: str
    category_id: Optional[str] = None
    project_id: Optional[str] = None
    alerts: Optional[List[dict]] = None


class UpdateBudgetRequest(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = None
    period: Optional[str] = None
    start_date: Optional[str] = None
    category_id: Optional[str] = None
    project_id: Optional[str] = None
    active: Optional[bool] = None


@router.get("")
async def list_budgets(
    active_only: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """List all budgets"""
    return {"budgets": budget_service.list_budgets(active_only)}


@router.get("/summary")
async def get_summary(current_user: dict = Depends(get_current_user)):
    """Get budget summary"""
    return budget_service.get_budget_summary()


@router.post("")
async def create_budget(
    request: CreateBudgetRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Create a new budget"""
    return budget_service.create_budget(
        name=request.name,
        amount=request.amount,
        period=request.period,
        start_date=request.start_date,
        category_id=request.category_id,
        project_id=request.project_id,
        alerts=request.alerts,
        created_by=current_user["id"]
    )


@router.get("/{budget_id}")
async def get_budget(
    budget_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific budget"""
    budget = budget_service.get_budget(budget_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget


@router.put("/{budget_id}")
async def update_budget(
    budget_id: str,
    request: UpdateBudgetRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update a budget"""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    budget = budget_service.update_budget(budget_id, updates)
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    return budget


@router.delete("/{budget_id}")
async def delete_budget(
    budget_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Delete a budget"""
    if budget_service.delete_budget(budget_id):
        return {"message": "Budget deleted"}
    raise HTTPException(status_code=404, detail="Budget not found")


@router.get("/{budget_id}/variance")
async def get_variance(
    budget_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get variance report for a budget"""
    return budget_service.get_variance_report(budget_id)
```

### 5.3 Register Budget Routes

**Update:** `backend/app/main.py`

```python
from app.routes import budgets

app.include_router(budgets.router, prefix="/api/v1/budgets", tags=["Budgets"])
```

### 5.4 Add Budget API to Frontend

**Add to:** `frontend/src/services/api.js`

```javascript
// Budget API
export const budgetAPI = {
  list: (activeOnly = true) => api.get('/api/v1/budgets', { params: { active_only: activeOnly } }),
  getSummary: () => api.get('/api/v1/budgets/summary'),
  get: (id) => api.get(`/api/v1/budgets/${id}`),
  create: (data) => api.post('/api/v1/budgets', data),
  update: (id, data) => api.put(`/api/v1/budgets/${id}`, data),
  delete: (id) => api.delete(`/api/v1/budgets/${id}`),
  getVariance: (id) => api.get(`/api/v1/budgets/${id}/variance`)
};
```

### 5.5 Create Budgets Page

**File:** `frontend/src/pages/Budgets.jsx`

```jsx
import { useState, useEffect } from 'react';
import { budgetAPI, categoriesAPI, projectsAPI } from '../services/api';

export default function Budgets() {
  const [budgets, setBudgets] = useState([]);
  const [summary, setSummary] = useState(null);
  const [categories, setCategories] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [selectedBudget, setSelectedBudget] = useState(null);
  const [varianceData, setVarianceData] = useState(null);
  
  const [formData, setFormData] = useState({
    name: '',
    amount: 0,
    period: 'monthly',
    start_date: new Date().toISOString().split('T')[0].slice(0, 8) + '01',
    category_id: '',
    project_id: ''
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [budgetsRes, summaryRes, categoriesRes, projectsRes] = await Promise.all([
        budgetAPI.list(),
        budgetAPI.getSummary(),
        categoriesAPI.getAll(),
        projectsAPI.getAll()
      ]);
      setBudgets(budgetsRes.data.budgets);
      setSummary(summaryRes.data);
      setCategories(categoriesRes.data.categories || []);
      setProjects(projectsRes.data.projects || []);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    try {
      await budgetAPI.create(formData);
      setShowForm(false);
      setFormData({
        name: '',
        amount: 0,
        period: 'monthly',
        start_date: new Date().toISOString().split('T')[0].slice(0, 8) + '01',
        category_id: '',
        project_id: ''
      });
      loadData();
    } catch (err) {
      alert('Failed to create budget');
    }
  };

  const handleDelete = async (budget) => {
    if (!confirm('Delete this budget?')) return;
    try {
      await budgetAPI.delete(budget.id);
      loadData();
    } catch (err) {
      alert('Failed to delete');
    }
  };

  const handleViewVariance = async (budget) => {
    try {
      const res = await budgetAPI.getVariance(budget.id);
      setVarianceData(res.data);
      setSelectedBudget(budget);
    } catch (err) {
      alert('Failed to load variance');
    }
  };

  const getProgressColor = (percentage) => {
    if (percentage >= 100) return '#ef4444';
    if (percentage >= 80) return '#f59e0b';
    return '#10b981';
  };

  const getCategoryName = (id) => {
    const cat = categories.find(c => c.id === id);
    return cat?.name || 'All Categories';
  };

  return (
    <>
      {/* Summary Cards */}
      {summary && (
        <div className="stats-grid mb-6">
          <div className="stat-card">
            <div className="stat-icon">💰</div>
            <div className="stat-content">
              <div className="stat-value">${summary.total_budgeted.toLocaleString()}</div>
              <div className="stat-label">Total Budgeted</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">📊</div>
            <div className="stat-content">
              <div className="stat-value">${summary.total_spent.toLocaleString()}</div>
              <div className="stat-label">Total Spent</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">✅</div>
            <div className="stat-content">
              <div className="stat-value">{summary.on_track_count}</div>
              <div className="stat-label">On Track</div>
            </div>
          </div>
          <div className="stat-card warning">
            <div className="stat-icon">⚠️</div>
            <div className="stat-content">
              <div className="stat-value">{summary.at_risk_count + summary.over_budget_count}</div>
              <div className="stat-label">At Risk / Over</div>
            </div>
          </div>
        </div>
      )}

      <div className="section">
        <div className="flex justify-between items-center mb-4">
          <h3 className="section-title" style={{ margin: 0 }}>Budgets</h3>
          <button className="btn btn-primary" onClick={() => setShowForm(true)}>
            ➕ New Budget
          </button>
        </div>

        {loading ? (
          <div className="text-center text-muted">Loading...</div>
        ) : budgets.length === 0 ? (
          <div className="text-center text-muted">No budgets created</div>
        ) : (
          <div className="budgets-grid">
            {budgets.map(budget => (
              <div key={budget.id} className="budget-card">
                <div className="budget-header">
                  <h4>{budget.name}</h4>
                  <span className="badge badge-info">{budget.period}</span>
                </div>
                
                <div className="budget-amounts">
                  <div>
                    <span className="budget-spent">${budget.spent.toLocaleString()}</span>
                    <span className="budget-total"> / ${budget.amount.toLocaleString()}</span>
                  </div>
                  <div className="budget-remaining">
                    ${budget.remaining?.toLocaleString() || 0} remaining
                  </div>
                </div>
                
                <div className="budget-progress">
                  <div 
                    className="budget-progress-bar"
                    style={{ 
                      width: `${Math.min(100, budget.percentage)}%`,
                      backgroundColor: getProgressColor(budget.percentage)
                    }}
                  />
                </div>
                <div className="budget-percentage" style={{ color: getProgressColor(budget.percentage) }}>
                  {budget.percentage.toFixed(1)}%
                </div>
                
                <div className="budget-meta">
                  <span>📁 {getCategoryName(budget.category_id)}</span>
                  <span>📅 {budget.start_date}</span>
                </div>
                
                <div className="budget-actions">
                  <button className="btn btn-sm btn-secondary" onClick={() => handleViewVariance(budget)}>
                    📊 Variance
                  </button>
                  <button className="btn btn-sm btn-danger" onClick={() => handleDelete(budget)}>
                    🗑️
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Variance Modal */}
      {selectedBudget && varianceData && (
        <div className="modal-overlay" onClick={() => setSelectedBudget(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Variance Analysis: {selectedBudget.name}</h3>
              <button className="modal-close" onClick={() => setSelectedBudget(null)}>×</button>
            </div>
            <div className="modal-body">
              <div className="variance-summary">
                <div className={`variance-amount ${varianceData.status}`}>
                  {varianceData.status === 'under' ? '+' : '-'}$
                  {Math.abs(varianceData.variance).toLocaleString()}
                </div>
                <div className="variance-label">
                  {varianceData.status === 'under' ? 'Under Budget' : 'Over Budget'}
                  ({Math.abs(varianceData.variance_percentage).toFixed(1)}%)
                </div>
              </div>
              
              <h4 className="mt-4 mb-2">Spending by Period</h4>
              <div className="spending-periods">
                {Object.entries(varianceData.spending_by_period || {}).map(([period, amount]) => (
                  <div key={period} className="period-item">
                    <span>{period}</span>
                    <span>${amount.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Form Modal */}
      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Create Budget</h3>
              <button className="modal-close" onClick={() => setShowForm(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">Budget Name *</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Q1 Marketing Budget"
                />
              </div>
              
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Amount *</label>
                  <input
                    type="number"
                    className="form-input"
                    value={formData.amount}
                    onChange={(e) => setFormData({ ...formData, amount: parseFloat(e.target.value) })}
                  />
                </div>
                
                <div className="form-group">
                  <label className="form-label">Period</label>
                  <select
                    className="form-select"
                    value={formData.period}
                    onChange={(e) => setFormData({ ...formData, period: e.target.value })}
                  >
                    <option value="monthly">Monthly</option>
                    <option value="quarterly">Quarterly</option>
                    <option value="yearly">Yearly</option>
                  </select>
                </div>
                
                <div className="form-group">
                  <label className="form-label">Start Date</label>
                  <input
                    type="date"
                    className="form-input"
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  />
                </div>
                
                <div className="form-group">
                  <label className="form-label">Category (optional)</label>
                  <select
                    className="form-select"
                    value={formData.category_id}
                    onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
                  >
                    <option value="">All Categories</option>
                    {categories.map(c => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
              <button 
                className="btn btn-primary" 
                onClick={handleSubmit}
                disabled={!formData.name || !formData.amount}
              >
                Create Budget
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
```

### 5.6 Add Budget Styles

**Add to:** `frontend/src/index.css`

```css
/* Budgets */
.budgets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.budget-card {
  padding: 20px;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background: var(--card-bg);
}

.budget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.budget-header h4 {
  margin: 0;
}

.budget-amounts {
  margin-bottom: 12px;
}

.budget-spent {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
}

.budget-total {
  font-size: 1rem;
  color: var(--text-muted);
}

.budget-remaining {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-top: 4px;
}

.budget-progress {
  height: 8px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.budget-progress-bar {
  height: 100%;
  transition: width 0.3s;
}

.budget-percentage {
  font-size: 0.9rem;
  font-weight: 600;
  text-align: right;
  margin-bottom: 12px;
}

.budget-meta {
  display: flex;
  gap: 16px;
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 16px;
}

.budget-actions {
  display: flex;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
}

.variance-summary {
  text-align: center;
  padding: 24px;
  background: var(--bg-tertiary);
  border-radius: 12px;
}

.variance-amount {
  font-size: 2rem;
  font-weight: 700;
}

.variance-amount.under {
  color: #10b981;
}

.variance-amount.over {
  color: #ef4444;
}

.variance-label {
  color: var(--text-muted);
  margin-top: 4px;
}

.spending-periods {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.period-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border-radius: 6px;
}
```

---

## TASK 6: ADD ALL ROUTES

### 6.1 Update App.jsx

```jsx
const RecurringItems = lazy(() => import('./pages/RecurringItems'));
const Budgets = lazy(() => import('./pages/Budgets'));

// Add routes:
<Route path="/recurring" element={
  <PrivateRoute roles={['admin']}>
    <Layout><RecurringItems /></Layout>
  </PrivateRoute>
} />
<Route path="/budgets" element={
  <PrivateRoute roles={['admin']}>
    <Layout><Budgets /></Layout>
  </PrivateRoute>
} />
```

### 6.2 Update Layout Navigation

```javascript
{ path: '/recurring', icon: '🔄', label: 'Recurring', roles: ['admin'] },
{ path: '/budgets', icon: '💰', label: 'Budgets', roles: ['admin'] },
```

---

## COMPLETION CHECKLIST - PART 2

### Recurring Transactions
- [ ] Recurring service
- [ ] Multiple frequencies support
- [ ] Next occurrence calculation
- [ ] Generate from template
- [ ] Preview occurrences
- [ ] Frontend page
- [ ] Pause/Resume toggle

### Budget Management
- [ ] Budget service
- [ ] Spending tracking
- [ ] Period calculations
- [ ] Alert system
- [ ] Variance analysis
- [ ] Summary stats
- [ ] Frontend page

---

**Continue to Part 3 for Document Management, API Keys, Scheduled Reports, and Dashboard Builder**
