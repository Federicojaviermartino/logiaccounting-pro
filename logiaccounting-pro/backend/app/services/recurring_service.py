"""
Recurring Transactions Service
Automate periodic transactions and payments
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.models.store import db


class RecurringService:
    """Manages recurring transaction templates"""

    _instance = None
    _templates: Dict[str, dict] = {}
    _counter = 0

    FREQUENCIES = {
        "daily": {"days": 1},
        "weekly": {"weeks": 1},
        "biweekly": {"weeks": 2},
        "monthly": {"months": 1},
        "quarterly": {"months": 3},
        "yearly": {"years": 1}
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._templates = {}
            cls._counter = 0
        return cls._instance

    def create_template(
        self,
        name: str,
        entity_type: str,
        template_data: dict,
        frequency: str,
        start_date: str,
        end_date: Optional[str] = None,
        day_of_month: Optional[int] = None,
        day_of_week: Optional[int] = None,
        auto_create: bool = False,
        created_by: str = None
    ) -> dict:
        """Create a recurring template"""
        self._counter += 1
        template_id = f"REC-{self._counter:04d}"

        next_occurrence = self._calculate_next_occurrence(
            start_date, frequency, day_of_month, day_of_week
        )

        template = {
            "id": template_id,
            "name": name,
            "entity_type": entity_type,
            "template_data": template_data,
            "frequency": frequency,
            "start_date": start_date,
            "end_date": end_date,
            "day_of_month": day_of_month,
            "day_of_week": day_of_week,
            "next_occurrence": next_occurrence,
            "last_generated": None,
            "auto_create": auto_create,
            "active": True,
            "created_by": created_by,
            "created_at": datetime.utcnow().isoformat(),
            "generation_count": 0
        }

        self._templates[template_id] = template
        return template

    def _calculate_next_occurrence(
        self,
        from_date: str,
        frequency: str,
        day_of_month: Optional[int] = None,
        day_of_week: Optional[int] = None
    ) -> str:
        """Calculate next occurrence date"""
        try:
            if 'T' in from_date:
                base_date = datetime.fromisoformat(from_date.replace('Z', '+00:00')).date()
            else:
                base_date = datetime.strptime(from_date, '%Y-%m-%d').date()
        except:
            base_date = datetime.utcnow().date()

        today = datetime.utcnow().date()

        if base_date > today:
            return base_date.isoformat()

        freq_delta = self.FREQUENCIES.get(frequency, {"days": 1})

        next_date = base_date
        while next_date <= today:
            if "days" in freq_delta:
                next_date += timedelta(days=freq_delta["days"])
            elif "weeks" in freq_delta:
                next_date += timedelta(weeks=freq_delta["weeks"])
            elif "months" in freq_delta:
                month = next_date.month + freq_delta["months"]
                year = next_date.year + (month - 1) // 12
                month = ((month - 1) % 12) + 1
                day = min(next_date.day, 28)
                next_date = next_date.replace(year=year, month=month, day=day)
            elif "years" in freq_delta:
                next_date = next_date.replace(year=next_date.year + freq_delta["years"])

        if day_of_month and frequency in ["monthly", "quarterly", "yearly"]:
            try:
                next_date = next_date.replace(day=min(day_of_month, 28))
            except ValueError:
                pass

        if day_of_week is not None and frequency == "weekly":
            days_ahead = day_of_week - next_date.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_date += timedelta(days=days_ahead)

        return next_date.isoformat()

    def update_template(self, template_id: str, updates: dict) -> Optional[dict]:
        """Update a recurring template"""
        if template_id not in self._templates:
            return None

        template = self._templates[template_id]

        for key, value in updates.items():
            if key in template and key not in ["id", "created_at", "created_by"]:
                template[key] = value

        if "frequency" in updates or "start_date" in updates:
            template["next_occurrence"] = self._calculate_next_occurrence(
                template["start_date"],
                template["frequency"],
                template.get("day_of_month"),
                template.get("day_of_week")
            )

        return template

    def delete_template(self, template_id: str) -> bool:
        """Delete a recurring template"""
        if template_id in self._templates:
            del self._templates[template_id]
            return True
        return False

    def toggle_active(self, template_id: str) -> Optional[dict]:
        """Toggle template active status"""
        if template_id not in self._templates:
            return None

        template = self._templates[template_id]
        template["active"] = not template["active"]
        return template

    def get_template(self, template_id: str) -> Optional[dict]:
        """Get a specific template"""
        return self._templates.get(template_id)

    def list_templates(self, user_id: Optional[str] = None, active_only: bool = False) -> List[dict]:
        """List all templates"""
        templates = list(self._templates.values())

        if user_id:
            templates = [t for t in templates if t["created_by"] == user_id]

        if active_only:
            templates = [t for t in templates if t["active"]]

        return sorted(templates, key=lambda t: t["next_occurrence"])

    def get_due_templates(self) -> List[dict]:
        """Get templates due for generation"""
        today = datetime.utcnow().date().isoformat()
        return [
            t for t in self._templates.values()
            if t["active"] and t["next_occurrence"] <= today
            and (not t["end_date"] or t["end_date"] >= today)
        ]

    def generate_from_template(self, template_id: str) -> Optional[dict]:
        """Generate entity from template"""
        template = self._templates.get(template_id)
        if not template:
            return None

        entity_type = template["entity_type"]
        data = template["template_data"].copy()

        data["date"] = datetime.utcnow().date().isoformat()
        data["created_at"] = datetime.utcnow().isoformat()
        data["recurring_template_id"] = template_id

        if entity_type == "transaction":
            created = db.transactions.create(data)
        elif entity_type == "payment":
            created = db.payments.create(data)
        else:
            return None

        template["last_generated"] = datetime.utcnow().isoformat()
        template["generation_count"] += 1
        template["next_occurrence"] = self._calculate_next_occurrence(
            template["next_occurrence"],
            template["frequency"],
            template.get("day_of_month"),
            template.get("day_of_week")
        )

        return created

    def preview_occurrences(self, template_id: str, count: int = 5) -> List[str]:
        """Preview next N occurrences"""
        template = self._templates.get(template_id)
        if not template:
            return []

        occurrences = []
        current = template["next_occurrence"]

        for _ in range(count):
            occurrences.append(current)
            current = self._calculate_next_occurrence(
                current,
                template["frequency"],
                template.get("day_of_month"),
                template.get("day_of_week")
            )

            if template["end_date"] and current > template["end_date"]:
                break

        return occurrences


recurring_service = RecurringService()
