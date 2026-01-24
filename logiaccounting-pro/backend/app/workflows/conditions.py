"""
Condition Builder & Evaluator
Advanced condition handling for workflow decisions
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import re
import logging

logger = logging.getLogger(__name__)


class ConditionBuilder:
    """Builds condition objects for the workflow builder UI."""

    FIELD_TYPES = {
        "string": ["equals", "not_equals", "contains", "not_contains", "starts_with", "ends_with", "is_empty", "is_not_empty", "matches"],
        "number": ["equals", "not_equals", "greater_than", "greater_than_or_equals", "less_than", "less_than_or_equals", "is_empty", "is_not_empty"],
        "boolean": ["equals", "not_equals"],
        "date": ["equals", "not_equals", "before", "after", "between", "is_empty", "is_not_empty"],
        "array": ["contains", "not_contains", "is_empty", "is_not_empty", "length_equals", "length_greater_than", "length_less_than"],
    }

    OPERATOR_LABELS = {
        "equals": "equals",
        "not_equals": "does not equal",
        "greater_than": "is greater than",
        "greater_than_or_equals": "is greater than or equal to",
        "less_than": "is less than",
        "less_than_or_equals": "is less than or equal to",
        "contains": "contains",
        "not_contains": "does not contain",
        "starts_with": "starts with",
        "ends_with": "ends with",
        "is_empty": "is empty",
        "is_not_empty": "is not empty",
        "matches": "matches pattern",
        "before": "is before",
        "after": "is after",
        "between": "is between",
        "in": "is one of",
        "not_in": "is not one of",
    }

    @classmethod
    def get_operators_for_type(cls, field_type: str) -> List[Dict]:
        """Get available operators for a field type."""
        operators = cls.FIELD_TYPES.get(field_type, cls.FIELD_TYPES["string"])
        return [
            {"value": op, "label": cls.OPERATOR_LABELS.get(op, op)}
            for op in operators
        ]

    @classmethod
    def build_simple(cls, field: str, operator: str, value: Any) -> Dict:
        """Build a simple condition."""
        return {
            "type": "simple",
            "field": field,
            "operator": operator,
            "value": value,
        }

    @classmethod
    def build_and(cls, conditions: List[Dict]) -> Dict:
        """Build an AND condition."""
        return {
            "type": "and",
            "conditions": conditions,
        }

    @classmethod
    def build_or(cls, conditions: List[Dict]) -> Dict:
        """Build an OR condition."""
        return {
            "type": "or",
            "conditions": conditions,
        }

    @classmethod
    def build_not(cls, condition: Dict) -> Dict:
        """Build a NOT condition."""
        return {
            "type": "not",
            "condition": condition,
        }

    @classmethod
    def validate(cls, condition: Dict) -> List[str]:
        """Validate a condition structure."""
        errors = []

        condition_type = condition.get("type", "simple")

        if condition_type in ["and", "or"]:
            conditions = condition.get("conditions", [])
            if not conditions:
                errors.append(f"{condition_type.upper()} condition requires at least one sub-condition")
            for i, sub in enumerate(conditions):
                sub_errors = cls.validate(sub)
                errors.extend([f"[{i}] {e}" for e in sub_errors])

        elif condition_type == "not":
            inner = condition.get("condition")
            if not inner:
                errors.append("NOT condition requires an inner condition")
            else:
                errors.extend(cls.validate(inner))

        else:  # simple
            if not condition.get("field"):
                errors.append("Field is required")
            if not condition.get("operator"):
                errors.append("Operator is required")
            # Value can be empty for is_empty/is_not_empty operators

        return errors


class DateConditionHelper:
    """Helper for date-based conditions."""

    @staticmethod
    def days_ago(days: int) -> datetime:
        """Get datetime for N days ago."""
        return datetime.utcnow() - timedelta(days=days)

    @staticmethod
    def days_from_now(days: int) -> datetime:
        """Get datetime for N days from now."""
        return datetime.utcnow() + timedelta(days=days)

    @staticmethod
    def start_of_day(dt: datetime = None) -> datetime:
        """Get start of day."""
        dt = dt or datetime.utcnow()
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def end_of_day(dt: datetime = None) -> datetime:
        """Get end of day."""
        dt = dt or datetime.utcnow()
        return dt.replace(hour=23, minute=59, second=59, microsecond=999999)

    @staticmethod
    def start_of_week(dt: datetime = None) -> datetime:
        """Get start of week (Monday)."""
        dt = dt or datetime.utcnow()
        days_since_monday = dt.weekday()
        return DateConditionHelper.start_of_day(dt - timedelta(days=days_since_monday))

    @staticmethod
    def start_of_month(dt: datetime = None) -> datetime:
        """Get start of month."""
        dt = dt or datetime.utcnow()
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def is_overdue(date_value: Union[str, datetime], reference: datetime = None) -> bool:
        """Check if a date is overdue."""
        if isinstance(date_value, str):
            date_value = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
        reference = reference or datetime.utcnow()
        return date_value < reference

    @staticmethod
    def days_until(date_value: Union[str, datetime]) -> int:
        """Get days until a date."""
        if isinstance(date_value, str):
            date_value = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
        delta = date_value - datetime.utcnow()
        return delta.days

    @staticmethod
    def days_since(date_value: Union[str, datetime]) -> int:
        """Get days since a date."""
        if isinstance(date_value, str):
            date_value = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
        delta = datetime.utcnow() - date_value
        return delta.days


class ConditionPresets:
    """Common condition presets for quick selection."""

    PRESETS = {
        "invoice_overdue": {
            "name": "Invoice is Overdue",
            "description": "Invoice due date has passed",
            "condition": {
                "type": "and",
                "conditions": [
                    {"field": "invoice.status", "operator": "not_equals", "value": "paid"},
                    {"field": "invoice.due_date", "operator": "before", "value": "{{now()}}"},
                ],
            },
        },
        "invoice_high_value": {
            "name": "High Value Invoice",
            "description": "Invoice amount exceeds threshold",
            "condition": {
                "field": "invoice.amount",
                "operator": "greater_than",
                "value": 10000,
            },
        },
        "customer_enterprise": {
            "name": "Enterprise Customer",
            "description": "Customer is enterprise tier",
            "condition": {
                "field": "customer.tier",
                "operator": "equals",
                "value": "enterprise",
            },
        },
        "ticket_urgent": {
            "name": "Urgent Ticket",
            "description": "Ticket priority is urgent or high",
            "condition": {
                "type": "or",
                "conditions": [
                    {"field": "ticket.priority", "operator": "equals", "value": "urgent"},
                    {"field": "ticket.priority", "operator": "equals", "value": "high"},
                ],
            },
        },
        "project_near_deadline": {
            "name": "Project Near Deadline",
            "description": "Project due within 7 days",
            "condition": {
                "type": "and",
                "conditions": [
                    {"field": "project.status", "operator": "not_equals", "value": "completed"},
                    {"field": "project.due_date", "operator": "before", "value": "{{days_from_now(7)}}"},
                ],
            },
        },
        "payment_failed": {
            "name": "Payment Failed",
            "description": "Payment status is failed",
            "condition": {
                "field": "payment.status",
                "operator": "equals",
                "value": "failed",
            },
        },
    }

    @classmethod
    def get_preset(cls, preset_id: str) -> Optional[Dict]:
        """Get a condition preset."""
        return cls.PRESETS.get(preset_id)

    @classmethod
    def list_presets(cls) -> List[Dict]:
        """List all available presets."""
        return [
            {
                "id": preset_id,
                "name": preset["name"],
                "description": preset["description"],
            }
            for preset_id, preset in cls.PRESETS.items()
        ]
