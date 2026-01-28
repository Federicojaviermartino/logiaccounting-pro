"""
Workflow Version Control Service
"""

from typing import Dict, Any, Optional, List
from uuid import uuid4
import logging

from app.utils.datetime_utils import utc_now
from app.workflows.models.workflow import Workflow
from app.workflows.models.store import workflow_store


logger = logging.getLogger(__name__)


class WorkflowVersionService:
    """Manages workflow versions with rollback capability."""

    def __init__(self):
        self._versions: Dict[str, List[Dict]] = {}
        self._max_versions = 50

    def save_version(self, workflow: Workflow, user_id: str, comment: str = None) -> Dict:
        """Save a new version snapshot."""
        wf_id = workflow.id
        versions = self._versions.setdefault(wf_id, [])
        version_number = len(versions) + 1

        version = {
            "id": str(uuid4()),
            "workflow_id": wf_id,
            "version": version_number,
            "snapshot": self._create_snapshot(workflow),
            "created_at": utc_now().isoformat(),
            "created_by": user_id,
            "comment": comment,
            "node_count": len(workflow.nodes),
        }

        versions.append(version)
        if len(versions) > self._max_versions:
            versions.pop(0)

        logger.info(f"Saved version {version_number} for workflow {wf_id}")
        return {"version": version_number, "id": version["id"]}

    def _create_snapshot(self, workflow: Workflow) -> Dict:
        return {
            "name": workflow.name,
            "description": workflow.description,
            "status": workflow.status.value if hasattr(workflow.status, 'value') else workflow.status,
            "trigger": workflow.trigger.dict() if hasattr(workflow.trigger, 'dict') else workflow.trigger,
            "nodes": [n.dict() if hasattr(n, 'dict') else n for n in workflow.nodes],
            "edges": workflow.edges,
            "settings": workflow.settings,
        }

    def list_versions(self, workflow_id: str, limit: int = 20) -> List[Dict]:
        versions = self._versions.get(workflow_id, [])
        return [
            {"id": v["id"], "version": v["version"], "created_at": v["created_at"],
             "created_by": v["created_by"], "comment": v["comment"], "node_count": v["node_count"]}
            for v in reversed(versions[-limit:])
        ]

    def get_version(self, workflow_id: str, version: int = None, version_id: str = None) -> Optional[Dict]:
        versions = self._versions.get(workflow_id, [])
        for v in versions:
            if (version_id and v["id"] == version_id) or (version and v["version"] == version):
                return v
        return None

    def compare_versions(self, workflow_id: str, version_a: int, version_b: int) -> Dict:
        v_a = self.get_version(workflow_id, version=version_a)
        v_b = self.get_version(workflow_id, version=version_b)
        if not v_a or not v_b:
            return {"error": "Version not found"}

        snap_a, snap_b = v_a["snapshot"], v_b["snapshot"]
        nodes_a = {n.get("id"): n for n in snap_a.get("nodes", [])}
        nodes_b = {n.get("id"): n for n in snap_b.get("nodes", [])}

        return {
            "version_a": version_a, "version_b": version_b,
            "nodes_added": len(set(nodes_b) - set(nodes_a)),
            "nodes_removed": len(set(nodes_a) - set(nodes_b)),
            "nodes_modified": len([nid for nid in set(nodes_a) & set(nodes_b) if nodes_a[nid] != nodes_b[nid]]),
        }

    def rollback(self, workflow_id: str, version: int, user_id: str) -> Dict:
        target = self.get_version(workflow_id, version=version)
        if not target:
            raise ValueError(f"Version {version} not found")

        workflow = workflow_store.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found")

        snapshot = target["snapshot"]
        updates = {
            "name": snapshot["name"],
            "description": snapshot["description"],
            "nodes": snapshot["nodes"],
            "edges": snapshot.get("edges", []),
        }

        updated = workflow_store.update_workflow(workflow_id, updates)
        new_ver = self.save_version(updated, user_id, f"Rollback to v{version}")

        return {"success": True, "rolled_back_to": version, "new_version": new_ver["version"]}


version_service = WorkflowVersionService()
