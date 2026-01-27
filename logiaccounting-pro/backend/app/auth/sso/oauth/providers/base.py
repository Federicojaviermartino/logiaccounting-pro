"""
Base OAuth2/OIDC Provider Implementation
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import os
import secrets
import hashlib
import base64
import time
import json
import urllib.parse

try:
    import httpx
except ImportError:
    httpx = None

try:
    import jwt
    from jwt import PyJWKClient
except ImportError:
    jwt = None
    PyJWKClient = None


class OAuthError(Exception):
    """OAuth authentication error"""

    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


@dataclass
class OAuthTokens:
    """OAuth token response"""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
    scope: Optional[str] = None


@dataclass
class OAuthUserInfo:
    """Normalized user information from OAuth provider"""
    provider_user_id: str
    email: str
    email_verified: bool = False
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    picture_url: Optional[str] = None
    groups: List[str] = None
    raw_attributes: Dict[str, Any] = None

    def __post_init__(self):
        if self.groups is None:
            self.groups = []
        if self.raw_attributes is None:
            self.raw_attributes = {}


class OAuthProvider(ABC):
    """Abstract base class for OAuth2/OIDC providers"""

    PROVIDER_NAME: str = "generic"
    AUTHORIZATION_ENDPOINT: str = ""
    TOKEN_ENDPOINT: str = ""
    USERINFO_ENDPOINT: str = ""
    JWKS_URI: str = ""
    REVOCATION_ENDPOINT: str = ""
    END_SESSION_ENDPOINT: str = ""

    DEFAULT_SCOPES: List[str] = ["openid", "email", "profile"]

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: List[str] = None,
        tenant_id: Optional[str] = None,
        domain: Optional[str] = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes or self.DEFAULT_SCOPES
        self.tenant_id = tenant_id
        self.domain = domain

        self._state_store: Dict[str, Dict] = {}
        self._nonce_store: Dict[str, str] = {}

    def generate_authorization_url(
        self,
        state: Optional[str] = None,
        nonce: Optional[str] = None,
        login_hint: Optional[str] = None,
        extra_params: Dict[str, str] = None,
    ) -> tuple[str, str, str]:
        """
        Generate OAuth authorization URL.
        Returns: (authorization_url, state, nonce)
        """
        state = state or secrets.token_urlsafe(32)
        nonce = nonce or secrets.token_urlsafe(32)

        code_verifier = secrets.token_urlsafe(64)
        code_challenge = self._generate_code_challenge(code_verifier)

        self._state_store[state] = {
            "code_verifier": code_verifier,
            "nonce": nonce,
            "created_at": time.time(),
        }

        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes),
            "state": state,
            "nonce": nonce,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        if login_hint:
            params["login_hint"] = login_hint

        if extra_params:
            params.update(extra_params)

        authorization_url = f"{self._get_authorization_endpoint()}?{urllib.parse.urlencode(params)}"

        return authorization_url, state, nonce

    async def exchange_code(
        self,
        code: str,
        state: str,
    ) -> OAuthTokens:
        """Exchange authorization code for tokens"""
        if httpx is None:
            raise OAuthError("httpx library not installed")

        state_data = self._state_store.pop(state, None)
        if not state_data:
            raise OAuthError("Invalid or expired state", "invalid_state")

        if time.time() - state_data["created_at"] > 600:
            raise OAuthError("State expired", "state_expired")

        code_verifier = state_data["code_verifier"]

        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
            "code_verifier": code_verifier,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._get_token_endpoint(),
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise OAuthError(
                    error_data.get("error_description", "Token exchange failed"),
                    error_data.get("error", "token_error"),
                    error_data,
                )

            token_data = response.json()

        return OAuthTokens(
            access_token=token_data["access_token"],
            token_type=token_data.get("token_type", "Bearer"),
            expires_in=token_data.get("expires_in", 3600),
            refresh_token=token_data.get("refresh_token"),
            id_token=token_data.get("id_token"),
            scope=token_data.get("scope"),
        )

    async def refresh_access_token(self, refresh_token: str) -> OAuthTokens:
        """Refresh access token using refresh token"""
        if httpx is None:
            raise OAuthError("httpx library not installed")

        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._get_token_endpoint(),
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise OAuthError(
                    error_data.get("error_description", "Token refresh failed"),
                    error_data.get("error", "refresh_error"),
                    error_data,
                )

            token_data = response.json()

        return OAuthTokens(
            access_token=token_data["access_token"],
            token_type=token_data.get("token_type", "Bearer"),
            expires_in=token_data.get("expires_in", 3600),
            refresh_token=token_data.get("refresh_token", refresh_token),
            id_token=token_data.get("id_token"),
            scope=token_data.get("scope"),
        )

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Get user information from provider"""
        if httpx is None:
            raise OAuthError("httpx library not installed")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self._get_userinfo_endpoint(),
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code != 200:
                raise OAuthError("Failed to get user info", "userinfo_error")

            user_data = response.json()

        return self._normalize_user_info(user_data)

    def validate_id_token(
        self,
        id_token: str,
        nonce: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Validate and decode ID token"""
        if jwt is None or PyJWKClient is None:
            raise OAuthError("PyJWT library not installed")

        jwks_uri = self._get_jwks_uri()
        if not jwks_uri:
            raise OAuthError("JWKS URI not configured", "config_error")

        try:
            jwks_client = PyJWKClient(jwks_uri)
            signing_key = jwks_client.get_signing_key_from_jwt(id_token)

            claims = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=["RS256", "ES256"],
                audience=self.client_id,
                issuer=self._get_expected_issuer(),
                options={"verify_exp": True, "verify_iat": True},
            )

            if nonce and claims.get("nonce") != nonce:
                raise OAuthError("Invalid nonce", "invalid_nonce")

            return claims

        except jwt.ExpiredSignatureError:
            raise OAuthError("ID token expired", "token_expired")
        except jwt.InvalidTokenError as e:
            raise OAuthError(f"Invalid ID token: {str(e)}", "invalid_token")

    async def revoke_token(self, token: str, token_type: str = "access_token") -> bool:
        """Revoke a token"""
        if httpx is None:
            return False

        revocation_endpoint = self._get_revocation_endpoint()
        if not revocation_endpoint:
            return False

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "token": token,
            "token_type_hint": token_type,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    revocation_endpoint,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                return response.status_code == 200
        except Exception:
            return False

    def get_logout_url(self, id_token: str = None, post_logout_uri: str = None) -> Optional[str]:
        """Get logout URL for single logout"""
        end_session_endpoint = self._get_end_session_endpoint()
        if not end_session_endpoint:
            return None

        params = {}
        if id_token:
            params["id_token_hint"] = id_token
        if post_logout_uri:
            params["post_logout_redirect_uri"] = post_logout_uri

        if params:
            return f"{end_session_endpoint}?{urllib.parse.urlencode(params)}"
        return end_session_endpoint

    @abstractmethod
    def _normalize_user_info(self, user_data: Dict[str, Any]) -> OAuthUserInfo:
        """Normalize provider-specific user data to standard format"""
        pass

    def _get_authorization_endpoint(self) -> str:
        """Get authorization endpoint URL"""
        return self.AUTHORIZATION_ENDPOINT

    def _get_token_endpoint(self) -> str:
        """Get token endpoint URL"""
        return self.TOKEN_ENDPOINT

    def _get_userinfo_endpoint(self) -> str:
        """Get userinfo endpoint URL"""
        return self.USERINFO_ENDPOINT

    def _get_jwks_uri(self) -> str:
        """Get JWKS URI"""
        return self.JWKS_URI

    def _get_revocation_endpoint(self) -> Optional[str]:
        """Get token revocation endpoint URL"""
        return self.REVOCATION_ENDPOINT or None

    def _get_end_session_endpoint(self) -> Optional[str]:
        """Get end session endpoint URL"""
        return self.END_SESSION_ENDPOINT or None

    def _get_expected_issuer(self) -> str:
        """Get expected token issuer for validation"""
        return self._get_authorization_endpoint().rsplit("/", 1)[0]

    def _generate_code_challenge(self, verifier: str) -> str:
        """Generate PKCE code challenge from verifier"""
        digest = hashlib.sha256(verifier.encode()).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

    @classmethod
    def from_connection(cls, connection: Dict[str, Any], redirect_uri: str) -> "OAuthProvider":
        """Create provider instance from SSO connection data"""
        config = connection.get("configuration", {})
        return cls(
            client_id=config.get("client_id", ""),
            client_secret=config.get("client_secret", ""),
            redirect_uri=redirect_uri,
            scopes=config.get("scopes", cls.DEFAULT_SCOPES),
            tenant_id=config.get("tenant_id"),
            domain=config.get("domain"),
        )
