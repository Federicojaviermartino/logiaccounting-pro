"""
GitHub OAuth2 Provider
"""

from typing import Dict, Any, List, Optional
from app.auth.sso.oauth.providers.base import OAuthProvider, OAuthUserInfo, OAuthError

try:
    import httpx
except ImportError:
    httpx = None


class GitHubOAuthProvider(OAuthProvider):
    """GitHub OAuth2 provider"""

    PROVIDER_NAME = "github"

    AUTHORIZATION_ENDPOINT = "https://github.com/login/oauth/authorize"
    TOKEN_ENDPOINT = "https://github.com/login/oauth/access_token"
    USERINFO_ENDPOINT = "https://api.github.com/user"

    DEFAULT_SCOPES = [
        "read:user",
        "user:email",
    ]

    ORGANIZATION_SCOPES = [
        "read:org",
    ]

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: List[str] = None,
        allowed_organizations: List[str] = None,
        **kwargs,
    ):
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scopes=scopes,
            **kwargs,
        )
        self.allowed_organizations = allowed_organizations or []

    def _get_jwks_uri(self) -> str:
        return ""

    def _normalize_user_info(self, user_data: Dict[str, Any]) -> OAuthUserInfo:
        """Normalize GitHub user data"""
        name_parts = (user_data.get("name") or "").split(" ", 1)
        first_name = name_parts[0] if name_parts else None
        last_name = name_parts[1] if len(name_parts) > 1 else None

        return OAuthUserInfo(
            provider_user_id=str(user_data.get("id", "")),
            email=user_data.get("email", ""),
            email_verified=True,
            first_name=first_name,
            last_name=last_name,
            display_name=user_data.get("name") or user_data.get("login"),
            picture_url=user_data.get("avatar_url"),
            groups=[],
            raw_attributes=user_data,
        )

    async def exchange_code(
        self,
        code: str,
        state: str,
    ):
        """Exchange code for tokens with GitHub-specific handling"""
        if httpx is None:
            raise OAuthError("httpx library not installed")

        state_data = self._state_store.pop(state, None)
        if not state_data:
            raise OAuthError("Invalid or expired state", "invalid_state")

        import time
        if time.time() - state_data["created_at"] > 600:
            raise OAuthError("State expired", "state_expired")

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_ENDPOINT,
                data=data,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise OAuthError(
                    error_data.get("error_description", "Token exchange failed"),
                    error_data.get("error", "token_error"),
                    error_data,
                )

            token_data = response.json()

            if "error" in token_data:
                raise OAuthError(
                    token_data.get("error_description", token_data["error"]),
                    token_data["error"],
                    token_data,
                )

        from app.auth.sso.oauth.providers.base import OAuthTokens
        return OAuthTokens(
            access_token=token_data["access_token"],
            token_type=token_data.get("token_type", "bearer"),
            expires_in=0,
            refresh_token=token_data.get("refresh_token"),
            scope=token_data.get("scope"),
        )

    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Get user info including primary email"""
        if httpx is None:
            raise OAuthError("httpx library not installed")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.USERINFO_ENDPOINT,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )

            if response.status_code != 200:
                raise OAuthError("Failed to get user info", "userinfo_error")

            user_data = response.json()

            if not user_data.get("email"):
                email_response = await client.get(
                    "https://api.github.com/user/emails",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                )

                if email_response.status_code == 200:
                    emails = email_response.json()
                    primary_email = next(
                        (e["email"] for e in emails if e.get("primary")),
                        emails[0]["email"] if emails else None
                    )
                    user_data["email"] = primary_email

            if self.allowed_organizations:
                orgs = await self.get_user_organizations(access_token)
                if not any(org in self.allowed_organizations for org in orgs):
                    raise OAuthError(
                        "User is not a member of allowed organizations",
                        "org_membership_required"
                    )

        user_info = self._normalize_user_info(user_data)

        if "read:org" in self.scopes:
            user_info.groups = await self.get_user_organizations(access_token)

        return user_info

    async def get_user_organizations(self, access_token: str) -> List[str]:
        """Get user's GitHub organization memberships"""
        if httpx is None:
            return []

        organizations = []

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.github.com/user/orgs",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                )

                if response.status_code == 200:
                    orgs = response.json()
                    organizations = [org["login"] for org in orgs]

        except Exception:
            pass

        return organizations

    async def get_user_teams(self, access_token: str, org: str) -> List[str]:
        """Get user's team memberships in an organization"""
        if httpx is None:
            return []

        teams = []

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.github.com/user/teams",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                )

                if response.status_code == 200:
                    all_teams = response.json()
                    teams = [
                        team["slug"]
                        for team in all_teams
                        if team.get("organization", {}).get("login") == org
                    ]

        except Exception:
            pass

        return teams

    def generate_authorization_url(
        self,
        state: Optional[str] = None,
        nonce: Optional[str] = None,
        login_hint: Optional[str] = None,
        extra_params: Dict[str, str] = None,
    ) -> tuple[str, str, str]:
        """Generate GitHub authorization URL"""
        import secrets
        import time
        import urllib.parse

        state = state or secrets.token_urlsafe(32)
        nonce = nonce or secrets.token_urlsafe(32)

        self._state_store[state] = {
            "nonce": nonce,
            "created_at": time.time(),
        }

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes),
            "state": state,
        }

        if login_hint:
            params["login"] = login_hint

        if extra_params:
            params.update(extra_params)

        authorization_url = f"{self.AUTHORIZATION_ENDPOINT}?{urllib.parse.urlencode(params)}"

        return authorization_url, state, nonce

    def validate_id_token(self, id_token: str, nonce: Optional[str] = None) -> Dict[str, Any]:
        """GitHub doesn't use ID tokens - raise error"""
        raise OAuthError("GitHub does not support OpenID Connect", "not_supported")
