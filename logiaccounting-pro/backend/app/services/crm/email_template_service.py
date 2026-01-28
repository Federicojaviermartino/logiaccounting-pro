"""
Email Template Service
Manages reusable email templates with variable substitution
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4
import re

from app.models.crm_store import crm_store
from app.utils.datetime_utils import utc_now


class EmailTemplateService:
    """
    Service for managing email templates
    """

    # Available merge fields
    MERGE_FIELDS = {
        "contact": [
            "{{contact.first_name}}",
            "{{contact.last_name}}",
            "{{contact.full_name}}",
            "{{contact.email}}",
            "{{contact.phone}}",
            "{{contact.job_title}}",
        ],
        "company": [
            "{{company.name}}",
            "{{company.website}}",
            "{{company.industry}}",
        ],
        "opportunity": [
            "{{opportunity.name}}",
            "{{opportunity.amount}}",
            "{{opportunity.stage}}",
        ],
        "sender": [
            "{{sender.name}}",
            "{{sender.email}}",
            "{{sender.title}}",
            "{{sender.phone}}",
        ],
        "other": [
            "{{today}}",
            "{{current_month}}",
            "{{current_year}}",
        ],
    }

    def create_template(
        self,
        tenant_id: str,
        name: str,
        subject: str,
        body: str,
        category: str = "general",
        created_by: str = None,
        is_shared: bool = True,
        **kwargs
    ) -> dict:
        """Create a new email template"""
        template_id = str(uuid4())
        template = {
            "id": template_id,
            "tenant_id": tenant_id,
            "name": name,
            "subject": subject,
            "body": body,
            "category": category,
            "created_by": created_by,
            "is_shared": is_shared,
            "created_at": utc_now().isoformat(),
            "updated_at": utc_now().isoformat(),
            "use_count": 0,
            **kwargs,
        }

        crm_store._email_templates[template_id] = template
        return template

    def update_template(self, template_id: str, user_id: str, **updates) -> dict:
        """Update template"""
        template = crm_store._email_templates.get(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        updates["updated_at"] = utc_now().isoformat()
        template.update(updates)
        return template

    def get_template(self, template_id: str) -> dict:
        """Get template by ID"""
        return crm_store._email_templates.get(template_id)

    def delete_template(self, template_id: str, user_id: str):
        """Delete template"""
        if template_id in crm_store._email_templates:
            del crm_store._email_templates[template_id]
            return True
        return False

    def list_templates(
        self,
        tenant_id: str,
        category: str = None,
        search: str = None,
        user_id: str = None,
    ) -> List[dict]:
        """List templates"""
        templates = [
            t for t in crm_store._email_templates.values()
            if t.get("tenant_id") == tenant_id
        ]

        # Filter by visibility
        if user_id:
            templates = [
                t for t in templates
                if t.get("is_shared") or t.get("created_by") == user_id
            ]

        if category:
            templates = [t for t in templates if t.get("category") == category]

        if search:
            search_lower = search.lower()
            templates = [
                t for t in templates
                if search_lower in t.get("name", "").lower()
                or search_lower in t.get("subject", "").lower()
            ]

        return sorted(templates, key=lambda x: x.get("name", ""))

    def render_template(
        self,
        template_id: str,
        context: Dict[str, Any],
    ) -> dict:
        """Render template with context variables"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        subject = self._substitute_variables(template["subject"], context)
        body = self._substitute_variables(template["body"], context)

        # Increment use count
        template["use_count"] = template.get("use_count", 0) + 1

        return {
            "subject": subject,
            "body": body,
            "template_id": template_id,
        }

    def _substitute_variables(self, text: str, context: Dict[str, Any]) -> str:
        """Replace merge fields with actual values"""
        # Build flat context
        flat_context = {}

        # Contact fields
        if "contact" in context:
            c = context["contact"]
            flat_context["contact.first_name"] = c.get("first_name", "")
            flat_context["contact.last_name"] = c.get("last_name", "")
            flat_context["contact.full_name"] = f"{c.get('first_name', '')} {c.get('last_name', '')}".strip()
            flat_context["contact.email"] = c.get("email", "")
            flat_context["contact.phone"] = c.get("phone", "")
            flat_context["contact.job_title"] = c.get("job_title", "")

        # Company fields
        if "company" in context:
            co = context["company"]
            flat_context["company.name"] = co.get("name", "")
            flat_context["company.website"] = co.get("website", "")
            flat_context["company.industry"] = co.get("industry", "")

        # Opportunity fields
        if "opportunity" in context:
            o = context["opportunity"]
            flat_context["opportunity.name"] = o.get("name", "")
            flat_context["opportunity.amount"] = f"${o.get('amount', 0):,.2f}"
            flat_context["opportunity.stage"] = o.get("stage_name", "")

        # Sender fields
        if "sender" in context:
            s = context["sender"]
            flat_context["sender.name"] = s.get("name", "")
            flat_context["sender.email"] = s.get("email", "")
            flat_context["sender.title"] = s.get("title", "")
            flat_context["sender.phone"] = s.get("phone", "")

        # Date fields
        now = utc_now()
        flat_context["today"] = now.strftime("%B %d, %Y")
        flat_context["current_month"] = now.strftime("%B")
        flat_context["current_year"] = str(now.year)

        # Custom fields
        if "custom" in context:
            for key, value in context["custom"].items():
                flat_context[f"custom.{key}"] = str(value)

        # Substitute
        result = text
        for key, value in flat_context.items():
            result = result.replace(f"{{{{{key}}}}}", value)

        return result

    def get_merge_fields(self) -> dict:
        """Get available merge fields"""
        return self.MERGE_FIELDS

    def duplicate_template(
        self,
        template_id: str,
        tenant_id: str,
        new_name: str,
        user_id: str,
    ) -> dict:
        """Duplicate a template"""
        original = self.get_template(template_id)
        if not original:
            raise ValueError(f"Template not found: {template_id}")

        return self.create_template(
            tenant_id=tenant_id,
            name=new_name,
            subject=original["subject"],
            body=original["body"],
            category=original.get("category", "general"),
            created_by=user_id,
        )

    def get_template_categories(self, tenant_id: str) -> List[str]:
        """Get all template categories"""
        templates = [
            t for t in crm_store._email_templates.values()
            if t.get("tenant_id") == tenant_id
        ]
        categories = set(t.get("category", "general") for t in templates)
        return sorted(list(categories))


# Service instance
email_template_service = EmailTemplateService()


# Pre-built templates
DEFAULT_TEMPLATES = [
    {
        "name": "Initial Outreach",
        "subject": "{{company.name}} + {{sender.company}} - Quick Question",
        "body": """Hi {{contact.first_name}},

I came across {{company.name}} and was impressed by what you're doing in the {{company.industry}} space.

I'm reaching out because we help companies like yours [brief value prop]. I'd love to learn more about your current challenges and see if there's a fit.

Would you have 15 minutes this week for a quick call?

Best,
{{sender.name}}
{{sender.title}}
{{sender.phone}}""",
        "category": "prospecting",
    },
    {
        "name": "Follow-up After Meeting",
        "subject": "Great speaking with you, {{contact.first_name}}",
        "body": """Hi {{contact.first_name}},

Thank you for taking the time to speak with me today. I really enjoyed learning more about {{company.name}} and your goals for this year.

As discussed, I'm attaching [relevant materials]. I'll follow up next week to continue our conversation.

In the meantime, please don't hesitate to reach out if you have any questions.

Best regards,
{{sender.name}}""",
        "category": "follow_up",
    },
    {
        "name": "Proposal Sent",
        "subject": "Proposal for {{opportunity.name}}",
        "body": """Hi {{contact.first_name}},

As promised, please find attached our proposal for {{opportunity.name}}.

The proposal includes:
- [Key deliverable 1]
- [Key deliverable 2]
- [Key deliverable 3]

Total investment: {{opportunity.amount}}

I'm happy to walk you through the details at your convenience. Would you have time this week for a brief call?

Looking forward to your feedback.

Best,
{{sender.name}}""",
        "category": "proposals",
    },
    {
        "name": "Check-in Email",
        "subject": "Checking in - {{company.name}}",
        "body": """Hi {{contact.first_name}},

I wanted to check in and see how things are going at {{company.name}}.

It's been a while since we last connected, and I'd love to hear about any new initiatives or challenges you're facing.

Do you have a few minutes to catch up this week?

Best,
{{sender.name}}""",
        "category": "relationship",
    },
]
