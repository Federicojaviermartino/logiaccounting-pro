# Phase 26: Advanced Workflow Engine v2 - Part 3
## AI Features & Template Marketplace

---

## Task 12: AI Workflow Suggestions

### 12.1 AI Suggestion Service

**File: `backend/app/workflows/services/ai_suggestion_service.py`**

```python
"""
AI Workflow Suggestion Service
Uses LLM to suggest workflows based on user context
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import json

from app.ai.services.llm_client import llm_client


logger = logging.getLogger(__name__)


class WorkflowSuggestion:
    """A suggested workflow"""
    
    def __init__(self, name: str, description: str, trigger: Dict, actions: List[Dict], confidence: float = 0.8, reasoning: str = None):
        self.name = name
        self.description = description
        self.trigger = trigger
        self.actions = actions
        self.confidence = confidence
        self.reasoning = reasoning


class AISuggestionService:
    """AI-powered workflow suggestions based on user context."""
    
    def __init__(self):
        self._system_prompt = """You are a workflow automation expert. Suggest relevant workflow automations.

Available triggers: entity_event, crm_event, schedule, threshold, manual
Available actions: send_email, notification, crm.create_lead, crm.create_deal, crm.assign_owner, webhook, delay

Respond with JSON:
{
  "suggestions": [
    {
      "name": "Workflow Name",
      "description": "What this does",
      "confidence": 0.9,
      "reasoning": "Why recommended",
      "trigger": {"type": "crm_event", "event": "lead.created"},
      "actions": [{"type": "crm.assign_owner", "config": {}}]
    }
  ]
}"""
    
    async def get_suggestions(self, tenant_id: str, context: Dict = None, max_suggestions: int = 5) -> List[WorkflowSuggestion]:
        """Get AI-powered workflow suggestions."""
        try:
            user_prompt = self._build_user_prompt(context)
            
            response = await llm_client.complete(
                system_prompt=self._system_prompt,
                user_prompt=user_prompt,
                max_tokens=2000,
                temperature=0.7,
            )
            
            return self._parse_response(response)[:max_suggestions]
            
        except Exception as e:
            logger.error(f"AI suggestion failed: {e}")
            return self._get_fallback_suggestions()
    
    async def natural_language_to_workflow(self, description: str, tenant_id: str) -> Dict:
        """Convert natural language to workflow definition."""
        try:
            prompt = f"""Convert this to a workflow:

"{description}"

Respond with JSON:
{{
  "name": "Name",
  "description": "Description",
  "trigger": {{"type": "trigger_type", "config": {{}}}},
  "nodes": [{{"id": "node_1", "type": "trigger"}}, {{"id": "node_2", "type": "action", "action_type": "send_email"}}],
  "edges": [{{"source": "node_1", "target": "node_2"}}]
}}"""
            
            response = await llm_client.complete(
                system_prompt=self._system_prompt,
                user_prompt=prompt,
                max_tokens=1500,
            )
            
            return json.loads(response)
            
        except Exception as e:
            raise ValueError(f"Failed to convert: {e}")
    
    async def explain_workflow(self, workflow: Dict) -> str:
        """Generate human-readable explanation."""
        try:
            prompt = f"""Explain this workflow simply:

{json.dumps(workflow, indent=2)}

Keep it concise (2-3 paragraphs)."""
            
            return await llm_client.complete(
                system_prompt="You explain workflows in simple terms.",
                user_prompt=prompt,
                max_tokens=500,
            )
            
        except Exception as e:
            return "Unable to generate explanation."
    
    def _build_user_prompt(self, context: Dict = None) -> str:
        parts = ["Suggest 5 practical workflow automations."]
        if context:
            if context.get("user_role"):
                parts.append(f"User role: {context['user_role']}")
            if context.get("industry"):
                parts.append(f"Industry: {context['industry']}")
        return "\n".join(parts)
    
    def _parse_response(self, response: str) -> List[WorkflowSuggestion]:
        try:
            data = json.loads(response)
            return [
                WorkflowSuggestion(
                    name=item.get("name", "Untitled"),
                    description=item.get("description", ""),
                    trigger=item.get("trigger", {}),
                    actions=item.get("actions", []),
                    confidence=item.get("confidence", 0.7),
                    reasoning=item.get("reasoning", ""),
                )
                for item in data.get("suggestions", [])
            ]
        except json.JSONDecodeError:
            return self._get_fallback_suggestions()
    
    def _get_fallback_suggestions(self) -> List[WorkflowSuggestion]:
        return [
            WorkflowSuggestion(
                name="New Lead Follow-up",
                description="Auto-create follow-up tasks for new leads",
                trigger={"type": "crm_event", "event": "lead.created"},
                actions=[{"type": "crm.assign_owner"}, {"type": "crm.create_activity"}],
                confidence=0.9,
                reasoning="Common lead management pattern",
            ),
        ]


ai_suggestion_service = AISuggestionService()
```

---

## Task 13: AI Action Nodes

**File: `backend/app/workflows/actions/ai_actions.py`**

```python
"""
AI-Powered Action Executors
"""

from typing import Dict, Any
import logging
import json

from app.workflows.actions.base import ActionExecutor, ActionResult
from app.ai.services.llm_client import llm_client


logger = logging.getLogger(__name__)


class AIGenerateTextAction(ActionExecutor):
    """Generate text using AI"""
    action_type = "ai.generate_text"
    
    async def execute(self, config: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            prompt = self.interpolate(config.get("prompt", ""), context)
            system_prompt = config.get("system_prompt", "You are a helpful assistant.")
            
            response = await llm_client.complete(system_prompt=system_prompt, user_prompt=prompt, max_tokens=500)
            
            return ActionResult(success=True, data={"generated_text": response})
        except Exception as e:
            return ActionResult(success=False, error=str(e))


class AIExtractDataAction(ActionExecutor):
    """Extract structured data from text"""
    action_type = "ai.extract_data"
    
    async def execute(self, config: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            text = self.interpolate(config.get("text", ""), context)
            fields = config.get("fields", [])
            
            prompt = f"Extract {', '.join(fields)} from:\n{text}\n\nRespond with JSON only."
            
            response = await llm_client.complete(
                system_prompt="Extract structured data. Respond only with JSON.",
                user_prompt=prompt,
                max_tokens=500,
                temperature=0.1,
            )
            
            return ActionResult(success=True, data={"extracted": json.loads(response)})
        except Exception as e:
            return ActionResult(success=False, error=str(e))


class AIClassifyAction(ActionExecutor):
    """Classify text into categories"""
    action_type = "ai.classify"
    
    async def execute(self, config: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            text = self.interpolate(config.get("text", ""), context)
            categories = config.get("categories", [])
            
            prompt = f"Classify into one category from [{', '.join(categories)}]:\n{text}\n\nJSON: {{\"category\": \"chosen\", \"confidence\": 0.9}}"
            
            response = await llm_client.complete(
                system_prompt="Classify text. Respond only with JSON.",
                user_prompt=prompt,
                max_tokens=200,
                temperature=0.1,
            )
            
            return ActionResult(success=True, data={"classification": json.loads(response)})
        except Exception as e:
            return ActionResult(success=False, error=str(e))


class AISentimentAction(ActionExecutor):
    """Analyze sentiment"""
    action_type = "ai.sentiment"
    
    async def execute(self, config: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            text = self.interpolate(config.get("text", ""), context)
            
            prompt = f'Analyze sentiment:\n"{text}"\n\nJSON: {{"sentiment": "positive|negative|neutral", "score": 0.0-1.0}}'
            
            response = await llm_client.complete(
                system_prompt="Analyze sentiment. Respond only with JSON.",
                user_prompt=prompt,
                max_tokens=200,
                temperature=0.1,
            )
            
            result = json.loads(response)
            return ActionResult(success=True, data={"sentiment": result.get("sentiment"), "score": result.get("score")})
        except Exception as e:
            return ActionResult(success=False, error=str(e))


class AIEmailDraftAction(ActionExecutor):
    """Draft email using AI"""
    action_type = "ai.draft_email"
    
    async def execute(self, config: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            purpose = self.interpolate(config.get("purpose", ""), context)
            tone = config.get("tone", "professional")
            
            prompt = f"Draft a {tone} email:\nPurpose: {purpose}\n\nFormat:\nSubject: [subject]\n\n[body]"
            
            response = await llm_client.complete(
                system_prompt=f"Draft {tone} business emails.",
                user_prompt=prompt,
                max_tokens=500,
            )
            
            lines = response.strip().split("\n")
            subject = ""
            body = response
            
            for i, line in enumerate(lines):
                if line.lower().startswith("subject:"):
                    subject = line[8:].strip()
                    body = "\n".join(lines[i+1:]).strip()
                    break
            
            return ActionResult(success=True, data={"subject": subject, "body": body})
        except Exception as e:
            return ActionResult(success=False, error=str(e))


AI_ACTIONS = {
    AIGenerateTextAction.action_type: AIGenerateTextAction,
    AIExtractDataAction.action_type: AIExtractDataAction,
    AIClassifyAction.action_type: AIClassifyAction,
    AISentimentAction.action_type: AISentimentAction,
    AIEmailDraftAction.action_type: AIEmailDraftAction,
}
```

---

## Task 14: Template Marketplace Service

**File: `backend/app/workflows/services/template_service.py`**

```python
"""
Workflow Template Marketplace Service
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import uuid4
import logging


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
        self.created_at = datetime.utcnow()
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
```

---

## Task 15: Template API Routes

**File: `backend/app/routes/workflows/templates.py`**

```python
"""
Workflow Template Marketplace API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel

from app.utils.auth import get_current_user
from app.workflows.services.template_service import template_service
from app.workflows.services.ai_suggestion_service import ai_suggestion_service


router = APIRouter()


@router.get("")
async def list_templates(category: Optional[str] = None, search: Optional[str] = None, tags: Optional[str] = None, is_official: Optional[bool] = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=50), current_user: dict = Depends(get_current_user)):
    tag_list = tags.split(",") if tags else None
    return template_service.list_templates(category=category, search=search, tags=tag_list, is_official=is_official, tenant_id=current_user.get("tenant_id"), page=page, page_size=page_size)


@router.get("/categories")
async def get_categories(current_user: dict = Depends(get_current_user)):
    return template_service.get_categories()


@router.get("/{template_id}")
async def get_template(template_id: str, current_user: dict = Depends(get_current_user)):
    template = template_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template_service._template_to_dict(template)


@router.get("/{template_id}/preview")
async def preview_template(template_id: str, current_user: dict = Depends(get_current_user)):
    template = template_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"id": template.id, "name": template.name, "definition": template.definition, "parameters": template.parameters}


class InstallRequest(BaseModel):
    parameters: Optional[dict] = None

@router.post("/{template_id}/install")
async def install_template(template_id: str, data: InstallRequest, current_user: dict = Depends(get_current_user)):
    return template_service.install_template(template_id=template_id, tenant_id=current_user.get("tenant_id"), user_id=current_user["id"], parameters=data.parameters)


class PublishRequest(BaseModel):
    workflow_id: str
    name: str
    description: str
    category: str
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = True

@router.post("/publish")
async def publish_template(data: PublishRequest, current_user: dict = Depends(get_current_user)):
    template = template_service.publish_template(workflow_id=data.workflow_id, tenant_id=current_user.get("tenant_id"), user_id=current_user["id"], name=data.name, description=data.description, category=data.category, tags=data.tags, is_public=data.is_public)
    return template_service._template_to_dict(template)


class RateRequest(BaseModel):
    rating: int

@router.post("/{template_id}/rate")
async def rate_template(template_id: str, data: RateRequest, current_user: dict = Depends(get_current_user)):
    template = template_service.rate_template(template_id=template_id, user_id=current_user["id"], rating=data.rating)
    return {"rating": template.rating, "rating_count": template.rating_count}


# AI Suggestions
@router.get("/suggestions")
async def get_suggestions(current_user: dict = Depends(get_current_user)):
    suggestions = await ai_suggestion_service.get_suggestions(tenant_id=current_user.get("tenant_id"), context={"user_role": current_user.get("role")})
    return {"suggestions": [{"name": s.name, "description": s.description, "trigger": s.trigger, "actions": s.actions, "confidence": s.confidence, "reasoning": s.reasoning} for s in suggestions]}


class NLRequest(BaseModel):
    description: str

@router.post("/from-description")
async def from_description(data: NLRequest, current_user: dict = Depends(get_current_user)):
    return await ai_suggestion_service.natural_language_to_workflow(description=data.description, tenant_id=current_user.get("tenant_id"))


class ExplainRequest(BaseModel):
    workflow: dict

@router.post("/explain")
async def explain_workflow(data: ExplainRequest, current_user: dict = Depends(get_current_user)):
    explanation = await ai_suggestion_service.explain_workflow(data.workflow)
    return {"explanation": explanation}
```

---

## Task 16: Template Marketplace UI

**File: `frontend/src/features/workflows/pages/TemplateMarketplace.jsx`**

```jsx
import React, { useState, useEffect } from 'react';
import { Search, Star, Download, Eye, Sparkles, Zap } from 'lucide-react';
import { workflowAPI } from '../../../services/api';

export default function TemplateMarketplace() {
  const [templates, setTemplates] = useState([]);
  const [categories, setCategories] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [installing, setInstalling] = useState(null);

  useEffect(() => { loadData(); }, [selectedCategory, searchQuery]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [templatesRes, categoriesRes] = await Promise.all([
        workflowAPI.listTemplates({ category: selectedCategory, search: searchQuery }),
        workflowAPI.getTemplateCategories(),
      ]);
      setTemplates(templatesRes.data.items || []);
      setCategories(categoriesRes.data || []);
    } catch (error) {
      console.error('Failed to load:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInstall = async (templateId) => {
    try {
      setInstalling(templateId);
      const result = await workflowAPI.installTemplate(templateId, {});
      alert(`Installed! Workflow: ${result.data.workflow_id}`);
      loadData();
    } catch (error) {
      alert('Failed to install');
    } finally {
      setInstalling(null);
    }
  };

  const handlePreview = async (template) => {
    const res = await workflowAPI.previewTemplate(template.id);
    setSelectedTemplate({ ...template, definition: res.data.definition });
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Workflow Templates</h1>
        <p className="text-gray-500">Pre-built automations ready to use</p>
      </div>

      <div className="grid grid-cols-[240px_1fr] gap-6">
        <aside className="bg-white border rounded-xl p-5 h-fit">
          <div className="flex items-center gap-2 px-3 py-2 border rounded-lg mb-5">
            <Search className="w-4 h-4 text-gray-400" />
            <input className="flex-1 outline-none" placeholder="Search..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
          </div>
          <h3 className="text-xs font-semibold text-gray-500 uppercase mb-3">Categories</h3>
          <button className={`w-full text-left px-3 py-2 rounded-lg mb-1 ${!selectedCategory ? 'bg-blue-50 text-blue-600' : ''}`} onClick={() => setSelectedCategory('')}>All</button>
          {categories.map((cat) => (
            <button key={cat.id} className={`w-full flex justify-between px-3 py-2 rounded-lg mb-1 ${selectedCategory === cat.id ? 'bg-blue-50 text-blue-600' : ''}`} onClick={() => setSelectedCategory(cat.id)}>
              {cat.name} <span className="text-xs text-gray-400">{cat.count}</span>
            </button>
          ))}
        </aside>

        <main className="grid grid-cols-2 gap-5">
          {templates.map((tpl) => (
            <div key={tpl.id} className="bg-white border rounded-xl p-5 flex flex-col">
              <div className="flex justify-between mb-3">
                {tpl.is_official && <span className="flex items-center gap-1 text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded"><Sparkles className="w-3 h-3" /> Official</span>}
                <span className="text-xs text-gray-400 uppercase">{tpl.category}</span>
              </div>
              <h3 className="font-semibold mb-2">{tpl.name}</h3>
              <p className="text-sm text-gray-500 flex-1 mb-3">{tpl.description}</p>
              <div className="flex gap-1 mb-4">{tpl.tags?.slice(0, 3).map((tag) => <span key={tag} className="text-xs bg-gray-100 px-2 py-1 rounded">{tag}</span>)}</div>
              <div className="flex justify-between items-center pt-4 border-t">
                <div className="flex gap-4 text-sm text-gray-500">
                  <span className="flex items-center gap-1"><Star className="w-4 h-4" /> {tpl.rating || 'N/A'}</span>
                  <span className="flex items-center gap-1"><Download className="w-4 h-4" /> {tpl.install_count}</span>
                </div>
                <div className="flex gap-2">
                  <button className="p-2 border rounded-lg" onClick={() => handlePreview(tpl)}><Eye className="w-4 h-4" /></button>
                  <button className="px-4 py-2 bg-blue-600 text-white rounded-lg" onClick={() => handleInstall(tpl.id)} disabled={installing === tpl.id}>
                    {installing === tpl.id ? '...' : 'Install'}
                  </button>
                </div>
              </div>
            </div>
          ))}
          {templates.length === 0 && !isLoading && <div className="col-span-2 text-center py-16 text-gray-400"><Zap className="w-12 h-12 mx-auto mb-4" /><p>No templates found</p></div>}
        </main>
      </div>

      {selectedTemplate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setSelectedTemplate(null)}>
          <div className="bg-white rounded-xl w-full max-w-lg p-6" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-xl font-bold mb-4">{selectedTemplate.name}</h2>
            <p className="text-gray-600 mb-4">{selectedTemplate.description}</p>
            <h4 className="font-medium mb-2">Structure</h4>
            <div className="space-y-2 mb-6">
              <div className="px-4 py-3 bg-green-50 text-green-700 rounded-lg">Trigger: {selectedTemplate.definition?.trigger?.type}</div>
              {selectedTemplate.definition?.nodes?.filter(n => n.type !== 'trigger').map((n, i) => (
                <div key={i} className="px-4 py-3 bg-blue-50 text-blue-700 rounded-lg">{n.action_type || n.type}</div>
              ))}
            </div>
            <div className="flex justify-end gap-3">
              <button className="px-4 py-2 border rounded-lg" onClick={() => setSelectedTemplate(null)}>Cancel</button>
              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg" onClick={() => { handleInstall(selectedTemplate.id); setSelectedTemplate(null); }}>Install</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## Summary: Part 3 Complete

### Files Created:

| File | Purpose | Lines |
|------|---------|-------|
| `ai_suggestion_service.py` | AI workflow suggestions | ~140 |
| `ai_actions.py` | AI-powered actions | ~140 |
| `template_service.py` | Template marketplace | ~180 |
| `templates.py` | Template API routes | ~90 |
| `TemplateMarketplace.jsx` | Marketplace UI | ~100 |
| **Total** | | **~650** |

### Features:

| Feature | Status |
|---------|--------|
| AI workflow suggestions | ✅ |
| Natural language to workflow | ✅ |
| AI workflow explanation | ✅ |
| AI text generation | ✅ |
| AI data extraction | ✅ |
| AI classification | ✅ |
| AI sentiment analysis | ✅ |
| AI email draft | ✅ |
| Template marketplace | ✅ |
| 6 built-in templates | ✅ |
| Template install/publish | ✅ |
| Template rating | ✅ |

### Next: Part 4 - Enhanced Builder & Execution Monitor
