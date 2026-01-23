"""
BI Store - Data models for reports and metrics
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import uuid4


class ReportStore:
    """In-memory store for reports"""

    def __init__(self):
        self._reports = {}
        self._schedules = {}
        self._metrics = {}
        self._executions = {}
        self._categories = {}
        self._favorites = {}  # user_id -> [report_ids]
        self._recent = {}     # user_id -> [report_ids]

        # Initialize default categories
        self._init_categories()

    def _init_categories(self):
        """Initialize default report categories"""
        default_categories = [
            {"id": "cat_financial", "name": "Financial", "icon": "💰"},
            {"id": "cat_operational", "name": "Operational", "icon": "⚙️"},
            {"id": "cat_sales", "name": "Sales", "icon": "📈"},
            {"id": "cat_inventory", "name": "Inventory", "icon": "📦"},
            {"id": "cat_projects", "name": "Projects", "icon": "📁"},
            {"id": "cat_custom", "name": "Custom", "icon": "🔧"},
        ]
        for cat in default_categories:
            self._categories[cat["id"]] = cat

    # Reports CRUD
    def create_report(self, data: dict) -> dict:
        report_id = data.get("id", str(uuid4()))
        data["id"] = report_id
        self._reports[report_id] = data
        return data

    def get_report(self, report_id: str) -> Optional[dict]:
        return self._reports.get(report_id)

    def update_report(self, report_id: str, updates: dict) -> Optional[dict]:
        if report_id not in self._reports:
            return None
        self._reports[report_id].update(updates)
        return self._reports[report_id]

    def delete_report(self, report_id: str) -> bool:
        if report_id in self._reports:
            del self._reports[report_id]
            return True
        return False

    def list_reports(
        self,
        user_id: str = None,
        category_id: str = None,
        search: str = None
    ) -> List[dict]:
        reports = list(self._reports.values())

        if user_id:
            reports = [
                r for r in reports
                if r.get("created_by") == user_id
                or r.get("is_public")
                or user_id in r.get("shared_with", [])
            ]

        if category_id:
            reports = [r for r in reports if r.get("category_id") == category_id]

        if search:
            search_lower = search.lower()
            reports = [
                r for r in reports
                if search_lower in r.get("name", "").lower()
                or search_lower in r.get("description", "").lower()
            ]

        return sorted(reports, key=lambda x: x.get("updated_at", ""), reverse=True)

    # Schedules CRUD
    def create_schedule(self, data: dict) -> dict:
        schedule_id = data.get("id", str(uuid4()))
        data["id"] = schedule_id
        self._schedules[schedule_id] = data
        return data

    def get_schedule(self, schedule_id: str) -> Optional[dict]:
        return self._schedules.get(schedule_id)

    def update_schedule(self, schedule_id: str, updates: dict) -> Optional[dict]:
        if schedule_id not in self._schedules:
            return None
        self._schedules[schedule_id].update(updates)
        return self._schedules[schedule_id]

    def delete_schedule(self, schedule_id: str) -> bool:
        if schedule_id in self._schedules:
            del self._schedules[schedule_id]
            return True
        return False

    def list_schedules(self, report_id: str = None, is_active: bool = None) -> List[dict]:
        schedules = list(self._schedules.values())

        if report_id:
            schedules = [s for s in schedules if s.get("report_id") == report_id]

        if is_active is not None:
            schedules = [s for s in schedules if s.get("is_active") == is_active]

        return schedules

    # Metrics CRUD
    def create_metric(self, data: dict) -> dict:
        metric_id = data.get("id", str(uuid4()))
        data["id"] = metric_id
        self._metrics[metric_id] = data
        return data

    def get_metric(self, metric_id: str) -> Optional[dict]:
        return self._metrics.get(metric_id)

    def get_metric_by_code(self, code: str) -> Optional[dict]:
        for metric in self._metrics.values():
            if metric.get("code") == code:
                return metric
        return None

    def update_metric(self, metric_id: str, updates: dict) -> Optional[dict]:
        if metric_id not in self._metrics:
            return None
        self._metrics[metric_id].update(updates)
        return self._metrics[metric_id]

    def delete_metric(self, metric_id: str) -> bool:
        if metric_id in self._metrics:
            del self._metrics[metric_id]
            return True
        return False

    def list_metrics(
        self,
        category: str = None,
        certified_only: bool = False
    ) -> List[dict]:
        metrics = list(self._metrics.values())

        if category:
            metrics = [m for m in metrics if m.get("category") == category]

        if certified_only:
            metrics = [m for m in metrics if m.get("certified")]

        return sorted(metrics, key=lambda x: x.get("name", ""))

    # Favorites
    def toggle_favorite(self, user_id: str, report_id: str) -> bool:
        if user_id not in self._favorites:
            self._favorites[user_id] = []

        if report_id in self._favorites[user_id]:
            self._favorites[user_id].remove(report_id)
            return False
        else:
            self._favorites[user_id].append(report_id)
            return True

    def get_favorites(self, user_id: str) -> List[dict]:
        report_ids = self._favorites.get(user_id, [])
        return [self._reports[rid] for rid in report_ids if rid in self._reports]

    # Recent
    def add_recent(self, user_id: str, report_id: str):
        if user_id not in self._recent:
            self._recent[user_id] = []

        # Remove if exists
        if report_id in self._recent[user_id]:
            self._recent[user_id].remove(report_id)

        # Add to front
        self._recent[user_id].insert(0, report_id)

        # Keep only last 10
        self._recent[user_id] = self._recent[user_id][:10]

    def get_recent(self, user_id: str) -> List[dict]:
        report_ids = self._recent.get(user_id, [])
        return [self._reports[rid] for rid in report_ids if rid in self._reports]

    # Categories
    def get_categories(self) -> List[dict]:
        return list(self._categories.values())


# Global instance
bi_store = ReportStore()
