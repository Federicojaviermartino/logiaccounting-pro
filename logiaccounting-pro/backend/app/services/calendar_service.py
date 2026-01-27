"""
Calendar Service
Events and scheduling
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.models.store import db


class CalendarService:
    """Manages calendar events"""

    _instance = None
    _events: Dict[str, dict] = {}
    _counter = 0

    EVENT_TYPES = [
        "payment_due", "payment_received", "delivery",
        "project_deadline", "meeting", "reminder", "custom"
    ]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._events = {}
            cls._counter = 0
        return cls._instance

    def create_event(
        self,
        title: str,
        event_type: str,
        start: str,
        end: str = None,
        all_day: bool = False,
        entity_type: str = None,
        entity_id: str = None,
        description: str = "",
        color: str = None,
        reminder: str = None,
        recurrence: dict = None,
        created_by: str = None
    ) -> dict:
        """Create a calendar event"""
        self._counter += 1
        event_id = f"EVT-{self._counter:05d}"

        # Default colors by type
        type_colors = {
            "payment_due": "#ef4444",
            "payment_received": "#10b981",
            "delivery": "#3b82f6",
            "project_deadline": "#8b5cf6",
            "meeting": "#f59e0b",
            "reminder": "#6b7280",
            "custom": "#667eea"
        }

        event = {
            "id": event_id,
            "title": title,
            "type": event_type,
            "start": start,
            "end": end or start,
            "all_day": all_day,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "description": description,
            "color": color or type_colors.get(event_type, "#667eea"),
            "reminder": reminder,
            "recurrence": recurrence,
            "created_by": created_by,
            "created_at": datetime.utcnow().isoformat()
        }

        self._events[event_id] = event
        return event

    def update_event(self, event_id: str, updates: dict) -> Optional[dict]:
        """Update an event"""
        if event_id not in self._events:
            return None

        event = self._events[event_id]
        for key, value in updates.items():
            if key in event and key not in ["id", "created_at"]:
                event[key] = value

        return event

    def delete_event(self, event_id: str) -> bool:
        """Delete an event"""
        if event_id in self._events:
            del self._events[event_id]
            return True
        return False

    def get_event(self, event_id: str) -> Optional[dict]:
        """Get an event"""
        return self._events.get(event_id)

    def get_events(
        self,
        start_date: str,
        end_date: str,
        event_type: str = None
    ) -> List[dict]:
        """Get events in date range"""
        events = []

        for event in self._events.values():
            event_start = event["start"][:10]
            event_end = event["end"][:10] if event["end"] else event_start

            # Check overlap
            if event_start <= end_date and event_end >= start_date:
                if event_type is None or event["type"] == event_type:
                    events.append(event)

        return sorted(events, key=lambda x: x["start"])

    def get_entity_events(self, entity_type: str, entity_id: str) -> List[dict]:
        """Get events for an entity"""
        return sorted(
            [e for e in self._events.values()
             if e["entity_type"] == entity_type and e["entity_id"] == entity_id],
            key=lambda x: x["start"]
        )

    def generate_system_events(self) -> List[dict]:
        """Generate events from payments, projects, etc."""
        generated = []

        # Payment due dates
        payments = db.payments.find_all()
        for payment in payments:
            if payment.get("due_date") and payment.get("status") != "paid":
                event = self.create_event(
                    title=f"Payment Due: ${payment.get('amount', 0):,.2f}",
                    event_type="payment_due",
                    start=payment["due_date"],
                    all_day=True,
                    entity_type="payment",
                    entity_id=payment["id"],
                    created_by="system"
                )
                generated.append(event)

        # Project deadlines
        projects = db.projects.find_all()
        for project in projects:
            if project.get("end_date") and project.get("status") != "completed":
                event = self.create_event(
                    title=f"Project Deadline: {project.get('name', 'Untitled')}",
                    event_type="project_deadline",
                    start=project["end_date"],
                    all_day=True,
                    entity_type="project",
                    entity_id=project["id"],
                    created_by="system"
                )
                generated.append(event)

        return generated

    def get_upcoming(self, days: int = 7) -> List[dict]:
        """Get upcoming events"""
        today = datetime.utcnow().date().isoformat()
        end_date = (datetime.utcnow() + timedelta(days=days)).date().isoformat()
        return self.get_events(today, end_date)


calendar_service = CalendarService()
