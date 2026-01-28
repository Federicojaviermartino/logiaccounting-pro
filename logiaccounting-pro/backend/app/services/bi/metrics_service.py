"""
Metrics Service
Semantic layer for business metrics definitions
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4

from app.utils.datetime_utils import utc_now

from app.models.bi_store import bi_store


class MetricsService:
    """
    Service for managing the metrics catalog (semantic layer)
    Provides consistent metric definitions across reports
    """

    SYSTEM_METRICS = {
        "total_revenue": {
            "id": "sys_total_revenue",
            "name": "Total Revenue",
            "code": "total_revenue",
            "description": "Sum of all invoice totals",
            "formula": "SUM(invoices.total)",
            "aggregation": "sum",
            "base_table": "invoices",
            "base_field": "total",
            "data_type": "currency",
            "format": "${value:,.2f}",
            "category": "financial",
            "is_system": True,
            "certified": True,
        },
        "total_expenses": {
            "id": "sys_total_expenses",
            "name": "Total Expenses",
            "code": "total_expenses",
            "description": "Sum of all expense transactions",
            "formula": "SUM(transactions.amount) WHERE type='expense'",
            "aggregation": "sum",
            "base_table": "transactions",
            "base_field": "amount",
            "filters": [{"field": "type", "operator": "eq", "value": "expense"}],
            "data_type": "currency",
            "format": "${value:,.2f}",
            "category": "financial",
            "is_system": True,
            "certified": True,
        },
        "gross_profit": {
            "id": "sys_gross_profit",
            "name": "Gross Profit",
            "code": "gross_profit",
            "description": "Revenue minus expenses",
            "formula": "total_revenue - total_expenses",
            "depends_on": ["total_revenue", "total_expenses"],
            "data_type": "currency",
            "format": "${value:,.2f}",
            "category": "financial",
            "is_system": True,
            "certified": True,
        },
        "profit_margin": {
            "id": "sys_profit_margin",
            "name": "Profit Margin",
            "code": "profit_margin",
            "description": "Profit as percentage of revenue",
            "formula": "(gross_profit / total_revenue) * 100",
            "depends_on": ["gross_profit", "total_revenue"],
            "data_type": "percent",
            "format": "{value:.1f}%",
            "category": "financial",
            "is_system": True,
            "certified": True,
        },
        "invoice_count": {
            "id": "sys_invoice_count",
            "name": "Invoice Count",
            "code": "invoice_count",
            "description": "Total number of invoices",
            "formula": "COUNT(invoices.id)",
            "aggregation": "count",
            "base_table": "invoices",
            "base_field": "id",
            "data_type": "integer",
            "format": "{value:,}",
            "category": "operational",
            "is_system": True,
            "certified": True,
        },
        "avg_invoice_value": {
            "id": "sys_avg_invoice_value",
            "name": "Average Invoice Value",
            "code": "avg_invoice_value",
            "description": "Average value per invoice",
            "formula": "AVG(invoices.total)",
            "aggregation": "avg",
            "base_table": "invoices",
            "base_field": "total",
            "data_type": "currency",
            "format": "${value:,.2f}",
            "category": "financial",
            "is_system": True,
            "certified": True,
        },
        "overdue_amount": {
            "id": "sys_overdue_amount",
            "name": "Overdue Amount",
            "code": "overdue_amount",
            "description": "Total amount from overdue invoices",
            "formula": "SUM(invoices.total) WHERE status='overdue'",
            "aggregation": "sum",
            "base_table": "invoices",
            "base_field": "total",
            "filters": [{"field": "status", "operator": "eq", "value": "overdue"}],
            "data_type": "currency",
            "format": "${value:,.2f}",
            "category": "financial",
            "is_system": True,
            "certified": True,
        },
        "collection_rate": {
            "id": "sys_collection_rate",
            "name": "Collection Rate",
            "code": "collection_rate",
            "description": "Percentage of invoices paid on time",
            "formula": "(paid_invoices / total_invoices) * 100",
            "data_type": "percent",
            "format": "{value:.1f}%",
            "category": "financial",
            "is_system": True,
            "certified": True,
        },
        "inventory_value": {
            "id": "sys_inventory_value",
            "name": "Inventory Value",
            "code": "inventory_value",
            "description": "Total value of inventory",
            "formula": "SUM(inventory.quantity * inventory.unit_cost)",
            "base_table": "inventory",
            "data_type": "currency",
            "format": "${value:,.2f}",
            "category": "inventory",
            "is_system": True,
            "certified": True,
        },
        "low_stock_items": {
            "id": "sys_low_stock_items",
            "name": "Low Stock Items",
            "code": "low_stock_items",
            "description": "Count of items below minimum stock",
            "formula": "COUNT(inventory.id) WHERE quantity < min_stock",
            "aggregation": "count",
            "base_table": "inventory",
            "base_field": "id",
            "filters": [{"field": "quantity", "operator": "lt", "field_compare": "min_stock"}],
            "data_type": "integer",
            "format": "{value:,}",
            "category": "inventory",
            "is_system": True,
            "certified": True,
        },
        "active_projects": {
            "id": "sys_active_projects",
            "name": "Active Projects",
            "code": "active_projects",
            "description": "Number of active projects",
            "formula": "COUNT(projects.id) WHERE status='active'",
            "aggregation": "count",
            "base_table": "projects",
            "base_field": "id",
            "filters": [{"field": "status", "operator": "eq", "value": "active"}],
            "data_type": "integer",
            "format": "{value:,}",
            "category": "projects",
            "is_system": True,
            "certified": True,
        },
        "project_budget_utilization": {
            "id": "sys_budget_utilization",
            "name": "Budget Utilization",
            "code": "budget_utilization",
            "description": "Percentage of budget spent across projects",
            "formula": "(SUM(projects.spent) / SUM(projects.budget)) * 100",
            "data_type": "percent",
            "format": "{value:.1f}%",
            "category": "projects",
            "is_system": True,
            "certified": True,
        },
    }

    def __init__(self):
        self._ensure_system_metrics()

    def _ensure_system_metrics(self):
        """Ensure system metrics exist in store"""
        for code, metric in self.SYSTEM_METRICS.items():
            existing = bi_store.get_metric_by_code(code)
            if not existing:
                bi_store.create_metric(metric)

    def create_metric(
        self,
        name: str,
        code: str,
        description: str,
        formula: str,
        data_type: str,
        category: str,
        user_id: str,
        **kwargs
    ) -> dict:
        """Create a custom metric"""
        existing = bi_store.get_metric_by_code(code)
        if existing:
            raise ValueError(f"Metric code already exists: {code}")

        metric = {
            "id": str(uuid4()),
            "name": name,
            "code": code,
            "description": description,
            "formula": formula,
            "data_type": data_type,
            "category": category,
            "format": kwargs.get("format", self._default_format(data_type)),
            "aggregation": kwargs.get("aggregation"),
            "base_table": kwargs.get("base_table"),
            "base_field": kwargs.get("base_field"),
            "filters": kwargs.get("filters", []),
            "depends_on": kwargs.get("depends_on", []),
            "created_by": user_id,
            "created_at": utc_now().isoformat(),
            "updated_at": utc_now().isoformat(),
            "is_system": False,
            "certified": False,
            "certified_by": None,
            "certified_at": None,
        }

        return bi_store.create_metric(metric)

    def update_metric(self, metric_id: str, user_id: str, **updates) -> dict:
        """Update a custom metric"""
        metric = bi_store.get_metric(metric_id)
        if not metric:
            raise ValueError(f"Metric not found: {metric_id}")

        if metric.get("is_system"):
            raise ValueError("Cannot modify system metrics")

        updates["updated_at"] = utc_now().isoformat()

        return bi_store.update_metric(metric_id, updates)

    def delete_metric(self, metric_id: str, user_id: str):
        """Delete a custom metric"""
        metric = bi_store.get_metric(metric_id)
        if not metric:
            raise ValueError(f"Metric not found: {metric_id}")

        if metric.get("is_system"):
            raise ValueError("Cannot delete system metrics")

        bi_store.delete_metric(metric_id)

    def certify_metric(self, metric_id: str, user_id: str) -> dict:
        """Certify a metric for organization-wide use"""
        metric = bi_store.get_metric(metric_id)
        if not metric:
            raise ValueError(f"Metric not found: {metric_id}")

        return bi_store.update_metric(metric_id, {
            "certified": True,
            "certified_by": user_id,
            "certified_at": utc_now().isoformat(),
        })

    def list_metrics(
        self,
        category: Optional[str] = None,
        certified_only: bool = False,
        search: Optional[str] = None
    ) -> List[dict]:
        """List metrics with filters"""
        metrics = bi_store.list_metrics(category=category, certified_only=certified_only)

        if search:
            search_lower = search.lower()
            metrics = [
                m for m in metrics
                if search_lower in m["name"].lower()
                or search_lower in m.get("description", "").lower()
                or search_lower in m["code"].lower()
            ]

        return metrics

    def get_metric(self, metric_id: str) -> dict:
        """Get a single metric by ID"""
        return bi_store.get_metric(metric_id)

    def get_metric_by_code(self, code: str) -> dict:
        """Get a metric by its code"""
        return bi_store.get_metric_by_code(code)

    def calculate_metric(
        self,
        metric_id: str,
        filters: Optional[Dict[str, Any]] = None,
        date_range: Optional[Dict[str, str]] = None
    ) -> Any:
        """Calculate metric value"""
        metric = bi_store.get_metric(metric_id)
        if not metric:
            raise ValueError(f"Metric not found: {metric_id}")

        # Return sample value for demo
        sample_values = {
            "currency": 125000.00,
            "percent": 23.5,
            "integer": 156,
            "decimal": 1234.56,
        }
        return sample_values.get(metric.get("data_type"), 0)

    def _default_format(self, data_type: str) -> str:
        """Get default format for data type"""
        formats = {
            "currency": "${value:,.2f}",
            "percent": "{value:.1f}%",
            "integer": "{value:,}",
            "decimal": "{value:,.2f}",
        }
        return formats.get(data_type, "{value}")

    def get_categories(self) -> List[str]:
        """Get all metric categories"""
        metrics = bi_store.list_metrics()
        categories = set(m.get("category", "other") for m in metrics)
        return sorted(list(categories))
