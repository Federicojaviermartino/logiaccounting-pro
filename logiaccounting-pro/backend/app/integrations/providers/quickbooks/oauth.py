"""
QuickBooks OAuth Handler
Manages OAuth flow for QuickBooks
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
import base64
import logging

logger = logging.getLogger(__name__)


class QuickBooksOAuth:
    """Handles QuickBooks OAuth flow."""

    TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    REVOKE_URL = "https://developer.api.intuit.com/v2/oauth2/tokens/revoke"

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_authorization_url(self, state: str, scopes: list = None) -> str:
        """Generate OAuth authorization URL."""
        if scopes is None:
            scopes = ["com.intuit.quickbooks.accounting"]

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "state": state,
        }

        base_url = "https://appcenter.intuit.com/connect/oauth2"
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{base_url}?{query}"

    async def exchange_code(self, code: str) -> Dict:
        """Exchange authorization code for tokens."""
        import aiohttp

        auth = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.TOKEN_URL, headers=headers, data=data) as response:
                result = await response.json()

                if response.status != 200:
                    logger.error(f"[QuickBooks OAuth] Token exchange failed: {result}")
                    raise Exception(result.get("error_description", "Token exchange failed"))

                return {
                    "access_token": result["access_token"],
                    "refresh_token": result["refresh_token"],
                    "expires_in": result["expires_in"],
                    "token_type": result["token_type"],
                    "obtained_at": datetime.utcnow().isoformat(),
                }

    async def refresh_token(self, refresh_token: str) -> Dict:
        """Refresh access token."""
        import aiohttp

        auth = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.TOKEN_URL, headers=headers, data=data) as response:
                result = await response.json()

                if response.status != 200:
                    logger.error(f"[QuickBooks OAuth] Token refresh failed: {result}")
                    raise Exception(result.get("error_description", "Token refresh failed"))

                return {
                    "access_token": result["access_token"],
                    "refresh_token": result.get("refresh_token", refresh_token),
                    "expires_in": result["expires_in"],
                    "token_type": result["token_type"],
                    "refreshed_at": datetime.utcnow().isoformat(),
                }

    async def revoke_token(self, token: str) -> bool:
        """Revoke access or refresh token."""
        import aiohttp

        auth = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        data = {"token": token}

        async with aiohttp.ClientSession() as session:
            async with session.post(self.REVOKE_URL, headers=headers, json=data) as response:
                return response.status == 200

    def is_token_expired(self, obtained_at: str, expires_in: int, buffer_minutes: int = 5) -> bool:
        """Check if token is expired or about to expire."""
        obtained = datetime.fromisoformat(obtained_at)
        expires_at = obtained + timedelta(seconds=expires_in)
        buffer = timedelta(minutes=buffer_minutes)

        return datetime.utcnow() >= (expires_at - buffer)
