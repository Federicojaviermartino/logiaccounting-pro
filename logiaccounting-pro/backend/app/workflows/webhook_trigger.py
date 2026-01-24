"""
Webhook Trigger Handler
Handles incoming webhooks that trigger workflows
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4
import hmac
import hashlib
import logging

logger = logging.getLogger(__name__)


class WebhookTrigger:
    """Represents a webhook trigger configuration."""

    def __init__(self, workflow_id: str, path: str = None):
        self.id = f"wht_{uuid4().hex[:12]}"
        self.workflow_id = workflow_id
        self.path = path or f"/webhooks/trigger/{self.id}"
        self.secret = uuid4().hex
        self.enabled = True
        self.created_at = datetime.utcnow()
        self.last_triggered_at: Optional[datetime] = None
        self.trigger_count = 0

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "path": self.path,
            "url": f"https://api.logiaccounting.com{self.path}",
            "secret": self.secret,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "last_triggered_at": self.last_triggered_at.isoformat() if self.last_triggered_at else None,
            "trigger_count": self.trigger_count,
        }


class WebhookTriggerHandler:
    """Manages webhook triggers for workflows."""

    def __init__(self):
        self._triggers: Dict[str, WebhookTrigger] = {}  # id -> trigger
        self._path_map: Dict[str, str] = {}  # path -> trigger_id

    def create_trigger(self, workflow_id: str, custom_path: str = None) -> WebhookTrigger:
        """Create a webhook trigger for a workflow."""
        trigger = WebhookTrigger(workflow_id, custom_path)
        self._triggers[trigger.id] = trigger
        self._path_map[trigger.path] = trigger.id

        logger.info(f"Created webhook trigger {trigger.id} for workflow {workflow_id}")
        return trigger

    def get_trigger(self, trigger_id: str) -> Optional[WebhookTrigger]:
        """Get trigger by ID."""
        return self._triggers.get(trigger_id)

    def get_trigger_by_path(self, path: str) -> Optional[WebhookTrigger]:
        """Get trigger by path."""
        trigger_id = self._path_map.get(path)
        if trigger_id:
            return self._triggers.get(trigger_id)
        return None

    def get_workflow_triggers(self, workflow_id: str) -> List[WebhookTrigger]:
        """Get all triggers for a workflow."""
        return [t for t in self._triggers.values() if t.workflow_id == workflow_id]

    def delete_trigger(self, trigger_id: str) -> bool:
        """Delete a webhook trigger."""
        trigger = self._triggers.get(trigger_id)
        if trigger:
            del self._triggers[trigger_id]
            if trigger.path in self._path_map:
                del self._path_map[trigger.path]
            logger.info(f"Deleted webhook trigger {trigger_id}")
            return True
        return False

    def regenerate_secret(self, trigger_id: str) -> Optional[str]:
        """Regenerate webhook secret."""
        trigger = self._triggers.get(trigger_id)
        if trigger:
            trigger.secret = uuid4().hex
            return trigger.secret
        return None

    def verify_signature(self, trigger_id: str, payload: bytes, signature: str) -> bool:
        """Verify webhook signature."""
        trigger = self._triggers.get(trigger_id)
        if not trigger:
            return False

        expected = hmac.new(
            trigger.secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        # Handle different signature formats
        if signature.startswith("sha256="):
            signature = signature[7:]

        return hmac.compare_digest(expected, signature)

    async def handle_webhook(self, path: str, payload: Dict, headers: Dict) -> Dict:
        """Handle incoming webhook."""
        trigger = self.get_trigger_by_path(path)

        if not trigger:
            logger.warning(f"Webhook trigger not found for path: {path}")
            return {"success": False, "error": "Trigger not found"}

        if not trigger.enabled:
            return {"success": False, "error": "Trigger is disabled"}

        # Update trigger stats
        trigger.last_triggered_at = datetime.utcnow()
        trigger.trigger_count += 1

        # Prepare trigger data
        trigger_data = {
            "trigger_type": "webhook",
            "webhook_id": trigger.id,
            "payload": payload,
            "headers": {k: v for k, v in headers.items() if k.lower() not in ["authorization", "cookie"]},
            "received_at": datetime.utcnow().isoformat(),
        }

        # Execute workflow
        from app.workflows.engine import workflow_engine
        from app.services.workflow_service import workflow_service

        workflow = workflow_service.get_workflow(trigger.workflow_id)
        if not workflow:
            return {"success": False, "error": "Workflow not found"}

        try:
            execution = await workflow_engine.execute(
                workflow,
                input_data=payload,
                trigger_data=trigger_data,
            )

            return {
                "success": True,
                "execution_id": execution.id,
                "status": execution.status.value,
            }

        except Exception as e:
            logger.error(f"Webhook execution failed: {e}")
            return {"success": False, "error": str(e)}


# Global webhook trigger handler
webhook_trigger_handler = WebhookTriggerHandler()
