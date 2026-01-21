# LogiAccounting Pro - Phase 12 Tasks Part 2

## OAUTH2 / OPENID CONNECT IMPLEMENTATION

---

## TASK 4: OAUTH2 PROVIDER SYSTEM

### 4.1 OAuth Module Init

**File:** `backend/app/auth/sso/oauth/__init__.py`

```python
"""
OAuth2 / OpenID Connect Authentication Module
"""

from .providers.base import OAuthProvider, OAuthUserInfo
from .providers.microsoft import MicrosoftProvider
from .providers.google import GoogleProvider
from .providers.okta import OktaProvider
from .providers.github import GitHubProvider
from .token_handler import OAuthTokenHandler
from .state_manager import OAuthStateManager

__all__ = [
    'OAuthProvider',
    'OAuthUserInfo',
    'MicrosoftProvider',
    'GoogleProvider',
    'OktaProvider',
    'GitHubProvider',
    'OAuthTokenHandler',
    'OAuthStateManager',
    'get_provider',
]


def get_provider(connection) -> OAuthProvider:
    """
    Factory function to get OAuth provider for connection
    """
    from flask import current_app
    import os
    
    base_url = os.getenv('BASE_URL', 'https://logiaccounting-pro.onrender.com')
    redirect_uri = f"{base_url}/api/v1/auth/sso/oauth/{connection.id}/callback"
    
    provider_map = {
        'microsoft': MicrosoftProvider,
        'azure_ad': MicrosoftProvider,
        'google': GoogleProvider,
        'okta': OktaProvider,
        'github': GitHubProvider,
    }
    
    provider_class = provider_map.get(connection.provider)
    
    if not provider_class:
        # Generic OAuth2 provider
        from .providers.generic import GenericOAuthProvider
        return GenericOAuthProvider(
            client_id=connection.oauth_client_id,
            client_secret=connection.oauth_client_secret,
            redirect_uri=redirect_uri,
            authorization_url=connection.oauth_authorization_url,
            token_url=connection.oauth_token_url,
            userinfo_url=connection.oauth_userinfo_url,
            scopes=connection.get_scopes_list(),
        )
    
    # Provider-specific initialization
    kwargs = {
        'client_id': connection.oauth_client_id,
        'client_secret': connection.oauth_client_secret,
        'redirect_uri': redirect_uri,
    }
    
    if connection.provider in ['microsoft', 'azure_ad']:
        # Extract tenant from discovery URL or use 'common'
        tenant = 'common'
        if connection.oidc_discovery_url:
            # Extract tenant from URL
            import re
            match = re.search(r'login\.microsoftonline\.com/([^/]+)', connection.oidc_discovery_url)
            if match:
                tenant = match.group(1)
        kwargs['tenant'] = tenant
    
    elif connection.provider == 'okta':
        # Extract domain from discovery URL
        if connection.oidc_discovery_url:
            from urllib.parse import urlparse
            parsed = urlparse(connection.oidc_discovery_url)
            kwargs['okta_domain'] = parsed.netloc
    
    elif connection.provider == 'google':
        # Extract hosted domain from allowed domains
        if connection.allowed_domains:
            kwargs['hosted_domain'] = connection.allowed_domains[0]
    
    return provider_class(**kwargs)
```

### 4.2 Base OAuth Provider

**File:** `backend/app/auth/sso/oauth/providers/base.py`

```python
"""
Base OAuth2 Provider Class
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from urllib.parse import urlencode
import httpx
import logging

logger = logging.getLogger(__name__)


@dataclass
class OAuthUserInfo:
    """Standardized user info from OAuth provider"""
    
    id: str
    email: str
    email_verified: bool = False
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    picture_url: Optional[str] = None
    groups: List[str] = None
    raw_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.groups is None:
            self.groups = []
        if self.raw_data is None:
            self.raw_data = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'email': self.email,
            'email_verified': self.email_verified,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'display_name': self.display_name,
            'picture_url': self.picture_url,
            'groups': self.groups,
        }


@dataclass
class OAuthTokens:
    """OAuth token response"""
    
    access_token: str
    token_type: str = 'Bearer'
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
    scope: Optional[str] = None
    
    @classmethod
    def from_response(cls, data: Dict[str, Any]) -> 'OAuthTokens':
        return cls(
            access_token=data['access_token'],
            token_type=data.get('token_type', 'Bearer'),
            expires_in=data.get('expires_in'),
            refresh_token=data.get('refresh_token'),
            id_token=data.get('id_token'),
            scope=data.get('scope'),
        )


class OAuthProvider(ABC):
    """Base class for OAuth2/OIDC providers"""
    
    name: str = "base"
    authorization_url: str = ""
    token_url: str = ""
    userinfo_url: str = ""
    revoke_url: Optional[str] = None
    scopes: List[str] = ["openid", "profile", "email"]
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: List[str] = None,
        **kwargs
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        
        if scopes:
            self.scopes = scopes
        
        self.extra_params = kwargs
    
    def get_authorization_url(
        self, 
        state: str, 
        nonce: Optional[str] = None,
        login_hint: Optional[str] = None,
    ) -> str:
        """
        Generate authorization URL for OAuth2 flow
        
        Args:
            state: CSRF state parameter
            nonce: OpenID Connect nonce
            login_hint: Pre-fill user email
            
        Returns:
            Authorization URL for redirect
        """
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(self.scopes),
            'state': state,
        }
        
        if nonce:
            params['nonce'] = nonce
        
        if login_hint:
            params['login_hint'] = login_hint
        
        # Add provider-specific parameters
        params.update(self._get_extra_auth_params())
        
        return f"{self.authorization_url}?{urlencode(params)}"
    
    async def exchange_code(self, code: str) -> OAuthTokens:
        """
        Exchange authorization code for tokens
        
        Args:
            code: Authorization code from callback
            
        Returns:
            OAuthTokens object
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': self.redirect_uri,
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                },
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                error_msg = error_data.get('error_description', error_data.get('error', 'Token exchange failed'))
                logger.error(f"Token exchange failed: {error_msg}")
                raise OAuthError(error_msg)
            
            data = response.json()
            return OAuthTokens.from_response(data)
    
    async def refresh_access_token(self, refresh_token: str) -> OAuthTokens:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New OAuthTokens
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    'grant_type': 'refresh_token',
                    'refresh_token': refresh_token,
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                },
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
            )
            
            if response.status_code != 200:
                raise OAuthError('Token refresh failed')
            
            data = response.json()
            return OAuthTokens.from_response(data)
    
    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """
        Fetch user info from provider
        
        Args:
            access_token: Valid access token
            
        Returns:
            OAuthUserInfo object
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.userinfo_url,
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Accept': 'application/json',
                },
            )
            
            if response.status_code != 200:
                raise OAuthError('Failed to fetch user info')
            
            data = response.json()
            return self._parse_user_info(data)
    
    async def revoke_token(self, token: str, token_type: str = 'access_token') -> bool:
        """
        Revoke a token
        
        Args:
            token: Token to revoke
            token_type: 'access_token' or 'refresh_token'
            
        Returns:
            True if successful
        """
        if not self.revoke_url:
            return False
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.revoke_url,
                data={
                    'token': token,
                    'token_type_hint': token_type,
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                },
            )
            
            return response.status_code == 200
    
    @abstractmethod
    def _parse_user_info(self, data: Dict[str, Any]) -> OAuthUserInfo:
        """
        Parse provider-specific user info response
        
        Must be implemented by each provider
        """
        pass
    
    def _get_extra_auth_params(self) -> Dict[str, str]:
        """
        Get provider-specific authorization parameters
        
        Override in subclasses for custom params
        """
        return {}


class OAuthError(Exception):
    """OAuth authentication error"""
    pass
```

### 4.3 Microsoft Entra ID Provider

**File:** `backend/app/auth/sso/oauth/providers/microsoft.py`

```python
"""
Microsoft Entra ID (Azure AD) OAuth2/OIDC Provider
"""

from typing import Dict, Any, List, Optional
import httpx
import logging

from .base import OAuthProvider, OAuthUserInfo, OAuthError

logger = logging.getLogger(__name__)


class MicrosoftProvider(OAuthProvider):
    """
    Microsoft Entra ID (formerly Azure AD) Provider
    
    Supports:
    - Single tenant authentication
    - Multi-tenant authentication
    - Personal Microsoft accounts (with 'common' or 'consumers')
    - Group claims
    """
    
    name = "microsoft"
    
    # URL templates
    AUTHORIZATION_URL_TEMPLATE = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
    TOKEN_URL_TEMPLATE = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    USERINFO_URL = "https://graph.microsoft.com/v1.0/me"
    GROUPS_URL = "https://graph.microsoft.com/v1.0/me/memberOf"
    
    # Default scopes
    scopes = [
        "openid",
        "profile", 
        "email",
        "User.Read",
        "GroupMember.Read.All",  # For group claims
    ]
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        tenant: str = "common",
        include_groups: bool = True,
        **kwargs
    ):
        """
        Initialize Microsoft provider
        
        Args:
            tenant: Azure AD tenant ID, or:
                    - 'common': Any Azure AD + personal accounts
                    - 'organizations': Any Azure AD account
                    - 'consumers': Personal accounts only
            include_groups: Whether to fetch group memberships
        """
        super().__init__(client_id, client_secret, redirect_uri, **kwargs)
        
        self.tenant = tenant
        self.include_groups = include_groups
        
        # Set URLs based on tenant
        self.authorization_url = self.AUTHORIZATION_URL_TEMPLATE.format(tenant=tenant)
        self.token_url = self.TOKEN_URL_TEMPLATE.format(tenant=tenant)
        self.userinfo_url = self.USERINFO_URL
    
    def _get_extra_auth_params(self) -> Dict[str, str]:
        """Microsoft-specific auth params"""
        return {
            'response_mode': 'query',
            'prompt': 'select_account',  # Always show account picker
        }
    
    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """
        Fetch user info including groups from Microsoft Graph
        """
        async with httpx.AsyncClient() as client:
            # Get basic user info
            user_response = await client.get(
                self.userinfo_url,
                headers={'Authorization': f'Bearer {access_token}'},
            )
            
            if user_response.status_code != 200:
                error_data = user_response.json()
                raise OAuthError(f"Failed to fetch user info: {error_data.get('error', {}).get('message', 'Unknown error')}")
            
            user_data = user_response.json()
            
            # Get group memberships
            groups = []
            if self.include_groups:
                groups = await self._fetch_groups(client, access_token)
            
            user_data['groups'] = groups
            
            return self._parse_user_info(user_data)
    
    async def _fetch_groups(
        self, 
        client: httpx.AsyncClient, 
        access_token: str
    ) -> List[str]:
        """
        Fetch user's group memberships from Microsoft Graph
        
        Returns list of group display names
        """
        try:
            response = await client.get(
                self.GROUPS_URL,
                headers={'Authorization': f'Bearer {access_token}'},
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch Microsoft groups: {response.status_code}")
                return []
            
            data = response.json()
            groups = []
            
            for item in data.get('value', []):
                # Filter for groups only (not roles, etc.)
                if item.get('@odata.type') == '#microsoft.graph.group':
                    group_name = item.get('displayName')
                    if group_name:
                        groups.append(group_name)
            
            # Handle pagination if needed
            next_link = data.get('@odata.nextLink')
            while next_link:
                response = await client.get(
                    next_link,
                    headers={'Authorization': f'Bearer {access_token}'},
                )
                if response.status_code != 200:
                    break
                    
                data = response.json()
                for item in data.get('value', []):
                    if item.get('@odata.type') == '#microsoft.graph.group':
                        group_name = item.get('displayName')
                        if group_name:
                            groups.append(group_name)
                
                next_link = data.get('@odata.nextLink')
            
            return groups
            
        except Exception as e:
            logger.warning(f"Error fetching Microsoft groups: {e}")
            return []
    
    def _parse_user_info(self, data: Dict[str, Any]) -> OAuthUserInfo:
        """Parse Microsoft Graph user response"""
        
        # Email can be in different fields
        email = (
            data.get('mail') or 
            data.get('userPrincipalName') or 
            data.get('email', '')
        )
        
        return OAuthUserInfo(
            id=data.get('id', ''),
            email=email,
            email_verified=True,  # Microsoft validates emails
            first_name=data.get('givenName'),
            last_name=data.get('surname'),
            display_name=data.get('displayName'),
            picture_url=None,  # Requires separate API call with specific permissions
            groups=data.get('groups', []),
            raw_data=data,
        )
```

### 4.4 Google Workspace Provider

**File:** `backend/app/auth/sso/oauth/providers/google.py`

```python
"""
Google Workspace OAuth2/OIDC Provider
"""

from typing import Dict, Any, Optional
from .base import OAuthProvider, OAuthUserInfo


class GoogleProvider(OAuthProvider):
    """
    Google Workspace / Google Cloud Identity Provider
    
    Supports:
    - Google Workspace accounts
    - Personal Google accounts
    - Domain restriction (hosted domain)
    """
    
    name = "google"
    
    authorization_url = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url = "https://oauth2.googleapis.com/token"
    userinfo_url = "https://openidconnect.googleapis.com/v1/userinfo"
    revoke_url = "https://oauth2.googleapis.com/revoke"
    
    scopes = ["openid", "profile", "email"]
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        hosted_domain: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Google provider
        
        Args:
            hosted_domain: Restrict to specific Google Workspace domain
        """
        super().__init__(client_id, client_secret, redirect_uri, **kwargs)
        self.hosted_domain = hosted_domain
    
    def _get_extra_auth_params(self) -> Dict[str, str]:
        """Google-specific auth params"""
        params = {
            'access_type': 'offline',  # Get refresh token
            'prompt': 'consent',  # Always show consent screen for refresh token
        }
        
        if self.hosted_domain:
            params['hd'] = self.hosted_domain
        
        return params
    
    def _parse_user_info(self, data: Dict[str, Any]) -> OAuthUserInfo:
        """Parse Google userinfo response"""
        return OAuthUserInfo(
            id=data.get('sub', ''),
            email=data.get('email', ''),
            email_verified=data.get('email_verified', False),
            first_name=data.get('given_name'),
            last_name=data.get('family_name'),
            display_name=data.get('name'),
            picture_url=data.get('picture'),
            groups=[],  # Google Admin SDK required for groups
            raw_data=data,
        )
```

### 4.5 Okta Provider

**File:** `backend/app/auth/sso/oauth/providers/okta.py`

```python
"""
Okta OAuth2/OIDC Provider
"""

from typing import Dict, Any
from .base import OAuthProvider, OAuthUserInfo


class OktaProvider(OAuthProvider):
    """
    Okta Identity Provider
    
    Supports:
    - Okta organizations
    - Custom authorization servers
    - Group claims (with proper Okta configuration)
    """
    
    name = "okta"
    
    scopes = ["openid", "profile", "email", "groups"]
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        okta_domain: str,
        authorization_server: str = "default",
        **kwargs
    ):
        """
        Initialize Okta provider
        
        Args:
            okta_domain: Okta organization domain (e.g., 'dev-123456.okta.com')
            authorization_server: Authorization server ID (default: 'default')
        """
        super().__init__(client_id, client_secret, redirect_uri, **kwargs)
        
        self.okta_domain = okta_domain
        self.authorization_server = authorization_server
        
        # Build URLs
        base_url = f"https://{okta_domain}/oauth2/{authorization_server}"
        self.authorization_url = f"{base_url}/v1/authorize"
        self.token_url = f"{base_url}/v1/token"
        self.userinfo_url = f"{base_url}/v1/userinfo"
        self.revoke_url = f"{base_url}/v1/revoke"
    
    def _get_extra_auth_params(self) -> Dict[str, str]:
        """Okta-specific auth params"""
        return {
            'response_mode': 'query',
        }
    
    def _parse_user_info(self, data: Dict[str, Any]) -> OAuthUserInfo:
        """Parse Okta userinfo response"""
        return OAuthUserInfo(
            id=data.get('sub', ''),
            email=data.get('email', ''),
            email_verified=data.get('email_verified', False),
            first_name=data.get('given_name'),
            last_name=data.get('family_name'),
            display_name=data.get('name'),
            picture_url=data.get('picture'),
            groups=data.get('groups', []),
            raw_data=data,
        )
```

### 4.6 GitHub Provider

**File:** `backend/app/auth/sso/oauth/providers/github.py`

```python
"""
GitHub OAuth2 Provider
"""

from typing import Dict, Any, List
import httpx
import logging

from .base import OAuthProvider, OAuthUserInfo, OAuthError

logger = logging.getLogger(__name__)


class GitHubProvider(OAuthProvider):
    """
    GitHub OAuth2 Provider
    
    Useful for developer-focused organizations
    """
    
    name = "github"
    
    authorization_url = "https://github.com/login/oauth/authorize"
    token_url = "https://github.com/login/oauth/access_token"
    userinfo_url = "https://api.github.com/user"
    emails_url = "https://api.github.com/user/emails"
    orgs_url = "https://api.github.com/user/orgs"
    
    scopes = ["read:user", "user:email", "read:org"]
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        allowed_orgs: List[str] = None,
        **kwargs
    ):
        """
        Initialize GitHub provider
        
        Args:
            allowed_orgs: Restrict to users in specific GitHub organizations
        """
        super().__init__(client_id, client_secret, redirect_uri, **kwargs)
        self.allowed_orgs = allowed_orgs or []
    
    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Fetch user info including emails and orgs"""
        async with httpx.AsyncClient() as client:
            headers = {
                'Authorization': f'token {access_token}',
                'Accept': 'application/json',
            }
            
            # Get basic user info
            user_response = await client.get(self.userinfo_url, headers=headers)
            if user_response.status_code != 200:
                raise OAuthError('Failed to fetch GitHub user info')
            user_data = user_response.json()
            
            # Get email if not in user data
            email = user_data.get('email')
            if not email:
                emails_response = await client.get(self.emails_url, headers=headers)
                if emails_response.status_code == 200:
                    emails = emails_response.json()
                    primary = next(
                        (e for e in emails if e.get('primary')),
                        emails[0] if emails else None
                    )
                    if primary:
                        email = primary.get('email')
                        user_data['email_verified'] = primary.get('verified', False)
            
            user_data['email'] = email
            
            # Get organizations
            orgs_response = await client.get(self.orgs_url, headers=headers)
            if orgs_response.status_code == 200:
                orgs = [org.get('login') for org in orgs_response.json()]
                user_data['orgs'] = orgs
            
            return self._parse_user_info(user_data)
    
    def _parse_user_info(self, data: Dict[str, Any]) -> OAuthUserInfo:
        """Parse GitHub user response"""
        
        # Split name into first/last
        name = data.get('name', '')
        name_parts = name.split(' ', 1) if name else ['', '']
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        return OAuthUserInfo(
            id=str(data.get('id', '')),
            email=data.get('email', ''),
            email_verified=data.get('email_verified', False),
            first_name=first_name,
            last_name=last_name,
            display_name=data.get('name') or data.get('login'),
            picture_url=data.get('avatar_url'),
            groups=data.get('orgs', []),
            raw_data=data,
        )
```

### 4.7 Generic OAuth Provider

**File:** `backend/app/auth/sso/oauth/providers/generic.py`

```python
"""
Generic OAuth2 Provider for custom IdPs
"""

from typing import Dict, Any, Optional, List
from .base import OAuthProvider, OAuthUserInfo


class GenericOAuthProvider(OAuthProvider):
    """
    Generic OAuth2 provider for custom identity providers
    
    Used when no specific provider implementation exists
    """
    
    name = "generic"
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        authorization_url: str,
        token_url: str,
        userinfo_url: str,
        scopes: List[str] = None,
        attribute_mapping: Dict[str, str] = None,
        **kwargs
    ):
        super().__init__(client_id, client_secret, redirect_uri, scopes, **kwargs)
        
        self.authorization_url = authorization_url
        self.token_url = token_url
        self.userinfo_url = userinfo_url
        
        # Custom attribute mapping
        self.attribute_mapping = attribute_mapping or {
            'id': 'sub',
            'email': 'email',
            'email_verified': 'email_verified',
            'first_name': 'given_name',
            'last_name': 'family_name',
            'display_name': 'name',
            'picture_url': 'picture',
            'groups': 'groups',
        }
    
    def _parse_user_info(self, data: Dict[str, Any]) -> OAuthUserInfo:
        """Parse user info using attribute mapping"""
        
        def get_value(key: str) -> Any:
            mapped_key = self.attribute_mapping.get(key, key)
            return data.get(mapped_key)
        
        return OAuthUserInfo(
            id=str(get_value('id') or ''),
            email=get_value('email') or '',
            email_verified=get_value('email_verified') or False,
            first_name=get_value('first_name'),
            last_name=get_value('last_name'),
            display_name=get_value('display_name'),
            picture_url=get_value('picture_url'),
            groups=get_value('groups') or [],
            raw_data=data,
        )
```

---

## TASK 5: OPENID CONNECT SUPPORT

### 5.1 OIDC Discovery

**File:** `backend/app/auth/sso/oidc/discovery.py`

```python
"""
OpenID Connect Discovery
Fetches and caches OIDC configuration from IdP
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import httpx
import logging

logger = logging.getLogger(__name__)


@dataclass
class OIDCConfiguration:
    """OpenID Connect Provider Configuration"""
    
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str
    jwks_uri: str
    
    # Optional endpoints
    revocation_endpoint: Optional[str] = None
    introspection_endpoint: Optional[str] = None
    end_session_endpoint: Optional[str] = None
    
    # Supported features
    scopes_supported: list = None
    response_types_supported: list = None
    grant_types_supported: list = None
    subject_types_supported: list = None
    id_token_signing_alg_values_supported: list = None
    token_endpoint_auth_methods_supported: list = None
    claims_supported: list = None
    
    # Cache info
    fetched_at: datetime = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OIDCConfiguration':
        return cls(
            issuer=data['issuer'],
            authorization_endpoint=data['authorization_endpoint'],
            token_endpoint=data['token_endpoint'],
            userinfo_endpoint=data.get('userinfo_endpoint', ''),
            jwks_uri=data['jwks_uri'],
            revocation_endpoint=data.get('revocation_endpoint'),
            introspection_endpoint=data.get('introspection_endpoint'),
            end_session_endpoint=data.get('end_session_endpoint'),
            scopes_supported=data.get('scopes_supported', []),
            response_types_supported=data.get('response_types_supported', []),
            grant_types_supported=data.get('grant_types_supported', []),
            subject_types_supported=data.get('subject_types_supported', []),
            id_token_signing_alg_values_supported=data.get('id_token_signing_alg_values_supported', []),
            token_endpoint_auth_methods_supported=data.get('token_endpoint_auth_methods_supported', []),
            claims_supported=data.get('claims_supported', []),
            fetched_at=datetime.utcnow(),
        )


class OIDCDiscovery:
    """
    OpenID Connect Discovery Service
    
    Fetches and caches OIDC configuration from well-known endpoint
    """
    
    # Configuration cache
    _cache: Dict[str, OIDCConfiguration] = {}
    CACHE_TTL = timedelta(hours=24)
    
    @classmethod
    async def get_configuration(
        cls, 
        discovery_url: str,
        force_refresh: bool = False
    ) -> OIDCConfiguration:
        """
        Get OIDC configuration for an issuer
        
        Args:
            discovery_url: The .well-known/openid-configuration URL
            force_refresh: Force refresh even if cached
            
        Returns:
            OIDCConfiguration object
        """
        # Check cache
        if not force_refresh and discovery_url in cls._cache:
            cached = cls._cache[discovery_url]
            if datetime.utcnow() - cached.fetched_at < cls.CACHE_TTL:
                return cached
        
        # Fetch configuration
        config = await cls._fetch_configuration(discovery_url)
        cls._cache[discovery_url] = config
        
        return config
    
    @classmethod
    async def _fetch_configuration(cls, discovery_url: str) -> OIDCConfiguration:
        """Fetch OIDC configuration from discovery endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(discovery_url, timeout=10)
            
            if response.status_code != 200:
                raise OIDCDiscoveryError(
                    f"Failed to fetch OIDC configuration: {response.status_code}"
                )
            
            data = response.json()
            
            # Validate required fields
            required = ['issuer', 'authorization_endpoint', 'token_endpoint', 'jwks_uri']
            for field in required:
                if field not in data:
                    raise OIDCDiscoveryError(f"Missing required field: {field}")
            
            logger.info(f"Fetched OIDC configuration for {data['issuer']}")
            
            return OIDCConfiguration.from_dict(data)
    
    @classmethod
    def clear_cache(cls, discovery_url: str = None):
        """Clear configuration cache"""
        if discovery_url:
            cls._cache.pop(discovery_url, None)
        else:
            cls._cache.clear()
    
    @classmethod
    def build_discovery_url(cls, issuer: str) -> str:
        """
        Build discovery URL from issuer
        
        Args:
            issuer: The OpenID Connect issuer URL
            
        Returns:
            Well-known configuration URL
        """
        issuer = issuer.rstrip('/')
        return f"{issuer}/.well-known/openid-configuration"


class OIDCDiscoveryError(Exception):
    """OIDC Discovery error"""
    pass
```

### 5.2 JWKS Validation

**File:** `backend/app/auth/sso/oidc/jwks.py`

```python
"""
JSON Web Key Set (JWKS) Validation
Validates JWT tokens using provider's public keys
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import httpx
from jose import jwt, jwk, JWTError
from jose.utils import base64url_decode
import logging

logger = logging.getLogger(__name__)


class JWKSClient:
    """
    JWKS Client for JWT validation
    
    Fetches and caches JWKS from IdP, validates JWTs
    """
    
    # JWKS cache
    _cache: Dict[str, Dict] = {}
    CACHE_TTL = timedelta(hours=24)
    
    @classmethod
    async def get_jwks(
        cls, 
        jwks_uri: str,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get JWKS from URI
        
        Args:
            jwks_uri: The JWKS endpoint URL
            force_refresh: Force refresh even if cached
            
        Returns:
            JWKS data
        """
        cache_key = jwks_uri
        
        # Check cache
        if not force_refresh and cache_key in cls._cache:
            cached = cls._cache[cache_key]
            if datetime.utcnow() - cached.get('fetched_at', datetime.min) < cls.CACHE_TTL:
                return cached['jwks']
        
        # Fetch JWKS
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_uri, timeout=10)
            
            if response.status_code != 200:
                raise JWKSError(f"Failed to fetch JWKS: {response.status_code}")
            
            jwks_data = response.json()
            
            # Cache
            cls._cache[cache_key] = {
                'jwks': jwks_data,
                'fetched_at': datetime.utcnow(),
            }
            
            logger.info(f"Fetched JWKS from {jwks_uri}")
            
            return jwks_data
    
    @classmethod
    async def validate_token(
        cls,
        token: str,
        jwks_uri: str,
        issuer: str,
        audience: str,
        algorithms: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Validate a JWT token
        
        Args:
            token: JWT token string
            jwks_uri: JWKS endpoint URL
            issuer: Expected token issuer
            audience: Expected token audience (client_id)
            algorithms: Allowed algorithms (default: RS256)
            
        Returns:
            Decoded token claims
        """
        algorithms = algorithms or ['RS256']
        
        # Get JWKS
        jwks_data = await cls.get_jwks(jwks_uri)
        
        # Decode header to get key ID
        try:
            header = jwt.get_unverified_header(token)
            kid = header.get('kid')
        except JWTError as e:
            raise JWKSError(f"Invalid token header: {e}")
        
        # Find matching key
        signing_key = None
        for key in jwks_data.get('keys', []):
            if key.get('kid') == kid:
                signing_key = key
                break
        
        if not signing_key:
            # Try refreshing JWKS (key rotation)
            jwks_data = await cls.get_jwks(jwks_uri, force_refresh=True)
            for key in jwks_data.get('keys', []):
                if key.get('kid') == kid:
                    signing_key = key
                    break
        
        if not signing_key:
            raise JWKSError(f"No matching key found for kid: {kid}")
        
        # Validate token
        try:
            claims = jwt.decode(
                token,
                signing_key,
                algorithms=algorithms,
                audience=audience,
                issuer=issuer,
            )
            
            return claims
            
        except jwt.ExpiredSignatureError:
            raise JWKSError("Token has expired")
        except jwt.JWTClaimsError as e:
            raise JWKSError(f"Invalid token claims: {e}")
        except JWTError as e:
            raise JWKSError(f"Token validation failed: {e}")
    
    @classmethod
    def clear_cache(cls, jwks_uri: str = None):
        """Clear JWKS cache"""
        if jwks_uri:
            cls._cache.pop(jwks_uri, None)
        else:
            cls._cache.clear()


class JWKSError(Exception):
    """JWKS validation error"""
    pass
```

---

## TASK 6: OAUTH2 ROUTES

**File:** `backend/app/routes/oauth.py`

```python
"""
OAuth2 / OpenID Connect Authentication Routes
"""

from flask import Blueprint, request, redirect, session, jsonify
from app.auth.sso.oauth import get_provider, OAuthError
from app.auth.sso.oidc.discovery import OIDCDiscovery
from app.auth.sso.oidc.jwks import JWKSClient
from app.models.sso_connection import SSOConnection
from app.services.sso_service import SSOService
from app.extensions import db
from datetime import datetime
import secrets
import logging
import os
import asyncio

logger = logging.getLogger(__name__)

oauth_bp = Blueprint('oauth', __name__, url_prefix='/api/v1/auth/sso/oauth')


def run_async(coro):
    """Run async function in sync context"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@oauth_bp.route('/<connection_id>/login', methods=['GET'])
def oauth_login(connection_id: str):
    """
    Initiate OAuth2 login flow
    
    Redirects user to Identity Provider for authentication
    """
    connection = SSOConnection.query.get(connection_id)
    
    if not connection or connection.protocol not in ['oauth2', 'oidc']:
        return jsonify({'error': 'Invalid SSO connection'}), 404
    
    if connection.status not in ['active', 'testing']:
        return jsonify({'error': 'SSO connection is not active'}), 403
    
    try:
        provider = get_provider(connection)
        
        # Generate state and nonce
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)
        
        # Store in session for validation
        session['oauth_state'] = state
        session['oauth_nonce'] = nonce
        session['oauth_connection_id'] = connection_id
        session['oauth_return_to'] = request.args.get('return_to', '/')
        
        # Get login hint if provided
        login_hint = request.args.get('login_hint')
        
        # Generate authorization URL
        auth_url = provider.get_authorization_url(
            state=state,
            nonce=nonce,
            login_hint=login_hint
        )
        
        logger.info(f"OAuth login initiated for connection {connection_id}")
        
        return redirect(auth_url)
        
    except Exception as e:
        logger.error(f"OAuth login error: {e}")
        return redirect(f'/login?error=oauth_error&message={str(e)}')


@oauth_bp.route('/<connection_id>/callback', methods=['GET'])
def oauth_callback(connection_id: str):
    """
    OAuth2 callback handler
    
    Processes authorization code and creates user session
    """
    connection = SSOConnection.query.get(connection_id)
    
    if not connection:
        return redirect('/login?error=invalid_connection')
    
    # Verify state
    state = request.args.get('state')
    stored_state = session.pop('oauth_state', None)
    stored_nonce = session.pop('oauth_nonce', None)
    stored_connection_id = session.pop('oauth_connection_id', None)
    return_to = session.pop('oauth_return_to', '/')
    
    if not state or state != stored_state:
        logger.warning(f"OAuth state mismatch for connection {connection_id}")
        return redirect('/login?error=invalid_state')
    
    # Check for errors from IdP
    error = request.args.get('error')
    if error:
        error_description = request.args.get('error_description', error)
        logger.error(f"OAuth error from IdP: {error} - {error_description}")
        return redirect(f'/login?error={error}&message={error_description}')
    
    # Get authorization code
    code = request.args.get('code')
    if not code:
        return redirect('/login?error=no_code')
    
    try:
        provider = get_provider(connection)
        
        # Exchange code for tokens
        tokens = run_async(provider.exchange_code(code))
        
        # Validate ID token if OIDC
        id_token_claims = None
        if tokens.id_token and connection.protocol == 'oidc':
            id_token_claims = run_async(_validate_id_token(
                connection, 
                tokens.id_token,
                stored_nonce
            ))
        
        # Get user info
        user_info = run_async(provider.get_user_info(tokens.access_token))
        
        # Validate email domain if restricted
        if connection.allowed_domains:
            if not connection.is_domain_allowed(user_info.email):
                logger.warning(
                    f"Domain not allowed for {user_info.email} on connection {connection_id}"
                )
                return redirect('/login?error=domain_not_allowed')
        
        # Find or create user
        user = SSOService.find_or_create_user_oauth(
            connection=connection,
            user_info=user_info,
            tokens={
                'access_token': tokens.access_token,
                'refresh_token': tokens.refresh_token,
                'id_token': tokens.id_token,
                'expires_in': tokens.expires_in,
            }
        )
        
        # Create application session
        app_tokens = SSOService.create_session(
            user=user,
            connection=connection,
            oauth_data={
                'access_token': tokens.access_token,
                'refresh_token': tokens.refresh_token,
                'id_token': tokens.id_token,
                'expires_in': tokens.expires_in,
                'user_info': user_info.to_dict(),
            }
        )
        
        # Update last used timestamp
        connection.last_used_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"OAuth authentication successful for user {user.email}")
        
        # Redirect to frontend with tokens
        base_url = os.getenv('FRONTEND_URL', '')
        callback_url = f"{base_url}/auth/callback"
        
        return redirect(
            f"{callback_url}?token={app_tokens['access_token']}"
            f"&refresh={app_tokens['refresh_token']}"
            f"&return_to={return_to}"
        )
        
    except OAuthError as e:
        logger.error(f"OAuth error: {e}")
        return redirect(f'/login?error=oauth_error&message={str(e)}')
    except Exception as e:
        logger.exception(f"OAuth callback error: {e}")
        return redirect(f'/login?error=oauth_error&message={str(e)}')


async def _validate_id_token(
    connection: SSOConnection, 
    id_token: str,
    nonce: str
) -> Dict:
    """Validate OIDC ID token"""
    
    # Get OIDC configuration
    if connection.oidc_discovery_url:
        config = await OIDCDiscovery.get_configuration(connection.oidc_discovery_url)
        jwks_uri = config.jwks_uri
        issuer = config.issuer
    elif connection.oidc_jwks_uri:
        jwks_uri = connection.oidc_jwks_uri
        issuer = connection.oauth_authorization_url.split('/oauth2')[0]  # Approximation
    else:
        raise OAuthError("No JWKS URI configured for OIDC validation")
    
    # Validate token
    claims = await JWKSClient.validate_token(
        token=id_token,
        jwks_uri=jwks_uri,
        issuer=issuer,
        audience=connection.oauth_client_id,
    )
    
    # Validate nonce if present
    if nonce and claims.get('nonce') != nonce:
        raise OAuthError("Invalid nonce in ID token")
    
    return claims


@oauth_bp.route('/<connection_id>/refresh', methods=['POST'])
def oauth_refresh(connection_id: str):
    """
    Refresh OAuth tokens
    """
    connection = SSOConnection.query.get(connection_id)
    
    if not connection:
        return jsonify({'error': 'Invalid connection'}), 404
    
    data = request.get_json()
    refresh_token = data.get('refresh_token')
    
    if not refresh_token:
        return jsonify({'error': 'Refresh token required'}), 400
    
    try:
        provider = get_provider(connection)
        tokens = run_async(provider.refresh_access_token(refresh_token))
        
        return jsonify({
            'access_token': tokens.access_token,
            'refresh_token': tokens.refresh_token,
            'expires_in': tokens.expires_in,
        })
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({'error': str(e)}), 400


@oauth_bp.route('/<connection_id>/logout', methods=['POST'])
def oauth_logout(connection_id: str):
    """
    OAuth logout - revoke tokens if supported
    """
    connection = SSOConnection.query.get(connection_id)
    
    if not connection:
        return jsonify({'error': 'Invalid connection'}), 404
    
    # Invalidate local session
    SSOService.logout_user_sso(connection_id)
    
    # Get end session URL if OIDC
    end_session_url = None
    if connection.protocol == 'oidc' and connection.oidc_discovery_url:
        try:
            config = run_async(
                OIDCDiscovery.get_configuration(connection.oidc_discovery_url)
            )
            end_session_url = config.end_session_endpoint
        except Exception:
            pass
    
    return jsonify({
        'success': True,
        'redirect': end_session_url or '/login'
    })
```

---

## TASK 7: STATE MANAGER

**File:** `backend/app/auth/sso/oauth/state_manager.py`

```python
"""
OAuth State Manager
Manages CSRF state and PKCE for OAuth flows
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import secrets
import hashlib
import base64
from app.extensions import redis_client
import json


@dataclass
class OAuthState:
    """OAuth state data"""
    
    state: str
    nonce: str
    connection_id: str
    return_to: str
    code_verifier: Optional[str] = None  # For PKCE
    created_at: datetime = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'state': self.state,
            'nonce': self.nonce,
            'connection_id': self.connection_id,
            'return_to': self.return_to,
            'code_verifier': self.code_verifier,
            'created_at': self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OAuthState':
        return cls(
            state=data['state'],
            nonce=data['nonce'],
            connection_id=data['connection_id'],
            return_to=data['return_to'],
            code_verifier=data.get('code_verifier'),
            created_at=datetime.fromisoformat(data['created_at']),
        )


class OAuthStateManager:
    """
    Manages OAuth state for CSRF protection and PKCE
    
    Uses Redis for distributed state storage
    """
    
    STATE_TTL = 600  # 10 minutes
    KEY_PREFIX = "oauth_state:"
    
    @classmethod
    def generate_state(
        cls,
        connection_id: str,
        return_to: str = '/',
        use_pkce: bool = False
    ) -> OAuthState:
        """
        Generate new OAuth state
        
        Args:
            connection_id: SSO connection ID
            return_to: URL to redirect after auth
            use_pkce: Enable PKCE (Proof Key for Code Exchange)
            
        Returns:
            OAuthState object
        """
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)
        
        code_verifier = None
        if use_pkce:
            code_verifier = secrets.token_urlsafe(64)
        
        oauth_state = OAuthState(
            state=state,
            nonce=nonce,
            connection_id=connection_id,
            return_to=return_to,
            code_verifier=code_verifier,
        )
        
        # Store in Redis
        cls._store_state(oauth_state)
        
        return oauth_state
    
    @classmethod
    def validate_state(cls, state: str) -> Optional[OAuthState]:
        """
        Validate and retrieve OAuth state
        
        Args:
            state: State parameter from callback
            
        Returns:
            OAuthState if valid, None otherwise
        """
        key = f"{cls.KEY_PREFIX}{state}"
        
        data = redis_client.get(key)
        if not data:
            return None
        
        # Delete state (one-time use)
        redis_client.delete(key)
        
        try:
            state_data = json.loads(data)
            oauth_state = OAuthState.from_dict(state_data)
            
            # Check expiry
            if datetime.utcnow() - oauth_state.created_at > timedelta(seconds=cls.STATE_TTL):
                return None
            
            return oauth_state
            
        except Exception:
            return None
    
    @classmethod
    def get_pkce_challenge(cls, code_verifier: str) -> tuple:
        """
        Generate PKCE code challenge from verifier
        
        Args:
            code_verifier: The code verifier string
            
        Returns:
            Tuple of (code_challenge, code_challenge_method)
        """
        # SHA256 hash
        digest = hashlib.sha256(code_verifier.encode()).digest()
        
        # Base64 URL encode
        code_challenge = base64.urlsafe_b64encode(digest).decode().rstrip('=')
        
        return code_challenge, 'S256'
    
    @classmethod
    def _store_state(cls, oauth_state: OAuthState):
        """Store state in Redis"""
        key = f"{cls.KEY_PREFIX}{oauth_state.state}"
        data = json.dumps(oauth_state.to_dict())
        
        redis_client.setex(key, cls.STATE_TTL, data)
```

---

## Continue to Part 3 for SCIM and Frontend Implementation

---

*Phase 12 Tasks Part 2 - LogiAccounting Pro*
*OAuth2/OpenID Connect Implementation*
