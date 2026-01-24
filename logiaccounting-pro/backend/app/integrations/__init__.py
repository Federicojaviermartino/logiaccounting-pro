"""
Integrations Module
Central hub for all integration providers
"""

from app.integrations.base import (
    BaseIntegration,
    IntegrationStatus,
    IntegrationCategory,
    IntegrationCapability,
    IntegrationError,
    WebhookEvent,
    SyncResult,
)
from app.integrations.registry import registry, register_integration
from app.integrations.connection import connection_manager, Connection


__all__ = [
    # Base classes
    'BaseIntegration',
    'IntegrationStatus',
    'IntegrationCategory',
    'IntegrationCapability',
    'IntegrationError',
    'WebhookEvent',
    'SyncResult',

    # Registry
    'registry',
    'register_integration',

    # Connection
    'connection_manager',
    'Connection',
]


def init_integrations():
    """Initialize all integration providers."""
    # Import providers to register them
    from app.integrations.providers import stripe, paypal, quickbooks, xero, zapier, slack

    print(f"[Integrations] Registered {len(registry.provider_ids)} providers:")
    for provider_id in registry.provider_ids:
        print(f"  - {provider_id}")
