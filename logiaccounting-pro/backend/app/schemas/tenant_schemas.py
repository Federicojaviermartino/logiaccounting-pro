"""
Multi-Tenancy Schemas
Pydantic models for tenant API validation
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from enum import Enum


# Enums

class TenantStatusEnum(str, Enum):
    PENDING = 'pending'
    ACTIVE = 'active'
    SUSPENDED = 'suspended'
    CANCELLED = 'cancelled'
    DELETED = 'deleted'


class TenantTierEnum(str, Enum):
    FREE = 'free'
    STANDARD = 'standard'
    PROFESSIONAL = 'professional'
    BUSINESS = 'business'
    ENTERPRISE = 'enterprise'


class IsolationLevelEnum(str, Enum):
    SHARED = 'shared'
    SCHEMA = 'schema'
    DATABASE = 'database'


class InvitationStatusEnum(str, Enum):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    EXPIRED = 'expired'
    REVOKED = 'revoked'


class MemberRoleEnum(str, Enum):
    OWNER = 'owner'
    ADMIN = 'admin'
    MANAGER = 'manager'
    MEMBER = 'member'
    VIEWER = 'viewer'


# Tenant Schemas

class TenantCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    display_name: Optional[str] = Field(None, max_length=200)
    owner_email: EmailStr
    billing_email: Optional[EmailStr] = None
    tier: Optional[TenantTierEnum] = TenantTierEnum.FREE
    country: Optional[str] = Field(None, max_length=2)
    timezone: Optional[str] = Field("UTC", max_length=50)
    locale: Optional[str] = Field("en", max_length=10)
    metadata: Optional[Dict[str, Any]] = None


class TenantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    display_name: Optional[str] = Field(None, max_length=200)
    billing_email: Optional[EmailStr] = None
    country: Optional[str] = Field(None, max_length=2)
    timezone: Optional[str] = Field(None, max_length=50)
    locale: Optional[str] = Field(None, max_length=10)
    metadata: Optional[Dict[str, Any]] = None


class TenantResponse(BaseModel):
    id: str
    name: str
    slug: str
    display_name: Optional[str] = None
    status: TenantStatusEnum
    tier: TenantTierEnum
    isolation_level: IsolationLevelEnum
    owner_id: Optional[str] = None
    owner_email: Optional[str] = None
    billing_email: Optional[str] = None
    country: Optional[str] = None
    timezone: str
    locale: str
    metadata: Dict[str, Any] = {}
    created_at: str
    updated_at: str
    activated_at: Optional[str] = None
    suspended_at: Optional[str] = None


class TenantListResponse(BaseModel):
    success: bool = True
    tenants: List[TenantResponse]
    pagination: Dict[str, Any]


class TenantDetailResponse(BaseModel):
    success: bool = True
    tenant: TenantResponse


# Domain Schemas

class DomainCreate(BaseModel):
    domain: str = Field(..., min_length=4, max_length=255)
    domain_type: Optional[str] = Field("custom", pattern="^(custom|subdomain)$")
    is_primary: Optional[bool] = False


class DomainResponse(BaseModel):
    id: str
    tenant_id: str
    domain: str
    domain_type: str
    is_primary: bool
    is_verified: bool
    verification_token: Optional[str] = None
    verification_method: str
    ssl_status: str
    created_at: str
    verified_at: Optional[str] = None


class DomainListResponse(BaseModel):
    success: bool = True
    domains: List[DomainResponse]


class DomainVerifyResponse(BaseModel):
    success: bool = True
    is_verified: bool
    message: str
    domain: Optional[DomainResponse] = None


# Settings Schemas

class TenantSettingsUpdate(BaseModel):
    # Branding
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    secondary_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    custom_css: Optional[str] = None
    # Email
    email_from_name: Optional[str] = None
    email_from_address: Optional[EmailStr] = None
    email_reply_to: Optional[EmailStr] = None
    email_footer: Optional[str] = None
    # Invoice
    invoice_prefix: Optional[str] = Field(None, max_length=10)
    invoice_starting_number: Optional[int] = Field(None, ge=1)
    invoice_footer: Optional[str] = None
    default_payment_terms: Optional[int] = Field(None, ge=0, le=365)
    default_tax_rate: Optional[float] = Field(None, ge=0, le=100)
    default_currency: Optional[str] = Field(None, max_length=3)


class SecuritySettingsUpdate(BaseModel):
    require_2fa: Optional[bool] = None
    allowed_ip_ranges: Optional[List[str]] = None
    session_timeout_minutes: Optional[int] = Field(None, ge=5, le=10080)
    password_min_length: Optional[int] = Field(None, ge=8, le=128)
    password_require_special: Optional[bool] = None


class TenantSettingsResponse(BaseModel):
    id: str
    tenant_id: str
    # Branding
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: str
    secondary_color: str
    custom_css: Optional[str] = None
    # Email
    email_from_name: Optional[str] = None
    email_from_address: Optional[str] = None
    email_reply_to: Optional[str] = None
    email_footer: Optional[str] = None
    # Invoice
    invoice_prefix: str
    invoice_starting_number: int
    invoice_footer: Optional[str] = None
    default_payment_terms: int
    default_tax_rate: float
    default_currency: str
    # Security
    require_2fa: bool
    allowed_ip_ranges: List[str]
    session_timeout_minutes: int
    password_min_length: int
    password_require_special: bool
    # API
    api_rate_limit: int
    created_at: str
    updated_at: str


class SettingsDetailResponse(BaseModel):
    success: bool = True
    settings: TenantSettingsResponse


# Subscription Schemas

class SubscriptionResponse(BaseModel):
    id: str
    tenant_id: str
    tier: TenantTierEnum
    status: str
    billing_cycle: str
    price_cents: int
    currency: str
    current_period_start: str
    current_period_end: Optional[str] = None
    trial_ends_at: Optional[str] = None
    cancelled_at: Optional[str] = None
    cancel_at_period_end: bool
    created_at: str


class SubscriptionDetailResponse(BaseModel):
    success: bool = True
    subscription: SubscriptionResponse


class SubscriptionUpgradeRequest(BaseModel):
    tier: TenantTierEnum
    billing_cycle: Optional[str] = Field("monthly", pattern="^(monthly|yearly)$")
    payment_method_id: Optional[str] = None


class SubscriptionCancelRequest(BaseModel):
    cancel_at_period_end: bool = True
    reason: Optional[str] = None


# Plan/Pricing Schemas

class PlanFeature(BaseModel):
    name: str
    description: str
    included: bool


class PricingPlan(BaseModel):
    tier: TenantTierEnum
    name: str
    description: str
    price_monthly: int
    price_yearly: int
    currency: str
    features: List[str]
    limits: Dict[str, Any]
    is_popular: bool = False


class PlanListResponse(BaseModel):
    success: bool = True
    plans: List[PricingPlan]


# Quota Schemas

class QuotaResponse(BaseModel):
    tenant_id: str
    tier: TenantTierEnum
    # Limits
    max_users: int
    max_storage_mb: int
    max_api_calls_daily: int
    max_invoices_monthly: int
    max_products: int
    max_projects: int
    max_integrations: int
    # Current usage
    current_users: int
    current_storage_mb: int
    current_api_calls_today: int
    current_invoices_month: int
    current_products: int
    current_projects: int
    current_integrations: int
    # Timestamps
    api_calls_reset_at: str
    invoices_reset_at: str
    updated_at: str


class QuotaDetailResponse(BaseModel):
    success: bool = True
    quota: QuotaResponse


class UsageSummary(BaseModel):
    resource: str
    current: int
    limit: int
    percentage: float
    unlimited: bool = False


class UsageSummaryResponse(BaseModel):
    success: bool = True
    tenant_id: str
    tier: str
    usage: List[UsageSummary]


# Feature Schemas

class FeatureResponse(BaseModel):
    id: str
    tenant_id: str
    feature_name: str
    is_enabled: bool
    config: Dict[str, Any]
    expires_at: Optional[str] = None
    created_at: str


class FeatureListResponse(BaseModel):
    success: bool = True
    features: List[FeatureResponse]


class FeatureEnableRequest(BaseModel):
    feature_name: str
    config: Optional[Dict[str, Any]] = None
    expires_at: Optional[str] = None


# Team/Invitation Schemas

class InvitationCreate(BaseModel):
    email: EmailStr
    role: MemberRoleEnum = MemberRoleEnum.MEMBER


class InvitationResponse(BaseModel):
    id: str
    tenant_id: str
    email: str
    role: str
    invited_by: Optional[str] = None
    status: InvitationStatusEnum
    expires_at: str
    accepted_at: Optional[str] = None
    created_at: str


class InvitationListResponse(BaseModel):
    success: bool = True
    invitations: List[InvitationResponse]


class InvitationAcceptRequest(BaseModel):
    token: str


class MemberResponse(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    role: str
    is_owner: bool
    permissions: List[str]
    joined_at: str
    # User info (joined)
    user_email: Optional[str] = None
    user_name: Optional[str] = None


class MemberListResponse(BaseModel):
    success: bool = True
    members: List[MemberResponse]
    total: int


class MemberUpdateRequest(BaseModel):
    role: MemberRoleEnum
    permissions: Optional[List[str]] = None


# Activity/Audit Schemas

class TenantActivityResponse(BaseModel):
    success: bool = True
    activities: List[Dict[str, Any]]
    pagination: Dict[str, Any]


# Statistics Schemas

class TenantStatsResponse(BaseModel):
    success: bool = True
    tenant_id: str
    members_count: int
    storage_used_mb: int
    api_calls_today: int
    invoices_this_month: int
    active_projects: int
    active_integrations: int
    last_activity_at: Optional[str] = None


# Billing Schemas

class BillingHistoryItem(BaseModel):
    id: str
    date: str
    description: str
    amount_cents: int
    currency: str
    status: str
    invoice_url: Optional[str] = None


class BillingHistoryResponse(BaseModel):
    success: bool = True
    items: List[BillingHistoryItem]


class PaymentMethodResponse(BaseModel):
    id: str
    type: str
    last_four: Optional[str] = None
    brand: Optional[str] = None
    exp_month: Optional[int] = None
    exp_year: Optional[int] = None
    is_default: bool


class PaymentMethodListResponse(BaseModel):
    success: bool = True
    payment_methods: List[PaymentMethodResponse]
