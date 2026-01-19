# LogiAccounting Pro - Phase 6 Tasks (Part 1/3)

## DASHBOARD BUILDER + REAL-TIME WEBSOCKET NOTIFICATIONS

---

## TASK 1: DASHBOARD BUILDER 📊

### 1.1 Create Dashboard Service

**File:** `backend/app/services/dashboard_service.py`

```python
"""
Custom Dashboard Builder Service
"""

from datetime import datetime
from typing import Dict, List, Optional
import secrets
from app.models.store import db


class DashboardService:
    """Manages custom dashboards and widgets"""
    
    _instance = None
    _dashboards: Dict[str, dict] = {}
    _counter = 0
    
    WIDGET_TYPES = {
        "kpi": {"min_w": 2, "min_h": 2, "max_w": 4, "max_h": 3},
        "line_chart": {"min_w": 4, "min_h": 3, "max_w": 12, "max_h": 6},
        "bar_chart": {"min_w": 4, "min_h": 3, "max_w": 12, "max_h": 6},
        "donut_chart": {"min_w": 3, "min_h": 3, "max_w": 6, "max_h": 5},
        "area_chart": {"min_w": 4, "min_h": 3, "max_w": 12, "max_h": 6},
        "gauge": {"min_w": 2, "min_h": 2, "max_w": 4, "max_h": 4},
        "data_table": {"min_w": 4, "min_h": 3, "max_w": 12, "max_h": 8},
        "progress_ring": {"min_w": 2, "min_h": 2, "max_w": 3, "max_h": 3},
        "sparkline": {"min_w": 2, "min_h": 1, "max_w": 4, "max_h": 2},
        "alerts_feed": {"min_w": 3, "min_h": 3, "max_w": 6, "max_h": 8},
        "calendar": {"min_w": 4, "min_h": 4, "max_w": 8, "max_h": 6},
        "notes": {"min_w": 2, "min_h": 2, "max_w": 6, "max_h": 6}
    }
    
    PRESET_TEMPLATES = [
        {
            "name": "Executive Overview",
            "description": "High-level business metrics",
            "layout": [
                {"type": "kpi", "x": 0, "y": 0, "w": 3, "h": 2, "config": {"metric": "total_revenue", "title": "Revenue"}},
                {"type": "kpi", "x": 3, "y": 0, "w": 3, "h": 2, "config": {"metric": "total_expenses", "title": "Expenses"}},
                {"type": "kpi", "x": 6, "y": 0, "w": 3, "h": 2, "config": {"metric": "net_profit", "title": "Net Profit"}},
                {"type": "kpi", "x": 9, "y": 0, "w": 3, "h": 2, "config": {"metric": "pending_payments", "title": "Pending"}},
                {"type": "line_chart", "x": 0, "y": 2, "w": 8, "h": 4, "config": {"metric": "revenue_trend", "title": "Revenue Trend"}},
                {"type": "donut_chart", "x": 8, "y": 2, "w": 4, "h": 4, "config": {"metric": "expenses_by_category", "title": "Expenses"}}
            ]
        },
        {
            "name": "Inventory Focus",
            "description": "Stock and materials tracking",
            "layout": [
                {"type": "kpi", "x": 0, "y": 0, "w": 3, "h": 2, "config": {"metric": "total_items", "title": "Total Items"}},
                {"type": "kpi", "x": 3, "y": 0, "w": 3, "h": 2, "config": {"metric": "low_stock_count", "title": "Low Stock"}},
                {"type": "kpi", "x": 6, "y": 0, "w": 3, "h": 2, "config": {"metric": "inventory_value", "title": "Total Value"}},
                {"type": "alerts_feed", "x": 9, "y": 0, "w": 3, "h": 6, "config": {"filter": "inventory"}},
                {"type": "bar_chart", "x": 0, "y": 2, "w": 9, "h": 4, "config": {"metric": "stock_by_category", "title": "Stock by Category"}}
            ]
        },
        {
            "name": "Cash Flow",
            "description": "Payments and cash management",
            "layout": [
                {"type": "kpi", "x": 0, "y": 0, "w": 4, "h": 2, "config": {"metric": "cash_in", "title": "Cash In"}},
                {"type": "kpi", "x": 4, "y": 0, "w": 4, "h": 2, "config": {"metric": "cash_out", "title": "Cash Out"}},
                {"type": "gauge", "x": 8, "y": 0, "w": 4, "h": 4, "config": {"metric": "collection_rate", "title": "Collection Rate"}},
                {"type": "area_chart", "x": 0, "y": 2, "w": 8, "h": 4, "config": {"metric": "cash_flow_trend", "title": "Cash Flow"}}
            ]
        }
    ]
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._dashboards = {}
            cls._counter = 0
        return cls._instance
    
    def create_dashboard(
        self,
        name: str,
        user_id: str,
        layout: List[dict] = None,
        is_default: bool = False,
        from_template: str = None
    ) -> dict:
        """Create a new dashboard"""
        self._counter += 1
        dashboard_id = f"DASH-{self._counter:04d}"
        
        # Use template layout if specified
        if from_template:
            template = next((t for t in self.PRESET_TEMPLATES if t["name"] == from_template), None)
            if template:
                layout = template["layout"]
        
        # Generate widget IDs
        final_layout = []
        for i, widget in enumerate(layout or []):
            final_layout.append({
                "widget_id": f"w{i+1}",
                **widget
            })
        
        # If setting as default, unset other defaults
        if is_default:
            for dash in self._dashboards.values():
                if dash["user_id"] == user_id:
                    dash["is_default"] = False
        
        dashboard = {
            "id": dashboard_id,
            "name": name,
            "user_id": user_id,
            "layout": final_layout,
            "is_default": is_default,
            "is_shared": False,
            "share_token": None,
            "refresh_interval": 60,  # seconds
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        self._dashboards[dashboard_id] = dashboard
        return dashboard
    
    def update_layout(self, dashboard_id: str, layout: List[dict]) -> Optional[dict]:
        """Update dashboard layout"""
        if dashboard_id not in self._dashboards:
            return None
        
        dashboard = self._dashboards[dashboard_id]
        dashboard["layout"] = layout
        dashboard["updated_at"] = datetime.utcnow().isoformat()
        return dashboard
    
    def add_widget(self, dashboard_id: str, widget: dict) -> Optional[dict]:
        """Add a widget to dashboard"""
        if dashboard_id not in self._dashboards:
            return None
        
        dashboard = self._dashboards[dashboard_id]
        widget_id = f"w{len(dashboard['layout']) + 1}"
        dashboard["layout"].append({"widget_id": widget_id, **widget})
        dashboard["updated_at"] = datetime.utcnow().isoformat()
        return dashboard
    
    def remove_widget(self, dashboard_id: str, widget_id: str) -> Optional[dict]:
        """Remove a widget from dashboard"""
        if dashboard_id not in self._dashboards:
            return None
        
        dashboard = self._dashboards[dashboard_id]
        dashboard["layout"] = [w for w in dashboard["layout"] if w["widget_id"] != widget_id]
        dashboard["updated_at"] = datetime.utcnow().isoformat()
        return dashboard
    
    def update_widget(self, dashboard_id: str, widget_id: str, updates: dict) -> Optional[dict]:
        """Update a specific widget"""
        if dashboard_id not in self._dashboards:
            return None
        
        dashboard = self._dashboards[dashboard_id]
        for widget in dashboard["layout"]:
            if widget["widget_id"] == widget_id:
                widget.update(updates)
                break
        
        dashboard["updated_at"] = datetime.utcnow().isoformat()
        return dashboard
    
    def share_dashboard(self, dashboard_id: str) -> Optional[str]:
        """Generate share token for dashboard"""
        if dashboard_id not in self._dashboards:
            return None
        
        dashboard = self._dashboards[dashboard_id]
        dashboard["is_shared"] = True
        dashboard["share_token"] = secrets.token_urlsafe(16)
        return dashboard["share_token"]
    
    def unshare_dashboard(self, dashboard_id: str) -> bool:
        """Remove sharing from dashboard"""
        if dashboard_id not in self._dashboards:
            return False
        
        dashboard = self._dashboards[dashboard_id]
        dashboard["is_shared"] = False
        dashboard["share_token"] = None
        return True
    
    def get_by_share_token(self, token: str) -> Optional[dict]:
        """Get dashboard by share token"""
        for dashboard in self._dashboards.values():
            if dashboard["share_token"] == token and dashboard["is_shared"]:
                return dashboard
        return None
    
    def get_dashboard(self, dashboard_id: str) -> Optional[dict]:
        """Get a specific dashboard"""
        return self._dashboards.get(dashboard_id)
    
    def list_dashboards(self, user_id: str) -> List[dict]:
        """List user's dashboards"""
        return [
            d for d in self._dashboards.values()
            if d["user_id"] == user_id
        ]
    
    def delete_dashboard(self, dashboard_id: str) -> bool:
        """Delete a dashboard"""
        if dashboard_id in self._dashboards:
            del self._dashboards[dashboard_id]
            return True
        return False
    
    def get_widget_types(self) -> dict:
        """Get available widget types"""
        return self.WIDGET_TYPES
    
    def get_templates(self) -> List[dict]:
        """Get preset templates"""
        return self.PRESET_TEMPLATES
    
    def get_widget_data(self, widget_type: str, config: dict) -> dict:
        """Get data for a specific widget"""
        metric = config.get("metric", "")
        
        # KPI metrics
        if widget_type == "kpi":
            return self._get_kpi_data(metric)
        
        # Chart metrics
        if widget_type in ["line_chart", "bar_chart", "area_chart"]:
            return self._get_chart_data(metric)
        
        # Donut chart
        if widget_type == "donut_chart":
            return self._get_donut_data(metric)
        
        # Gauge
        if widget_type == "gauge":
            return self._get_gauge_data(metric)
        
        # Alerts feed
        if widget_type == "alerts_feed":
            return self._get_alerts_data(config.get("filter"))
        
        return {"error": "Unknown widget type"}
    
    def _get_kpi_data(self, metric: str) -> dict:
        """Get KPI metric value"""
        transactions = db.transactions.find_all()
        materials = db.materials.find_all()
        payments = db.payments.find_all()
        
        if metric == "total_revenue":
            value = sum(t.get("amount", 0) for t in transactions if t.get("type") == "income")
            return {"value": value, "format": "currency", "trend": 5.2}
        
        if metric == "total_expenses":
            value = sum(t.get("amount", 0) for t in transactions if t.get("type") == "expense")
            return {"value": value, "format": "currency", "trend": -2.1}
        
        if metric == "net_profit":
            income = sum(t.get("amount", 0) for t in transactions if t.get("type") == "income")
            expense = sum(t.get("amount", 0) for t in transactions if t.get("type") == "expense")
            return {"value": income - expense, "format": "currency", "trend": 8.3}
        
        if metric == "pending_payments":
            pending = [p for p in payments if p.get("status") == "pending"]
            return {"value": sum(p.get("amount", 0) for p in pending), "format": "currency", "count": len(pending)}
        
        if metric == "total_items":
            return {"value": len(materials), "format": "number"}
        
        if metric == "low_stock_count":
            low = [m for m in materials if m.get("quantity", 0) <= m.get("min_stock", 0)]
            return {"value": len(low), "format": "number", "alert": len(low) > 0}
        
        if metric == "inventory_value":
            value = sum(m.get("quantity", 0) * m.get("unit_cost", 0) for m in materials)
            return {"value": value, "format": "currency"}
        
        return {"value": 0, "format": "number"}
    
    def _get_chart_data(self, metric: str) -> dict:
        """Get chart data"""
        transactions = db.transactions.find_all()
        
        if metric == "revenue_trend":
            # Group by month
            by_month = {}
            for t in transactions:
                if t.get("type") == "income":
                    month = t.get("date", "")[:7]
                    by_month[month] = by_month.get(month, 0) + t.get("amount", 0)
            
            labels = sorted(by_month.keys())[-6:]
            values = [by_month.get(m, 0) for m in labels]
            return {"labels": labels, "datasets": [{"label": "Revenue", "data": values}]}
        
        if metric == "cash_flow_trend":
            by_month = {}
            for t in transactions:
                month = t.get("date", "")[:7]
                if month not in by_month:
                    by_month[month] = {"income": 0, "expense": 0}
                if t.get("type") == "income":
                    by_month[month]["income"] += t.get("amount", 0)
                else:
                    by_month[month]["expense"] += t.get("amount", 0)
            
            labels = sorted(by_month.keys())[-6:]
            return {
                "labels": labels,
                "datasets": [
                    {"label": "Income", "data": [by_month.get(m, {}).get("income", 0) for m in labels]},
                    {"label": "Expense", "data": [by_month.get(m, {}).get("expense", 0) for m in labels]}
                ]
            }
        
        return {"labels": [], "datasets": []}
    
    def _get_donut_data(self, metric: str) -> dict:
        """Get donut chart data"""
        transactions = db.transactions.find_all()
        categories = db.categories.find_all()
        
        if metric == "expenses_by_category":
            by_cat = {}
            for t in transactions:
                if t.get("type") == "expense":
                    cat_id = t.get("category_id", "uncategorized")
                    by_cat[cat_id] = by_cat.get(cat_id, 0) + t.get("amount", 0)
            
            # Map to category names
            cat_names = {c["id"]: c["name"] for c in categories}
            labels = [cat_names.get(c, "Other") for c in by_cat.keys()]
            values = list(by_cat.values())
            
            return {"labels": labels, "data": values}
        
        return {"labels": [], "data": []}
    
    def _get_gauge_data(self, metric: str) -> dict:
        """Get gauge data"""
        payments = db.payments.find_all()
        
        if metric == "collection_rate":
            total = len(payments)
            paid = len([p for p in payments if p.get("status") == "paid"])
            rate = (paid / total * 100) if total > 0 else 0
            return {"value": rate, "min": 0, "max": 100, "format": "percent"}
        
        return {"value": 0, "min": 0, "max": 100}
    
    def _get_alerts_data(self, filter_type: str = None) -> dict:
        """Get alerts feed data"""
        materials = db.materials.find_all()
        payments = db.payments.find_all()
        
        alerts = []
        
        # Low stock alerts
        if filter_type in [None, "inventory"]:
            for m in materials:
                if m.get("quantity", 0) <= m.get("min_stock", 0):
                    alerts.append({
                        "type": "warning",
                        "message": f"Low stock: {m.get('name')}",
                        "entity_type": "material",
                        "entity_id": m.get("id")
                    })
        
        # Overdue payments
        if filter_type in [None, "payments"]:
            today = datetime.utcnow().date().isoformat()
            for p in payments:
                if p.get("status") == "pending" and p.get("due_date", "") < today:
                    alerts.append({
                        "type": "error",
                        "message": f"Overdue payment: ${p.get('amount')}",
                        "entity_type": "payment",
                        "entity_id": p.get("id")
                    })
        
        return {"alerts": alerts[:10]}


dashboard_service = DashboardService()
```

### 1.2 Create Dashboard Routes

**File:** `backend/app/routes/dashboards.py`

```python
"""
Dashboard Builder routes
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.dashboard_service import dashboard_service
from app.utils.auth import get_current_user

router = APIRouter()


class CreateDashboardRequest(BaseModel):
    name: str
    layout: Optional[List[dict]] = None
    is_default: bool = False
    from_template: Optional[str] = None


class UpdateLayoutRequest(BaseModel):
    layout: List[dict]


class AddWidgetRequest(BaseModel):
    type: str
    x: int
    y: int
    w: int
    h: int
    config: dict = {}


class UpdateWidgetRequest(BaseModel):
    x: Optional[int] = None
    y: Optional[int] = None
    w: Optional[int] = None
    h: Optional[int] = None
    config: Optional[dict] = None


@router.get("/widget-types")
async def get_widget_types():
    """Get available widget types"""
    return {"types": dashboard_service.get_widget_types()}


@router.get("/templates")
async def get_templates():
    """Get preset templates"""
    return {"templates": dashboard_service.get_templates()}


@router.get("")
async def list_dashboards(current_user: dict = Depends(get_current_user)):
    """List user's dashboards"""
    return {"dashboards": dashboard_service.list_dashboards(current_user["id"])}


@router.post("")
async def create_dashboard(
    request: CreateDashboardRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new dashboard"""
    return dashboard_service.create_dashboard(
        name=request.name,
        user_id=current_user["id"],
        layout=request.layout,
        is_default=request.is_default,
        from_template=request.from_template
    )


@router.get("/shared/{token}")
async def get_shared_dashboard(token: str):
    """Get shared dashboard by token"""
    dashboard = dashboard_service.get_by_share_token(token)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.get("/{dashboard_id}")
async def get_dashboard(
    dashboard_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific dashboard"""
    dashboard = dashboard_service.get_dashboard(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.put("/{dashboard_id}/layout")
async def update_layout(
    dashboard_id: str,
    request: UpdateLayoutRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update dashboard layout"""
    dashboard = dashboard_service.update_layout(dashboard_id, request.layout)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.post("/{dashboard_id}/widgets")
async def add_widget(
    dashboard_id: str,
    request: AddWidgetRequest,
    current_user: dict = Depends(get_current_user)
):
    """Add widget to dashboard"""
    dashboard = dashboard_service.add_widget(dashboard_id, request.model_dump())
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.put("/{dashboard_id}/widgets/{widget_id}")
async def update_widget(
    dashboard_id: str,
    widget_id: str,
    request: UpdateWidgetRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update a widget"""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    dashboard = dashboard_service.update_widget(dashboard_id, widget_id, updates)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.delete("/{dashboard_id}/widgets/{widget_id}")
async def remove_widget(
    dashboard_id: str,
    widget_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove widget from dashboard"""
    dashboard = dashboard_service.remove_widget(dashboard_id, widget_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.post("/{dashboard_id}/share")
async def share_dashboard(
    dashboard_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Generate share link"""
    token = dashboard_service.share_dashboard(dashboard_id)
    if not token:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return {"share_token": token, "share_url": f"/dashboard/shared/{token}"}


@router.delete("/{dashboard_id}/share")
async def unshare_dashboard(
    dashboard_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove sharing"""
    if dashboard_service.unshare_dashboard(dashboard_id):
        return {"message": "Sharing disabled"}
    raise HTTPException(status_code=404, detail="Dashboard not found")


@router.delete("/{dashboard_id}")
async def delete_dashboard(
    dashboard_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete dashboard"""
    if dashboard_service.delete_dashboard(dashboard_id):
        return {"message": "Dashboard deleted"}
    raise HTTPException(status_code=404, detail="Dashboard not found")


@router.get("/{dashboard_id}/widgets/{widget_id}/data")
async def get_widget_data(
    dashboard_id: str,
    widget_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get data for a widget"""
    dashboard = dashboard_service.get_dashboard(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    widget = next((w for w in dashboard["layout"] if w["widget_id"] == widget_id), None)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    
    return dashboard_service.get_widget_data(widget["type"], widget.get("config", {}))
```

### 1.3 Register Dashboard Routes

**Update:** `backend/app/main.py`

```python
from app.routes import dashboards

app.include_router(dashboards.router, prefix="/api/v1/dashboards", tags=["Dashboards"])
```

### 1.4 Add Dashboard API to Frontend

**Add to:** `frontend/src/services/api.js`

```javascript
// Dashboard Builder API
export const dashboardAPI = {
  getWidgetTypes: () => api.get('/api/v1/dashboards/widget-types'),
  getTemplates: () => api.get('/api/v1/dashboards/templates'),
  list: () => api.get('/api/v1/dashboards'),
  create: (data) => api.post('/api/v1/dashboards', data),
  get: (id) => api.get(`/api/v1/dashboards/${id}`),
  getShared: (token) => api.get(`/api/v1/dashboards/shared/${token}`),
  updateLayout: (id, layout) => api.put(`/api/v1/dashboards/${id}/layout`, { layout }),
  addWidget: (id, widget) => api.post(`/api/v1/dashboards/${id}/widgets`, widget),
  updateWidget: (id, widgetId, updates) => api.put(`/api/v1/dashboards/${id}/widgets/${widgetId}`, updates),
  removeWidget: (id, widgetId) => api.delete(`/api/v1/dashboards/${id}/widgets/${widgetId}`),
  share: (id) => api.post(`/api/v1/dashboards/${id}/share`),
  unshare: (id) => api.delete(`/api/v1/dashboards/${id}/share`),
  delete: (id) => api.delete(`/api/v1/dashboards/${id}`),
  getWidgetData: (dashboardId, widgetId) => api.get(`/api/v1/dashboards/${dashboardId}/widgets/${widgetId}/data`)
};
```

### 1.5 Create Dashboard Builder Page

**File:** `frontend/src/pages/DashboardBuilder.jsx`

```jsx
import { useState, useEffect, useCallback } from 'react';
import { dashboardAPI } from '../services/api';
import GridLayout from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

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
      setDashboards(dashboardsRes.data.dashboards);
      setWidgetTypes(typesRes.data.types);
      setTemplates(templatesRes.data.templates);
      
      // Load default or first dashboard
      const defaultDash = dashboardsRes.data.dashboards.find(d => d.is_default) 
                          || dashboardsRes.data.dashboards[0];
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

  const handleLayoutChange = useCallback(async (newLayout) => {
    if (!currentDashboard || !editMode) return;
    
    const updatedLayout = currentDashboard.layout.map(widget => {
      const layoutItem = newLayout.find(l => l.i === widget.widget_id);
      if (layoutItem) {
        return { ...widget, x: layoutItem.x, y: layoutItem.y, w: layoutItem.w, h: layoutItem.h };
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
        w: typeConfig.min_w,
        h: typeConfig.min_h,
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
      setDashboards(dashboards.filter(d => d.id !== currentDashboard.id));
      setCurrentDashboard(dashboards[0] || null);
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
            ➕ New
          </button>
        </div>
        
        <div className="dashboard-actions">
          <button 
            className={`btn btn-sm ${editMode ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setEditMode(!editMode)}
          >
            {editMode ? '✓ Done Editing' : '✏️ Edit'}
          </button>
          {editMode && (
            <button className="btn btn-sm btn-secondary" onClick={() => setShowAddWidget(true)}>
              ➕ Add Widget
            </button>
          )}
          <button className="btn btn-sm btn-secondary" onClick={handleShare}>
            🔗 Share
          </button>
          {editMode && (
            <button className="btn btn-sm btn-danger" onClick={handleDeleteDashboard}>
              🗑️
            </button>
          )}
        </div>
      </div>

      {/* Dashboard Grid */}
      {currentDashboard ? (
        <GridLayout
          className="dashboard-grid"
          layout={currentDashboard.layout.map(w => ({
            i: w.widget_id,
            x: w.x,
            y: w.y,
            w: w.w,
            h: w.h,
            minW: widgetTypes[w.type]?.min_w || 2,
            minH: widgetTypes[w.type]?.min_h || 2
          }))}
          cols={12}
          rowHeight={80}
          width={1200}
          isDraggable={editMode}
          isResizable={editMode}
          onLayoutChange={handleLayoutChange}
        >
          {currentDashboard.layout.map(widget => (
            <div key={widget.widget_id} className="widget-container">
              {renderWidget(widget)}
            </div>
          ))}
        </GridLayout>
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
              <button className="modal-close" onClick={() => setShowNewDashboard(false)}>×</button>
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
              <button className="modal-close" onClick={() => setShowAddWidget(false)}>×</button>
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
                      {type === 'kpi' && '🔢'}
                      {type === 'line_chart' && '📈'}
                      {type === 'bar_chart' && '📊'}
                      {type === 'donut_chart' && '🍩'}
                      {type === 'area_chart' && '📉'}
                      {type === 'gauge' && '📏'}
                      {type === 'data_table' && '📋'}
                      {type === 'alerts_feed' && '🔔'}
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
```

### 1.6 Create Widget Components

**File:** `frontend/src/components/dashboard/widgets/KPIWidget.jsx`

```jsx
import { useState, useEffect } from 'react';
import { dashboardAPI } from '../../../services/api';

export default function KPIWidget({ widget, dashboardId, onRemove }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const res = await dashboardAPI.getWidgetData(dashboardId, widget.widget_id);
      setData(res.data);
    } catch (err) {
      console.error('Failed to load KPI data:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatValue = (value, format) => {
    if (format === 'currency') return `$${value.toLocaleString()}`;
    if (format === 'percent') return `${value.toFixed(1)}%`;
    return value.toLocaleString();
  };

  if (loading) return <div className="widget-loading">Loading...</div>;

  return (
    <div className="widget kpi-widget">
      {onRemove && (
        <button className="widget-remove" onClick={onRemove}>×</button>
      )}
      <div className="kpi-title">{widget.config?.title || 'KPI'}</div>
      <div className="kpi-value">{formatValue(data?.value || 0, data?.format)}</div>
      {data?.trend !== undefined && (
        <div className={`kpi-trend ${data.trend >= 0 ? 'positive' : 'negative'}`}>
          {data.trend >= 0 ? '↑' : '↓'} {Math.abs(data.trend)}%
        </div>
      )}
      {data?.count !== undefined && (
        <div className="kpi-count">{data.count} items</div>
      )}
    </div>
  );
}
```

**File:** `frontend/src/components/dashboard/widgets/ChartWidget.jsx`

```jsx
import { useState, useEffect, useRef } from 'react';
import { dashboardAPI } from '../../../services/api';
import Chart from 'chart.js/auto';

export default function ChartWidget({ widget, dashboardId, onRemove }) {
  const [data, setData] = useState(null);
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  useEffect(() => {
    loadData();
    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, []);

  useEffect(() => {
    if (data && chartRef.current) {
      renderChart();
    }
  }, [data]);

  const loadData = async () => {
    try {
      const res = await dashboardAPI.getWidgetData(dashboardId, widget.widget_id);
      setData(res.data);
    } catch (err) {
      console.error('Failed to load chart data:', err);
    }
  };

  const renderChart = () => {
    if (chartInstance.current) {
      chartInstance.current.destroy();
    }

    const chartType = widget.type === 'bar_chart' ? 'bar' 
                    : widget.type === 'area_chart' ? 'line' 
                    : 'line';

    chartInstance.current = new Chart(chartRef.current, {
      type: chartType,
      data: {
        labels: data.labels,
        datasets: data.datasets.map((ds, i) => ({
          ...ds,
          borderColor: i === 0 ? '#667eea' : '#10b981',
          backgroundColor: widget.type === 'area_chart' 
            ? (i === 0 ? 'rgba(102, 126, 234, 0.2)' : 'rgba(16, 185, 129, 0.2)')
            : (i === 0 ? '#667eea' : '#10b981'),
          fill: widget.type === 'area_chart',
          tension: 0.4
        }))
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: data.datasets.length > 1 }
        }
      }
    });
  };

  return (
    <div className="widget chart-widget">
      {onRemove && (
        <button className="widget-remove" onClick={onRemove}>×</button>
      )}
      <div className="widget-title">{widget.config?.title || 'Chart'}</div>
      <div className="chart-container">
        <canvas ref={chartRef} />
      </div>
    </div>
  );
}
```

**File:** `frontend/src/components/dashboard/widgets/DonutWidget.jsx`

```jsx
import { useState, useEffect, useRef } from 'react';
import { dashboardAPI } from '../../../services/api';
import Chart from 'chart.js/auto';

export default function DonutWidget({ widget, dashboardId, onRemove }) {
  const [data, setData] = useState(null);
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  useEffect(() => {
    loadData();
    return () => {
      if (chartInstance.current) chartInstance.current.destroy();
    };
  }, []);

  useEffect(() => {
    if (data && chartRef.current) renderChart();
  }, [data]);

  const loadData = async () => {
    try {
      const res = await dashboardAPI.getWidgetData(dashboardId, widget.widget_id);
      setData(res.data);
    } catch (err) {
      console.error('Failed to load donut data:', err);
    }
  };

  const renderChart = () => {
    if (chartInstance.current) chartInstance.current.destroy();

    const colors = ['#667eea', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

    chartInstance.current = new Chart(chartRef.current, {
      type: 'doughnut',
      data: {
        labels: data.labels,
        datasets: [{
          data: data.data,
          backgroundColor: colors.slice(0, data.labels.length),
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '60%',
        plugins: {
          legend: { position: 'right' }
        }
      }
    });
  };

  return (
    <div className="widget donut-widget">
      {onRemove && <button className="widget-remove" onClick={onRemove}>×</button>}
      <div className="widget-title">{widget.config?.title || 'Chart'}</div>
      <div className="chart-container">
        <canvas ref={chartRef} />
      </div>
    </div>
  );
}
```

**File:** `frontend/src/components/dashboard/widgets/GaugeWidget.jsx`

```jsx
import { useState, useEffect } from 'react';
import { dashboardAPI } from '../../../services/api';

export default function GaugeWidget({ widget, dashboardId, onRemove }) {
  const [data, setData] = useState({ value: 0, min: 0, max: 100 });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const res = await dashboardAPI.getWidgetData(dashboardId, widget.widget_id);
      setData(res.data);
    } catch (err) {
      console.error('Failed to load gauge data:', err);
    }
  };

  const percentage = ((data.value - data.min) / (data.max - data.min)) * 100;
  const rotation = (percentage / 100) * 180 - 90;

  return (
    <div className="widget gauge-widget">
      {onRemove && <button className="widget-remove" onClick={onRemove}>×</button>}
      <div className="widget-title">{widget.config?.title || 'Gauge'}</div>
      <div className="gauge-container">
        <svg viewBox="0 0 100 60" className="gauge-svg">
          <path 
            d="M10 50 A 40 40 0 0 1 90 50" 
            fill="none" 
            stroke="var(--bg-tertiary)" 
            strokeWidth="8"
            strokeLinecap="round"
          />
          <path 
            d="M10 50 A 40 40 0 0 1 90 50" 
            fill="none" 
            stroke="var(--primary)" 
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={`${percentage * 1.26} 126`}
          />
        </svg>
        <div className="gauge-value">{data.value.toFixed(1)}%</div>
      </div>
    </div>
  );
}
```

**File:** `frontend/src/components/dashboard/widgets/AlertsWidget.jsx`

```jsx
import { useState, useEffect } from 'react';
import { dashboardAPI } from '../../../services/api';

export default function AlertsWidget({ widget, dashboardId, onRemove }) {
  const [data, setData] = useState({ alerts: [] });

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const res = await dashboardAPI.getWidgetData(dashboardId, widget.widget_id);
      setData(res.data);
    } catch (err) {
      console.error('Failed to load alerts:', err);
    }
  };

  return (
    <div className="widget alerts-widget">
      {onRemove && <button className="widget-remove" onClick={onRemove}>×</button>}
      <div className="widget-title">🔔 Alerts</div>
      <div className="alerts-list">
        {data.alerts.length === 0 ? (
          <div className="no-alerts">✅ No alerts</div>
        ) : (
          data.alerts.map((alert, i) => (
            <div key={i} className={`alert-item ${alert.type}`}>
              {alert.type === 'error' ? '🔴' : '🟡'} {alert.message}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
```

### 1.7 Add Dashboard Styles

**Add to:** `frontend/src/index.css`

```css
/* Dashboard Builder */
.dashboard-builder {
  min-height: calc(100vh - 200px);
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.dashboard-tabs {
  display: flex;
  gap: 8px;
}

.dashboard-tab {
  padding: 8px 16px;
  border: none;
  background: var(--bg-tertiary);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.dashboard-tab.active {
  background: var(--primary);
  color: white;
}

.dashboard-tab.add {
  background: transparent;
  border: 1px dashed var(--border-color);
}

.dashboard-actions {
  display: flex;
  gap: 8px;
}

.dashboard-grid {
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 16px;
  min-height: 500px;
}

.widget-container {
  background: var(--card-bg);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.widget {
  height: 100%;
  padding: 16px;
  position: relative;
}

.widget-remove {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--danger);
  color: white;
  border: none;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s;
}

.widget:hover .widget-remove {
  opacity: 1;
}

.widget-title {
  font-weight: 600;
  margin-bottom: 12px;
  font-size: 0.9rem;
  color: var(--text-muted);
}

.widget-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-muted);
}

/* KPI Widget */
.kpi-widget {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
}

.kpi-title {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.kpi-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
}

.kpi-trend {
  font-size: 0.9rem;
  font-weight: 500;
  margin-top: 8px;
}

.kpi-trend.positive { color: #10b981; }
.kpi-trend.negative { color: #ef4444; }

.kpi-count {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-top: 4px;
}

/* Chart Widget */
.chart-container {
  height: calc(100% - 40px);
}

/* Gauge Widget */
.gauge-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: calc(100% - 40px);
}

.gauge-svg {
  width: 120px;
  height: 70px;
}

.gauge-value {
  font-size: 1.5rem;
  font-weight: 700;
  margin-top: -20px;
}

/* Alerts Widget */
.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-y: auto;
  max-height: calc(100% - 40px);
}

.alert-item {
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 0.85rem;
}

.alert-item.warning { background: rgba(245, 158, 11, 0.1); }
.alert-item.error { background: rgba(239, 68, 68, 0.1); }

.no-alerts {
  text-align: center;
  color: var(--text-muted);
  padding: 24px;
}

/* Widget Palette */
.widget-palette {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 16px;
}

.widget-type-card {
  padding: 20px;
  border: 2px solid var(--border-color);
  border-radius: 12px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.widget-type-card:hover {
  border-color: var(--primary);
  transform: translateY(-2px);
}

.widget-type-icon {
  font-size: 2rem;
  margin-bottom: 8px;
}

.widget-type-name {
  font-weight: 500;
  text-transform: capitalize;
  font-size: 0.9rem;
}

.widget-type-size {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 4px;
}
```

---

## TASK 2: REAL-TIME WEBSOCKET NOTIFICATIONS ⚡

### 2.1 Create WebSocket Manager

**File:** `backend/app/services/websocket_manager.py`

```python
"""
WebSocket Connection Manager
Real-time notifications
"""

from typing import Dict, List, Set
from fastapi import WebSocket
import json
from datetime import datetime


class WebSocketManager:
    """Manages WebSocket connections and broadcasting"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}  # user_id -> websocket
        self.user_roles: Dict[str, str] = {}  # user_id -> role
    
    async def connect(self, websocket: WebSocket, user_id: str, role: str):
        """Accept and store connection"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_roles[user_id] = role
        print(f"WebSocket connected: {user_id} ({role})")
    
    def disconnect(self, user_id: str):
        """Remove connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_roles:
            del self.user_roles[user_id]
        print(f"WebSocket disconnected: {user_id}")
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send message to specific user"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                print(f"Error sending to {user_id}: {e}")
                self.disconnect(user_id)
    
    async def send_to_role(self, role: str, message: dict):
        """Send message to all users with specific role"""
        for user_id, user_role in self.user_roles.items():
            if user_role == role:
                await self.send_to_user(user_id, message)
    
    async def broadcast(self, message: dict):
        """Send message to all connected users"""
        for user_id in list(self.active_connections.keys()):
            await self.send_to_user(user_id, message)
    
    async def notify(
        self,
        event_type: str,
        data: dict,
        target_users: List[str] = None,
        target_roles: List[str] = None
    ):
        """Send notification to targeted users/roles"""
        message = {
            "type": "notification",
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if target_users:
            for user_id in target_users:
                await self.send_to_user(user_id, message)
        elif target_roles:
            for role in target_roles:
                await self.send_to_role(role, message)
        else:
            await self.broadcast(message)
    
    def get_connected_users(self) -> List[str]:
        """Get list of connected user IDs"""
        return list(self.active_connections.keys())


ws_manager = WebSocketManager()
```

### 2.2 Create WebSocket Routes

**File:** `backend/app/routes/websocket.py`

```python
"""
WebSocket routes
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.services.websocket_manager import ws_manager
from app.utils.auth import decode_token
import json

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    """WebSocket connection endpoint"""
    
    # Validate token
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        role = payload.get("role", "user")
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    await ws_manager.connect(websocket, user_id, role)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                # Handle ping/pong for keepalive
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)
```

### 2.3 Add Helper to Send Notifications

**Add to:** `backend/app/services/websocket_manager.py`

```python
# Notification event types and helpers
async def notify_transaction_created(transaction: dict, user_id: str):
    await ws_manager.notify(
        "transaction.created",
        {"transaction": transaction},
        target_roles=["admin"]
    )

async def notify_payment_due(payment: dict):
    await ws_manager.notify(
        "payment.due_soon",
        {"payment": payment},
        target_roles=["admin"]
    )

async def notify_low_stock(material: dict):
    await ws_manager.notify(
        "inventory.low_stock",
        {"material": material},
        target_roles=["admin"]
    )

async def notify_approval_required(approval: dict, approver_ids: List[str]):
    await ws_manager.notify(
        "approval.required",
        {"approval": approval},
        target_users=approver_ids
    )

async def notify_budget_threshold(budget: dict, threshold: int):
    await ws_manager.notify(
        "budget.threshold_reached",
        {"budget": budget, "threshold": threshold},
        target_roles=["admin"]
    )
```

### 2.4 Register WebSocket Route

**Update:** `backend/app/main.py`

```python
from app.routes import websocket

app.include_router(websocket.router, tags=["WebSocket"])
```

### 2.5 Create WebSocket Context

**File:** `frontend/src/contexts/WebSocketContext.jsx`

```jsx
import { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { useAuth } from './AuthContext';

const WebSocketContext = createContext(null);

export function WebSocketProvider({ children }) {
  const { token, isAuthenticated } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    if (!token || wsRef.current?.readyState === WebSocket.OPEN) return;

    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws?token=${token}`;
    
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      
      // Start ping interval
      const pingInterval = setInterval(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: 'ping' }));
        }
      }, 30000);
      
      wsRef.current.pingInterval = pingInterval;
    };

    wsRef.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        
        if (message.type === 'notification') {
          const notification = {
            id: Date.now(),
            event: message.event,
            data: message.data,
            timestamp: message.timestamp,
            read: false
          };
          
          setNotifications(prev => [notification, ...prev].slice(0, 50));
          
          // Show toast
          showToast(notification);
          
          // Request desktop notification permission
          if (Notification.permission === 'granted') {
            new Notification('LogiAccounting Pro', {
              body: getNotificationMessage(notification),
              icon: '/logo192.png'
            });
          }
        }
      } catch (e) {
        console.error('WebSocket message error:', e);
      }
    };

    wsRef.current.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      
      if (wsRef.current?.pingInterval) {
        clearInterval(wsRef.current.pingInterval);
      }
      
      // Reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(connect, 3000);
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }, [token]);

  useEffect(() => {
    if (isAuthenticated && token) {
      connect();
    }
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [isAuthenticated, token, connect]);

  const showToast = (notification) => {
    // Dispatch custom event for toast
    window.dispatchEvent(new CustomEvent('show-toast', { 
      detail: notification 
    }));
  };

  const getNotificationMessage = (notification) => {
    const messages = {
      'transaction.created': 'New transaction created',
      'payment.due_soon': 'Payment due soon',
      'payment.overdue': 'Payment overdue',
      'inventory.low_stock': 'Low stock alert',
      'approval.required': 'Approval required',
      'approval.completed': 'Approval completed',
      'budget.threshold_reached': 'Budget threshold reached',
      'anomaly.detected': 'Anomaly detected'
    };
    return messages[notification.event] || 'New notification';
  };

  const markAsRead = (notificationId) => {
    setNotifications(prev => 
      prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  const clearNotifications = () => {
    setNotifications([]);
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <WebSocketContext.Provider value={{
      isConnected,
      notifications,
      unreadCount,
      markAsRead,
      markAllAsRead,
      clearNotifications
    }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export const useWebSocket = () => useContext(WebSocketContext);
```

### 2.6 Create Notification Bell Component

**File:** `frontend/src/components/NotificationBell.jsx`

```jsx
import { useState, useRef, useEffect } from 'react';
import { useWebSocket } from '../contexts/WebSocketContext';

export default function NotificationBell() {
  const { notifications, unreadCount, markAsRead, markAllAsRead, clearNotifications } = useWebSocket();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getEventIcon = (event) => {
    const icons = {
      'transaction.created': '💰',
      'payment.due_soon': '⏰',
      'payment.overdue': '🔴',
      'inventory.low_stock': '📦',
      'approval.required': '✅',
      'approval.completed': '✔️',
      'budget.threshold_reached': '💸',
      'anomaly.detected': '⚠️'
    };
    return icons[event] || '🔔';
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="notification-bell" ref={dropdownRef}>
      <button 
        className="bell-button"
        onClick={() => setIsOpen(!isOpen)}
      >
        🔔
        {unreadCount > 0 && (
          <span className="bell-badge">{unreadCount > 9 ? '9+' : unreadCount}</span>
        )}
      </button>

      {isOpen && (
        <div className="notification-dropdown">
          <div className="notification-header">
            <h4>Notifications</h4>
            {notifications.length > 0 && (
              <div className="notification-actions">
                <button onClick={markAllAsRead}>Mark all read</button>
                <button onClick={clearNotifications}>Clear</button>
              </div>
            )}
          </div>

          <div className="notification-list">
            {notifications.length === 0 ? (
              <div className="no-notifications">
                No notifications
              </div>
            ) : (
              notifications.map(notification => (
                <div 
                  key={notification.id}
                  className={`notification-item ${!notification.read ? 'unread' : ''}`}
                  onClick={() => markAsRead(notification.id)}
                >
                  <span className="notification-icon">
                    {getEventIcon(notification.event)}
                  </span>
                  <div className="notification-content">
                    <div className="notification-message">
                      {notification.event.replace(/\./g, ' ').replace(/_/g, ' ')}
                    </div>
                    <div className="notification-time">
                      {formatTime(notification.timestamp)}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
```

### 2.7 Create Toast Container

**File:** `frontend/src/components/ToastContainer.jsx`

```jsx
import { useState, useEffect } from 'react';

export default function ToastContainer() {
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    const handleShowToast = (event) => {
      const notification = event.detail;
      const toast = {
        id: notification.id,
        event: notification.event,
        message: notification.event.replace(/\./g, ' ').replace(/_/g, ' ')
      };
      
      setToasts(prev => [...prev, toast]);
      
      // Auto remove after 5 seconds
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== toast.id));
      }, 5000);
    };

    window.addEventListener('show-toast', handleShowToast);
    return () => window.removeEventListener('show-toast', handleShowToast);
  }, []);

  const removeToast = (id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  const getEventIcon = (event) => {
    const icons = {
      'transaction.created': '💰',
      'payment.due_soon': '⏰',
      'payment.overdue': '🔴',
      'inventory.low_stock': '📦',
      'approval.required': '✅',
      'budget.threshold_reached': '💸',
      'anomaly.detected': '⚠️'
    };
    return icons[event] || '🔔';
  };

  return (
    <div className="toast-container">
      {toasts.map(toast => (
        <div key={toast.id} className="toast">
          <span className="toast-icon">{getEventIcon(toast.event)}</span>
          <span className="toast-message">{toast.message}</span>
          <button className="toast-close" onClick={() => removeToast(toast.id)}>×</button>
        </div>
      ))}
    </div>
  );
}
```

### 2.8 Add Notification Styles

**Add to:** `frontend/src/index.css`

```css
/* Notification Bell */
.notification-bell {
  position: relative;
}

.bell-button {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  position: relative;
  padding: 8px;
}

.bell-badge {
  position: absolute;
  top: 0;
  right: 0;
  background: #ef4444;
  color: white;
  font-size: 0.7rem;
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 600;
}

.notification-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  width: 360px;
  background: var(--card-bg);
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  overflow: hidden;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
}

.notification-header h4 {
  margin: 0;
}

.notification-actions {
  display: flex;
  gap: 12px;
}

.notification-actions button {
  background: none;
  border: none;
  color: var(--primary);
  cursor: pointer;
  font-size: 0.85rem;
}

.notification-list {
  max-height: 400px;
  overflow-y: auto;
}

.notification-item {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.notification-item:hover {
  background: var(--bg-hover);
}

.notification-item.unread {
  background: rgba(102, 126, 234, 0.05);
}

.notification-icon {
  font-size: 1.25rem;
}

.notification-content {
  flex: 1;
}

.notification-message {
  font-size: 0.9rem;
  text-transform: capitalize;
}

.notification-time {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-top: 2px;
}

.no-notifications {
  padding: 40px;
  text-align: center;
  color: var(--text-muted);
}

/* Toast Notifications */
.toast-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  z-index: 10000;
}

.toast {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--card-bg);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.toast-icon {
  font-size: 1.25rem;
}

.toast-message {
  flex: 1;
  font-size: 0.9rem;
  text-transform: capitalize;
}

.toast-close {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: var(--text-muted);
}
```

### 2.9 Integrate Components

**Update:** `frontend/src/App.jsx`

```jsx
import { WebSocketProvider } from './contexts/WebSocketContext';
import ToastContainer from './components/ToastContainer';

// Wrap app with WebSocketProvider
<WebSocketProvider>
  {/* ... existing routes ... */}
  <ToastContainer />
</WebSocketProvider>
```

**Update:** `frontend/src/components/Layout.jsx`

Add NotificationBell to header:
```jsx
import NotificationBell from './NotificationBell';

// In header section:
<div className="header-actions">
  <NotificationBell />
  {/* ... other actions ... */}
</div>
```

---

## TASK 3: ADD ROUTES

### 3.1 Update App.jsx

```jsx
const DashboardBuilder = lazy(() => import('./pages/DashboardBuilder'));

<Route path="/dashboard-builder" element={
  <PrivateRoute roles={['admin']}>
    <Layout><DashboardBuilder /></Layout>
  </PrivateRoute>
} />
```

### 3.2 Update Layout Navigation

```javascript
{ path: '/dashboard-builder', icon: '📊', label: 'Dashboard Builder', roles: ['admin'] },
```

---

## COMPLETION CHECKLIST - PART 1

### Dashboard Builder
- [ ] Dashboard service
- [ ] Dashboard routes
- [ ] Widget types (KPI, charts, gauge, alerts)
- [ ] Drag-drop layout (react-grid-layout)
- [ ] Preset templates
- [ ] Share functionality
- [ ] Auto-refresh

### WebSocket Notifications
- [ ] WebSocket manager
- [ ] WebSocket routes
- [ ] WebSocket context (frontend)
- [ ] Notification bell
- [ ] Toast notifications
- [ ] Desktop notifications
- [ ] Reconnection logic

---

## NEW FRONTEND DEPENDENCIES

```bash
npm install react-grid-layout
```

---

**Continue to Part 2 for Bank Reconciliation, Client Portal, and Supplier Portal**
