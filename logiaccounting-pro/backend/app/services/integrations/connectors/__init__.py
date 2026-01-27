"""
Phase 14: Integration Connectors
All platform-specific connectors
"""

from .quickbooks import QuickBooksConnector
from .xero import XeroConnector
from .salesforce import SalesforceConnector
from .hubspot import HubSpotConnector
from .shopify import ShopifyConnector
from .stripe import StripeConnector
from .plaid import PlaidConnector

# Connector registry
CONNECTORS = {
    "quickbooks": QuickBooksConnector,
    "xero": XeroConnector,
    "salesforce": SalesforceConnector,
    "hubspot": HubSpotConnector,
    "shopify": ShopifyConnector,
    "stripe": StripeConnector,
    "plaid": PlaidConnector,
}


def get_connector_class(provider: str):
    """Get connector class for a provider"""
    return CONNECTORS.get(provider)


def get_available_connectors():
    """Get list of available connectors"""
    return list(CONNECTORS.keys())


__all__ = [
    "QuickBooksConnector",
    "XeroConnector",
    "SalesforceConnector",
    "HubSpotConnector",
    "ShopifyConnector",
    "StripeConnector",
    "PlaidConnector",
    "CONNECTORS",
    "get_connector_class",
    "get_available_connectors",
]
