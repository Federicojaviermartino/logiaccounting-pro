"""
LLM Client
Unified interface for LLM providers (Anthropic, OpenAI)
"""

import json
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from ..config import get_ai_config, LLMProvider, ModelTier
from ..models.ai_usage import AIUsage


@dataclass
class LLMResponse:
    """LLM response wrapper"""
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    raw_response: Optional[Dict] = None


class LLMClient:
    """Unified LLM client supporting multiple providers"""

    def __init__(self):
        self.config = get_ai_config()
        self._anthropic_client = None
        self._openai_client = None

    def _get_anthropic_client(self):
        """Get or create Anthropic client"""
        if self._anthropic_client is None:
            try:
                import anthropic
                self._anthropic_client = anthropic.Anthropic(
                    api_key=self.config.llm.anthropic_api_key
                )
            except ImportError:
                raise RuntimeError("anthropic package not installed")
        return self._anthropic_client

    def _get_openai_client(self):
        """Get or create OpenAI client"""
        if self._openai_client is None:
            try:
                import openai
                self._openai_client = openai.OpenAI(
                    api_key=self.config.llm.openai_api_key
                )
            except ImportError:
                raise RuntimeError("openai package not installed")
        return self._openai_client

    def _get_model_name(self, tier: ModelTier) -> str:
        """Get model name for tier and provider"""
        provider = self.config.llm.provider

        if provider == LLMProvider.ANTHROPIC:
            models = {
                ModelTier.FAST: "claude-3-haiku-20240307",
                ModelTier.BALANCED: "claude-3-5-sonnet-20241022",
                ModelTier.POWERFUL: "claude-3-opus-20240229",
            }
        else:
            models = {
                ModelTier.FAST: "gpt-4o-mini",
                ModelTier.BALANCED: "gpt-4o",
                ModelTier.POWERFUL: "gpt-4-turbo",
            }

        return models.get(tier, models[ModelTier.BALANCED])

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tier: ModelTier = ModelTier.BALANCED,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        tenant_id: Optional[str] = None,
        feature: str = "general",
    ) -> LLMResponse:
        """
        Generate completion from LLM

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            tier: Model tier to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            tenant_id: Tenant ID for usage tracking
            feature: Feature name for usage tracking

        Returns:
            LLMResponse with generated content
        """
        start_time = time.time()
        model = self._get_model_name(tier)
        provider = self.config.llm.provider

        try:
            if provider == LLMProvider.ANTHROPIC:
                response = await self._anthropic_complete(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            else:
                response = await self._openai_complete(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

            latency_ms = int((time.time() - start_time) * 1000)
            response.latency_ms = latency_ms

            # Track usage
            if tenant_id:
                AIUsage.record_usage(
                    tenant_id=tenant_id,
                    feature=feature,
                    provider=provider.value,
                    model=model,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                    latency_ms=latency_ms,
                )

            return response

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            if tenant_id:
                AIUsage.record_usage(
                    tenant_id=tenant_id,
                    feature=feature,
                    provider=provider.value,
                    model=model,
                    input_tokens=0,
                    output_tokens=0,
                    latency_ms=latency_ms,
                    error=str(e),
                )
            raise

    async def _anthropic_complete(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """Anthropic API completion"""
        client = self._get_anthropic_client()

        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = client.messages.create(**kwargs)

        return LLMResponse(
            content=response.content[0].text,
            model=model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            latency_ms=0,
            raw_response={"id": response.id, "stop_reason": response.stop_reason},
        )

    async def _openai_complete(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """OpenAI API completion"""
        client = self._get_openai_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            model=model,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            latency_ms=0,
            raw_response={"id": response.id, "finish_reason": response.choices[0].finish_reason},
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        tier: ModelTier = ModelTier.BALANCED,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        tenant_id: Optional[str] = None,
        feature: str = "chat",
    ) -> LLMResponse:
        """
        Multi-turn chat completion

        Args:
            messages: List of {"role": "user"|"assistant", "content": "..."}
            system_prompt: Optional system prompt
            tier: Model tier to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            tenant_id: Tenant ID for usage tracking
            feature: Feature name for usage tracking

        Returns:
            LLMResponse with generated content
        """
        start_time = time.time()
        model = self._get_model_name(tier)
        provider = self.config.llm.provider

        try:
            if provider == LLMProvider.ANTHROPIC:
                response = await self._anthropic_chat(
                    messages=messages,
                    system_prompt=system_prompt,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            else:
                response = await self._openai_chat(
                    messages=messages,
                    system_prompt=system_prompt,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

            latency_ms = int((time.time() - start_time) * 1000)
            response.latency_ms = latency_ms

            if tenant_id:
                AIUsage.record_usage(
                    tenant_id=tenant_id,
                    feature=feature,
                    provider=provider.value,
                    model=model,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                    latency_ms=latency_ms,
                )

            return response

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            if tenant_id:
                AIUsage.record_usage(
                    tenant_id=tenant_id,
                    feature=feature,
                    provider=provider.value,
                    model=model,
                    input_tokens=0,
                    output_tokens=0,
                    latency_ms=latency_ms,
                    error=str(e),
                )
            raise

    async def _anthropic_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """Anthropic chat completion"""
        client = self._get_anthropic_client()

        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = client.messages.create(**kwargs)

        return LLMResponse(
            content=response.content[0].text,
            model=model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            latency_ms=0,
            raw_response={"id": response.id, "stop_reason": response.stop_reason},
        )

    async def _openai_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """OpenAI chat completion"""
        client = self._get_openai_client()

        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)

        response = client.chat.completions.create(
            model=model,
            messages=formatted_messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            model=model,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            latency_ms=0,
            raw_response={"id": response.id, "finish_reason": response.choices[0].finish_reason},
        )

    async def extract_json(
        self,
        prompt: str,
        schema_hint: Optional[str] = None,
        tier: ModelTier = ModelTier.FAST,
        tenant_id: Optional[str] = None,
        feature: str = "extraction",
    ) -> Dict[str, Any]:
        """
        Extract structured JSON from text

        Args:
            prompt: Text to extract from
            schema_hint: Optional JSON schema hint
            tier: Model tier to use
            tenant_id: Tenant ID for usage tracking
            feature: Feature name for usage tracking

        Returns:
            Extracted JSON data
        """
        system_prompt = """You are a data extraction assistant. Extract structured data from the given text.
Always respond with valid JSON only, no explanation or markdown."""

        if schema_hint:
            system_prompt += f"\n\nExpected JSON schema:\n{schema_hint}"

        response = await self.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            tier=tier,
            temperature=0.1,
            tenant_id=tenant_id,
            feature=feature,
        )

        # Parse JSON from response
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        return json.loads(content)


# Singleton instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get singleton LLM client instance"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
