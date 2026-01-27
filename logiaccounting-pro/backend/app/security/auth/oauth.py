"""
OAuth Manager
OAuth 2.0 authentication with Google, Microsoft, and GitHub
"""

import secrets
import hashlib
import base64
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List
from urllib.parse import urlencode
import logging
import httpx

logger = logging.getLogger(__name__)


class OAuthProvider(str, Enum):
    """Supported OAuth providers."""
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    GITHUB = "github"


@dataclass
class OAuthTokenData:
    """OAuth token response data."""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    id_token: Optional[str] = None
    expires_at: Optional[datetime] = None

    def __post_init__(self):
        if self.expires_at is None:
            self.expires_at = datetime.utcnow() + timedelta(seconds=self.expires_in)

    def is_expired(self) -> bool:
        """Check if the access token is expired."""
        if self.expires_at is None:
            return True
        return datetime.utcnow() >= self.expires_at


@dataclass
class OAuthUserInfo:
    """Normalized OAuth user information."""
    provider: OAuthProvider
    provider_user_id: str
    email: Optional[str] = None
    email_verified: bool = False
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None
    locale: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "provider": self.provider.value,
            "provider_user_id": self.provider_user_id,
            "email": self.email,
            "email_verified": self.email_verified,
            "name": self.name,
            "given_name": self.given_name,
            "family_name": self.family_name,
            "picture": self.picture,
            "locale": self.locale,
        }


@dataclass
class OAuthProviderConfig:
    """Configuration for an OAuth provider."""
    client_id: str
    client_secret: str
    authorize_url: str
    token_url: str
    userinfo_url: str
    scopes: List[str]
    redirect_uri: Optional[str] = None


class OAuthManager:
    """
    OAuth 2.0 Manager for third-party authentication.
    Supports Google, Microsoft, and GitHub.
    """

    PROVIDER_CONFIGS = {
        OAuthProvider.GOOGLE: {
            "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
            "scopes": ["openid", "email", "profile"],
        },
        OAuthProvider.MICROSOFT: {
            "authorize_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            "userinfo_url": "https://graph.microsoft.com/v1.0/me",
            "scopes": ["openid", "email", "profile", "User.Read"],
        },
        OAuthProvider.GITHUB: {
            "authorize_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "userinfo_url": "https://api.github.com/user",
            "scopes": ["user:email", "read:user"],
        },
    }

    def __init__(
        self,
        redirect_base_url: str,
        google_client_id: Optional[str] = None,
        google_client_secret: Optional[str] = None,
        microsoft_client_id: Optional[str] = None,
        microsoft_client_secret: Optional[str] = None,
        github_client_id: Optional[str] = None,
        github_client_secret: Optional[str] = None,
    ):
        self.redirect_base_url = redirect_base_url.rstrip("/")
        self._providers: Dict[OAuthProvider, OAuthProviderConfig] = {}
        self._state_store: Dict[str, Dict[str, Any]] = {}
        self._pkce_store: Dict[str, str] = {}

        if google_client_id and google_client_secret:
            self._configure_provider(
                OAuthProvider.GOOGLE,
                google_client_id,
                google_client_secret,
            )

        if microsoft_client_id and microsoft_client_secret:
            self._configure_provider(
                OAuthProvider.MICROSOFT,
                microsoft_client_id,
                microsoft_client_secret,
            )

        if github_client_id and github_client_secret:
            self._configure_provider(
                OAuthProvider.GITHUB,
                github_client_id,
                github_client_secret,
            )

    def _configure_provider(
        self,
        provider: OAuthProvider,
        client_id: str,
        client_secret: str,
    ) -> None:
        """Configure an OAuth provider."""
        config = self.PROVIDER_CONFIGS[provider]

        self._providers[provider] = OAuthProviderConfig(
            client_id=client_id,
            client_secret=client_secret,
            authorize_url=config["authorize_url"],
            token_url=config["token_url"],
            userinfo_url=config["userinfo_url"],
            scopes=config["scopes"],
            redirect_uri=f"{self.redirect_base_url}/auth/callback/{provider.value}",
        )

        logger.info(f"Configured OAuth provider: {provider.value}")

    def get_available_providers(self) -> List[OAuthProvider]:
        """Get list of configured OAuth providers."""
        return list(self._providers.keys())

    def is_provider_configured(self, provider: OAuthProvider) -> bool:
        """Check if a provider is configured."""
        return provider in self._providers

    def _generate_state(self) -> str:
        """Generate a secure state parameter."""
        return secrets.token_urlsafe(32)

    def _generate_pkce(self) -> tuple[str, str]:
        """Generate PKCE code verifier and challenge."""
        code_verifier = secrets.token_urlsafe(64)

        digest = hashlib.sha256(code_verifier.encode()).digest()
        code_challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")

        return code_verifier, code_challenge

    def get_authorization_url(
        self,
        provider: OAuthProvider,
        extra_scopes: Optional[List[str]] = None,
        state_data: Optional[Dict[str, Any]] = None,
        use_pkce: bool = True,
    ) -> tuple[str, str]:
        """
        Generate OAuth authorization URL.

        Args:
            provider: The OAuth provider
            extra_scopes: Additional scopes to request
            state_data: Additional data to associate with the state
            use_pkce: Whether to use PKCE (recommended)

        Returns:
            Tuple of (authorization_url, state)
        """
        if provider not in self._providers:
            raise ValueError(f"OAuth provider not configured: {provider.value}")

        config = self._providers[provider]
        state = self._generate_state()

        self._state_store[state] = {
            "provider": provider,
            "created_at": datetime.utcnow(),
            "data": state_data or {},
        }

        scopes = list(config.scopes)
        if extra_scopes:
            scopes.extend(extra_scopes)

        params = {
            "client_id": config.client_id,
            "redirect_uri": config.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "state": state,
        }

        if provider == OAuthProvider.GOOGLE:
            params["access_type"] = "offline"
            params["prompt"] = "consent"

        if provider == OAuthProvider.MICROSOFT:
            params["response_mode"] = "query"

        if use_pkce and provider != OAuthProvider.GITHUB:
            code_verifier, code_challenge = self._generate_pkce()
            self._pkce_store[state] = code_verifier
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"

        url = f"{config.authorize_url}?{urlencode(params)}"

        logger.debug(f"Generated authorization URL for {provider.value}")

        return url, state

    def validate_state(self, state: str, max_age_minutes: int = 10) -> Optional[Dict[str, Any]]:
        """
        Validate and consume OAuth state parameter.

        Args:
            state: The state parameter from the callback
            max_age_minutes: Maximum age of the state

        Returns:
            State data if valid, None otherwise
        """
        if state not in self._state_store:
            logger.warning("Invalid OAuth state: not found")
            return None

        state_data = self._state_store.pop(state)
        created_at = state_data["created_at"]

        if datetime.utcnow() - created_at > timedelta(minutes=max_age_minutes):
            logger.warning("Invalid OAuth state: expired")
            if state in self._pkce_store:
                del self._pkce_store[state]
            return None

        return state_data

    async def exchange_code(
        self,
        provider: OAuthProvider,
        code: str,
        state: str,
    ) -> OAuthTokenData:
        """
        Exchange authorization code for tokens.

        Args:
            provider: The OAuth provider
            code: The authorization code
            state: The state parameter (for PKCE lookup)

        Returns:
            OAuthTokenData with tokens
        """
        if provider not in self._providers:
            raise ValueError(f"OAuth provider not configured: {provider.value}")

        config = self._providers[provider]

        data = {
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "code": code,
            "redirect_uri": config.redirect_uri,
            "grant_type": "authorization_code",
        }

        if state in self._pkce_store:
            data["code_verifier"] = self._pkce_store.pop(state)

        headers = {"Accept": "application/json"}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                config.token_url,
                data=data,
                headers=headers,
            )

            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.text}")
                raise Exception(f"Token exchange failed: {response.status_code}")

            token_data = response.json()

        logger.info(f"Successfully exchanged code for tokens from {provider.value}")

        return OAuthTokenData(
            access_token=token_data["access_token"],
            token_type=token_data.get("token_type", "Bearer"),
            expires_in=token_data.get("expires_in", 3600),
            refresh_token=token_data.get("refresh_token"),
            scope=token_data.get("scope"),
            id_token=token_data.get("id_token"),
        )

    async def refresh_token(
        self,
        provider: OAuthProvider,
        refresh_token: str,
    ) -> OAuthTokenData:
        """
        Refresh an access token.

        Args:
            provider: The OAuth provider
            refresh_token: The refresh token

        Returns:
            New OAuthTokenData
        """
        if provider not in self._providers:
            raise ValueError(f"OAuth provider not configured: {provider.value}")

        config = self._providers[provider]

        data = {
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                config.token_url,
                data=data,
                headers={"Accept": "application/json"},
            )

            if response.status_code != 200:
                logger.error(f"Token refresh failed: {response.text}")
                raise Exception(f"Token refresh failed: {response.status_code}")

            token_data = response.json()

        logger.info(f"Successfully refreshed token from {provider.value}")

        return OAuthTokenData(
            access_token=token_data["access_token"],
            token_type=token_data.get("token_type", "Bearer"),
            expires_in=token_data.get("expires_in", 3600),
            refresh_token=token_data.get("refresh_token", refresh_token),
            scope=token_data.get("scope"),
            id_token=token_data.get("id_token"),
        )

    async def get_user_info(
        self,
        provider: OAuthProvider,
        access_token: str,
    ) -> OAuthUserInfo:
        """
        Get user information from OAuth provider.

        Args:
            provider: The OAuth provider
            access_token: The access token

        Returns:
            OAuthUserInfo with user details
        """
        if provider not in self._providers:
            raise ValueError(f"OAuth provider not configured: {provider.value}")

        config = self._providers[provider]

        headers = {"Authorization": f"Bearer {access_token}"}

        if provider == OAuthProvider.GITHUB:
            headers["Accept"] = "application/vnd.github+json"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                config.userinfo_url,
                headers=headers,
            )

            if response.status_code != 200:
                logger.error(f"Failed to get user info: {response.text}")
                raise Exception(f"Failed to get user info: {response.status_code}")

            user_data = response.json()

            if provider == OAuthProvider.GITHUB and not user_data.get("email"):
                emails_response = await client.get(
                    "https://api.github.com/user/emails",
                    headers=headers,
                )
                if emails_response.status_code == 200:
                    emails = emails_response.json()
                    primary_email = next(
                        (e for e in emails if e.get("primary")),
                        emails[0] if emails else None,
                    )
                    if primary_email:
                        user_data["email"] = primary_email.get("email")
                        user_data["email_verified"] = primary_email.get("verified", False)

        logger.info(f"Successfully retrieved user info from {provider.value}")

        return self._normalize_user_info(provider, user_data)

    def _normalize_user_info(
        self,
        provider: OAuthProvider,
        data: Dict[str, Any],
    ) -> OAuthUserInfo:
        """Normalize user info from different providers to a common format."""
        if provider == OAuthProvider.GOOGLE:
            return OAuthUserInfo(
                provider=provider,
                provider_user_id=data.get("sub", ""),
                email=data.get("email"),
                email_verified=data.get("email_verified", False),
                name=data.get("name"),
                given_name=data.get("given_name"),
                family_name=data.get("family_name"),
                picture=data.get("picture"),
                locale=data.get("locale"),
                raw_data=data,
            )

        elif provider == OAuthProvider.MICROSOFT:
            return OAuthUserInfo(
                provider=provider,
                provider_user_id=data.get("id", ""),
                email=data.get("mail") or data.get("userPrincipalName"),
                email_verified=True,
                name=data.get("displayName"),
                given_name=data.get("givenName"),
                family_name=data.get("surname"),
                picture=None,
                locale=data.get("preferredLanguage"),
                raw_data=data,
            )

        elif provider == OAuthProvider.GITHUB:
            name_parts = (data.get("name") or "").split(" ", 1)
            given_name = name_parts[0] if name_parts else None
            family_name = name_parts[1] if len(name_parts) > 1 else None

            return OAuthUserInfo(
                provider=provider,
                provider_user_id=str(data.get("id", "")),
                email=data.get("email"),
                email_verified=data.get("email_verified", False),
                name=data.get("name") or data.get("login"),
                given_name=given_name,
                family_name=family_name,
                picture=data.get("avatar_url"),
                locale=None,
                raw_data=data,
            )

        else:
            return OAuthUserInfo(
                provider=provider,
                provider_user_id=str(data.get("id", data.get("sub", ""))),
                email=data.get("email"),
                raw_data=data,
            )

    async def revoke_token(
        self,
        provider: OAuthProvider,
        token: str,
    ) -> bool:
        """
        Revoke an OAuth token.

        Args:
            provider: The OAuth provider
            token: The token to revoke

        Returns:
            True if successful
        """
        revoke_urls = {
            OAuthProvider.GOOGLE: "https://oauth2.googleapis.com/revoke",
            OAuthProvider.MICROSOFT: "https://login.microsoftonline.com/common/oauth2/v2.0/logout",
        }

        if provider not in revoke_urls:
            logger.warning(f"Token revocation not supported for {provider.value}")
            return False

        async with httpx.AsyncClient() as client:
            if provider == OAuthProvider.GOOGLE:
                response = await client.post(
                    revoke_urls[provider],
                    data={"token": token},
                )
            else:
                response = await client.get(
                    revoke_urls[provider],
                    params={"post_logout_redirect_uri": self.redirect_base_url},
                )

            success = response.status_code in (200, 204, 302)

            if success:
                logger.info(f"Successfully revoked token for {provider.value}")
            else:
                logger.warning(f"Failed to revoke token: {response.status_code}")

            return success

    def cleanup_expired_states(self, max_age_minutes: int = 10) -> int:
        """
        Clean up expired OAuth states.

        Returns:
            Number of states removed
        """
        cutoff = datetime.utcnow() - timedelta(minutes=max_age_minutes)
        expired = [
            state for state, data in self._state_store.items()
            if data["created_at"] < cutoff
        ]

        for state in expired:
            del self._state_store[state]
            if state in self._pkce_store:
                del self._pkce_store[state]

        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired OAuth states")

        return len(expired)
