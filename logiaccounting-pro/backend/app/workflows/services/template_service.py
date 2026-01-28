"""
Workflow Template Marketplace Service
"""

from typing import Dict, Any, Optional, List
from uuid import uuid4
import logging

from app.utils.datetime_utils import utc_now


logger = logging.getLogger(__name__)


class WorkflowTemplate:
    def __init__(self, name: str, description: str, category: str, definition: Dict, author_name: str = "System", is_official: bool = False, tags: List[str] = None, parameters: List[Dict] = None):
        self.id = f"tpl_{uuid4().hex[:12]}"
        self.name = name
        self.description = description
        self.category = category
        self.definition = definition
        self.author_name = author_name
        self.is_official = is_official
        self.is_public = True
        self.tenant_id = None
        self.tags = tags or []
        self.parameters = parameters or []
        self.created_at = utc_now()
        self.install_count = 0
        self.rating = 0.0
        self.rating_count = 0


class TemplateService:
    CATEGORIES = ["financial", "crm", "operations", "notifications", "integrations", "hr", "custom"]

    def __init__(self):
        self._templates: Dict[str, WorkflowTemplate] = {}
        self._load_builtin_templates()

    def _load_builtin_templates(self):
        builtin = [
            {
                "name": "Invoice Overdue Reminder",
                "description": "Send reminder emails when invoices become overdue.",
                "category": "financial",
                "tags": ["invoice", "reminder", "email"],
                "definition": {
                    "trigger": {"type": "entity_event", "entity": "invoice", "event": "overdue"},
                    "nodes": [{"id": "trigger_1", "type": "trigger"}, {"id": "email_1", "type": "action", "action_type": "send_email"}],
                    "edges": [{"source": "trigger_1", "target": "email_1"}],
                },
            },
            {
                "name": "New Lead Assignment",
                "description": "Auto-assign new leads using round-robin and create follow-up tasks.",
                "category": "crm",
                "tags": ["lead", "assignment", "task"],
                "definition": {
                    "trigger": {"type": "crm_event", "event": "lead.created"},
                    "nodes": [{"id": "trigger_1", "type": "trigger"}, {"id": "assign_1", "type": "action", "action_type": "crm.assign_owner"}, {"id": "task_1", "type": "action", "action_type": "crm.create_activity"}],
                    "edges": [{"source": "trigger_1", "target": "assign_1"}, {"source": "assign_1", "target": "task_1"}],
                },
            },
            {
                "name": "Deal Won Notification",
                "description": "Notify team when a deal is won.",
                "category": "crm",
                "tags": ["deal", "notification", "celebration"],
                "definition": {
                    "trigger": {"type": "crm_event", "event": "deal.won"},
                    "nodes": [{"id": "trigger_1", "type": "trigger"}, {"id": "notify_1", "type": "action", "action_type": "notification"}],
                    "edges": [{"source": "trigger_1", "target": "notify_1"}],
                },
            },
            {
                "name": "Quote Follow-up",
                "description": "Create follow-up task 3 days after quote is sent.",
                "category": "crm",
                "tags": ["quote", "follow-up", "delay"],
                "definition": {
                    "trigger": {"type": "crm_event", "event": "quote.sent"},
                    "nodes": [{"id": "trigger_1", "type": "trigger"}, {"id": "delay_1", "type": "delay", "config": {"duration": "3d"}}, {"id": "task_1", "type": "action", "action_type": "crm.create_activity"}],
                    "edges": [{"source": "trigger_1", "target": "delay_1"}, {"source": "delay_1", "target": "task_1"}],
                },
            },
            {
                "name": "Low Stock Alert",
                "description": "Alert when inventory falls below minimum.",
                "category": "operations",
                "tags": ["inventory", "alert", "threshold"],
                "definition": {
                    "trigger": {"type": "threshold", "metric": "inventory.low_stock_count", "threshold": 1},
                    "nodes": [{"id": "trigger_1", "type": "trigger"}, {"id": "notify_1", "type": "action", "action_type": "notification"}, {"id": "email_1", "type": "action", "action_type": "send_email"}],
                    "edges": [{"source": "trigger_1", "target": "notify_1"}, {"source": "notify_1", "target": "email_1"}],
                },
            },
            {
                "name": "At-Risk Account Alert",
                "description": "Alert when customer health score drops below 40.",
                "category": "crm",
                "tags": ["account", "health", "alert"],
                "definition": {
                    "trigger": {"type": "crm_event", "event": "company.health_changed"},
                    "conditions": [{"type": "all", "rules": [{"field": "entity.health_score", "operator": "less_than", "value": 40}]}],
                    "nodes": [{"id": "trigger_1", "type": "trigger"}, {"id": "task_1", "type": "action", "action_type": "crm.create_activity"}, {"id": "notify_1", "type": "action", "action_type": "notification"}],
                    "edges": [{"source": "trigger_1", "target": "task_1"}, {"source": "task_1", "target": "notify_1"}],
                },
            },
        ]

        for tpl_data in builtin:
            template = WorkflowTemplate(
                name=tpl_data["name"],
                description=tpl_data["description"],
                category=tpl_data["category"],
                definition=tpl_data["definition"],
                author_name="LogiAccounting",
                is_official=True,
                tags=tpl_data.get("tags", []),
            )
            self._templates[template.id] = template

    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        return self._templates.get(template_id)

    def list_templates(self, category: str = None, search: str = None, tags: List[str] = None, is_official: bool = None, tenant_id: str = None, page: int = 1, page_size: int = 20) -> Dict:
        templates = list(self._templates.values())

        templates = [t for t in templates if t.is_public or t.tenant_id == tenant_id]

        if category:
            templates = [t for t in templates if t.category == category]
        if is_official is not None:
            templates = [t for t in templates if t.is_official == is_official]
        if search:
            search_lower = search.lower()
            templates = [t for t in templates if search_lower in t.name.lower() or search_lower in t.description.lower()]
        if tags:
            templates = [t for t in templates if any(tag in t.tags for tag in tags)]

        templates = sorted(templates, key=lambda t: t.install_count, reverse=True)

        total = len(templates)
        skip = (page - 1) * page_size
        templates = templates[skip:skip + page_size]

        return {"items": [self._template_to_dict(t) for t in templates], "total": total, "page": page, "page_size": page_size}

    def install_template(self, template_id: str, tenant_id: str, user_id: str, parameters: Dict = None) -> Dict:
        template = self._templates.get(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        from app.workflows.models.store import workflow_store

        workflow = workflow_store.create_workflow(
            name=template.name,
            description=template.description,
            tenant_id=tenant_id,
            created_by=user_id,
            trigger=template.definition.get("trigger", {}),
            nodes=template.definition.get("nodes", []),
            edges=template.definition.get("edges", []),
        )

        template.install_count += 1

        return {"workflow_id": workflow.id, "template_id": template_id, "template_name": template.name}

    def publish_template(self, workflow_id: str, tenant_id: str, user_id: str, name: str, description: str, category: str, tags: List[str] = None, is_public: bool = True) -> WorkflowTemplate:
        from app.workflows.models.store import workflow_store

        workflow = workflow_store.get_workflow(workflow_id)
        if not workflow or workflow.tenant_id != tenant_id:
            raise ValueError("Workflow not found or access denied")

        template = WorkflowTemplate(
            name=name,
            description=description,
            category=category,
            definition={"trigger": workflow.trigger, "nodes": workflow.nodes, "edges": workflow.edges},
            author_name=user_id,
            is_official=False,
            tags=tags or [],
        )
        template.is_public = is_public
        template.tenant_id = tenant_id if not is_public else None

        self._templates[template.id] = template
        return template

    def rate_template(self, template_id: str, user_id: str, rating: int) -> WorkflowTemplate:
        template = self._templates.get(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        rating = max(1, min(5, rating))
        total = template.rating * template.rating_count + rating
        template.rating_count += 1
        template.rating = total / template.rating_count
        return template

    def get_categories(self) -> List[Dict]:
        counts = {}
        for template in self._templates.values():
            if template.is_public:
                counts[template.category] = counts.get(template.category, 0) + 1
        return [{"id": cat, "name": cat.title(), "count": counts.get(cat, 0)} for cat in self.CATEGORIES]

    def _template_to_dict(self, template: WorkflowTemplate) -> Dict:
        return {
            "id": template.id, "name": template.name, "description": template.description,
            "category": template.category, "author_name": template.author_name, "is_official": template.is_official,
            "tags": template.tags, "parameters": template.parameters, "install_count": template.install_count,
            "rating": round(template.rating, 1), "rating_count": template.rating_count, "created_at": template.created_at.isoformat(),
        }


template_service = TemplateService()
