"""
OAuth2 Provider Implementations
"""

from app.auth.sso.oauth.providers.base import OAuthProvider, OAuthError
from app.auth.sso.oauth.providers.microsoft import MicrosoftOAuthProvider
from app.auth.sso.oauth.providers.google import GoogleOAuthProvider
from app.auth.sso.oauth.providers.okta import OktaOAuthProvider
from app.auth.sso.oauth.providers.github import GitHubOAuthProvider

__all__ = [
    "OAuthProvider",
    "OAuthError",
    "MicrosoftOAuthProvider",
    "GoogleOAuthProvider",
    "OktaOAuthProvider",
    "GitHubOAuthProvider",
]
