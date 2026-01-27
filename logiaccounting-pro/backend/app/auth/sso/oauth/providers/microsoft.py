"""
Microsoft Azure AD / Entra ID OAuth2/OIDC Provider
"""

from typing import Dict, Any, List, Optional
from app.auth.sso.oauth.providers.base import OAuthProvider, OAuthUserInfo, OAuthError

try:
    import httpx
except ImportError:
    httpx = None


class MicrosoftOAuthProvider(OAuthProvider):
    """Microsoft Azure AD / Entra ID OAuth2/OIDC provider"""

    PROVIDER_NAME = "microsoft"

    DEFAULT_SCOPES = [
        "openid",
        "email",
        "profile",
        "User.Read",
        "offline_access",
    ]

    GROUP_SCOPES = [
        "GroupMember.Read.All",
    ]

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: List[str] = None,
        tenant_id: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scopes=scopes,
            tenant_id=tenant_id,
            **kwargs,
        )
        self.tenant_id = tenant_id or "common"

    def _get_base_url(self) -> str:
        """Get Azure AD base URL for tenant"""
        return f"https://login.microsoftonline.com/{self.tenant_id}"

    def _get_authorization_endpoint(self) -> str:
        return f"{self._get_base_url()}/oauth2/v2.0/authorize"

    def _get_token_endpoint(self) -> str:
        return f"{self._get_base_url()}/oauth2/v2.0/token"

    def _get_userinfo_endpoint(self) -> str:
        return "https://graph.microsoft.com/v1.0/me"

    def _get_jwks_uri(self) -> str:
        return f"{self._get_base_url()}/discovery/v2.0/keys"

    def _get_end_session_endpoint(self) -> str:
        return f"{self._get_base_url()}/oauth2/v2.0/logout"

    def _get_expected_issuer(self) -> str:
        if self.tenant_id == "common":
            return None
        return f"https://login.microsoftonline.com/{self.tenant_id}/v2.0"

    def _normalize_user_info(self, user_data: Dict[str, Any]) -> OAuthUserInfo:
        """Normalize Microsoft Graph API user data"""
        return OAuthUserInfo(
            provider_user_id=user_data.get("id", ""),
            email=user_data.get("mail") or user_data.get("userPrincipalName", ""),
            email_verified=True,
            first_name=user_data.get("givenName"),
            last_name=user_data.get("surname"),
            display_name=user_data.get("displayName"),
            picture_url=None,
            groups=[],
            raw_attributes=user_data,
        )

    async def get_user_groups(self, access_token: str) -> List[str]:
        """Get user's group memberships from Microsoft Graph"""
        if httpx is None:
            return []

        groups = []
        url = "https://graph.microsoft.com/v1.0/me/memberOf"

        try:
            async with httpx.AsyncClient() as client:
                while url:
                    response = await client.get(
                        url,
                        headers={"Authorization": f"Bearer {access_token}"},
                    )

                    if response.status_code != 200:
                        break

                    data = response.json()
                    for item in data.get("value", []):
                        if item.get("@odata.type") == "#microsoft.graph.group":
                            groups.append(item.get("displayName", item.get("id")))

                    url = data.get("@odata.nextLink")

        except Exception:
            pass

        return groups

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Get user information including groups"""
        user_info = await super().get_user_info(access_token)

        if "GroupMember.Read.All" in self.scopes:
            user_info.groups = await self.get_user_groups(access_token)

        return user_info

    def generate_authorization_url(
        self,
        state: Optional[str] = None,
        nonce: Optional[str] = None,
        login_hint: Optional[str] = None,
        extra_params: Dict[str, str] = None,
    ) -> tuple[str, str, str]:
        """Generate authorization URL with Microsoft-specific params"""
        extra = extra_params or {}

        if self.tenant_id and self.tenant_id != "common":
            extra["domain_hint"] = self.tenant_id

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
        """Validate Microsoft ID token with multi-tenant support"""
        try:
            import jwt as pyjwt
            from jwt import PyJWKClient
        except ImportError:
            raise OAuthError("PyJWT library not installed")

        jwks_uri = self._get_jwks_uri()

        try:
            jwks_client = PyJWKClient(jwks_uri)
            signing_key = jwks_client.get_signing_key_from_jwt(id_token)

            options = {"verify_exp": True, "verify_iat": True}

            if self.tenant_id == "common":
                options["verify_iss"] = False

            claims = pyjwt.decode(
                id_token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.client_id,
                options=options,
            )

            if nonce and claims.get("nonce") != nonce:
                raise OAuthError("Invalid nonce", "invalid_nonce")

            return claims

        except pyjwt.ExpiredSignatureError:
            raise OAuthError("ID token expired", "token_expired")
        except pyjwt.InvalidTokenError as e:
            raise OAuthError(f"Invalid ID token: {str(e)}", "invalid_token")
