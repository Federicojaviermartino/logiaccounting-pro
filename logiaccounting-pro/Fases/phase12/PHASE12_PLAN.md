# LogiAccounting Pro - Phase 12: Enterprise SSO

## SAML 2.0 & OAuth2/OpenID Connect Implementation

---

## 📋 EXECUTIVE SUMMARY

Phase 12 transforms LogiAccounting Pro into an enterprise-ready platform by implementing Single Sign-On (SSO) capabilities. This enables seamless integration with corporate identity providers like Microsoft Entra ID (Azure AD), Okta, Google Workspace, and other SAML/OAuth2 compliant systems.

### Business Value

| Benefit | Description |
|---------|-------------|
| **Enterprise Sales** | Unlock enterprise customers requiring SSO compliance |
| **Security Compliance** | Meet SOC2, ISO 27001, HIPAA requirements |
| **User Experience** | One-click login with existing corporate credentials |
| **IT Management** | Centralized user provisioning and deprovisioning |
| **Reduced Support** | Eliminate password reset requests |

### Supported Protocols

| Protocol | Use Case | Providers |
|----------|----------|-----------|
| **SAML 2.0** | Enterprise IdP integration | Okta, Azure AD, OneLogin, PingIdentity |
| **OAuth 2.0** | Social & modern auth | Google, Microsoft, GitHub |
| **OpenID Connect** | Identity layer on OAuth | All major providers |
| **SCIM 2.0** | User provisioning | Automated user sync |

---

## 🏗️ ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AUTHENTICATION FLOW                               │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
│    User      │     │ LogiAccounting│    │   Identity   │     │  SCIM    │
│   Browser    │     │   Pro (SP)    │    │   Provider   │     │ Endpoint │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └────┬─────┘
       │                    │                    │                   │
       │  1. Access App     │                    │                   │
       │───────────────────>│                    │                   │
       │                    │                    │                   │
       │  2. Redirect to IdP│                    │                   │
       │<───────────────────│                    │                   │
       │                    │                    │                   │
       │  3. Login at IdP   │                    │                   │
       │─────────────────────────────────────────>                   │
       │                    │                    │                   │
       │  4. SAML Response / OAuth Token         │                   │
       │<─────────────────────────────────────────                   │
       │                    │                    │                   │
       │  5. POST Assertion │                    │                   │
       │───────────────────>│                    │                   │
       │                    │                    │                   │
       │                    │  6. Validate       │                   │
       │                    │─────────────────────>                  │
       │                    │                    │                   │
       │  7. Create Session │                    │                   │
       │<───────────────────│                    │                   │
       │                    │                    │                   │
       │                    │  8. Sync Users (SCIM)                  │
       │                    │<───────────────────────────────────────│
       │                    │                    │                   │

Legend:
  SP = Service Provider (LogiAccounting Pro)
  IdP = Identity Provider (Okta, Azure AD, etc.)
  SCIM = System for Cross-domain Identity Management
```

---

## 📁 PROJECT STRUCTURE

```
backend/app/
├── auth/
│   ├── __init__.py
│   ├── sso/
│   │   ├── __init__.py
│   │   ├── saml/
│   │   │   ├── __init__.py
│   │   │   ├── config.py           # SAML configuration
│   │   │   ├── metadata.py         # SP metadata generation
│   │   │   ├── processor.py        # SAML assertion processing
│   │   │   ├── validator.py        # Signature validation
│   │   │   └── utils.py            # Helper functions
│   │   │
│   │   ├── oauth/
│   │   │   ├── __init__.py
│   │   │   ├── config.py           # OAuth2 configuration
│   │   │   ├── providers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py         # Base provider class
│   │   │   │   ├── microsoft.py    # Azure AD / Entra ID
│   │   │   │   ├── google.py       # Google Workspace
│   │   │   │   ├── okta.py         # Okta
│   │   │   │   └── github.py       # GitHub (for developers)
│   │   │   ├── token_handler.py    # Token management
│   │   │   └── state_manager.py    # OAuth state handling
│   │   │
│   │   ├── oidc/
│   │   │   ├── __init__.py
│   │   │   ├── discovery.py        # OIDC discovery
│   │   │   ├── claims.py           # Claims processing
│   │   │   └── jwks.py             # JWKS validation
│   │   │
│   │   └── scim/
│   │       ├── __init__.py
│   │       ├── schemas.py          # SCIM schemas
│   │       ├── resources.py        # User/Group resources
│   │       ├── filters.py          # SCIM filter parsing
│   │       └── provisioning.py     # User provisioning logic
│   │
│   └── services/
│       ├── sso_service.py          # SSO business logic
│       ├── idp_service.py          # IdP management
│       └── session_service.py      # Session handling
│
├── models/
│   ├── sso_connection.py           # SSO connection model
│   ├── idp_config.py               # IdP configuration model
│   └── sso_session.py              # SSO session model
│
├── routes/
│   ├── sso.py                      # SSO endpoints
│   ├── saml.py                     # SAML endpoints
│   ├── oauth.py                    # OAuth endpoints
│   └── scim.py                     # SCIM endpoints
│
└── schemas/
    ├── sso_schemas.py              # Pydantic schemas
    └── scim_schemas.py             # SCIM schemas

frontend/src/
├── features/
│   └── sso/
│       ├── components/
│       │   ├── SSOLoginButton.tsx
│       │   ├── IdentityProviderCard.tsx
│       │   ├── SSOConfigForm.tsx
│       │   └── SCIMSettings.tsx
│       ├── pages/
│       │   ├── SSOSettingsPage.tsx
│       │   └── SSOCallbackPage.tsx
│       └── hooks/
│           └── useSSO.ts
│
└── pages/
    └── admin/
        └── SSOManagement.tsx
```

---

## 🔧 TECHNOLOGY STACK

### Backend Dependencies

```txt
# requirements.txt additions

# SAML
python3-saml==1.16.0
xmlsec==1.3.13
lxml==5.1.0

# OAuth2 / OIDC
authlib==1.3.0
httpx==0.26.0
python-jose[cryptography]==3.3.0
PyJWT==2.8.0

# SCIM
scim2-filter-parser==0.5.0
```

### Frontend Dependencies

```json
{
  "dependencies": {
    "@azure/msal-browser": "^3.5.0",
    "@azure/msal-react": "^2.0.0"
  }
}
```

---

## 📊 DATABASE SCHEMA

### SSO Connection Model

```sql
-- SSO Connections Table
CREATE TABLE sso_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    
    -- Connection Info
    name VARCHAR(255) NOT NULL,
    protocol VARCHAR(20) NOT NULL CHECK (protocol IN ('saml', 'oauth2', 'oidc')),
    provider VARCHAR(50) NOT NULL,  -- 'okta', 'azure_ad', 'google', 'custom'
    status VARCHAR(20) DEFAULT 'inactive' CHECK (status IN ('active', 'inactive', 'testing')),
    
    -- SAML Configuration
    saml_entity_id VARCHAR(500),
    saml_sso_url VARCHAR(500),
    saml_slo_url VARCHAR(500),
    saml_certificate TEXT,
    saml_sign_request BOOLEAN DEFAULT true,
    saml_want_assertions_signed BOOLEAN DEFAULT true,
    saml_name_id_format VARCHAR(100) DEFAULT 'urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress',
    
    -- OAuth2 / OIDC Configuration
    oauth_client_id VARCHAR(255),
    oauth_client_secret_encrypted TEXT,
    oauth_authorization_url VARCHAR(500),
    oauth_token_url VARCHAR(500),
    oauth_userinfo_url VARCHAR(500),
    oauth_scopes TEXT DEFAULT 'openid profile email',
    oidc_discovery_url VARCHAR(500),
    oidc_jwks_uri VARCHAR(500),
    
    -- Attribute Mapping
    attribute_mapping JSONB DEFAULT '{
        "email": "email",
        "first_name": "given_name",
        "last_name": "family_name",
        "groups": "groups"
    }'::jsonb,
    
    -- Role Mapping
    role_mapping JSONB DEFAULT '{}'::jsonb,
    default_role VARCHAR(50) DEFAULT 'client',
    
    -- SCIM Configuration
    scim_enabled BOOLEAN DEFAULT false,
    scim_token_encrypted TEXT,
    scim_sync_groups BOOLEAN DEFAULT false,
    
    -- Security Settings
    allowed_domains TEXT[],
    enforce_sso BOOLEAN DEFAULT false,
    allow_idp_initiated BOOLEAN DEFAULT true,
    session_duration_hours INTEGER DEFAULT 8,
    
    -- Metadata
    metadata_url VARCHAR(500),
    metadata_xml TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    
    UNIQUE(organization_id, name)
);

-- SSO Sessions Table
CREATE TABLE sso_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    connection_id UUID NOT NULL REFERENCES sso_connections(id),
    
    -- Session Info
    session_index VARCHAR(255),
    name_id VARCHAR(255),
    name_id_format VARCHAR(100),
    
    -- OAuth Tokens (encrypted)
    access_token_encrypted TEXT,
    refresh_token_encrypted TEXT,
    id_token TEXT,
    token_expires_at TIMESTAMP,
    
    -- Session State
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    
    INDEX idx_sso_sessions_user (user_id),
    INDEX idx_sso_sessions_connection (connection_id)
);

-- SCIM Sync Log
CREATE TABLE scim_sync_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID NOT NULL REFERENCES sso_connections(id),
    
    operation VARCHAR(20) NOT NULL,  -- 'create', 'update', 'delete', 'sync'
    resource_type VARCHAR(20) NOT NULL,  -- 'user', 'group'
    external_id VARCHAR(255),
    internal_id UUID,
    
    status VARCHAR(20) NOT NULL,  -- 'success', 'failed', 'skipped'
    error_message TEXT,
    request_payload JSONB,
    response_payload JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_scim_logs_connection (connection_id),
    INDEX idx_scim_logs_created (created_at)
);

-- User External Identities
CREATE TABLE user_external_identities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    connection_id UUID NOT NULL REFERENCES sso_connections(id),
    
    external_id VARCHAR(255) NOT NULL,
    provider_user_id VARCHAR(255),
    email VARCHAR(255),
    
    -- Profile from IdP
    profile_data JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    
    UNIQUE(connection_id, external_id),
    INDEX idx_external_identities_user (user_id)
);
```

---

## 🔐 FEATURE SPECIFICATIONS

### 12.1 SAML 2.0 Implementation

#### Service Provider (SP) Configuration

```python
# backend/app/auth/sso/saml/config.py

from dataclasses import dataclass
from typing import Optional, Dict, Any
import os

@dataclass
class SAMLServiceProviderConfig:
    """Service Provider configuration for SAML"""
    
    # Entity ID (unique identifier for SP)
    entity_id: str
    
    # Assertion Consumer Service URL (where IdP sends SAML response)
    acs_url: str
    
    # Single Logout Service URL
    sls_url: str
    
    # SP Certificate and Private Key
    sp_cert: str
    sp_key: str
    
    # Metadata URL
    metadata_url: str
    
    # Security settings
    want_assertions_signed: bool = True
    want_messages_signed: bool = True
    want_name_id_encrypted: bool = False
    authn_requests_signed: bool = True
    logout_requests_signed: bool = True
    logout_responses_signed: bool = True
    
    # Name ID format
    name_id_format: str = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
    
    @classmethod
    def from_env(cls, org_slug: str) -> "SAMLServiceProviderConfig":
        """Create SP config from environment variables"""
        base_url = os.getenv("BASE_URL", "https://logiaccounting-pro.onrender.com")
        
        return cls(
            entity_id=f"{base_url}/saml/{org_slug}/metadata",
            acs_url=f"{base_url}/api/v1/auth/saml/{org_slug}/acs",
            sls_url=f"{base_url}/api/v1/auth/saml/{org_slug}/sls",
            sp_cert=os.getenv("SAML_SP_CERT", ""),
            sp_key=os.getenv("SAML_SP_KEY", ""),
            metadata_url=f"{base_url}/api/v1/auth/saml/{org_slug}/metadata",
        )


@dataclass  
class SAMLIdentityProviderConfig:
    """Identity Provider configuration for SAML"""
    
    # Entity ID of the IdP
    entity_id: str
    
    # SSO URL (where to send SAML requests)
    sso_url: str
    
    # SLO URL (for logout)
    slo_url: Optional[str] = None
    
    # IdP X.509 Certificate
    x509_cert: str = ""
    
    # Additional certificates (for rotation)
    x509_cert_multi: list = None
    
    # Binding types
    sso_binding: str = "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
    slo_binding: str = "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
    
    @classmethod
    def from_metadata_url(cls, url: str) -> "SAMLIdentityProviderConfig":
        """Parse IdP metadata from URL"""
        import requests
        from lxml import etree
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        return cls.from_metadata_xml(response.text)
    
    @classmethod
    def from_metadata_xml(cls, xml: str) -> "SAMLIdentityProviderConfig":
        """Parse IdP metadata from XML"""
        from onelogin.saml2.idp_metadata_parser import OneLogin_Saml2_IdPMetadataParser
        
        parsed = OneLogin_Saml2_IdPMetadataParser.parse(xml)
        idp_data = parsed.get("idp", {})
        
        return cls(
            entity_id=idp_data.get("entityId", ""),
            sso_url=idp_data.get("singleSignOnService", {}).get("url", ""),
            slo_url=idp_data.get("singleLogoutService", {}).get("url"),
            x509_cert=idp_data.get("x509cert", ""),
        )
```

#### SAML Assertion Processor

```python
# backend/app/auth/sso/saml/processor.py

from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils
import logging

logger = logging.getLogger(__name__)


class SAMLProcessor:
    """Process SAML assertions and responses"""
    
    def __init__(self, sp_config: Dict[str, Any], idp_config: Dict[str, Any]):
        self.settings = {
            "strict": True,
            "debug": False,
            "sp": sp_config,
            "idp": idp_config,
            "security": {
                "nameIdEncrypted": False,
                "authnRequestsSigned": True,
                "logoutRequestSigned": True,
                "logoutResponseSigned": True,
                "signMetadata": True,
                "wantMessagesSigned": True,
                "wantAssertionsSigned": True,
                "wantNameIdEncrypted": False,
                "requestedAuthnContext": False,
                "signatureAlgorithm": "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
                "digestAlgorithm": "http://www.w3.org/2001/04/xmlenc#sha256",
            },
        }
    
    def create_authn_request(self, request_data: Dict[str, Any]) -> Tuple[str, str]:
        """
        Create SAML authentication request
        Returns: (redirect_url, request_id)
        """
        auth = OneLogin_Saml2_Auth(request_data, self.settings)
        
        # Generate redirect URL
        redirect_url = auth.login(return_to=request_data.get("return_to", "/"))
        request_id = auth.get_last_request_id()
        
        logger.info(f"Created SAML AuthnRequest with ID: {request_id}")
        
        return redirect_url, request_id
    
    def process_response(
        self, 
        request_data: Dict[str, Any], 
        expected_request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process SAML response from IdP
        Returns: User attributes from assertion
        """
        auth = OneLogin_Saml2_Auth(request_data, self.settings)
        
        # Process the response
        auth.process_response(request_id=expected_request_id)
        
        errors = auth.get_errors()
        if errors:
            error_reason = auth.get_last_error_reason()
            logger.error(f"SAML Response errors: {errors}, Reason: {error_reason}")
            raise SAMLValidationError(f"SAML validation failed: {error_reason}")
        
        if not auth.is_authenticated():
            raise SAMLValidationError("User not authenticated")
        
        # Extract user attributes
        attributes = auth.get_attributes()
        name_id = auth.get_nameid()
        name_id_format = auth.get_nameid_format()
        session_index = auth.get_session_index()
        session_expiration = auth.get_session_expiration()
        
        logger.info(f"SAML authentication successful for: {name_id}")
        
        return {
            "name_id": name_id,
            "name_id_format": name_id_format,
            "session_index": session_index,
            "session_expiration": session_expiration,
            "attributes": self._normalize_attributes(attributes),
            "raw_attributes": attributes,
        }
    
    def create_logout_request(
        self, 
        request_data: Dict[str, Any],
        name_id: str,
        session_index: str
    ) -> str:
        """Create SAML logout request"""
        auth = OneLogin_Saml2_Auth(request_data, self.settings)
        
        return auth.logout(
            name_id=name_id,
            session_index=session_index,
            return_to=request_data.get("return_to", "/")
        )
    
    def process_logout_response(self, request_data: Dict[str, Any]) -> bool:
        """Process SAML logout response"""
        auth = OneLogin_Saml2_Auth(request_data, self.settings)
        
        # Check if this is a logout request from IdP
        if "SAMLRequest" in request_data.get("get_data", {}):
            # IdP-initiated logout
            auth.process_slo(keep_local_session=False)
        else:
            # SP-initiated logout response
            auth.process_slo()
        
        errors = auth.get_errors()
        if errors:
            logger.error(f"SAML Logout errors: {errors}")
            return False
        
        return True
    
    def get_metadata(self) -> str:
        """Generate SP metadata XML"""
        from onelogin.saml2.metadata import OneLogin_Saml2_Metadata
        
        metadata = OneLogin_Saml2_Metadata.builder(
            sp=self.settings["sp"],
            authnsign=self.settings["security"]["authnRequestsSigned"],
            wsign=self.settings["security"]["wantAssertionsSigned"],
        )
        
        return metadata
    
    def _normalize_attributes(self, attributes: Dict[str, list]) -> Dict[str, Any]:
        """Normalize SAML attributes to standard format"""
        # Common attribute mappings
        mappings = {
            # Standard SAML attributes
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress": "email",
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname": "first_name",
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname": "last_name",
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name": "display_name",
            "http://schemas.microsoft.com/ws/2008/06/identity/claims/groups": "groups",
            # Simple attribute names
            "email": "email",
            "firstName": "first_name",
            "lastName": "last_name",
            "displayName": "display_name",
            "groups": "groups",
        }
        
        normalized = {}
        for attr_key, values in attributes.items():
            mapped_key = mappings.get(attr_key, attr_key)
            # Take first value for single-valued attributes
            if mapped_key in ["email", "first_name", "last_name", "display_name"]:
                normalized[mapped_key] = values[0] if values else None
            else:
                normalized[mapped_key] = values
        
        return normalized


class SAMLValidationError(Exception):
    """SAML validation error"""
    pass
```

### 12.2 OAuth2 / OpenID Connect Implementation

#### OAuth2 Provider Base Class

```python
# backend/app/auth/sso/oauth/providers/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from authlib.integrations.requests_client import OAuth2Session
import httpx
import logging

logger = logging.getLogger(__name__)


@dataclass
class OAuthUserInfo:
    """Standardized user info from OAuth provider"""
    id: str
    email: str
    email_verified: bool
    first_name: Optional[str]
    last_name: Optional[str]
    display_name: Optional[str]
    picture_url: Optional[str]
    groups: list
    raw_data: Dict[str, Any]


class OAuthProvider(ABC):
    """Base class for OAuth2 providers"""
    
    name: str = "base"
    authorization_url: str
    token_url: str
    userinfo_url: str
    scopes: list = ["openid", "profile", "email"]
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        **kwargs
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.extra_params = kwargs
    
    def get_authorization_url(self, state: str, nonce: Optional[str] = None) -> str:
        """Generate authorization URL for redirect"""
        session = OAuth2Session(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            scope=" ".join(self.scopes),
        )
        
        params = {"state": state}
        if nonce:
            params["nonce"] = nonce
        
        # Add provider-specific params
        params.update(self._get_extra_auth_params())
        
        url, _ = session.create_authorization_url(
            self.authorization_url,
            **params
        )
        
        return url
    
    async def exchange_code(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Accept": "application/json"},
            )
            
            response.raise_for_status()
            return response.json()
    
    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Fetch user info from provider"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.userinfo_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
            
            response.raise_for_status()
            data = response.json()
            
            return self._parse_user_info(data)
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Accept": "application/json"},
            )
            
            response.raise_for_status()
            return response.json()
    
    @abstractmethod
    def _parse_user_info(self, data: Dict[str, Any]) -> OAuthUserInfo:
        """Parse provider-specific user info response"""
        pass
    
    def _get_extra_auth_params(self) -> Dict[str, str]:
        """Get provider-specific authorization params"""
        return {}
```

#### Microsoft Entra ID (Azure AD) Provider

```python
# backend/app/auth/sso/oauth/providers/microsoft.py

from typing import Dict, Any, Optional, List
from .base import OAuthProvider, OAuthUserInfo
import httpx


class MicrosoftProvider(OAuthProvider):
    """Microsoft Entra ID (Azure AD) OAuth2 / OIDC provider"""
    
    name = "microsoft"
    
    # Can be customized per tenant
    authorization_url_template = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
    token_url_template = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    userinfo_url = "https://graph.microsoft.com/v1.0/me"
    groups_url = "https://graph.microsoft.com/v1.0/me/memberOf"
    
    scopes = ["openid", "profile", "email", "User.Read", "GroupMember.Read.All"]
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        tenant: str = "common",  # 'common', 'organizations', or specific tenant ID
        **kwargs
    ):
        super().__init__(client_id, client_secret, redirect_uri, **kwargs)
        self.tenant = tenant
        self.authorization_url = self.authorization_url_template.format(tenant=tenant)
        self.token_url = self.token_url_template.format(tenant=tenant)
    
    def _get_extra_auth_params(self) -> Dict[str, str]:
        return {
            "response_mode": "query",
            "prompt": "select_account",  # Allow user to choose account
        }
    
    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Fetch user info including groups from Microsoft Graph"""
        async with httpx.AsyncClient() as client:
            # Get basic user info
            user_response = await client.get(
                self.userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_response.raise_for_status()
            user_data = user_response.json()
            
            # Get group memberships
            groups = await self._get_user_groups(client, access_token)
            user_data["groups"] = groups
            
            return self._parse_user_info(user_data)
    
    async def _get_user_groups(
        self, 
        client: httpx.AsyncClient, 
        access_token: str
    ) -> List[str]:
        """Fetch user's group memberships"""
        try:
            response = await client.get(
                self.groups_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            groups = []
            
            for item in data.get("value", []):
                if item.get("@odata.type") == "#microsoft.graph.group":
                    groups.append(item.get("displayName", ""))
            
            return groups
            
        except Exception as e:
            logger.warning(f"Failed to fetch Microsoft groups: {e}")
            return []
    
    def _parse_user_info(self, data: Dict[str, Any]) -> OAuthUserInfo:
        return OAuthUserInfo(
            id=data.get("id", ""),
            email=data.get("mail") or data.get("userPrincipalName", ""),
            email_verified=True,  # Microsoft validates emails
            first_name=data.get("givenName"),
            last_name=data.get("surname"),
            display_name=data.get("displayName"),
            picture_url=None,  # Requires separate Graph API call
            groups=data.get("groups", []),
            raw_data=data,
        )
```

#### Google Workspace Provider

```python
# backend/app/auth/sso/oauth/providers/google.py

from typing import Dict, Any
from .base import OAuthProvider, OAuthUserInfo


class GoogleProvider(OAuthProvider):
    """Google Workspace OAuth2 / OIDC provider"""
    
    name = "google"
    authorization_url = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url = "https://oauth2.googleapis.com/token"
    userinfo_url = "https://openidconnect.googleapis.com/v1/userinfo"
    
    scopes = ["openid", "profile", "email"]
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        hosted_domain: str = None,  # Restrict to specific domain
        **kwargs
    ):
        super().__init__(client_id, client_secret, redirect_uri, **kwargs)
        self.hosted_domain = hosted_domain
    
    def _get_extra_auth_params(self) -> Dict[str, str]:
        params = {
            "access_type": "offline",  # Get refresh token
            "prompt": "consent",
        }
        
        if self.hosted_domain:
            params["hd"] = self.hosted_domain
        
        return params
    
    def _parse_user_info(self, data: Dict[str, Any]) -> OAuthUserInfo:
        return OAuthUserInfo(
            id=data.get("sub", ""),
            email=data.get("email", ""),
            email_verified=data.get("email_verified", False),
            first_name=data.get("given_name"),
            last_name=data.get("family_name"),
            display_name=data.get("name"),
            picture_url=data.get("picture"),
            groups=[],  # Google Workspace Admin SDK needed for groups
            raw_data=data,
        )
```

#### Okta Provider

```python
# backend/app/auth/sso/oauth/providers/okta.py

from typing import Dict, Any, List
from .base import OAuthProvider, OAuthUserInfo
import httpx


class OktaProvider(OAuthProvider):
    """Okta OAuth2 / OIDC provider"""
    
    name = "okta"
    scopes = ["openid", "profile", "email", "groups"]
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        okta_domain: str,  # e.g., 'dev-123456.okta.com'
        **kwargs
    ):
        super().__init__(client_id, client_secret, redirect_uri, **kwargs)
        self.okta_domain = okta_domain
        
        self.authorization_url = f"https://{okta_domain}/oauth2/default/v1/authorize"
        self.token_url = f"https://{okta_domain}/oauth2/default/v1/token"
        self.userinfo_url = f"https://{okta_domain}/oauth2/default/v1/userinfo"
    
    def _parse_user_info(self, data: Dict[str, Any]) -> OAuthUserInfo:
        return OAuthUserInfo(
            id=data.get("sub", ""),
            email=data.get("email", ""),
            email_verified=data.get("email_verified", False),
            first_name=data.get("given_name"),
            last_name=data.get("family_name"),
            display_name=data.get("name"),
            picture_url=data.get("picture"),
            groups=data.get("groups", []),
            raw_data=data,
        )
```

### 12.3 SCIM 2.0 Provisioning

```python
# backend/app/auth/sso/scim/resources.py

from flask import Blueprint, request, jsonify
from functools import wraps
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime

scim_bp = Blueprint('scim', __name__, url_prefix='/scim/v2')


def scim_auth_required(f):
    """Validate SCIM bearer token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return scim_error('Unauthorized', 401)
        
        token = auth_header.replace('Bearer ', '')
        
        # Validate token against stored SCIM tokens
        connection = validate_scim_token(token)
        if not connection:
            return scim_error('Invalid token', 401)
        
        request.scim_connection = connection
        return f(*args, **kwargs)
    
    return decorated


def scim_error(detail: str, status: int, scim_type: str = None) -> tuple:
    """Generate SCIM error response"""
    error = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
        "detail": detail,
        "status": status,
    }
    if scim_type:
        error["scimType"] = scim_type
    
    return jsonify(error), status


# ==================== Users Resource ====================

@scim_bp.route('/Users', methods=['GET'])
@scim_auth_required
def list_users():
    """List users with SCIM filtering and pagination"""
    connection = request.scim_connection
    
    # Parse query parameters
    filter_param = request.args.get('filter', '')
    start_index = int(request.args.get('startIndex', 1))
    count = int(request.args.get('count', 100))
    
    # Parse SCIM filter
    users, total = get_users_with_filter(
        connection.organization_id,
        filter_param,
        start_index,
        count
    )
    
    return jsonify({
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": total,
        "startIndex": start_index,
        "itemsPerPage": len(users),
        "Resources": [user_to_scim(u) for u in users],
    })


@scim_bp.route('/Users/<user_id>', methods=['GET'])
@scim_auth_required
def get_user(user_id: str):
    """Get single user by ID"""
    connection = request.scim_connection
    
    user = get_user_by_external_id(connection.id, user_id)
    if not user:
        return scim_error('User not found', 404)
    
    return jsonify(user_to_scim(user))


@scim_bp.route('/Users', methods=['POST'])
@scim_auth_required
def create_user():
    """Create new user via SCIM"""
    connection = request.scim_connection
    data = request.get_json()
    
    # Validate required fields
    if not data.get('userName'):
        return scim_error('userName is required', 400, 'invalidValue')
    
    # Check if user already exists
    existing = get_user_by_username(connection.organization_id, data['userName'])
    if existing:
        return scim_error('User already exists', 409, 'uniqueness')
    
    # Create user
    user = create_user_from_scim(connection, data)
    
    log_scim_operation(connection.id, 'create', 'user', user.id, data)
    
    return jsonify(user_to_scim(user)), 201


@scim_bp.route('/Users/<user_id>', methods=['PUT'])
@scim_auth_required
def update_user(user_id: str):
    """Replace user (full update)"""
    connection = request.scim_connection
    data = request.get_json()
    
    user = get_user_by_external_id(connection.id, user_id)
    if not user:
        return scim_error('User not found', 404)
    
    # Update user
    user = update_user_from_scim(user, data)
    
    log_scim_operation(connection.id, 'update', 'user', user.id, data)
    
    return jsonify(user_to_scim(user))


@scim_bp.route('/Users/<user_id>', methods=['PATCH'])
@scim_auth_required
def patch_user(user_id: str):
    """Partial update user"""
    connection = request.scim_connection
    data = request.get_json()
    
    user = get_user_by_external_id(connection.id, user_id)
    if not user:
        return scim_error('User not found', 404)
    
    # Process PATCH operations
    operations = data.get('Operations', [])
    for op in operations:
        apply_scim_patch(user, op)
    
    user.save()
    
    log_scim_operation(connection.id, 'patch', 'user', user.id, data)
    
    return jsonify(user_to_scim(user))


@scim_bp.route('/Users/<user_id>', methods=['DELETE'])
@scim_auth_required
def delete_user(user_id: str):
    """Delete/deactivate user"""
    connection = request.scim_connection
    
    user = get_user_by_external_id(connection.id, user_id)
    if not user:
        return scim_error('User not found', 404)
    
    # Deactivate rather than delete
    user.is_active = False
    user.deactivated_at = datetime.utcnow()
    user.save()
    
    log_scim_operation(connection.id, 'delete', 'user', user.id, None)
    
    return '', 204


# ==================== Helper Functions ====================

def user_to_scim(user) -> Dict[str, Any]:
    """Convert user model to SCIM representation"""
    return {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": str(user.external_id or user.id),
        "externalId": str(user.external_id or user.id),
        "userName": user.email,
        "name": {
            "givenName": user.first_name,
            "familyName": user.last_name,
            "formatted": f"{user.first_name} {user.last_name}",
        },
        "displayName": user.name,
        "emails": [
            {
                "value": user.email,
                "type": "work",
                "primary": True,
            }
        ],
        "active": user.is_active,
        "groups": [
            {"value": g.id, "display": g.name}
            for g in user.groups
        ],
        "meta": {
            "resourceType": "User",
            "created": user.created_at.isoformat() + "Z",
            "lastModified": user.updated_at.isoformat() + "Z",
        },
    }


def create_user_from_scim(connection, data: Dict[str, Any]):
    """Create user from SCIM payload"""
    from app.models.user import User
    
    name_data = data.get('name', {})
    emails = data.get('emails', [])
    primary_email = next(
        (e['value'] for e in emails if e.get('primary')),
        emails[0]['value'] if emails else data.get('userName')
    )
    
    user = User(
        email=primary_email,
        first_name=name_data.get('givenName', ''),
        last_name=name_data.get('familyName', ''),
        organization_id=connection.organization_id,
        is_active=data.get('active', True),
        role=connection.default_role,
        external_id=data.get('externalId') or str(uuid.uuid4()),
        sso_connection_id=connection.id,
    )
    
    # Generate random password (user will use SSO)
    user.set_password(uuid.uuid4().hex)
    user.save()
    
    # Map groups if provided
    if data.get('groups') and connection.scim_sync_groups:
        sync_user_groups(user, data['groups'], connection)
    
    return user
```

---

## 🌐 API ENDPOINTS

### SSO Routes

```python
# backend/app/routes/sso.py

from flask import Blueprint, request, jsonify, redirect, session
from app.auth.sso.saml.processor import SAMLProcessor
from app.auth.sso.oauth.providers import get_provider
from app.services.sso_service import SSOService
import secrets

sso_bp = Blueprint('sso', __name__, url_prefix='/api/v1/auth/sso')


# ==================== SSO Discovery ====================

@sso_bp.route('/discover', methods=['POST'])
def discover_sso():
    """
    Discover SSO connection by email domain
    Returns available SSO options for the domain
    """
    data = request.get_json()
    email = data.get('email', '')
    
    if not email or '@' not in email:
        return jsonify({'error': 'Invalid email'}), 400
    
    domain = email.split('@')[1].lower()
    
    connections = SSOService.get_connections_by_domain(domain)
    
    if not connections:
        return jsonify({
            'sso_available': False,
            'message': 'No SSO configured for this domain'
        })
    
    return jsonify({
        'sso_available': True,
        'connections': [
            {
                'id': str(c.id),
                'name': c.name,
                'provider': c.provider,
                'protocol': c.protocol,
            }
            for c in connections
        ]
    })


# ==================== SAML Endpoints ====================

@sso_bp.route('/saml/<connection_id>/login', methods=['GET'])
def saml_login(connection_id: str):
    """Initiate SAML login"""
    connection = SSOService.get_connection(connection_id)
    if not connection or connection.protocol != 'saml':
        return jsonify({'error': 'Invalid SSO connection'}), 404
    
    processor = SAMLProcessor(
        sp_config=connection.get_sp_config(),
        idp_config=connection.get_idp_config()
    )
    
    request_data = prepare_saml_request(request)
    redirect_url, request_id = processor.create_authn_request(request_data)
    
    # Store request ID for validation
    session['saml_request_id'] = request_id
    session['saml_connection_id'] = connection_id
    
    return redirect(redirect_url)


@sso_bp.route('/saml/<connection_id>/acs', methods=['POST'])
def saml_acs(connection_id: str):
    """SAML Assertion Consumer Service (callback)"""
    connection = SSOService.get_connection(connection_id)
    if not connection:
        return redirect(f'/login?error=invalid_connection')
    
    processor = SAMLProcessor(
        sp_config=connection.get_sp_config(),
        idp_config=connection.get_idp_config()
    )
    
    try:
        request_data = prepare_saml_request(request)
        expected_id = session.pop('saml_request_id', None)
        
        result = processor.process_response(request_data, expected_id)
        
        # Find or create user
        user = SSOService.find_or_create_user(
            connection=connection,
            attributes=result['attributes'],
            name_id=result['name_id'],
            session_index=result['session_index']
        )
        
        # Create application session
        tokens = SSOService.create_session(user, connection, result)
        
        # Redirect to frontend with tokens
        return redirect(
            f'/auth/callback?token={tokens["access_token"]}'
            f'&refresh={tokens["refresh_token"]}'
        )
        
    except Exception as e:
        logger.error(f"SAML ACS error: {e}")
        return redirect(f'/login?error=saml_error&message={str(e)}')


@sso_bp.route('/saml/<connection_id>/metadata', methods=['GET'])
def saml_metadata(connection_id: str):
    """Get SP metadata for IdP configuration"""
    connection = SSOService.get_connection(connection_id)
    if not connection:
        return jsonify({'error': 'Invalid connection'}), 404
    
    processor = SAMLProcessor(
        sp_config=connection.get_sp_config(),
        idp_config=connection.get_idp_config()
    )
    
    metadata = processor.get_metadata()
    
    return metadata, 200, {'Content-Type': 'application/xml'}


@sso_bp.route('/saml/<connection_id>/sls', methods=['GET', 'POST'])
def saml_sls(connection_id: str):
    """SAML Single Logout Service"""
    connection = SSOService.get_connection(connection_id)
    if not connection:
        return redirect('/login')
    
    processor = SAMLProcessor(
        sp_config=connection.get_sp_config(),
        idp_config=connection.get_idp_config()
    )
    
    request_data = prepare_saml_request(request)
    success = processor.process_logout_response(request_data)
    
    if success:
        # Clear local session
        SSOService.logout_user(connection_id)
    
    return redirect('/login?logout=success')


# ==================== OAuth2 / OIDC Endpoints ====================

@sso_bp.route('/oauth/<connection_id>/login', methods=['GET'])
def oauth_login(connection_id: str):
    """Initiate OAuth2 login"""
    connection = SSOService.get_connection(connection_id)
    if not connection or connection.protocol not in ['oauth2', 'oidc']:
        return jsonify({'error': 'Invalid SSO connection'}), 404
    
    provider = get_provider(connection)
    
    # Generate state and nonce
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    
    # Store in session
    session['oauth_state'] = state
    session['oauth_nonce'] = nonce
    session['oauth_connection_id'] = connection_id
    
    auth_url = provider.get_authorization_url(state, nonce)
    
    return redirect(auth_url)


@sso_bp.route('/oauth/<connection_id>/callback', methods=['GET'])
async def oauth_callback(connection_id: str):
    """OAuth2 callback handler"""
    connection = SSOService.get_connection(connection_id)
    if not connection:
        return redirect('/login?error=invalid_connection')
    
    # Verify state
    state = request.args.get('state')
    stored_state = session.pop('oauth_state', None)
    
    if not state or state != stored_state:
        return redirect('/login?error=invalid_state')
    
    # Check for errors
    error = request.args.get('error')
    if error:
        error_desc = request.args.get('error_description', '')
        return redirect(f'/login?error={error}&message={error_desc}')
    
    # Exchange code for tokens
    code = request.args.get('code')
    if not code:
        return redirect('/login?error=no_code')
    
    try:
        provider = get_provider(connection)
        
        # Exchange code
        tokens = await provider.exchange_code(code)
        
        # Get user info
        user_info = await provider.get_user_info(tokens['access_token'])
        
        # Verify email domain if restricted
        if connection.allowed_domains:
            email_domain = user_info.email.split('@')[1].lower()
            if email_domain not in connection.allowed_domains:
                return redirect('/login?error=domain_not_allowed')
        
        # Find or create user
        user = SSOService.find_or_create_user_oauth(
            connection=connection,
            user_info=user_info,
            tokens=tokens
        )
        
        # Create application session
        app_tokens = SSOService.create_session(user, connection, {
            'oauth_tokens': tokens,
            'user_info': user_info.raw_data
        })
        
        return redirect(
            f'/auth/callback?token={app_tokens["access_token"]}'
            f'&refresh={app_tokens["refresh_token"]}'
        )
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return redirect(f'/login?error=oauth_error&message={str(e)}')


# ==================== SSO Management ====================

@sso_bp.route('/connections', methods=['GET'])
@admin_required
def list_connections():
    """List all SSO connections for organization"""
    org_id = get_current_org_id()
    connections = SSOService.get_connections(org_id)
    
    return jsonify({
        'connections': [c.to_dict() for c in connections]
    })


@sso_bp.route('/connections', methods=['POST'])
@admin_required
def create_connection():
    """Create new SSO connection"""
    data = request.get_json()
    org_id = get_current_org_id()
    
    connection = SSOService.create_connection(org_id, data)
    
    return jsonify(connection.to_dict()), 201


@sso_bp.route('/connections/<connection_id>', methods=['PUT'])
@admin_required
def update_connection(connection_id: str):
    """Update SSO connection"""
    data = request.get_json()
    
    connection = SSOService.update_connection(connection_id, data)
    
    return jsonify(connection.to_dict())


@sso_bp.route('/connections/<connection_id>', methods=['DELETE'])
@admin_required
def delete_connection(connection_id: str):
    """Delete SSO connection"""
    SSOService.delete_connection(connection_id)
    
    return '', 204


@sso_bp.route('/connections/<connection_id>/test', methods=['POST'])
@admin_required
def test_connection(connection_id: str):
    """Test SSO connection configuration"""
    result = SSOService.test_connection(connection_id)
    
    return jsonify(result)
```

---

## 🖥️ FRONTEND COMPONENTS

### SSO Login Button

```typescript
// frontend/src/features/sso/components/SSOLoginButton.tsx

import React from 'react';
import { SSOConnection } from '../types';

interface SSOLoginButtonProps {
  connection: SSOConnection;
  className?: string;
}

const providerIcons: Record<string, string> = {
  microsoft: '/icons/microsoft.svg',
  google: '/icons/google.svg',
  okta: '/icons/okta.svg',
  onelogin: '/icons/onelogin.svg',
  default: '/icons/sso-key.svg',
};

const providerLabels: Record<string, string> = {
  microsoft: 'Microsoft',
  google: 'Google',
  okta: 'Okta',
  onelogin: 'OneLogin',
  saml: 'SSO',
};

export const SSOLoginButton: React.FC<SSOLoginButtonProps> = ({
  connection,
  className = '',
}) => {
  const handleClick = () => {
    const protocol = connection.protocol;
    const baseUrl = `/api/v1/auth/sso/${protocol}/${connection.id}/login`;
    
    // Redirect to SSO login
    window.location.href = baseUrl;
  };

  const icon = providerIcons[connection.provider] || providerIcons.default;
  const label = providerLabels[connection.provider] || connection.name;

  return (
    <button
      onClick={handleClick}
      className={`
        flex items-center justify-center gap-3 w-full px-4 py-3
        border border-gray-300 rounded-lg
        bg-white hover:bg-gray-50
        transition-colors duration-200
        text-gray-700 font-medium
        ${className}
      `}
    >
      <img src={icon} alt="" className="w-5 h-5" />
      <span>Continue with {label}</span>
    </button>
  );
};
```

### SSO Configuration Form

```typescript
// frontend/src/features/sso/components/SSOConfigForm.tsx

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { SSOConnection, SSOProtocol, SSOProvider } from '../types';

interface SSOConfigFormProps {
  connection?: SSOConnection;
  onSubmit: (data: Partial<SSOConnection>) => Promise<void>;
  onCancel: () => void;
}

export const SSOConfigForm: React.FC<SSOConfigFormProps> = ({
  connection,
  onSubmit,
  onCancel,
}) => {
  const [protocol, setProtocol] = useState<SSOProtocol>(
    connection?.protocol || 'saml'
  );
  const [isLoading, setIsLoading] = useState(false);

  const { register, handleSubmit, watch, formState: { errors } } = useForm({
    defaultValues: connection || {
      name: '',
      protocol: 'saml',
      provider: 'custom',
      status: 'inactive',
    },
  });

  const onFormSubmit = async (data: any) => {
    setIsLoading(true);
    try {
      await onSubmit(data);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
      {/* Basic Info */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Basic Information</h3>
        
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Connection Name
          </label>
          <input
            {...register('name', { required: 'Name is required' })}
            type="text"
            placeholder="e.g., Corporate SSO"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
          />
          {errors.name && (
            <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Protocol
          </label>
          <select
            {...register('protocol')}
            onChange={(e) => setProtocol(e.target.value as SSOProtocol)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
          >
            <option value="saml">SAML 2.0</option>
            <option value="oauth2">OAuth 2.0</option>
            <option value="oidc">OpenID Connect</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Identity Provider
          </label>
          <select
            {...register('provider')}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
          >
            <option value="microsoft">Microsoft Entra ID (Azure AD)</option>
            <option value="google">Google Workspace</option>
            <option value="okta">Okta</option>
            <option value="onelogin">OneLogin</option>
            <option value="custom">Custom / Other</option>
          </select>
        </div>
      </div>

      {/* SAML Configuration */}
      {protocol === 'saml' && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">SAML Configuration</h3>
          
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-medium text-blue-900">Service Provider (SP) Details</h4>
            <p className="text-sm text-blue-700 mt-1">
              Use these values to configure your Identity Provider:
            </p>
            <div className="mt-3 space-y-2 text-sm">
              <div>
                <span className="font-medium">Entity ID:</span>
                <code className="ml-2 bg-blue-100 px-2 py-1 rounded">
                  {`${window.location.origin}/saml/${connection?.id || '{connection_id}'}/metadata`}
                </code>
              </div>
              <div>
                <span className="font-medium">ACS URL:</span>
                <code className="ml-2 bg-blue-100 px-2 py-1 rounded">
                  {`${window.location.origin}/api/v1/auth/sso/saml/${connection?.id || '{connection_id}'}/acs`}
                </code>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              IdP Metadata URL
            </label>
            <input
              {...register('metadata_url')}
              type="url"
              placeholder="https://idp.example.com/metadata"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            />
            <p className="mt-1 text-sm text-gray-500">
              Or paste the metadata XML below
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              IdP Metadata XML
            </label>
            <textarea
              {...register('metadata_xml')}
              rows={6}
              placeholder="Paste IdP metadata XML here..."
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm font-mono text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              IdP SSO URL
            </label>
            <input
              {...register('saml_sso_url')}
              type="url"
              placeholder="https://idp.example.com/sso"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              IdP Certificate
            </label>
            <textarea
              {...register('saml_certificate')}
              rows={4}
              placeholder="-----BEGIN CERTIFICATE-----&#10;...&#10;-----END CERTIFICATE-----"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm font-mono text-sm"
            />
          </div>
        </div>
      )}

      {/* OAuth2 / OIDC Configuration */}
      {(protocol === 'oauth2' || protocol === 'oidc') && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">
            {protocol === 'oidc' ? 'OpenID Connect' : 'OAuth 2.0'} Configuration
          </h3>

          {protocol === 'oidc' && (
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Discovery URL (/.well-known/openid-configuration)
              </label>
              <input
                {...register('oidc_discovery_url')}
                type="url"
                placeholder="https://idp.example.com/.well-known/openid-configuration"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Client ID
            </label>
            <input
              {...register('oauth_client_id', { required: 'Client ID is required' })}
              type="text"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Client Secret
            </label>
            <input
              {...register('oauth_client_secret')}
              type="password"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            />
          </div>

          {protocol === 'oauth2' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Authorization URL
                </label>
                <input
                  {...register('oauth_authorization_url')}
                  type="url"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Token URL
                </label>
                <input
                  {...register('oauth_token_url')}
                  type="url"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  User Info URL
                </label>
                <input
                  {...register('oauth_userinfo_url')}
                  type="url"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                />
              </div>
            </>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Scopes
            </label>
            <input
              {...register('oauth_scopes')}
              type="text"
              defaultValue="openid profile email"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            />
          </div>
        </div>
      )}

      {/* Attribute Mapping */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Attribute Mapping</h3>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Email Attribute
            </label>
            <input
              {...register('attribute_mapping.email')}
              type="text"
              defaultValue="email"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              First Name Attribute
            </label>
            <input
              {...register('attribute_mapping.first_name')}
              type="text"
              defaultValue="given_name"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Last Name Attribute
            </label>
            <input
              {...register('attribute_mapping.last_name')}
              type="text"
              defaultValue="family_name"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Groups Attribute
            </label>
            <input
              {...register('attribute_mapping.groups')}
              type="text"
              defaultValue="groups"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            />
          </div>
        </div>
      </div>

      {/* Security Settings */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Security Settings</h3>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Allowed Email Domains (comma-separated)
          </label>
          <input
            {...register('allowed_domains')}
            type="text"
            placeholder="example.com, company.org"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
          />
        </div>

        <div className="flex items-center">
          <input
            {...register('enforce_sso')}
            type="checkbox"
            className="h-4 w-4 rounded border-gray-300 text-blue-600"
          />
          <label className="ml-2 text-sm text-gray-700">
            Enforce SSO (disable password login for this domain)
          </label>
        </div>

        <div className="flex items-center">
          <input
            {...register('allow_idp_initiated')}
            type="checkbox"
            defaultChecked
            className="h-4 w-4 rounded border-gray-300 text-blue-600"
          />
          <label className="ml-2 text-sm text-gray-700">
            Allow IdP-initiated login
          </label>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3 pt-4 border-t">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isLoading}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {isLoading ? 'Saving...' : connection ? 'Update Connection' : 'Create Connection'}
        </button>
      </div>
    </form>
  );
};
```

---

## ⏱️ IMPLEMENTATION TIMELINE

| Week | Tasks | Hours |
|------|-------|-------|
| **Week 1** | Database schema, models, SAML config | 12h |
| **Week 2** | SAML processor, metadata, validation | 14h |
| **Week 3** | OAuth2 providers (Microsoft, Google, Okta) | 12h |
| **Week 4** | OIDC discovery, JWKS validation | 8h |
| **Week 5** | SCIM 2.0 endpoints | 10h |
| **Week 6** | Frontend SSO management UI | 12h |
| **Week 7** | Login flow integration, testing | 10h |
| **Week 8** | Security audit, documentation | 8h |

**Total: ~86 hours (8 weeks)**

---

## ✅ FEATURE CHECKLIST

| # | Feature | Priority | Status |
|---|---------|----------|--------|
| 12.1 | Database schema for SSO | P0 | 🔲 |
| 12.2 | SAML 2.0 SP configuration | P0 | 🔲 |
| 12.3 | SAML assertion processing | P0 | 🔲 |
| 12.4 | SAML metadata generation | P0 | 🔲 |
| 12.5 | Microsoft Entra ID provider | P0 | 🔲 |
| 12.6 | Google Workspace provider | P0 | 🔲 |
| 12.7 | Okta provider | P1 | 🔲 |
| 12.8 | OIDC discovery & JWKS | P1 | 🔲 |
| 12.9 | SCIM 2.0 User provisioning | P1 | 🔲 |
| 12.10 | SCIM 2.0 Group sync | P2 | 🔲 |
| 12.11 | SSO login UI | P0 | 🔲 |
| 12.12 | Admin SSO management UI | P0 | 🔲 |
| 12.13 | Domain-based SSO discovery | P1 | 🔲 |
| 12.14 | Role mapping from IdP groups | P1 | 🔲 |
| 12.15 | Single Logout (SLO) | P2 | 🔲 |
| 12.16 | Session management | P0 | 🔲 |

---

*Phase 12 Plan - LogiAccounting Pro*
*Enterprise SSO (SAML 2.0 / OAuth2 / OpenID Connect)*
