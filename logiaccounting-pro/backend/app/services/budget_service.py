"""
Budget Management Service
Track and manage budgets by category, project, or department
"""

from datetime import datetime
from typing import Dict, List, Optional
from app.models.store import db
from app.utils.datetime_utils import utc_now


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
        period: str,
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
            "created_at": utc_now().isoformat()
        }

        budget["spent"] = self._calculate_spent(budget)

        self._budgets[budget_id] = budget
        return budget

    def _calculate_spent(self, budget: dict) -> float:
        """Calculate total spent against a budget"""
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

        if budget["project_id"]:
            filtered = [t for t in filtered if t.get("project_id") == budget["project_id"]]

        return sum(t.get("amount", 0) for t in filtered)

    def _get_period_end(self, start_date: str, period: str) -> str:
        """Get the end date for a budget period"""
        try:
            start = datetime.fromisoformat(start_date)
        except:
            start = utc_now()

        if period == "monthly":
            month = start.month + 1
            year = start.year
            if month > 12:
                month = 1
                year += 1
            end = start.replace(year=year, month=month, day=1) - timedelta(days=1)
        elif period == "quarterly":
            month = start.month + 3
            year = start.year
            while month > 12:
                month -= 12
                year += 1
            end = start.replace(year=year, month=month, day=1) - timedelta(days=1)
        elif period == "yearly":
            end = start.replace(year=start.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month = start.month + 1
            year = start.year
            if month > 12:
                month = 1
                year += 1
            end = start.replace(year=year, month=month, day=1) - timedelta(days=1)

        return end.strftime("%Y-%m-%d")

    def update_budget(self, budget_id: str, updates: dict) -> Optional[dict]:
        """Update a budget"""
        if budget_id not in self._budgets:
            return None

        budget = self._budgets[budget_id]

        for key, value in updates.items():
            if key in budget and key not in ["id", "created_at", "created_by", "spent"]:
                budget[key] = value

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

        by_period = {}
        for t in filtered:
            period_key = t.get("date", "")[:7]
            by_period[period_key] = by_period.get(period_key, 0) + t.get("amount", 0)

        return {
            "budget": budget,
            "variance": variance,
            "variance_percentage": variance_percentage,
            "status": "over" if variance < 0 else "under",
            "spending_by_period": by_period,
            "period_end": period_end
        }


from datetime import timedelta
budget_service = BudgetService()
