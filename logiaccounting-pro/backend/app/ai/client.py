"""
AI Client Manager
Unified interface for different AI providers
"""

from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod
import asyncio
import logging
import time
from datetime import datetime

import httpx
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from app.ai.config import AIConfig, AIProvider, ModelConfig, ai_config

logger = logging.getLogger(__name__)


class AIClient(ABC):
    """Abstract base class for AI clients."""

    @abstractmethod
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        """Send chat messages and get response."""
        pass

    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> str:
        """Complete a prompt."""
        pass

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embeddings for text."""
        pass

    @abstractmethod
    async def vision(self, image_data: bytes, prompt: str, **kwargs) -> str:
        """Process image with vision model."""
        pass


class AnthropicClient(AIClient):
    """Anthropic Claude API client."""

    def __init__(self, config: AIConfig):
        self.config = config
        self.client = AsyncAnthropic(api_key=config.anthropic_api_key)

    async def chat(self, messages: List[Dict], model_config: ModelConfig = None, system: str = None, **kwargs) -> str:
        """Send chat messages to Claude."""
        model_config = model_config or self.config.chat_model

        try:
            response = await self.client.messages.create(
                model=model_config.model_name,
                max_tokens=model_config.max_tokens,
                temperature=model_config.temperature,
                system=system or "",
                messages=messages,
                **kwargs,
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Anthropic chat error: {e}")
            raise

    async def complete(self, prompt: str, model_config: ModelConfig = None, **kwargs) -> str:
        """Complete a prompt using Claude."""
        return await self.chat(
            messages=[{"role": "user", "content": prompt}],
            model_config=model_config,
            **kwargs,
        )

    async def embed(self, text: str) -> List[float]:
        """Anthropic doesn't have embeddings - use OpenAI fallback."""
        raise NotImplementedError("Use OpenAI for embeddings")

    async def vision(self, image_data: bytes, prompt: str, model_config: ModelConfig = None, **kwargs) -> str:
        """Process image with Claude Vision."""
        import base64

        model_config = model_config or self.config.vision_model

        # Encode image to base64
        image_b64 = base64.b64encode(image_data).decode("utf-8")

        # Detect image type
        if image_data[:8] == b'\x89PNG\r\n\x1a\n':
            media_type = "image/png"
        elif image_data[:2] == b'\xff\xd8':
            media_type = "image/jpeg"
        else:
            media_type = "image/png"  # Default

        try:
            response = await self.client.messages.create(
                model=model_config.model_name,
                max_tokens=model_config.max_tokens,
                temperature=model_config.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
                **kwargs,
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Anthropic vision error: {e}")
            raise


class OpenAIClient(AIClient):
    """OpenAI API client."""

    def __init__(self, config: AIConfig):
        self.config = config
        self.client = AsyncOpenAI(api_key=config.openai_api_key)

    async def chat(self, messages: List[Dict], model_config: ModelConfig = None, system: str = None, **kwargs) -> str:
        """Send chat messages to GPT."""
        model_config = model_config or self.config.chat_model

        # Add system message if provided
        all_messages = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(messages)

        try:
            response = await self.client.chat.completions.create(
                model=model_config.model_name,
                max_tokens=model_config.max_tokens,
                temperature=model_config.temperature,
                messages=all_messages,
                **kwargs,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            raise

    async def complete(self, prompt: str, model_config: ModelConfig = None, **kwargs) -> str:
        """Complete a prompt."""
        return await self.chat(
            messages=[{"role": "user", "content": prompt}],
            model_config=model_config,
            **kwargs,
        )

    async def embed(self, text: str, model: str = None) -> List[float]:
        """Generate embeddings."""
        model = model or self.config.embedding_model.model_name

        try:
            response = await self.client.embeddings.create(
                model=model,
                input=text,
            )

            return response.data[0].embedding

        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise

    async def vision(self, image_data: bytes, prompt: str, model_config: ModelConfig = None, **kwargs) -> str:
        """Process image with GPT-4 Vision."""
        import base64

        model_config = model_config or self.config.vision_model
        image_b64 = base64.b64encode(image_data).decode("utf-8")

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                max_tokens=model_config.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_b64}",
                                },
                            },
                        ],
                    }
                ],
                **kwargs,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI vision error: {e}")
            raise


class AIClientManager:
    """Manages AI client instances."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.config = ai_config
        self._clients: Dict[AIProvider, AIClient] = {}
        self._request_counts: Dict[str, int] = {}
        self._last_request_time: Dict[str, float] = {}
        self._initialized = True

    def get_client(self, provider: AIProvider = None) -> AIClient:
        """Get AI client for provider."""
        provider = provider or self.config.default_provider

        if provider not in self._clients:
            if provider == AIProvider.ANTHROPIC:
                self._clients[provider] = AnthropicClient(self.config)
            elif provider == AIProvider.OPENAI:
                self._clients[provider] = OpenAIClient(self.config)
            else:
                raise ValueError(f"Unsupported provider: {provider}")

        return self._clients[provider]

    async def chat(self, messages: List[Dict], provider: AIProvider = None, **kwargs) -> str:
        """Send chat request to default or specified provider."""
        client = self.get_client(provider)
        return await client.chat(messages, **kwargs)

    async def complete(self, prompt: str, provider: AIProvider = None, **kwargs) -> str:
        """Send completion request."""
        client = self.get_client(provider)
        return await client.complete(prompt, **kwargs)

    async def embed(self, text: str) -> List[float]:
        """Generate embeddings (uses OpenAI)."""
        client = self.get_client(AIProvider.OPENAI)
        return await client.embed(text)

    async def vision(self, image_data: bytes, prompt: str, provider: AIProvider = None, **kwargs) -> str:
        """Process image with vision model."""
        client = self.get_client(provider)
        return await client.vision(image_data, prompt, **kwargs)


# Global client manager
ai_client = AIClientManager()
