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
