"""
Workflow Scheduler
Cron and interval-based workflow scheduling
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import asyncio
import logging
from croniter import croniter

from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


class ScheduledJob:
    """Represents a scheduled workflow job."""

    def __init__(self, workflow_id: str, schedule_type: str, schedule_config: Dict):
        self.workflow_id = workflow_id
        self.schedule_type = schedule_type  # "cron", "interval", "daily", "weekly"
        self.schedule_config = schedule_config
        self.enabled = True
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.run_count = 0
        self.error_count = 0
        self.last_error: Optional[str] = None

        # Calculate next run time
        self._calculate_next_run()

    def _calculate_next_run(self):
        """Calculate the next run time."""
        now = utc_now()

        if self.schedule_type == "cron":
            cron_expr = self.schedule_config.get("cron", "0 * * * *")
            try:
                cron = croniter(cron_expr, now)
                self.next_run = cron.get_next(datetime)
            except Exception as e:
                logger.error(f"Invalid cron expression: {cron_expr} - {e}")
                self.next_run = None

        elif self.schedule_type == "interval":
            interval_seconds = self.schedule_config.get("interval_seconds", 3600)
            self.next_run = now + timedelta(seconds=interval_seconds)

        elif self.schedule_type == "daily":
            time_str = self.schedule_config.get("time", "09:00")
            hour, minute = map(int, time_str.split(":"))
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            self.next_run = next_run

        elif self.schedule_type == "weekly":
            day = self.schedule_config.get("day", 0)  # 0 = Monday
            time_str = self.schedule_config.get("time", "09:00")
            hour, minute = map(int, time_str.split(":"))

            days_ahead = day - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7

            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
            self.next_run = next_run

    def mark_executed(self, success: bool = True, error: str = None):
        """Mark job as executed and calculate next run."""
        self.last_run = utc_now()
        self.run_count += 1

        if not success:
            self.error_count += 1
            self.last_error = error

        self._calculate_next_run()

    def is_due(self) -> bool:
        """Check if job is due for execution."""
        if not self.enabled or not self.next_run:
            return False
        return utc_now() >= self.next_run

    def to_dict(self) -> Dict:
        return {
            "workflow_id": self.workflow_id,
            "schedule_type": self.schedule_type,
            "schedule_config": self.schedule_config,
            "enabled": self.enabled,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "run_count": self.run_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
        }


class WorkflowScheduler:
    """Manages scheduled workflow execution."""

    def __init__(self):
        self._jobs: Dict[str, ScheduledJob] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._check_interval = 60  # seconds
        self._on_execute: Optional[Callable] = None

    def set_executor(self, executor: Callable):
        """Set the workflow executor callback."""
        self._on_execute = executor

    def add_job(self, workflow_id: str, schedule_type: str, schedule_config: Dict) -> ScheduledJob:
        """Add a scheduled job."""
        job = ScheduledJob(workflow_id, schedule_type, schedule_config)
        self._jobs[workflow_id] = job
        logger.info(f"Scheduled job added: {workflow_id} ({schedule_type})")
        return job

    def remove_job(self, workflow_id: str) -> bool:
        """Remove a scheduled job."""
        if workflow_id in self._jobs:
            del self._jobs[workflow_id]
            logger.info(f"Scheduled job removed: {workflow_id}")
            return True
        return False

    def update_job(self, workflow_id: str, schedule_type: str = None, schedule_config: Dict = None) -> Optional[ScheduledJob]:
        """Update a scheduled job."""
        job = self._jobs.get(workflow_id)
        if not job:
            return None

        if schedule_type:
            job.schedule_type = schedule_type
        if schedule_config:
            job.schedule_config = schedule_config

        job._calculate_next_run()
        return job

    def enable_job(self, workflow_id: str) -> bool:
        """Enable a scheduled job."""
        job = self._jobs.get(workflow_id)
        if job:
            job.enabled = True
            job._calculate_next_run()
            return True
        return False

    def disable_job(self, workflow_id: str) -> bool:
        """Disable a scheduled job."""
        job = self._jobs.get(workflow_id)
        if job:
            job.enabled = False
            return True
        return False

    def get_job(self, workflow_id: str) -> Optional[ScheduledJob]:
        """Get a scheduled job."""
        return self._jobs.get(workflow_id)

    def get_all_jobs(self) -> List[ScheduledJob]:
        """Get all scheduled jobs."""
        return list(self._jobs.values())

    def get_due_jobs(self) -> List[ScheduledJob]:
        """Get jobs that are due for execution."""
        return [job for job in self._jobs.values() if job.is_due()]

    async def start(self):
        """Start the scheduler."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Workflow scheduler started")

    async def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Workflow scheduler stopped")

    async def _run_loop(self):
        """Main scheduler loop."""
        while self._running:
            try:
                await self._check_and_execute()
                await asyncio.sleep(self._check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(self._check_interval)

    async def _check_and_execute(self):
        """Check for due jobs and execute them."""
        due_jobs = self.get_due_jobs()

        for job in due_jobs:
            if self._on_execute:
                try:
                    logger.info(f"Executing scheduled workflow: {job.workflow_id}")
                    await self._on_execute(job.workflow_id, {
                        "trigger_type": "schedule",
                        "schedule_type": job.schedule_type,
                        "scheduled_time": job.next_run.isoformat() if job.next_run else None,
                    })
                    job.mark_executed(success=True)
                except Exception as e:
                    logger.error(f"Scheduled execution failed: {job.workflow_id} - {e}")
                    job.mark_executed(success=False, error=str(e))

    async def run_now(self, workflow_id: str) -> bool:
        """Manually trigger a scheduled workflow."""
        job = self._jobs.get(workflow_id)
        if not job or not self._on_execute:
            return False

        try:
            await self._on_execute(workflow_id, {
                "trigger_type": "manual",
                "triggered_at": utc_now().isoformat(),
            })
            return True
        except Exception as e:
            logger.error(f"Manual execution failed: {workflow_id} - {e}")
            return False

    def get_schedule_preview(self, schedule_type: str, schedule_config: Dict, count: int = 5) -> List[datetime]:
        """Preview upcoming execution times."""
        times = []
        temp_job = ScheduledJob("preview", schedule_type, schedule_config)

        for _ in range(count):
            if temp_job.next_run:
                times.append(temp_job.next_run)
                temp_job.last_run = temp_job.next_run
                temp_job._calculate_next_run()
            else:
                break

        return times


# Global scheduler instance
workflow_scheduler = WorkflowScheduler()


class CronExpressionHelper:
    """Helper for building cron expressions."""

    PRESETS = {
        "every_minute": "* * * * *",
        "every_5_minutes": "*/5 * * * *",
        "every_15_minutes": "*/15 * * * *",
        "every_30_minutes": "*/30 * * * *",
        "every_hour": "0 * * * *",
        "every_2_hours": "0 */2 * * *",
        "every_6_hours": "0 */6 * * *",
        "every_12_hours": "0 */12 * * *",
        "daily_midnight": "0 0 * * *",
        "daily_9am": "0 9 * * *",
        "daily_6pm": "0 18 * * *",
        "weekly_monday": "0 9 * * 1",
        "weekly_friday": "0 17 * * 5",
        "monthly_first": "0 9 1 * *",
        "monthly_last": "0 9 L * *",
        "quarterly": "0 9 1 1,4,7,10 *",
    }

    @classmethod
    def get_preset(cls, name: str) -> Optional[str]:
        """Get a preset cron expression."""
        return cls.PRESETS.get(name)

    @classmethod
    def list_presets(cls) -> List[Dict]:
        """List available presets."""
        return [
            {"name": name, "cron": cron, "description": cls._describe(cron)}
            for name, cron in cls.PRESETS.items()
        ]

    @classmethod
    def _describe(cls, cron: str) -> str:
        """Generate human-readable description."""
        descriptions = {
            "* * * * *": "Every minute",
            "*/5 * * * *": "Every 5 minutes",
            "*/15 * * * *": "Every 15 minutes",
            "*/30 * * * *": "Every 30 minutes",
            "0 * * * *": "Every hour",
            "0 */2 * * *": "Every 2 hours",
            "0 */6 * * *": "Every 6 hours",
            "0 */12 * * *": "Every 12 hours",
            "0 0 * * *": "Daily at midnight",
            "0 9 * * *": "Daily at 9:00 AM",
            "0 18 * * *": "Daily at 6:00 PM",
            "0 9 * * 1": "Weekly on Monday at 9:00 AM",
            "0 17 * * 5": "Weekly on Friday at 5:00 PM",
            "0 9 1 * *": "Monthly on the 1st at 9:00 AM",
            "0 9 L * *": "Monthly on the last day at 9:00 AM",
            "0 9 1 1,4,7,10 *": "Quarterly on the 1st at 9:00 AM",
        }
        return descriptions.get(cron, cron)

    @classmethod
    def build(cls, minute: str = "*", hour: str = "*", day: str = "*", month: str = "*", weekday: str = "*") -> str:
        """Build a cron expression from components."""
        return f"{minute} {hour} {day} {month} {weekday}"

    @classmethod
    def validate(cls, cron: str) -> tuple[bool, str]:
        """Validate a cron expression."""
        try:
            croniter(cron)
            return True, "Valid cron expression"
        except Exception as e:
            return False, str(e)

    @classmethod
    def get_next_runs(cls, cron: str, count: int = 5) -> List[datetime]:
        """Get next N run times for a cron expression."""
        try:
            now = utc_now()
            cron_iter = croniter(cron, now)
            return [cron_iter.get_next(datetime) for _ in range(count)]
        except Exception:
            return []
