"""
Report Scheduler Service
Automated report generation and distribution
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import uuid4
import asyncio

from app.models.bi_store import bi_store


class SchedulerService:
    """
    Service for scheduling automated report generation and distribution
    """

    def __init__(self):
        self._running_jobs = {}

    def create_schedule(
        self,
        report_id: str,
        name: str,
        cron_expression: str,
        format: str,
        recipients: List[str],
        parameters: Optional[Dict[str, Any]] = None,
        user_id: str = None,
        **kwargs
    ) -> dict:
        """Create a new report schedule"""
        # Validate cron expression
        if not self._validate_cron(cron_expression):
            raise ValueError("Invalid cron expression")

        # Validate report exists
        report = bi_store.get_report(report_id)
        if not report:
            raise ValueError(f"Report not found: {report_id}")

        schedule = {
            "id": str(uuid4()),
            "report_id": report_id,
            "name": name,
            "cron_expression": cron_expression,
            "format": format,
            "recipients": recipients,
            "parameters": parameters or {},
            "created_by": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "is_active": True,
            "last_run": None,
            "next_run": self._calculate_next_run(cron_expression),
            "run_count": 0,
            "failure_count": 0,
            "last_error": None,
            "subject_template": kwargs.get("subject_template", "Report: {report_name}"),
            "body_template": kwargs.get("body_template", "Please find attached your scheduled report."),
            "include_inline": kwargs.get("include_inline", False),
            "cc_recipients": kwargs.get("cc_recipients", []),
            "max_retries": kwargs.get("max_retries", 3),
            "retry_delay_minutes": kwargs.get("retry_delay_minutes", 5),
        }

        return bi_store.create_schedule(schedule)

    def update_schedule(
        self,
        schedule_id: str,
        user_id: str,
        **updates
    ) -> dict:
        """Update an existing schedule"""
        schedule = bi_store.get_schedule(schedule_id)
        if not schedule:
            raise ValueError(f"Schedule not found: {schedule_id}")

        # Recalculate next run if cron changed
        if "cron_expression" in updates:
            if not self._validate_cron(updates["cron_expression"]):
                raise ValueError("Invalid cron expression")
            updates["next_run"] = self._calculate_next_run(updates["cron_expression"])

        updates["updated_at"] = datetime.utcnow().isoformat()

        return bi_store.update_schedule(schedule_id, updates)

    def delete_schedule(self, schedule_id: str, user_id: str):
        """Delete a schedule"""
        schedule = bi_store.get_schedule(schedule_id)
        if not schedule:
            raise ValueError(f"Schedule not found: {schedule_id}")

        bi_store.delete_schedule(schedule_id)

    def list_schedules(
        self,
        report_id: Optional[str] = None,
        user_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[dict]:
        """List schedules with optional filters"""
        return bi_store.list_schedules(report_id=report_id, is_active=is_active)

    def get_due_schedules(self) -> List[dict]:
        """Get schedules that are due to run"""
        now = datetime.utcnow()
        all_schedules = bi_store.list_schedules(is_active=True)

        due = []
        for schedule in all_schedules:
            next_run = datetime.fromisoformat(schedule["next_run"])
            if next_run <= now:
                due.append(schedule)

        return due

    async def execute_schedule(self, schedule_id: str) -> dict:
        """Execute a scheduled report"""
        schedule = bi_store.get_schedule(schedule_id)
        if not schedule:
            raise ValueError(f"Schedule not found: {schedule_id}")

        execution = {
            "id": str(uuid4()),
            "schedule_id": schedule_id,
            "report_id": schedule["report_id"],
            "started_at": datetime.utcnow().isoformat(),
            "status": "running",
            "recipients_count": len(schedule["recipients"]),
        }

        try:
            # Update schedule
            bi_store.update_schedule(schedule_id, {
                "last_run": datetime.utcnow().isoformat(),
                "next_run": self._calculate_next_run(schedule["cron_expression"]),
                "run_count": schedule["run_count"] + 1,
                "last_error": None,
            })

            execution["status"] = "completed"
            execution["completed_at"] = datetime.utcnow().isoformat()

        except Exception as e:
            # Handle failure
            bi_store.update_schedule(schedule_id, {
                "last_run": datetime.utcnow().isoformat(),
                "failure_count": schedule["failure_count"] + 1,
                "last_error": str(e),
            })

            execution["status"] = "failed"
            execution["error"] = str(e)
            execution["completed_at"] = datetime.utcnow().isoformat()

        return execution

    def _validate_cron(self, expression: str) -> bool:
        """Validate cron expression"""
        try:
            parts = expression.split()
            return len(parts) == 5
        except:
            return False

    def _calculate_next_run(self, cron_expression: str) -> str:
        """Calculate next run time from cron expression"""
        # Simplified - returns 1 hour from now
        return (datetime.utcnow() + timedelta(hours=1)).isoformat()

    def _get_content_type(self, format: str) -> str:
        """Get MIME type for format"""
        types = {
            "pdf": "application/pdf",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "csv": "text/csv",
            "html": "text/html",
        }
        return types.get(format, "application/octet-stream")


class SchedulerRunner:
    """
    Background runner for scheduled reports
    """

    def __init__(self):
        self.scheduler_service = SchedulerService()
        self._is_running = False

    async def start(self):
        """Start the scheduler loop"""
        self._is_running = True

        while self._is_running:
            try:
                # Check for due schedules
                due_schedules = self.scheduler_service.get_due_schedules()

                # Execute each due schedule
                for schedule in due_schedules:
                    asyncio.create_task(
                        self.scheduler_service.execute_schedule(schedule["id"])
                    )

                # Wait before next check (1 minute)
                await asyncio.sleep(60)

            except Exception as e:
                print(f"Scheduler error: {e}")
                await asyncio.sleep(60)

    def stop(self):
        """Stop the scheduler loop"""
        self._is_running = False
