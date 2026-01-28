"""
Team Collaboration Service
Comments, mentions, tasks, reactions
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re
from app.models.store import db
from app.utils.datetime_utils import utc_now


class CollaborationService:
    """Manages comments, tasks, and mentions"""

    _instance = None
    _comments: Dict[str, dict] = {}
    _tasks: Dict[str, dict] = {}
    _comment_counter = 0
    _task_counter = 0

    REACTIONS = ["👍", "👎", "✅", "❌", "❓", "🎉", "❤️", "👀"]

    TASK_STATUSES = ["pending", "in_progress", "completed", "cancelled"]
    TASK_PRIORITIES = ["low", "medium", "high", "urgent"]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._comments = {}
            cls._tasks = {}
            cls._comment_counter = 0
            cls._task_counter = 0
        return cls._instance

    # ========== COMMENTS ==========

    def create_comment(
        self,
        entity_type: str,
        entity_id: str,
        content: str,
        author_id: str,
        author_name: str,
        author_email: str,
        attachments: List[str] = None,
        thread_id: str = None
    ) -> dict:
        """Create a new comment"""
        self._comment_counter += 1
        comment_id = f"CMT-{self._comment_counter:05d}"

        # Extract mentions from content
        mentions = self._extract_mentions(content)

        comment = {
            "id": comment_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "content": content,
            "mentions": mentions,
            "author_id": author_id,
            "author_name": author_name,
            "author_email": author_email,
            "attachments": attachments or [],
            "reactions": {},
            "thread_id": thread_id,
            "replies_count": 0,
            "is_edited": False,
            "created_at": utc_now().isoformat(),
            "updated_at": utc_now().isoformat()
        }

        self._comments[comment_id] = comment

        # Update parent's reply count if this is a reply
        if thread_id and thread_id in self._comments:
            self._comments[thread_id]["replies_count"] += 1

        return comment

    def _extract_mentions(self, content: str) -> List[str]:
        """Extract @mentions from content"""
        # Match @username or @email patterns
        pattern = r'@(\w+(?:@[\w.-]+)?)'
        matches = re.findall(pattern, content)
        return list(set(matches))

    def update_comment(self, comment_id: str, content: str) -> Optional[dict]:
        """Update comment content"""
        if comment_id not in self._comments:
            return None

        comment = self._comments[comment_id]
        comment["content"] = content
        comment["mentions"] = self._extract_mentions(content)
        comment["is_edited"] = True
        comment["updated_at"] = utc_now().isoformat()

        return comment

    def delete_comment(self, comment_id: str) -> bool:
        """Delete a comment"""
        if comment_id not in self._comments:
            return False

        comment = self._comments[comment_id]

        # Update parent's reply count
        if comment.get("thread_id") and comment["thread_id"] in self._comments:
            self._comments[comment["thread_id"]]["replies_count"] -= 1

        # Delete all replies if this is a parent
        if not comment.get("thread_id"):
            for c in list(self._comments.values()):
                if c.get("thread_id") == comment_id:
                    del self._comments[c["id"]]

        del self._comments[comment_id]
        return True

    def add_reaction(self, comment_id: str, reaction: str, user_id: str) -> Optional[dict]:
        """Add reaction to comment"""
        if comment_id not in self._comments:
            return None
        if reaction not in self.REACTIONS:
            return None

        comment = self._comments[comment_id]

        if reaction not in comment["reactions"]:
            comment["reactions"][reaction] = []

        if user_id not in comment["reactions"][reaction]:
            comment["reactions"][reaction].append(user_id)

        return comment

    def remove_reaction(self, comment_id: str, reaction: str, user_id: str) -> Optional[dict]:
        """Remove reaction from comment"""
        if comment_id not in self._comments:
            return None

        comment = self._comments[comment_id]

        if reaction in comment["reactions"] and user_id in comment["reactions"][reaction]:
            comment["reactions"][reaction].remove(user_id)
            if not comment["reactions"][reaction]:
                del comment["reactions"][reaction]

        return comment

    def get_comment(self, comment_id: str) -> Optional[dict]:
        """Get a comment"""
        return self._comments.get(comment_id)

    def get_entity_comments(self, entity_type: str, entity_id: str) -> List[dict]:
        """Get all comments for an entity"""
        comments = [
            c for c in self._comments.values()
            if c["entity_type"] == entity_type and c["entity_id"] == entity_id and not c.get("thread_id")
        ]

        # Add replies to each comment
        for comment in comments:
            comment["replies"] = sorted(
                [c for c in self._comments.values() if c.get("thread_id") == comment["id"]],
                key=lambda x: x["created_at"]
            )

        return sorted(comments, key=lambda x: x["created_at"], reverse=True)

    def get_user_mentions(self, user_id: str, user_email: str, unread_only: bool = False) -> List[dict]:
        """Get comments mentioning a user"""
        mentions = []
        search_terms = [user_id, user_email.split("@")[0], user_email]

        for comment in self._comments.values():
            for mention in comment.get("mentions", []):
                if any(term in mention.lower() for term in [t.lower() for t in search_terms if t]):
                    mentions.append(comment)
                    break

        return sorted(mentions, key=lambda x: x["created_at"], reverse=True)

    # ========== TASKS ==========

    def create_task(
        self,
        title: str,
        entity_type: str,
        entity_id: str,
        assigned_to: str,
        assigned_by: str,
        due_date: str = None,
        priority: str = "medium",
        notes: str = ""
    ) -> dict:
        """Create a new task"""
        self._task_counter += 1
        task_id = f"TASK-{self._task_counter:05d}"

        task = {
            "id": task_id,
            "title": title,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "assigned_to": assigned_to,
            "assigned_by": assigned_by,
            "due_date": due_date,
            "priority": priority,
            "status": "pending",
            "notes": notes,
            "completed_at": None,
            "created_at": utc_now().isoformat()
        }

        self._tasks[task_id] = task
        return task

    def update_task(self, task_id: str, updates: dict) -> Optional[dict]:
        """Update a task"""
        if task_id not in self._tasks:
            return None

        task = self._tasks[task_id]

        for key, value in updates.items():
            if key in task and key not in ["id", "created_at"]:
                task[key] = value

        # Set completed_at when status changes to completed
        if updates.get("status") == "completed" and not task["completed_at"]:
            task["completed_at"] = utc_now().isoformat()

        return task

    def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def get_task(self, task_id: str) -> Optional[dict]:
        """Get a task"""
        return self._tasks.get(task_id)

    def get_user_tasks(
        self,
        user_id: str,
        status: str = None,
        include_assigned_by: bool = False
    ) -> List[dict]:
        """Get tasks for a user"""
        tasks = []

        for task in self._tasks.values():
            if task["assigned_to"] == user_id:
                tasks.append(task)
            elif include_assigned_by and task["assigned_by"] == user_id:
                tasks.append(task)

        if status:
            tasks = [t for t in tasks if t["status"] == status]

        return sorted(tasks, key=lambda x: (x.get("due_date") or "9999", x["created_at"]))

    def get_entity_tasks(self, entity_type: str, entity_id: str) -> List[dict]:
        """Get tasks for an entity"""
        return sorted(
            [t for t in self._tasks.values() if t["entity_type"] == entity_type and t["entity_id"] == entity_id],
            key=lambda x: x["created_at"],
            reverse=True
        )

    def get_overdue_tasks(self) -> List[dict]:
        """Get all overdue tasks"""
        today = utc_now().date().isoformat()
        return [
            t for t in self._tasks.values()
            if t["status"] not in ["completed", "cancelled"]
            and t.get("due_date")
            and t["due_date"] < today
        ]

    def get_activity_feed(self, entity_type: str, entity_id: str, limit: int = 20) -> List[dict]:
        """Get combined activity feed for an entity"""
        activities = []

        # Add comments
        for comment in self._comments.values():
            if comment["entity_type"] == entity_type and comment["entity_id"] == entity_id:
                activities.append({
                    "type": "comment",
                    "data": comment,
                    "timestamp": comment["created_at"]
                })

        # Add tasks
        for task in self._tasks.values():
            if task["entity_type"] == entity_type and task["entity_id"] == entity_id:
                activities.append({
                    "type": "task",
                    "data": task,
                    "timestamp": task["created_at"]
                })

        return sorted(activities, key=lambda x: x["timestamp"], reverse=True)[:limit]


collaboration_service = CollaborationService()
