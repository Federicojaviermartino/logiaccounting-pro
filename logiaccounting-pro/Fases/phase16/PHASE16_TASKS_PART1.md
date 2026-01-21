# LogiAccounting Pro - Phase 16 Tasks Part 1

## CORE MULTI-TENANCY SYSTEM

---

## TASK 1: DATABASE MODELS

### 1.1 Tenant Model

**File:** `backend/app/tenancy/models/tenant.py`

```python
"""
Tenant Model
Core tenant/organization entity
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from app.extensions import db
import uuid
import enum


class TenantStatus(str, enum.Enum):
    """Tenant status options"""
    PENDING = 'pending'
    ACTIVE = 'active'
    SUSPENDED = 'suspended'
    CANCELLED = 'cancelled'
    DELETED = 'deleted'


class TenantTier(str, enum.Enum):
    """Tenant tier options"""
    FREE = 'free'
    STANDARD = 'standard'
    PROFESSIONAL = 'professional'
    BUSINESS = 'business'
    ENTERPRISE = 'enterprise'


class IsolationLevel(str, enum.Enum):
    """Data isolation level"""
    SHARED_DATABASE = 'shared_database'
    SCHEMA = 'schema'
    DATABASE = 'database'


class Tenant(db.Model):
    """Tenant/Organization model"""
    
    __tablename__ = 'tenants'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Identification
    slug = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255))
    
    # Contact
    email = Column(String(255), nullable=False)
    phone = Column(String(50))
    
    # Address
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(2))  # ISO country code
    
    # Tax Information
    tax_id = Column(String(50))
    vat_number = Column(String(50))
    
    # Status
    status = Column(String(50), default=TenantStatus.ACTIVE.value, index=True)
    suspended_at = Column(db.DateTime)
    suspended_reason = Column(Text)
    
    # Isolation Strategy
    isolation_level = Column(String(50), default=IsolationLevel.SHARED_DATABASE.value)
    database_name = Column(String(100))
    schema_name = Column(String(100))
    
    # Tier
    tier = Column(String(50), default=TenantTier.STANDARD.value)
    
    # Timestamps
    created_at = Column(db.DateTime, default=datetime.utcnow)
    updated_at = Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(db.DateTime)
    
    # Owner
    owner_id = Column(UUID(as_uuid=True))
    
    # Relationships
    settings = relationship('TenantSettings', back_populates='tenant', uselist=False, cascade='all, delete-orphan')
    domains = relationship('TenantDomain', back_populates='tenant', cascade='all, delete-orphan')
    subscription = relationship('TenantSubscription', back_populates='tenant', uselist=False, cascade='all, delete-orphan')
    quotas = relationship('TenantQuota', back_populates='tenant', uselist=False, cascade='all, delete-orphan')
    features = relationship('TenantFeature', back_populates='tenant', cascade='all, delete-orphan')
    invitations = relationship('TenantInvitation', back_populates='tenant', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.slug and self.name:
            self.slug = self._generate_slug(self.name)
    
    @staticmethod
    def _generate_slug(name: str) -> str:
        """Generate URL-safe slug from name"""
        import re
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')
        return slug[:100]
    
    @property
    def is_active(self) -> bool:
        """Check if tenant is active"""
        return self.status == TenantStatus.ACTIVE.value
    
    @property
    def is_enterprise(self) -> bool:
        """Check if tenant is enterprise tier"""
        return self.tier == TenantTier.ENTERPRISE.value
    
    @property
    def primary_domain(self) -> Optional['TenantDomain']:
        """Get primary domain"""
        for domain in self.domains:
            if domain.is_primary and domain.is_active:
                return domain
        return None
    
    def suspend(self, reason: str = None):
        """Suspend the tenant"""
        self.status = TenantStatus.SUSPENDED.value
        self.suspended_at = datetime.utcnow()
        self.suspended_reason = reason
    
    def activate(self):
        """Activate the tenant"""
        self.status = TenantStatus.ACTIVE.value
        self.suspended_at = None
        self.suspended_reason = None
    
    def soft_delete(self):
        """Soft delete the tenant"""
        self.status = TenantStatus.DELETED.value
        self.deleted_at = datetime.utcnow()
    
    def has_feature(self, feature_key: str) -> bool:
        """Check if tenant has a feature enabled"""
        for feature in self.features:
            if feature.feature_key == feature_key and feature.is_enabled:
                # Check expiration
                if feature.expires_at and feature.expires_at < datetime.utcnow():
                    return False
                return True
        return False
    
    def get_quota(self, resource: str) -> Optional[int]:
        """Get quota limit for a resource"""
        if not self.quotas:
            return None
        return getattr(self.quotas, f'max_{resource}', None)
    
    def get_usage(self, resource: str) -> int:
        """Get current usage for a resource"""
        if not self.quotas:
            return 0
        return getattr(self.quotas, f'current_{resource}', 0)
    
    def check_quota(self, resource: str, amount: int = 1) -> bool:
        """Check if resource usage is within quota"""
        limit = self.get_quota(resource)
        if limit is None:  # Unlimited
            return True
        
        current = self.get_usage(resource)
        return (current + amount) <= limit
    
    def to_dict(self, include_settings: bool = False) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            'id': str(self.id),
            'slug': self.slug,
            'name': self.name,
            'legal_name': self.legal_name,
            'email': self.email,
            'phone': self.phone,
            'address': {
                'line1': self.address_line1,
                'line2': self.address_line2,
                'city': self.city,
                'state': self.state,
                'postal_code': self.postal_code,
                'country': self.country,
            },
            'status': self.status,
            'tier': self.tier,
            'isolation_level': self.isolation_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        
        if include_settings and self.settings:
            data['settings'] = self.settings.to_dict()
        
        if self.primary_domain:
            data['primary_domain'] = self.primary_domain.domain
        
        return data


class TenantDomain(db.Model):
    """Tenant custom domain"""
    
    __tablename__ = 'tenant_domains'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    
    # Domain
    domain = Column(String(255), unique=True, nullable=False, index=True)
    domain_type = Column(String(50), default='subdomain')
    # 'subdomain' or 'custom'
    
    # Verification
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(100))
    verified_at = Column(db.DateTime)
    
    # SSL
    ssl_enabled = Column(Boolean, default=True)
    ssl_certificate_id = Column(String(255))
    
    # Status
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tenant = relationship('Tenant', back_populates='domains')
    
    def generate_verification_token(self) -> str:
        """Generate domain verification token"""
        import secrets
        self.verification_token = f"logiaccounting-verify-{secrets.token_hex(16)}"
        return self.verification_token
    
    def verify(self) -> bool:
        """Mark domain as verified"""
        self.is_verified = True
        self.verified_at = datetime.utcnow()
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'domain': self.domain,
            'domain_type': self.domain_type,
            'is_verified': self.is_verified,
            'is_primary': self.is_primary,
            'is_active': self.is_active,
            'ssl_enabled': self.ssl_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
```

### 1.2 Tenant Settings Model

**File:** `backend/app/tenancy/models/tenant_settings.py`

```python
"""
Tenant Settings Model
Configuration and branding for tenants
"""

from datetime import datetime
from typing import Dict, Any
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from app.extensions import db
import uuid


class TenantSettings(db.Model):
    """Tenant configuration and branding"""
    
    __tablename__ = 'tenant_settings'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    # Branding
    logo_url = Column(Text)
    logo_dark_url = Column(Text)
    favicon_url = Column(Text)
    primary_color = Column(String(7), default='#2563eb')
    secondary_color = Column(String(7), default='#1e40af')
    
    # Locale
    default_language = Column(String(10), default='en')
    default_timezone = Column(String(50), default='UTC')
    default_currency = Column(String(3), default='USD')
    date_format = Column(String(20), default='YYYY-MM-DD')
    number_format = Column(String(20), default='1,234.56')
    
    # Features
    features_enabled = Column(JSONB, default=dict)
    modules_enabled = Column(ARRAY(Text), default=[])
    
    # Security
    password_policy = Column(JSONB, default=dict)
    # {min_length: 8, require_uppercase: true, require_number: true, require_special: false}
    session_timeout_minutes = Column(Integer, default=60)
    mfa_required = Column(Boolean, default=False)
    ip_whitelist = Column(ARRAY(Text), default=[])
    
    # Email
    email_from_name = Column(String(255))
    email_from_address = Column(String(255))
    email_reply_to = Column(String(255))
    
    # Notifications
    notification_settings = Column(JSONB, default=dict)
    
    # Custom settings
    custom_settings = Column(JSONB, default=dict)
    
    updated_at = Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship('Tenant', back_populates='settings')
    
    DEFAULT_PASSWORD_POLICY = {
        'min_length': 8,
        'require_uppercase': True,
        'require_lowercase': True,
        'require_number': True,
        'require_special': False,
        'max_age_days': 90,
    }
    
    @property
    def effective_password_policy(self) -> Dict[str, Any]:
        """Get password policy with defaults"""
        policy = {**self.DEFAULT_PASSWORD_POLICY}
        if self.password_policy:
            policy.update(self.password_policy)
        return policy
    
    def get_branding(self) -> Dict[str, Any]:
        """Get branding settings"""
        return {
            'logo_url': self.logo_url,
            'logo_dark_url': self.logo_dark_url,
            'favicon_url': self.favicon_url,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
        }
    
    def get_locale(self) -> Dict[str, Any]:
        """Get locale settings"""
        return {
            'language': self.default_language,
            'timezone': self.default_timezone,
            'currency': self.default_currency,
            'date_format': self.date_format,
            'number_format': self.number_format,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'branding': self.get_branding(),
            'locale': self.get_locale(),
            'security': {
                'password_policy': self.effective_password_policy,
                'session_timeout_minutes': self.session_timeout_minutes,
                'mfa_required': self.mfa_required,
                'ip_whitelist': self.ip_whitelist or [],
            },
            'email': {
                'from_name': self.email_from_name,
                'from_address': self.email_from_address,
                'reply_to': self.email_reply_to,
            },
            'features_enabled': self.features_enabled or {},
            'modules_enabled': self.modules_enabled or [],
            'notification_settings': self.notification_settings or {},
            'custom_settings': self.custom_settings or {},
        }
```

### 1.3 Tenant Subscription & Quota Models

**File:** `backend/app/tenancy/models/tenant_subscription.py`

```python
"""
Tenant Subscription Model
Subscription and billing information
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.extensions import db
import uuid


class TenantSubscription(db.Model):
    """Tenant subscription/billing"""
    
    __tablename__ = 'tenant_subscriptions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    
    # Plan
    plan_id = Column(String(100), nullable=False)
    plan_name = Column(String(255), nullable=False)
    
    # Billing
    billing_cycle = Column(String(20), default='monthly')
    # 'monthly', 'quarterly', 'annual'
    
    price_amount = Column(Numeric(10, 2), nullable=False, default=0)
    price_currency = Column(String(3), default='USD')
    
    # Status
    status = Column(String(50), default='active', index=True)
    # 'trial', 'active', 'past_due', 'cancelled', 'expired'
    
    # Dates
    trial_ends_at = Column(db.DateTime)
    current_period_start = Column(db.DateTime)
    current_period_end = Column(db.DateTime)
    cancelled_at = Column(db.DateTime)
    
    # Payment
    payment_method_id = Column(String(255))
    stripe_subscription_id = Column(String(255))
    stripe_customer_id = Column(String(255))
    
    # Auto-renewal
    auto_renew = Column(Boolean, default=True)
    
    created_at = Column(db.DateTime, default=datetime.utcnow)
    updated_at = Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship('Tenant', back_populates='subscription')
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is active"""
        return self.status in ['active', 'trial']
    
    @property
    def is_trial(self) -> bool:
        """Check if in trial period"""
        return self.status == 'trial' and self.trial_ends_at and self.trial_ends_at > datetime.utcnow()
    
    @property
    def days_remaining(self) -> int:
        """Days remaining in current period"""
        if not self.current_period_end:
            return 0
        delta = self.current_period_end - datetime.utcnow()
        return max(0, delta.days)
    
    @property
    def trial_days_remaining(self) -> int:
        """Days remaining in trial"""
        if not self.is_trial or not self.trial_ends_at:
            return 0
        delta = self.trial_ends_at - datetime.utcnow()
        return max(0, delta.days)
    
    def start_trial(self, days: int = 14):
        """Start trial period"""
        self.status = 'trial'
        self.trial_ends_at = datetime.utcnow() + timedelta(days=days)
        self.current_period_start = datetime.utcnow()
        self.current_period_end = self.trial_ends_at
    
    def activate(self):
        """Activate subscription"""
        self.status = 'active'
        self.current_period_start = datetime.utcnow()
        
        # Set period end based on billing cycle
        if self.billing_cycle == 'monthly':
            self.current_period_end = datetime.utcnow() + timedelta(days=30)
        elif self.billing_cycle == 'quarterly':
            self.current_period_end = datetime.utcnow() + timedelta(days=90)
        elif self.billing_cycle == 'annual':
            self.current_period_end = datetime.utcnow() + timedelta(days=365)
    
    def cancel(self, immediate: bool = False):
        """Cancel subscription"""
        self.cancelled_at = datetime.utcnow()
        
        if immediate:
            self.status = 'cancelled'
            self.current_period_end = datetime.utcnow()
        else:
            # Will expire at end of current period
            self.auto_renew = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'plan_id': self.plan_id,
            'plan_name': self.plan_name,
            'billing_cycle': self.billing_cycle,
            'price': {
                'amount': float(self.price_amount) if self.price_amount else 0,
                'currency': self.price_currency,
            },
            'status': self.status,
            'is_trial': self.is_trial,
            'trial_days_remaining': self.trial_days_remaining,
            'days_remaining': self.days_remaining,
            'current_period_start': self.current_period_start.isoformat() if self.current_period_start else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'auto_renew': self.auto_renew,
        }


class TenantQuota(db.Model):
    """Tenant resource quotas and usage"""
    
    __tablename__ = 'tenant_quotas'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    # Resource Limits
    max_users = Column(Integer, default=5)
    max_storage_mb = Column(Integer, default=1024)
    max_api_calls_per_month = Column(Integer, default=10000)
    max_invoices_per_month = Column(Integer, default=100)
    max_products = Column(Integer, default=500)
    max_projects = Column(Integer, default=50)
    max_integrations = Column(Integer, default=3)
    
    # Current Usage
    current_users = Column(Integer, default=0)
    current_storage_mb = Column(Numeric(10, 2), default=0)
    current_api_calls = Column(Integer, default=0)
    current_invoices = Column(Integer, default=0)
    current_products = Column(Integer, default=0)
    current_projects = Column(Integer, default=0)
    current_integrations = Column(Integer, default=0)
    
    # Usage Reset
    usage_reset_day = Column(Integer, default=1)
    last_reset_at = Column(db.DateTime)
    
    updated_at = Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship('Tenant', back_populates='quotas')
    
    def check_limit(self, resource: str, amount: int = 1) -> bool:
        """Check if adding amount would exceed limit"""
        max_val = getattr(self, f'max_{resource}', None)
        if max_val is None:  # Unlimited
            return True
        
        current = getattr(self, f'current_{resource}', 0) or 0
        return (current + amount) <= max_val
    
    def increment_usage(self, resource: str, amount: int = 1):
        """Increment resource usage"""
        attr = f'current_{resource}'
        current = getattr(self, attr, 0) or 0
        setattr(self, attr, current + amount)
    
    def decrement_usage(self, resource: str, amount: int = 1):
        """Decrement resource usage"""
        attr = f'current_{resource}'
        current = getattr(self, attr, 0) or 0
        setattr(self, attr, max(0, current - amount))
    
    def reset_monthly_usage(self):
        """Reset monthly usage counters"""
        self.current_api_calls = 0
        self.current_invoices = 0
        self.last_reset_at = datetime.utcnow()
    
    def get_usage_percentage(self, resource: str) -> float:
        """Get usage percentage for a resource"""
        max_val = getattr(self, f'max_{resource}', None)
        if max_val is None or max_val == 0:
            return 0.0
        
        current = getattr(self, f'current_{resource}', 0) or 0
        return (current / max_val) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        resources = ['users', 'storage_mb', 'api_calls_per_month', 'invoices_per_month', 
                     'products', 'projects', 'integrations']
        
        quotas = {}
        for resource in resources:
            max_key = f'max_{resource}'
            current_key = f'current_{resource.replace("_per_month", "")}'
            
            max_val = getattr(self, max_key, None)
            current_val = getattr(self, current_key, 0) or 0
            
            quotas[resource] = {
                'limit': max_val,
                'used': float(current_val) if isinstance(current_val, (int, float)) else current_val,
                'percentage': self.get_usage_percentage(resource.replace("_per_month", "")) if max_val else 0,
            }
        
        return {
            'quotas': quotas,
            'last_reset_at': self.last_reset_at.isoformat() if self.last_reset_at else None,
        }
```

### 1.4 Tenant Feature Model

**File:** `backend/app/tenancy/models/tenant_feature.py`

```python
"""
Tenant Feature Model
Feature flags per tenant
"""

from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.extensions import db
import uuid


class TenantFeature(db.Model):
    """Tenant feature flag"""
    
    __tablename__ = 'tenant_features'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    
    feature_key = Column(String(100), nullable=False)
    is_enabled = Column(Boolean, default=False)
    
    # Override settings
    config = Column(JSONB, default=dict)
    
    # Validity
    enabled_at = Column(db.DateTime)
    expires_at = Column(db.DateTime)
    
    created_at = Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tenant = relationship('Tenant', back_populates='features')
    
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'feature_key', name='uq_tenant_feature'),
    )
    
    @property
    def is_active(self) -> bool:
        """Check if feature is currently active"""
        if not self.is_enabled:
            return False
        
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        
        return True
    
    def enable(self, expires_at: datetime = None):
        """Enable the feature"""
        self.is_enabled = True
        self.enabled_at = datetime.utcnow()
        self.expires_at = expires_at
    
    def disable(self):
        """Disable the feature"""
        self.is_enabled = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'feature_key': self.feature_key,
            'is_enabled': self.is_enabled,
            'is_active': self.is_active,
            'config': self.config or {},
            'enabled_at': self.enabled_at.isoformat() if self.enabled_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
        }


# Feature definitions
FEATURE_DEFINITIONS = {
    'basic_invoicing': {
        'name': 'Basic Invoicing',
        'description': 'Create and manage invoices',
        'tiers': ['free', 'standard', 'professional', 'business', 'enterprise'],
    },
    'inventory': {
        'name': 'Inventory Management',
        'description': 'Track products and stock levels',
        'tiers': ['standard', 'professional', 'business', 'enterprise'],
    },
    'reports': {
        'name': 'Reports & Analytics',
        'description': 'Generate business reports',
        'tiers': ['standard', 'professional', 'business', 'enterprise'],
    },
    'projects': {
        'name': 'Project Management',
        'description': 'Manage projects and track progress',
        'tiers': ['professional', 'business', 'enterprise'],
    },
    'api_access': {
        'name': 'API Access',
        'description': 'Access the REST API',
        'tiers': ['professional', 'business', 'enterprise'],
    },
    'audit': {
        'name': 'Audit Trail',
        'description': 'Complete audit logging',
        'tiers': ['business', 'enterprise'],
    },
    'sso': {
        'name': 'Single Sign-On',
        'description': 'SAML/OIDC authentication',
        'tiers': ['business', 'enterprise'],
    },
    'custom_domain': {
        'name': 'Custom Domain',
        'description': 'Use your own domain',
        'tiers': ['business', 'enterprise'],
    },
    'dedicated_db': {
        'name': 'Dedicated Database',
        'description': 'Isolated database instance',
        'tiers': ['enterprise'],
    },
    'priority_support': {
        'name': 'Priority Support',
        'description': '24/7 priority support',
        'tiers': ['enterprise'],
    },
}


def get_features_for_tier(tier: str) -> list:
    """Get list of features for a tier"""
    features = []
    for key, definition in FEATURE_DEFINITIONS.items():
        if tier in definition.get('tiers', []):
            features.append(key)
    return features
```

### 1.5 Tenant Invitation Model

**File:** `backend/app/tenancy/models/tenant_invitation.py`

```python
"""
Tenant Invitation Model
User invitations to tenant
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.extensions import db
import uuid
import secrets


class TenantInvitation(db.Model):
    """Tenant invitation"""
    
    __tablename__ = 'tenant_invitations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    
    # Invitation
    email = Column(String(255), nullable=False, index=True)
    role = Column(String(100), nullable=False)
    
    # Token
    token = Column(String(255), unique=True, nullable=False, index=True)
    
    # Status
    status = Column(String(50), default='pending')
    # 'pending', 'accepted', 'expired', 'cancelled'
    
    # Dates
    expires_at = Column(db.DateTime, nullable=False)
    accepted_at = Column(db.DateTime)
    
    # Inviter
    invited_by = Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    
    created_at = Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tenant = relationship('Tenant', back_populates='invitations')
    inviter = relationship('User', foreign_keys=[invited_by])
    
    def __init__(self, **kwargs):
        if 'token' not in kwargs:
            kwargs['token'] = secrets.token_urlsafe(32)
        if 'expires_at' not in kwargs:
            kwargs['expires_at'] = datetime.utcnow() + timedelta(days=7)
        super().__init__(**kwargs)
    
    @property
    def is_valid(self) -> bool:
        """Check if invitation is still valid"""
        return (
            self.status == 'pending' and 
            self.expires_at > datetime.utcnow()
        )
    
    def accept(self):
        """Accept the invitation"""
        self.status = 'accepted'
        self.accepted_at = datetime.utcnow()
    
    def cancel(self):
        """Cancel the invitation"""
        self.status = 'cancelled'
    
    def expire(self):
        """Mark as expired"""
        self.status = 'expired'
    
    @classmethod
    def find_by_token(cls, token: str) -> Optional['TenantInvitation']:
        """Find invitation by token"""
        return cls.query.filter(
            cls.token == token,
            cls.status == 'pending',
            cls.expires_at > datetime.utcnow()
        ).first()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'email': self.email,
            'role': self.role,
            'status': self.status,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_valid': self.is_valid,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
```

---

## TASK 2: TENANT CONTEXT & MIDDLEWARE

### 2.1 Tenant Context

**File:** `backend/app/tenancy/core/tenant_context.py`

```python
"""
Tenant Context
Thread-local storage for current tenant
"""

from contextvars import ContextVar
from typing import Optional, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from app.tenancy.models.tenant import Tenant

logger = logging.getLogger(__name__)

# Context variable for current tenant
_current_tenant: ContextVar[Optional['Tenant']] = ContextVar('current_tenant', default=None)


class TenantContext:
    """Tenant context manager"""
    
    @staticmethod
    def get_current_tenant() -> Optional['Tenant']:
        """Get current tenant from context"""
        return _current_tenant.get()
    
    @staticmethod
    def set_current_tenant(tenant: Optional['Tenant']):
        """Set current tenant in context"""
        _current_tenant.set(tenant)
        if tenant:
            logger.debug(f"Tenant context set: {tenant.slug}")
        else:
            logger.debug("Tenant context cleared")
    
    @staticmethod
    def get_current_tenant_id() -> Optional[str]:
        """Get current tenant ID"""
        tenant = _current_tenant.get()
        return str(tenant.id) if tenant else None
    
    @staticmethod
    def clear():
        """Clear tenant context"""
        _current_tenant.set(None)
    
    @staticmethod
    def require_tenant() -> 'Tenant':
        """Get current tenant or raise error"""
        tenant = _current_tenant.get()
        if not tenant:
            raise TenantContextError("No tenant in context")
        return tenant


class TenantContextError(Exception):
    """Raised when tenant context is required but not set"""
    pass


class tenant_context:
    """Context manager for temporary tenant context"""
    
    def __init__(self, tenant: 'Tenant'):
        self.tenant = tenant
        self.previous_tenant = None
    
    def __enter__(self):
        self.previous_tenant = TenantContext.get_current_tenant()
        TenantContext.set_current_tenant(self.tenant)
        return self.tenant
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        TenantContext.set_current_tenant(self.previous_tenant)


# Convenience functions
def get_current_tenant() -> Optional['Tenant']:
    """Get current tenant"""
    return TenantContext.get_current_tenant()


def get_current_tenant_id() -> Optional[str]:
    """Get current tenant ID"""
    return TenantContext.get_current_tenant_id()


def require_tenant() -> 'Tenant':
    """Require tenant in context"""
    return TenantContext.require_tenant()
```

### 2.2 Tenant Resolver

**File:** `backend/app/tenancy/core/tenant_resolver.py`

```python
"""
Tenant Resolver
Resolve tenant from request
"""

from flask import request, g
from typing import Optional
import logging

from app.tenancy.models.tenant import Tenant, TenantDomain, TenantStatus

logger = logging.getLogger(__name__)


class TenantResolver:
    """Resolve tenant from various sources"""
    
    # Base domain for subdomains
    BASE_DOMAIN = 'logiaccounting.com'
    
    @classmethod
    def resolve(cls) -> Optional[Tenant]:
        """
        Resolve tenant from request
        Priority:
        1. Custom domain
        2. Subdomain
        3. X-Tenant-ID header
        4. JWT claim (tenant_id in token)
        """
        tenant = None
        
        # 1. Try custom domain / subdomain
        tenant = cls._resolve_from_domain()
        if tenant:
            return tenant
        
        # 2. Try header
        tenant = cls._resolve_from_header()
        if tenant:
            return tenant
        
        # 3. Try JWT claim
        tenant = cls._resolve_from_jwt()
        if tenant:
            return tenant
        
        return None
    
    @classmethod
    def _resolve_from_domain(cls) -> Optional[Tenant]:
        """Resolve from request host"""
        host = request.host.lower()
        
        # Remove port if present
        if ':' in host:
            host = host.split(':')[0]
        
        # Check for custom domain
        domain = TenantDomain.query.filter(
            TenantDomain.domain == host,
            TenantDomain.is_active == True,
            TenantDomain.is_verified == True
        ).first()
        
        if domain:
            tenant = domain.tenant
            if tenant.is_active:
                logger.debug(f"Tenant resolved from custom domain: {host} -> {tenant.slug}")
                return tenant
        
        # Check for subdomain
        if cls.BASE_DOMAIN in host:
            subdomain = host.replace(f'.{cls.BASE_DOMAIN}', '').replace(cls.BASE_DOMAIN, '')
            
            if subdomain and subdomain not in ['www', 'app', 'api']:
                tenant = Tenant.query.filter(
                    Tenant.slug == subdomain,
                    Tenant.status == TenantStatus.ACTIVE.value
                ).first()
                
                if tenant:
                    logger.debug(f"Tenant resolved from subdomain: {subdomain}")
                    return tenant
        
        return None
    
    @classmethod
    def _resolve_from_header(cls) -> Optional[Tenant]:
        """Resolve from X-Tenant-ID header"""
        tenant_header = request.headers.get('X-Tenant-ID') or request.headers.get('X-Tenant-Slug')
        
        if tenant_header:
            # Try as slug first, then ID
            tenant = Tenant.query.filter(
                Tenant.slug == tenant_header,
                Tenant.status == TenantStatus.ACTIVE.value
            ).first()
            
            if not tenant:
                tenant = Tenant.query.filter(
                    Tenant.id == tenant_header,
                    Tenant.status == TenantStatus.ACTIVE.value
                ).first()
            
            if tenant:
                logger.debug(f"Tenant resolved from header: {tenant_header}")
                return tenant
        
        return None
    
    @classmethod
    def _resolve_from_jwt(cls) -> Optional[Tenant]:
        """Resolve from JWT token"""
        # Check if user is already loaded with organization
        if hasattr(g, 'current_user') and g.current_user:
            user = g.current_user
            if hasattr(user, 'organization_id') and user.organization_id:
                # Map organization to tenant
                tenant = Tenant.query.filter(
                    Tenant.id == user.organization_id,
                    Tenant.status == TenantStatus.ACTIVE.value
                ).first()
                
                if tenant:
                    logger.debug(f"Tenant resolved from JWT user: {tenant.slug}")
                    return tenant
        
        return None
    
    @classmethod
    def resolve_by_slug(cls, slug: str) -> Optional[Tenant]:
        """Resolve tenant by slug"""
        return Tenant.query.filter(
            Tenant.slug == slug,
            Tenant.status == TenantStatus.ACTIVE.value
        ).first()
    
    @classmethod
    def resolve_by_id(cls, tenant_id: str) -> Optional[Tenant]:
        """Resolve tenant by ID"""
        return Tenant.query.filter(
            Tenant.id == tenant_id,
            Tenant.status == TenantStatus.ACTIVE.value
        ).first()
```

### 2.3 Tenant Middleware

**File:** `backend/app/tenancy/core/tenant_middleware.py`

```python
"""
Tenant Middleware
Flask middleware for tenant context
"""

from flask import Flask, request, g, jsonify
from functools import wraps
import logging

from app.tenancy.core.tenant_context import TenantContext
from app.tenancy.core.tenant_resolver import TenantResolver

logger = logging.getLogger(__name__)


class TenantMiddleware:
    """Middleware to set tenant context on each request"""
    
    # Paths that don't require tenant context
    EXCLUDED_PATHS = [
        '/api/v1/auth/login',
        '/api/v1/auth/register',
        '/api/v1/auth/forgot-password',
        '/api/v1/auth/reset-password',
        '/api/v1/plans',
        '/api/v1/invitations',
        '/health',
        '/static',
    ]
    
    def __init__(self, app: Flask = None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize middleware with Flask app"""
        app.before_request(self._before_request)
        app.after_request(self._after_request)
    
    def _before_request(self):
        """Set tenant context before each request"""
        # Skip excluded paths
        if self._is_excluded_path():
            return
        
        # Resolve tenant
        tenant = TenantResolver.resolve()
        
        if tenant:
            # Set in context
            TenantContext.set_current_tenant(tenant)
            g.tenant = tenant
            g.tenant_id = str(tenant.id)
            
            # Check if tenant is suspended
            if not tenant.is_active:
                TenantContext.clear()
                return jsonify({
                    'success': False,
                    'error': 'Tenant is suspended',
                    'code': 'TENANT_SUSPENDED'
                }), 403
        else:
            g.tenant = None
            g.tenant_id = None
    
    def _after_request(self, response):
        """Clean up after request"""
        TenantContext.clear()
        return response
    
    def _is_excluded_path(self) -> bool:
        """Check if current path is excluded"""
        path = request.path
        
        for excluded in self.EXCLUDED_PATHS:
            if path.startswith(excluded):
                return True
        
        return False


def require_tenant(f):
    """Decorator to require tenant context"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        tenant = TenantContext.get_current_tenant()
        
        if not tenant:
            return jsonify({
                'success': False,
                'error': 'Tenant context required',
                'code': 'TENANT_REQUIRED'
            }), 400
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_tenant_feature(feature_key: str):
    """Decorator to require specific tenant feature"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            tenant = TenantContext.get_current_tenant()
            
            if not tenant:
                return jsonify({
                    'success': False,
                    'error': 'Tenant context required',
                    'code': 'TENANT_REQUIRED'
                }), 400
            
            if not tenant.has_feature(feature_key):
                return jsonify({
                    'success': False,
                    'error': f'Feature not available: {feature_key}',
                    'code': 'FEATURE_NOT_AVAILABLE'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def check_quota(resource: str, amount: int = 1):
    """Decorator to check quota before operation"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            tenant = TenantContext.get_current_tenant()
            
            if not tenant:
                return jsonify({
                    'success': False,
                    'error': 'Tenant context required',
                    'code': 'TENANT_REQUIRED'
                }), 400
            
            if not tenant.check_quota(resource, amount):
                return jsonify({
                    'success': False,
                    'error': f'Quota exceeded for: {resource}',
                    'code': 'QUOTA_EXCEEDED'
                }), 429
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
```

---

## TASK 3: TENANT-AWARE BASE MODEL

### 3.1 Base Model with Tenant ID

**File:** `backend/app/tenancy/core/tenant_aware_model.py`

```python
"""
Tenant-Aware Base Model
Base model class with automatic tenant filtering
"""

from sqlalchemy import Column, ForeignKey, event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declared_attr
from app.extensions import db
from app.tenancy.core.tenant_context import TenantContext, TenantContextError
import logging

logger = logging.getLogger(__name__)


class TenantAwareMixin:
    """Mixin for models that belong to a tenant"""
    
    @declared_attr
    def tenant_id(cls):
        return Column(
            UUID(as_uuid=True),
            ForeignKey('tenants.id', ondelete='CASCADE'),
            nullable=False,
            index=True
        )
    
    @classmethod
    def __declare_last__(cls):
        """Set up event listeners after model is fully declared"""
        # Auto-set tenant_id on insert
        @event.listens_for(cls, 'before_insert')
        def set_tenant_id(mapper, connection, target):
            if target.tenant_id is None:
                tenant = TenantContext.get_current_tenant()
                if tenant:
                    target.tenant_id = tenant.id
                else:
                    raise TenantContextError(
                        f"Cannot create {cls.__name__} without tenant context"
                    )


class TenantAwareQuery(db.Query):
    """Query class that automatically filters by tenant"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._with_tenant_filter = True
    
    def without_tenant_filter(self):
        """Disable tenant filtering for this query"""
        self._with_tenant_filter = False
        return self
    
    def _apply_tenant_filter(self):
        """Apply tenant filter if applicable"""
        if not self._with_tenant_filter:
            return self
        
        # Check if model has tenant_id
        mapper = self._entity_from_pre_ent_zero()
        if mapper is None:
            return self
        
        model = mapper.entity
        if not hasattr(model, 'tenant_id'):
            return self
        
        # Get current tenant
        tenant = TenantContext.get_current_tenant()
        if tenant:
            return self.filter(model.tenant_id == tenant.id)
        
        return self
    
    def __iter__(self):
        return super()._apply_tenant_filter().__iter__()
    
    def count(self):
        return super()._apply_tenant_filter().count()
    
    def first(self):
        return super()._apply_tenant_filter().first()
    
    def all(self):
        return super()._apply_tenant_filter().all()
    
    def one(self):
        return super()._apply_tenant_filter().one()
    
    def one_or_none(self):
        return super()._apply_tenant_filter().one_or_none()


# Alternative: Use SQLAlchemy events for automatic filtering
def setup_tenant_filtering(app):
    """Set up automatic tenant filtering via events"""
    
    @event.listens_for(db.session, 'do_orm_execute')
    def _add_tenant_filter(execute_state):
        """Add tenant filter to all queries"""
        if execute_state.is_select:
            # Get the model being queried
            mapper = execute_state.bind_mapper
            if mapper is None:
                return
            
            model = mapper.entity
            
            # Check if model has tenant_id
            if not hasattr(model, 'tenant_id'):
                return
            
            # Check if we should skip filtering
            if execute_state.execution_options.get('skip_tenant_filter'):
                return
            
            # Get current tenant
            tenant = TenantContext.get_current_tenant()
            if not tenant:
                return
            
            # Add filter
            execute_state.statement = execute_state.statement.where(
                model.tenant_id == tenant.id
            )
```

### 3.2 Query Filter Helper

**File:** `backend/app/tenancy/core/query_filter.py`

```python
"""
Query Filter Helper
Utilities for tenant-filtered queries
"""

from typing import Type, TypeVar, Optional, List
from sqlalchemy.orm import Query
from app.extensions import db
from app.tenancy.core.tenant_context import TenantContext

T = TypeVar('T')


class TenantQueryHelper:
    """Helper for tenant-aware queries"""
    
    @staticmethod
    def query(model: Type[T]) -> Query:
        """
        Get a tenant-filtered query for a model
        
        Usage:
            users = TenantQueryHelper.query(User).filter(User.is_active == True).all()
        """
        query = db.session.query(model)
        
        if hasattr(model, 'tenant_id'):
            tenant = TenantContext.get_current_tenant()
            if tenant:
                query = query.filter(model.tenant_id == tenant.id)
        
        return query
    
    @staticmethod
    def get_by_id(model: Type[T], id: str) -> Optional[T]:
        """Get a record by ID with tenant filtering"""
        query = TenantQueryHelper.query(model)
        return query.filter(model.id == id).first()
    
    @staticmethod
    def get_all(model: Type[T], **filters) -> List[T]:
        """Get all records with tenant filtering and additional filters"""
        query = TenantQueryHelper.query(model)
        
        for key, value in filters.items():
            if hasattr(model, key):
                query = query.filter(getattr(model, key) == value)
        
        return query.all()
    
    @staticmethod
    def count(model: Type[T], **filters) -> int:
        """Count records with tenant filtering"""
        query = TenantQueryHelper.query(model)
        
        for key, value in filters.items():
            if hasattr(model, key):
                query = query.filter(getattr(model, key) == value)
        
        return query.count()
    
    @staticmethod
    def exists(model: Type[T], **filters) -> bool:
        """Check if record exists with tenant filtering"""
        return TenantQueryHelper.count(model, **filters) > 0
    
    @staticmethod
    def create(model: Type[T], **data) -> T:
        """Create a record with automatic tenant_id"""
        instance = model(**data)
        
        # Tenant ID will be set by the before_insert event
        
        db.session.add(instance)
        db.session.commit()
        
        return instance
    
    @staticmethod
    def update(model: Type[T], id: str, **data) -> Optional[T]:
        """Update a record with tenant filtering"""
        instance = TenantQueryHelper.get_by_id(model, id)
        
        if not instance:
            return None
        
        for key, value in data.items():
            if hasattr(instance, key) and key != 'id' and key != 'tenant_id':
                setattr(instance, key, value)
        
        db.session.commit()
        
        return instance
    
    @staticmethod
    def delete(model: Type[T], id: str) -> bool:
        """Delete a record with tenant filtering"""
        instance = TenantQueryHelper.get_by_id(model, id)
        
        if not instance:
            return False
        
        db.session.delete(instance)
        db.session.commit()
        
        return True


# Convenience function
def tenant_query(model: Type[T]) -> Query:
    """Shortcut for TenantQueryHelper.query"""
    return TenantQueryHelper.query(model)
```

---

## TASK 4: SHARED DATABASE ISOLATION

### 4.1 Shared Database Strategy

**File:** `backend/app/tenancy/isolation/shared_database.py`

```python
"""
Shared Database Isolation
Row-level tenant isolation using tenant_id column
"""

from typing import Type, TypeVar, List, Optional
from sqlalchemy import event
from sqlalchemy.orm import Session
from app.extensions import db
from app.tenancy.core.tenant_context import TenantContext, TenantContextError
from app.tenancy.core.tenant_aware_model import TenantAwareMixin
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class SharedDatabaseIsolation:
    """
    Shared database isolation strategy
    All tenants share the same database, isolated by tenant_id column
    """
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self._setup_listeners()
    
    def _setup_listeners(self):
        """Set up SQLAlchemy event listeners"""
        
        # Before insert: set tenant_id
        @event.listens_for(Session, 'before_flush')
        def before_flush(session, flush_context, instances):
            """Set tenant_id on new objects"""
            for obj in session.new:
                self._set_tenant_id(obj)
            
            # Validate tenant_id on dirty objects
            for obj in session.dirty:
                self._validate_tenant_id(obj)
        
        # Query filter: automatic tenant filtering
        @event.listens_for(Session, 'do_orm_execute')
        def receive_do_orm_execute(orm_execute_state):
            """Add tenant filter to queries"""
            if not orm_execute_state.is_select:
                return
            
            # Skip if explicitly disabled
            if orm_execute_state.execution_options.get('skip_tenant_filter'):
                return
            
            # Get mapper
            if orm_execute_state.bind_mapper is None:
                return
            
            model = orm_execute_state.bind_mapper.entity
            
            # Check if model is tenant-aware
            if not self._is_tenant_aware(model):
                return
            
            # Get current tenant
            tenant = TenantContext.get_current_tenant()
            if not tenant:
                logger.warning(f"Query on {model.__name__} without tenant context")
                return
            
            # Add filter
            orm_execute_state.statement = orm_execute_state.statement.where(
                model.tenant_id == tenant.id
            )
    
    def _is_tenant_aware(self, model: Type) -> bool:
        """Check if model is tenant-aware"""
        return hasattr(model, 'tenant_id') and hasattr(model, '__tablename__')
    
    def _set_tenant_id(self, obj):
        """Set tenant_id on object if applicable"""
        if not self._is_tenant_aware(type(obj)):
            return
        
        if obj.tenant_id is not None:
            return
        
        tenant = TenantContext.get_current_tenant()
        if tenant:
            obj.tenant_id = tenant.id
            logger.debug(f"Set tenant_id on {type(obj).__name__}: {tenant.id}")
        else:
            raise TenantContextError(
                f"Cannot create {type(obj).__name__} without tenant context"
            )
    
    def _validate_tenant_id(self, obj):
        """Validate that tenant_id hasn't changed"""
        if not self._is_tenant_aware(type(obj)):
            return
        
        # Check if tenant_id was modified
        from sqlalchemy import inspect
        history = inspect(obj).attrs.tenant_id.history
        
        if history.has_changes() and history.deleted:
            raise ValueError(
                f"Cannot change tenant_id on {type(obj).__name__}"
            )


class CrossTenantQuery:
    """
    Helper for cross-tenant queries (admin operations)
    Use with caution - bypasses tenant isolation
    """
    
    def __init__(self, model: Type[T]):
        self.model = model
    
    def __enter__(self):
        """Enter cross-tenant context"""
        return self._get_unfiltered_query()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit cross-tenant context"""
        pass
    
    def _get_unfiltered_query(self):
        """Get query without tenant filter"""
        return db.session.query(self.model).execution_options(
            skip_tenant_filter=True
        )


def cross_tenant_query(model: Type[T]):
    """
    Get a query that bypasses tenant filtering
    
    Usage:
        query = cross_tenant_query(User)
        all_users = query.all()
    """
    return db.session.query(model).execution_options(
        skip_tenant_filter=True
    )


def with_tenant(tenant_id: str, model: Type[T]):
    """
    Get a query for a specific tenant
    
    Usage:
        query = with_tenant('tenant-123', User)
        users = query.filter(User.is_active == True).all()
    """
    return db.session.query(model).filter(
        model.tenant_id == tenant_id
    ).execution_options(skip_tenant_filter=True)
```

---

## Continue to Part 2 for Services, API Routes & Frontend

---

*Phase 16 Tasks Part 1 - LogiAccounting Pro*
*Core Multi-Tenancy System*
