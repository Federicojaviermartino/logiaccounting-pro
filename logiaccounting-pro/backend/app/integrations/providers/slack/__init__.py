"""
Slack Integration Provider
"""

from app.integrations.providers.slack.client import SlackIntegration
from app.integrations.providers.slack.commands import SlackCommandHandler


__all__ = [
    'SlackIntegration',
    'SlackCommandHandler',
]
