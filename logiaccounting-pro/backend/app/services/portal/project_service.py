"""
Portal Project Service
Customer project visibility
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4
import logging

from app.models.store import db

logger = logging.getLogger(__name__)


class PortalProjectService:
    """Customer project visibility service."""

    def __init__(self):
        self._feedbacks: Dict[str, List[Dict]] = {}
        self._approvals: Dict[str, Dict] = {}

    def list_projects(self, customer_id: str, status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """List customer projects."""
        projects = [p for p in db.projects.find_all() if p.get("client_id") == customer_id]

        if status:
            projects = [p for p in projects if p.get("status") == status]

        projects.sort(key=lambda p: p.get("created_at", ""), reverse=True)

        total = len(projects)
        skip = (page - 1) * page_size
        projects = projects[skip:skip + page_size]

        return {"items": [self._project_to_dict(p) for p in projects], "total": total, "page": page, "page_size": page_size}

    def get_project(self, project_id: str, customer_id: str) -> Optional[Dict]:
        """Get project detail."""
        project = db.projects.find_by_id(project_id)
        if not project or project.get("client_id") != customer_id:
            return None
        return self._project_to_dict(project, include_details=True)

    def get_project_timeline(self, project_id: str, customer_id: str) -> Optional[List[Dict]]:
        """Get project timeline/milestones."""
        project = db.projects.find_by_id(project_id)
        if not project or project.get("client_id") != customer_id:
            return None

        milestones = project.get("milestones", [])
        timeline = []

        for ms in milestones:
            timeline.append({
                "id": ms.get("id"),
                "name": ms.get("name"),
                "description": ms.get("description"),
                "due_date": ms.get("due_date"),
                "status": ms.get("status", "pending"),
                "completed_at": ms.get("completed_at"),
                "progress": ms.get("progress", 0),
            })

        timeline.sort(key=lambda t: t.get("due_date", ""))
        return timeline

    def get_project_documents(self, project_id: str, customer_id: str) -> List[Dict]:
        """Get project documents."""
        project = db.projects.find_by_id(project_id)
        if not project or project.get("client_id") != customer_id:
            return []

        documents = []
        all_docs = db.documents.find_all() if hasattr(db, 'documents') else []

        for doc in all_docs:
            if doc.get("project_id") == project_id and doc.get("shared_with_client", True):
                documents.append({
                    "id": doc["id"],
                    "name": doc.get("name"),
                    "type": doc.get("type"),
                    "size": doc.get("size"),
                    "uploaded_at": doc.get("created_at"),
                    "category": doc.get("category"),
                })

        return documents

    def submit_feedback(self, project_id: str, customer_id: str, content: str, rating: int = None) -> Dict:
        """Submit project feedback."""
        project = db.projects.find_by_id(project_id)
        if not project or project.get("client_id") != customer_id:
            raise ValueError("Project not found")

        feedback = {
            "id": f"fb_{uuid4().hex[:12]}",
            "project_id": project_id,
            "customer_id": customer_id,
            "content": content,
            "rating": rating,
            "created_at": datetime.utcnow().isoformat(),
        }

        if project_id not in self._feedbacks:
            self._feedbacks[project_id] = []
        self._feedbacks[project_id].append(feedback)

        return feedback

    def approve_deliverable(self, project_id: str, deliverable_id: str, customer_id: str, approved: bool, comment: str = None) -> Dict:
        """Approve or reject a deliverable."""
        project = db.projects.find_by_id(project_id)
        if not project or project.get("client_id") != customer_id:
            raise ValueError("Project not found")

        approval = {
            "id": f"appr_{uuid4().hex[:12]}",
            "project_id": project_id,
            "deliverable_id": deliverable_id,
            "customer_id": customer_id,
            "approved": approved,
            "comment": comment,
            "created_at": datetime.utcnow().isoformat(),
        }

        self._approvals[deliverable_id] = approval

        return approval

    def get_project_stats(self, customer_id: str) -> Dict[str, Any]:
        """Get project statistics."""
        projects = [p for p in db.projects.find_all() if p.get("client_id") == customer_id]

        return {
            "total": len(projects),
            "active": len([p for p in projects if p.get("status") == "active"]),
            "completed": len([p for p in projects if p.get("status") == "completed"]),
            "on_hold": len([p for p in projects if p.get("status") == "on_hold"]),
        }

    def _project_to_dict(self, project: Dict, include_details: bool = False) -> Dict:
        result = {
            "id": project["id"],
            "name": project.get("name"),
            "description": project.get("description"),
            "status": project.get("status"),
            "progress": project.get("progress", 0),
            "start_date": project.get("start_date"),
            "end_date": project.get("end_date"),
            "budget": project.get("budget"),
            "created_at": project.get("created_at"),
        }

        if include_details:
            result["milestones"] = project.get("milestones", [])
            result["team_members"] = project.get("team_members", [])
            result["tags"] = project.get("tags", [])

        return result


portal_project_service = PortalProjectService()
