"""
Custom Dashboard Builder Service
"""

from datetime import datetime
from typing import Dict, List, Optional
import secrets
from app.models.store import db
from app.utils.datetime_utils import utc_now


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
            "created_at": utc_now().isoformat(),
            "updated_at": utc_now().isoformat()
        }

        self._dashboards[dashboard_id] = dashboard
        return dashboard

    def update_layout(self, dashboard_id: str, layout: List[dict]) -> Optional[dict]:
        """Update dashboard layout"""
        if dashboard_id not in self._dashboards:
            return None

        dashboard = self._dashboards[dashboard_id]
        dashboard["layout"] = layout
        dashboard["updated_at"] = utc_now().isoformat()
        return dashboard

    def add_widget(self, dashboard_id: str, widget: dict) -> Optional[dict]:
        """Add a widget to dashboard"""
        if dashboard_id not in self._dashboards:
            return None

        dashboard = self._dashboards[dashboard_id]
        widget_id = f"w{len(dashboard['layout']) + 1}"
        dashboard["layout"].append({"widget_id": widget_id, **widget})
        dashboard["updated_at"] = utc_now().isoformat()
        return dashboard

    def remove_widget(self, dashboard_id: str, widget_id: str) -> Optional[dict]:
        """Remove a widget from dashboard"""
        if dashboard_id not in self._dashboards:
            return None

        dashboard = self._dashboards[dashboard_id]
        dashboard["layout"] = [w for w in dashboard["layout"] if w["widget_id"] != widget_id]
        dashboard["updated_at"] = utc_now().isoformat()
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

        dashboard["updated_at"] = utc_now().isoformat()
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

        if metric == "cash_in":
            value = sum(t.get("amount", 0) for t in transactions if t.get("type") == "income")
            return {"value": value, "format": "currency", "trend": 3.5}

        if metric == "cash_out":
            value = sum(t.get("amount", 0) for t in transactions if t.get("type") == "expense")
            return {"value": value, "format": "currency", "trend": -1.2}

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

        if metric == "stock_by_category":
            materials = db.materials.find_all()
            categories = db.categories.find_all()
            cat_names = {c["id"]: c["name"] for c in categories}

            by_cat = {}
            for m in materials:
                cat_id = m.get("category_id", "uncategorized")
                cat_name = cat_names.get(cat_id, "Other")
                by_cat[cat_name] = by_cat.get(cat_name, 0) + m.get("quantity", 0)

            labels = list(by_cat.keys())
            values = list(by_cat.values())
            return {"labels": labels, "datasets": [{"label": "Stock", "data": values}]}

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
            today = utc_now().date().isoformat()
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
