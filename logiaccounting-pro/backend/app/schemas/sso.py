"""
SSO Pydantic schemas for request/response validation
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class SSOProtocol(str, Enum):
    SAML = "saml"
    OAUTH2 = "oauth2"
    OIDC = "oidc"


class SSOProviderType(str, Enum):
    MICROSOFT = "microsoft"
    GOOGLE = "google"
    OKTA = "okta"
    GITHUB = "github"
    CUSTOM = "custom"


class SSOConnectionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


# SSO Connection Schemas
class SAMLConfigurationCreate(BaseModel):
    idp_entity_id: str
    idp_sso_url: str
    idp_slo_url: Optional[str] = None
    idp_certificate: str
    sp_certificate: Optional[str] = None
    sp_private_key: Optional[str] = None
    name_id_format: Optional[str] = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
    attribute_mapping: Optional[Dict[str, str]] = None
    jit_provisioning: bool = True
    default_role: str = "client"
    role_mapping: Optional[Dict[str, str]] = None


class OAuthConfigurationCreate(BaseModel):
    client_id: str
    client_secret: str
    scopes: Optional[List[str]] = None
    tenant_id: Optional[str] = None
    domain: Optional[str] = None
    authorization_server: Optional[str] = None
    jit_provisioning: bool = True
    default_role: str = "client"
    role_mapping: Optional[Dict[str, str]] = None


class SSOConnectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    protocol: SSOProtocol
    provider_type: Optional[SSOProviderType] = None
    domains: List[str] = Field(..., min_items=1)
    configuration: Dict[str, Any]
    status: SSOConnectionStatus = SSOConnectionStatus.PENDING


class SSOConnectionUpdate(BaseModel):
    name: Optional[str] = None
    domains: Optional[List[str]] = None
    configuration: Optional[Dict[str, Any]] = None
    status: Optional[SSOConnectionStatus] = None


class SSOConnectionResponse(BaseModel):
    id: str
    name: str
    protocol: str
    provider_type: Optional[str] = None
    domains: List[str]
    status: str
    scim_enabled: bool = False
    created_at: str
    updated_at: str


# SSO Authentication Schemas
class SSOLoginInitiate(BaseModel):
    email: Optional[str] = None
    connection_id: Optional[str] = None


class SSOLoginInitiateResponse(BaseModel):
    redirect_url: str
    state: Optional[str] = None
    connection_id: str
    protocol: str


class SSOCallbackRequest(BaseModel):
    code: Optional[str] = None
    state: Optional[str] = None
    saml_response: Optional[str] = Field(None, alias="SAMLResponse")
    relay_state: Optional[str] = Field(None, alias="RelayState")
    error: Optional[str] = None
    error_description: Optional[str] = None


class SSOLoginResponse(BaseModel):
    success: bool = True
    token: str
    user: Dict[str, Any]
    sso: Dict[str, Any]


# Domain Discovery
class DomainDiscoveryRequest(BaseModel):
    email: str


class DomainDiscoveryResponse(BaseModel):
    sso_enabled: bool
    connection_id: Optional[str] = None
    connection_name: Optional[str] = None
    protocol: Optional[str] = None
    provider_type: Optional[str] = None


# SCIM Schemas
class SCIMTokenResponse(BaseModel):
    token: str
    endpoint: str


class SCIMConfigUpdate(BaseModel):
    scim_enabled: bool


# SSO Session Schemas
class SSOSessionResponse(BaseModel):
    id: str
    connection_id: str
    user_id: Optional[str] = None
    status: str
    created_at: str
    expires_at: Optional[str] = None


# External Identity Schemas
class ExternalIdentityResponse(BaseModel):
    id: str
    user_id: str
    connection_id: str
    external_user_id: str
    external_email: str
    last_login_at: Optional[str] = None
    created_at: str


# SCIM Sync Log Schemas
class SCIMSyncLogResponse(BaseModel):
    id: str
    connection_id: str
    operation: str
    status: str
    details: Optional[Dict[str, Any]] = None
    created_at: str
