"""
Activity Management Service
Handles calls, emails, meetings, tasks, and notes
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import uuid4

from app.models.crm_store import crm_store


class ActivityService:
    """
    Service for managing CRM activities
    """

    # Activity types
    ACTIVITY_TYPES = [
        "call",
        "email",
        "meeting",
        "task",
        "note",
        "demo",
        "follow_up",
    ]

    # Call outcomes
    CALL_OUTCOMES = [
        "answered",
        "no_answer",
        "left_voicemail",
        "busy",
        "wrong_number",
        "callback_requested",
    ]

    # Email statuses
    EMAIL_STATUSES = [
        "draft",
        "sent",
        "opened",
        "clicked",
        "replied",
        "bounced",
    ]

    def create_activity(
        self,
        tenant_id: str,
        type: str,
        subject: str,
        owner_id: str,
        description: str = None,
        lead_id: str = None,
        contact_id: str = None,
        company_id: str = None,
        opportunity_id: str = None,
        due_date: str = None,
        duration_minutes: int = None,
        **kwargs
    ) -> dict:
        """Create a new activity"""
        if type not in self.ACTIVITY_TYPES:
            raise ValueError(f"Invalid activity type: {type}")

        activity_data = {
            "tenant_id": tenant_id,
            "type": type,
            "subject": subject,
            "description": description,
            "owner_id": owner_id,
            "lead_id": lead_id,
            "contact_id": contact_id,
            "company_id": company_id,
            "opportunity_id": opportunity_id,
            "due_date": due_date,
            "duration_minutes": duration_minutes,
            "status": "scheduled",
            **kwargs,
        }

        return crm_store.create_activity(activity_data)

    def update_activity(self, activity_id: str, user_id: str, **updates) -> dict:
        """Update activity"""
        return crm_store.update_activity(activity_id, updates)

    def get_activity(self, activity_id: str) -> dict:
        """Get activity by ID"""
        return crm_store.get_activity(activity_id)

    def delete_activity(self, activity_id: str, user_id: str):
        """Delete activity"""
        return crm_store.delete_activity(activity_id)

    def list_activities(
        self,
        tenant_id: str,
        type: str = None,
        lead_id: str = None,
        contact_id: str = None,
        company_id: str = None,
        opportunity_id: str = None,
        owner_id: str = None,
        status: str = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """List activities with filters"""
        skip = (page - 1) * page_size
        activities, total = crm_store.list_activities(
            tenant_id=tenant_id,
            type=type,
            lead_id=lead_id,
            contact_id=contact_id,
            company_id=company_id,
            opportunity_id=opportunity_id,
            owner_id=owner_id,
            status=status,
            skip=skip,
            limit=page_size,
        )

        return {
            "items": activities,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    def complete_activity(
        self,
        activity_id: str,
        user_id: str,
        outcome: str = None,
        notes: str = None,
    ) -> dict:
        """Mark activity as completed"""
        updates = {
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "completed_by": user_id,
        }

        if outcome:
            updates["outcome"] = outcome
        if notes:
            updates["completion_notes"] = notes

        return crm_store.update_activity(activity_id, updates)

    def cancel_activity(self, activity_id: str, user_id: str, reason: str = None) -> dict:
        """Cancel activity"""
        return crm_store.update_activity(activity_id, {
            "status": "cancelled",
            "cancelled_at": datetime.utcnow().isoformat(),
            "cancelled_by": user_id,
            "cancel_reason": reason,
        })

    def reschedule_activity(
        self,
        activity_id: str,
        user_id: str,
        new_date: str,
    ) -> dict:
        """Reschedule activity to new date"""
        activity = crm_store.get_activity(activity_id)
        if not activity:
            raise ValueError(f"Activity not found: {activity_id}")

        # Track reschedule history
        reschedule_history = activity.get("reschedule_history", [])
        reschedule_history.append({
            "from_date": activity.get("due_date"),
            "to_date": new_date,
            "rescheduled_at": datetime.utcnow().isoformat(),
            "rescheduled_by": user_id,
        })

        return crm_store.update_activity(activity_id, {
            "due_date": new_date,
            "reschedule_history": reschedule_history,
            "reschedule_count": len(reschedule_history),
        })

    # ==========================================
    # CALL LOGGING
    # ==========================================

    def log_call(
        self,
        tenant_id: str,
        owner_id: str,
        subject: str,
        outcome: str,
        duration_minutes: int = None,
        contact_id: str = None,
        lead_id: str = None,
        company_id: str = None,
        opportunity_id: str = None,
        notes: str = None,
        phone_number: str = None,
        direction: str = "outbound",  # inbound, outbound
    ) -> dict:
        """Log a completed call"""
        if outcome not in self.CALL_OUTCOMES:
            raise ValueError(f"Invalid call outcome: {outcome}")

        activity = self.create_activity(
            tenant_id=tenant_id,
            type="call",
            subject=subject,
            owner_id=owner_id,
            description=notes,
            contact_id=contact_id,
            lead_id=lead_id,
            company_id=company_id,
            opportunity_id=opportunity_id,
            duration_minutes=duration_minutes,
            call_outcome=outcome,
            phone_number=phone_number,
            call_direction=direction,
        )

        # Mark as completed immediately
        return self.complete_activity(activity["id"], owner_id, outcome)

    # ==========================================
    # EMAIL TRACKING
    # ==========================================

    def log_email(
        self,
        tenant_id: str,
        owner_id: str,
        subject: str,
        body: str = None,
        contact_id: str = None,
        lead_id: str = None,
        opportunity_id: str = None,
        template_id: str = None,
        to_email: str = None,
    ) -> dict:
        """Log a sent email"""
        activity = self.create_activity(
            tenant_id=tenant_id,
            type="email",
            subject=subject,
            owner_id=owner_id,
            description=body,
            contact_id=contact_id,
            lead_id=lead_id,
            opportunity_id=opportunity_id,
            email_template_id=template_id,
            to_email=to_email,
            email_status="sent",
        )

        return self.complete_activity(activity["id"], owner_id, "sent")

    def track_email_open(self, activity_id: str) -> dict:
        """Track email open event"""
        activity = crm_store.get_activity(activity_id)
        if not activity:
            return None

        open_count = activity.get("email_open_count", 0) + 1

        updates = {
            "email_status": "opened",
            "email_open_count": open_count,
        }

        if open_count == 1:
            updates["first_opened_at"] = datetime.utcnow().isoformat()
        updates["last_opened_at"] = datetime.utcnow().isoformat()

        return crm_store.update_activity(activity_id, updates)

    def track_email_click(self, activity_id: str, url: str = None) -> dict:
        """Track email link click"""
        activity = crm_store.get_activity(activity_id)
        if not activity:
            return None

        click_count = activity.get("email_click_count", 0) + 1

        return crm_store.update_activity(activity_id, {
            "email_status": "clicked",
            "email_click_count": click_count,
            "last_clicked_at": datetime.utcnow().isoformat(),
            "last_clicked_url": url,
        })

    # ==========================================
    # MEETING SCHEDULING
    # ==========================================

    def schedule_meeting(
        self,
        tenant_id: str,
        owner_id: str,
        subject: str,
        start_time: str,
        end_time: str,
        contact_id: str = None,
        lead_id: str = None,
        company_id: str = None,
        opportunity_id: str = None,
        location: str = None,
        meeting_link: str = None,
        attendees: List[str] = None,
        description: str = None,
    ) -> dict:
        """Schedule a meeting"""
        # Calculate duration
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        duration = int((end - start).total_seconds() / 60)

        return self.create_activity(
            tenant_id=tenant_id,
            type="meeting",
            subject=subject,
            owner_id=owner_id,
            description=description,
            contact_id=contact_id,
            lead_id=lead_id,
            company_id=company_id,
            opportunity_id=opportunity_id,
            due_date=start_time,
            duration_minutes=duration,
            meeting_start=start_time,
            meeting_end=end_time,
            meeting_location=location,
            meeting_link=meeting_link,
            meeting_attendees=attendees or [],
        )

    # ==========================================
    # TASK MANAGEMENT
    # ==========================================

    def create_task(
        self,
        tenant_id: str,
        owner_id: str,
        subject: str,
        due_date: str,
        priority: str = "medium",
        contact_id: str = None,
        lead_id: str = None,
        company_id: str = None,
        opportunity_id: str = None,
        description: str = None,
    ) -> dict:
        """Create a task"""
        return self.create_activity(
            tenant_id=tenant_id,
            type="task",
            subject=subject,
            owner_id=owner_id,
            description=description,
            contact_id=contact_id,
            lead_id=lead_id,
            company_id=company_id,
            opportunity_id=opportunity_id,
            due_date=due_date,
            task_priority=priority,
        )

    def get_overdue_tasks(self, tenant_id: str, owner_id: str = None) -> List[dict]:
        """Get overdue tasks"""
        activities, _ = crm_store.list_activities(
            tenant_id=tenant_id,
            type="task",
            owner_id=owner_id,
            status="scheduled",
            limit=1000,
        )

        now = datetime.utcnow().isoformat()
        return [a for a in activities if a.get("due_date") and a["due_date"] < now]

    def get_upcoming_activities(
        self,
        tenant_id: str,
        owner_id: str = None,
        days: int = 7,
    ) -> List[dict]:
        """Get activities for next N days"""
        activities, _ = crm_store.list_activities(
            tenant_id=tenant_id,
            owner_id=owner_id,
            status="scheduled",
            limit=1000,
        )

        now = datetime.utcnow()
        end_date = (now + timedelta(days=days)).isoformat()

        upcoming = [
            a for a in activities
            if a.get("due_date") and now.isoformat() <= a["due_date"] <= end_date
        ]

        return sorted(upcoming, key=lambda x: x.get("due_date", ""))

    # ==========================================
    # ANALYTICS
    # ==========================================

    def get_activity_stats(
        self,
        tenant_id: str,
        owner_id: str = None,
        days: int = 30,
    ) -> dict:
        """Get activity statistics"""
        activities, _ = crm_store.list_activities(
            tenant_id=tenant_id,
            owner_id=owner_id,
            limit=10000,
        )

        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        recent = [a for a in activities if a.get("created_at", "") >= cutoff]

        # Count by type
        by_type = {}
        for activity in recent:
            t = activity.get("type", "other")
            by_type[t] = by_type.get(t, 0) + 1

        # Count by status
        completed = len([a for a in recent if a.get("status") == "completed"])
        scheduled = len([a for a in recent if a.get("status") == "scheduled"])

        # Call outcomes
        calls = [a for a in recent if a.get("type") == "call"]
        call_outcomes = {}
        for call in calls:
            outcome = call.get("call_outcome", "unknown")
            call_outcomes[outcome] = call_outcomes.get(outcome, 0) + 1

        return {
            "period_days": days,
            "total_activities": len(recent),
            "completed": completed,
            "scheduled": scheduled,
            "completion_rate": (completed / len(recent) * 100) if recent else 0,
            "by_type": by_type,
            "call_outcomes": call_outcomes,
            "emails_sent": by_type.get("email", 0),
            "meetings_held": len([
                a for a in recent
                if a.get("type") == "meeting" and a.get("status") == "completed"
            ]),
        }


# Service instance
activity_service = ActivityService()
