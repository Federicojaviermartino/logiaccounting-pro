"""
Okta OAuth2/OIDC Provider
"""

from typing import Dict, Any, List, Optional
from app.auth.sso.oauth.providers.base import OAuthProvider, OAuthUserInfo, OAuthError

try:
    import httpx
except ImportError:
    httpx = None


class OktaOAuthProvider(OAuthProvider):
    """Okta OAuth2/OIDC provider"""

    PROVIDER_NAME = "okta"

    DEFAULT_SCOPES = [
        "openid",
        "email",
        "profile",
        "groups",
        "offline_access",
    ]

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: List[str] = None,
        domain: str = None,
        authorization_server: str = "default",
        **kwargs,
    ):
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scopes=scopes,
            domain=domain,
            **kwargs,
        )

        if not domain:
            raise OAuthError("Okta domain is required", "config_error")

        self.okta_domain = domain
        self.authorization_server = authorization_server

    def _get_base_url(self) -> str:
        """Get Okta base URL"""
        domain = self.okta_domain
        if not domain.startswith("https://"):
            domain = f"https://{domain}"
        if domain.endswith("/"):
            domain = domain[:-1]

        if self.authorization_server:
            return f"{domain}/oauth2/{self.authorization_server}"
        return f"{domain}/oauth2"

    def _get_authorization_endpoint(self) -> str:
        return f"{self._get_base_url()}/v1/authorize"

    def _get_token_endpoint(self) -> str:
        return f"{self._get_base_url()}/v1/token"

    def _get_userinfo_endpoint(self) -> str:
        return f"{self._get_base_url()}/v1/userinfo"

    def _get_jwks_uri(self) -> str:
        return f"{self._get_base_url()}/v1/keys"

    def _get_revocation_endpoint(self) -> str:
        return f"{self._get_base_url()}/v1/revoke"

    def _get_end_session_endpoint(self) -> str:
        return f"{self._get_base_url()}/v1/logout"

    def _get_expected_issuer(self) -> str:
        return self._get_base_url()

    def _normalize_user_info(self, user_data: Dict[str, Any]) -> OAuthUserInfo:
        """Normalize Okta userinfo response"""
        groups = user_data.get("groups", [])
        if isinstance(groups, str):
            groups = [groups]

        return OAuthUserInfo(
            provider_user_id=user_data.get("sub", ""),
            email=user_data.get("email", ""),
            email_verified=user_data.get("email_verified", False),
            first_name=user_data.get("given_name"),
            last_name=user_data.get("family_name"),
            display_name=user_data.get("name"),
            picture_url=user_data.get("picture"),
            groups=groups,
            raw_attributes=user_data,
        )

    def validate_id_token(
        self,
        id_token: str,
        nonce: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Validate Okta ID token and extract groups"""
        claims = super().validate_id_token(id_token, nonce)
        return claims

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Get user info from Okta with groups from token"""
        user_info = await super().get_user_info(access_token)
        return user_info

    def generate_authorization_url(
        self,
        state: Optional[str] = None,
        nonce: Optional[str] = None,
        login_hint: Optional[str] = None,
        extra_params: Dict[str, str] = None,
    ) -> tuple[str, str, str]:
        """Generate authorization URL with Okta-specific params"""
        extra = extra_params or {}

        extra["prompt"] = "login"

        return super().generate_authorization_url(
            state=state,
            nonce=nonce,
            login_hint=login_hint,
            extra_params=extra,
        )

    async def introspect_token(self, token: str, token_type: str = "access_token") -> Dict[str, Any]:
        """Introspect a token to get its claims and status"""
        if httpx is None:
            raise OAuthError("httpx library not installed")

        introspect_url = f"{self._get_base_url()}/v1/introspect"

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "token": token,
            "token_type_hint": token_type,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                introspect_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                raise OAuthError("Token introspection failed", "introspect_error")

            return response.json()
