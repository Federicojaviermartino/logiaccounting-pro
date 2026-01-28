"""
Approval request action executor.
Creates approval requests and pauses workflow until resolved.
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging
import re
import uuid

from app.utils.datetime_utils import utc_now
from app.workflows.actions import ActionExecutor


logger = logging.getLogger(__name__)


class ApprovalActionExecutor(ActionExecutor):
    """Creates approval requests."""

    async def execute(
        self,
        config: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create an approval request.

        Config:
            approvers: List of user IDs
            approver_role: Role that can approve
            title: Approval title
            description: Approval description
            timeout_hours: Hours until escalation/expiry
            escalation_email: Email for escalation
            require_all: Require all approvers (default: False - any one)
        """
        approvers = config.get("approvers", [])
        approver_role = config.get("approver_role")

        if not approvers and approver_role:
            approvers = await self._get_users_by_role(approver_role)

        if not approvers:
            return {
                "created": False,
                "error": "No approvers specified"
            }

        timeout_hours = config.get("timeout_hours", 24)

        approval = {
            "id": f"approval_{uuid.uuid4().hex[:12]}",
            "status": "pending",
            "title": self._interpolate(config.get("title", "Approval Required"), variables),
            "description": self._interpolate(config.get("description", ""), variables),
            "approvers": approvers,
            "approver_role": approver_role,
            "require_all": config.get("require_all", False),
            "responses": {},
            "timeout_hours": timeout_hours,
            "expires_at": (utc_now() + timedelta(hours=timeout_hours)).isoformat(),
            "escalation_email": config.get("escalation_email"),
            "workflow_execution_id": variables.get("execution_id"),
            "entity_type": variables.get("entity"),
            "entity_id": variables.get("entity_id"),
            "created_at": utc_now().isoformat()
        }

        await self._save_approval(approval)

        await self._notify_approvers(approval, config)

        logger.info(f"Created approval request {approval['id']}")

        return {
            "created": True,
            "approval_id": approval["id"],
            "approvers": approvers,
            "waiting": True
        }

    async def _get_users_by_role(self, role: str) -> List[str]:
        """Get user IDs by role."""
        return []

    async def _save_approval(self, approval: Dict[str, Any]):
        """Save approval request."""
        pass

    async def _notify_approvers(
        self,
        approval: Dict[str, Any],
        config: Dict[str, Any]
    ):
        """Send notifications to approvers."""
        from app.workflows.actions.notification_action import NotificationActionExecutor

        notifier = NotificationActionExecutor()

        await notifier.execute({
            "recipients": approval["approvers"],
            "title": f"Approval Required: {approval['title']}",
            "message": approval["description"],
            "priority": "high",
            "link": f"/approvals/{approval['id']}"
        }, {})

    def _interpolate(self, text: str, variables: Dict[str, Any]) -> str:
        """Interpolate variables."""
        def replace(match):
            key = match.group(1).strip()
            parts = key.split(".")
            value = variables
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return match.group(0)
            return str(value) if value is not None else match.group(0)

        return re.sub(r'\{\{([^}]+)\}\}', replace, text)
