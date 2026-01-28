"""
Scheduled Reports Service
Automate report generation and delivery
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.models.store import db
from app.utils.datetime_utils import utc_now


def generate_report_data(report_type: str, columns: list, filters: dict) -> dict:
    """Generate report data based on type"""
    if report_type == "financial":
        transactions = db.transactions.find_all()
        return {"data": transactions, "type": "financial"}
    elif report_type == "inventory":
        materials = db.materials.find_all()
        return {"data": materials, "type": "inventory"}
    elif report_type == "payments":
        payments = db.payments.find_all()
        return {"data": payments, "type": "payments"}
    elif report_type == "projects":
        projects = db.projects.find_all()
        return {"data": projects, "type": "projects"}
    return {"data": [], "type": report_type}


class ReportSchedulerService:
    """Manages scheduled report generation"""

    _instance = None
    _schedules: Dict[str, dict] = {}
    _history: List[dict] = []
    _counter = 0

    FREQUENCIES = {
        "daily": {"days": 1},
        "weekly": {"days": 7},
        "biweekly": {"days": 14},
        "monthly": {"days": 30},
        "quarterly": {"days": 90}
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._schedules = {}
            cls._history = []
            cls._counter = 0
        return cls._instance

    def create_schedule(
        self,
        name: str,
        report_type: str,
        report_config: dict,
        frequency: str,
        time_of_day: str,
        day_of_week: Optional[int] = None,
        day_of_month: Optional[int] = None,
        recipients: List[str] = None,
        format: str = "pdf",
        created_by: str = None
    ) -> dict:
        """Create a new report schedule"""
        self._counter += 1
        schedule_id = f"SCH-{self._counter:04d}"

        # Calculate next run
        next_run = self._calculate_next_run(frequency, time_of_day, day_of_week, day_of_month)

        schedule = {
            "id": schedule_id,
            "name": name,
            "report_type": report_type,
            "report_config": report_config,
            "frequency": frequency,
            "time_of_day": time_of_day,
            "day_of_week": day_of_week,
            "day_of_month": day_of_month,
            "recipients": recipients or [],
            "format": format,
            "active": True,
            "last_run": None,
            "next_run": next_run,
            "run_count": 0,
            "created_by": created_by,
            "created_at": utc_now().isoformat()
        }

        self._schedules[schedule_id] = schedule
        return schedule

    def _calculate_next_run(
        self,
        frequency: str,
        time_of_day: str,
        day_of_week: Optional[int] = None,
        day_of_month: Optional[int] = None
    ) -> str:
        """Calculate next run datetime"""
        now = utc_now()
        hour, minute = map(int, time_of_day.split(':'))

        # Start with today at the specified time
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # If time has passed today, start from tomorrow
        if next_run <= now:
            next_run += timedelta(days=1)

        # Adjust for weekly
        if frequency == "weekly" and day_of_week is not None:
            while next_run.weekday() != day_of_week:
                next_run += timedelta(days=1)

        # Adjust for monthly
        if frequency in ["monthly", "quarterly"] and day_of_month is not None:
            try:
                next_run = next_run.replace(day=min(day_of_month, 28))
                if next_run <= now:
                    if frequency == "monthly":
                        if next_run.month == 12:
                            next_run = next_run.replace(year=next_run.year + 1, month=1)
                        else:
                            next_run = next_run.replace(month=next_run.month + 1)
                    else:  # quarterly
                        next_run = next_run.replace(month=((next_run.month - 1 + 3) % 12) + 1)
            except ValueError:
                pass

        return next_run.isoformat()

    def update_schedule(self, schedule_id: str, updates: dict) -> Optional[dict]:
        """Update a schedule"""
        if schedule_id not in self._schedules:
            return None

        schedule = self._schedules[schedule_id]

        for key, value in updates.items():
            if key in schedule and key not in ["id", "created_at", "created_by"]:
                schedule[key] = value

        # Recalculate next run if frequency changed
        if any(k in updates for k in ["frequency", "time_of_day", "day_of_week", "day_of_month"]):
            schedule["next_run"] = self._calculate_next_run(
                schedule["frequency"],
                schedule["time_of_day"],
                schedule.get("day_of_week"),
                schedule.get("day_of_month")
            )

        return schedule

    def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule"""
        if schedule_id in self._schedules:
            del self._schedules[schedule_id]
            return True
        return False

    def toggle_schedule(self, schedule_id: str) -> Optional[dict]:
        """Toggle schedule active status"""
        if schedule_id not in self._schedules:
            return None

        schedule = self._schedules[schedule_id]
        schedule["active"] = not schedule["active"]
        return schedule

    def run_schedule(self, schedule_id: str) -> dict:
        """Manually run a scheduled report"""
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            return {"error": "Schedule not found"}

        # Generate report
        report_data = generate_report_data(
            report_type=schedule["report_type"],
            columns=schedule["report_config"].get("columns", []),
            filters=schedule["report_config"].get("filters", {})
        )

        # Record in history
        run_record = {
            "schedule_id": schedule_id,
            "schedule_name": schedule["name"],
            "run_at": utc_now().isoformat(),
            "status": "success",
            "recipients": schedule["recipients"],
            "format": schedule["format"],
            "row_count": len(report_data.get("data", []))
        }

        self._history.append(run_record)

        # Update schedule
        schedule["last_run"] = utc_now().isoformat()
        schedule["run_count"] += 1
        schedule["next_run"] = self._calculate_next_run(
            schedule["frequency"],
            schedule["time_of_day"],
            schedule.get("day_of_week"),
            schedule.get("day_of_month")
        )

        return {
            "success": True,
            "run_record": run_record,
            "data_preview": report_data.get("data", [])[:5]
        }

    def get_schedule(self, schedule_id: str) -> Optional[dict]:
        """Get a specific schedule"""
        return self._schedules.get(schedule_id)

    def list_schedules(self, active_only: bool = False) -> List[dict]:
        """List all schedules"""
        schedules = list(self._schedules.values())
        if active_only:
            schedules = [s for s in schedules if s["active"]]
        return sorted(schedules, key=lambda s: s["next_run"] or "")

    def get_due_schedules(self) -> List[dict]:
        """Get schedules that are due to run"""
        now = utc_now().isoformat()
        return [
            s for s in self._schedules.values()
            if s["active"] and s["next_run"] and s["next_run"] <= now
        ]

    def get_history(self, schedule_id: Optional[str] = None, limit: int = 50) -> List[dict]:
        """Get run history"""
        history = self._history
        if schedule_id:
            history = [h for h in history if h["schedule_id"] == schedule_id]
        return sorted(history, key=lambda h: h["run_at"], reverse=True)[:limit]


report_scheduler = ReportSchedulerService()
