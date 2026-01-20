"""
Google OAuth2/OIDC Provider
"""

from typing import Dict, Any, List, Optional
from app.auth.sso.oauth.providers.base import OAuthProvider, OAuthUserInfo


class GoogleOAuthProvider(OAuthProvider):
    """Google OAuth2/OIDC provider"""

    PROVIDER_NAME = "google"

    AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
    USERINFO_ENDPOINT = "https://openidconnect.googleapis.com/v1/userinfo"
    JWKS_URI = "https://www.googleapis.com/oauth2/v3/certs"
    REVOCATION_ENDPOINT = "https://oauth2.googleapis.com/revoke"

    DEFAULT_SCOPES = [
        "openid",
        "email",
        "profile",
    ]

    WORKSPACE_SCOPES = [
        "https://www.googleapis.com/auth/admin.directory.group.readonly",
    ]

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: List[str] = None,
        hosted_domain: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scopes=scopes,
            **kwargs,
        )
        self.hosted_domain = hosted_domain or kwargs.get("domain")

    def _get_expected_issuer(self) -> str:
        return "https://accounts.google.com"

    def _normalize_user_info(self, user_data: Dict[str, Any]) -> OAuthUserInfo:
        """Normalize Google userinfo response"""
        return OAuthUserInfo(
            provider_user_id=user_data.get("sub", ""),
            email=user_data.get("email", ""),
            email_verified=user_data.get("email_verified", False),
            first_name=user_data.get("given_name"),
            last_name=user_data.get("family_name"),
            display_name=user_data.get("name"),
            picture_url=user_data.get("picture"),
            groups=[],
            raw_attributes=user_data,
        )

    def generate_authorization_url(
        self,
        state: Optional[str] = None,
        nonce: Optional[str] = None,
        login_hint: Optional[str] = None,
        extra_params: Dict[str, str] = None,
    ) -> tuple[str, str, str]:
        """Generate authorization URL with Google-specific params"""
        extra = extra_params or {}

        if self.hosted_domain:
            extra["hd"] = self.hosted_domain

        extra["access_type"] = "offline"
        extra["prompt"] = "consent"

        return super().generate_authorization_url(
            state=state,
            nonce=nonce,
            login_hint=login_hint,
            extra_params=extra,
        )

    def validate_id_token(
        self,
        id_token: str,
        nonce: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Validate Google ID token with hosted domain check"""
        claims = super().validate_id_token(id_token, nonce)

        if self.hosted_domain:
            token_hd = claims.get("hd")
            if token_hd != self.hosted_domain:
                from app.auth.sso.oauth.providers.base import OAuthError
                raise OAuthError(
                    f"Invalid hosted domain: expected {self.hosted_domain}, got {token_hd}",
                    "invalid_hd"
                )

        return claims
