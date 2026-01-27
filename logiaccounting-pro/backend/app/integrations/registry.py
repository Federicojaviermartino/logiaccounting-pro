"""
Integration Registry
Central catalog of available integrations
"""

from typing import Dict, Type, List, Optional
from app.integrations.base import BaseIntegration, IntegrationCategory
import logging

logger = logging.getLogger(__name__)


class IntegrationRegistry:
    """Manages registration and discovery of integrations."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._integrations: Dict[str, Type[BaseIntegration]] = {}
            cls._instance._initialized = False
        return cls._instance

    def register(self, integration_class: Type[BaseIntegration]):
        """Register an integration provider."""
        provider_id = integration_class.PROVIDER_ID

        if not provider_id:
            raise ValueError("Integration must have a PROVIDER_ID")

        if provider_id in self._integrations:
            logger.warning(f"Overwriting existing integration: {provider_id}")

        self._integrations[provider_id] = integration_class
        logger.info(f"Registered integration: {provider_id}")

    def get(self, provider_id: str) -> Optional[Type[BaseIntegration]]:
        """Get integration class by provider ID."""
        return self._integrations.get(provider_id)

    def create_instance(self, provider_id: str, credentials: Dict = None) -> Optional[BaseIntegration]:
        """Create an instance of an integration."""
        integration_class = self.get(provider_id)
        if integration_class:
            return integration_class(credentials=credentials)
        return None

    def list_all(self) -> List[Dict]:
        """List all registered integrations."""
        return [
            cls(credentials={}).get_metadata()
            for cls in self._integrations.values()
        ]

    def list_by_category(self, category: IntegrationCategory) -> List[Dict]:
        """List integrations by category."""
        return [
            cls(credentials={}).get_metadata()
            for cls in self._integrations.values()
            if cls.CATEGORY == category
        ]

    def get_categories(self) -> List[Dict]:
        """Get all categories with their integrations."""
        categories = {}

        for cls in self._integrations.values():
            cat = cls.CATEGORY.value
            if cat not in categories:
                categories[cat] = {
                    "id": cat,
                    "name": cat.replace("_", " ").title(),
                    "integrations": [],
                }
            categories[cat]["integrations"].append(cls(credentials={}).get_metadata())

        return list(categories.values())

    @property
    def provider_ids(self) -> List[str]:
        """Get list of registered provider IDs."""
        return list(self._integrations.keys())


# Global registry instance
registry = IntegrationRegistry()


def register_integration(cls: Type[BaseIntegration]) -> Type[BaseIntegration]:
    """Decorator to register an integration."""
    registry.register(cls)
    return cls
