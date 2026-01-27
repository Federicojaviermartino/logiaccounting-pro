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
