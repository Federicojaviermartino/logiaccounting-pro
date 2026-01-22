"""
Delay action executor.
Pauses workflow execution for a specified duration.
"""
from typing import Dict, Any
import asyncio
import logging

from app.workflows.actions import ActionExecutor


logger = logging.getLogger(__name__)


class DelayActionExecutor(ActionExecutor):
    """Executes delay/wait actions."""

    async def execute(
        self,
        config: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Delay execution.

        Config:
            duration: Number of time units to wait
            unit: Time unit (seconds, minutes, hours, days)
        """
        duration = config.get("duration", 0)
        unit = config.get("unit", "seconds")

        multipliers = {
            "seconds": 1,
            "minutes": 60,
            "hours": 3600,
            "days": 86400
        }

        wait_seconds = duration * multipliers.get(unit, 1)

        if wait_seconds > 300:
            logger.info(f"Long delay requested: {duration} {unit}")
            return {
                "delayed": True,
                "seconds": wait_seconds,
                "long_delay": True,
                "message": f"Long delay of {duration} {unit} requested"
            }

        await asyncio.sleep(wait_seconds)

        logger.info(f"Completed delay of {duration} {unit}")

        return {
            "delayed": True,
            "seconds": wait_seconds
        }
