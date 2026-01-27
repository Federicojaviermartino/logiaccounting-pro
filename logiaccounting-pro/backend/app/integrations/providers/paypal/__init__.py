"""
PayPal Integration Provider
"""

from app.integrations.providers.paypal.client import PayPalIntegration
from app.integrations.providers.paypal.webhooks import paypal_webhook_handler, PayPalWebhookHandler


__all__ = [
    'PayPalIntegration',
    'paypal_webhook_handler',
    'PayPalWebhookHandler',
]
