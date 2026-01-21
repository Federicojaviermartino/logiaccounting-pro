# LogiAccounting Pro - Phase 16: Multi-Tenancy Architecture

## Enterprise Multi-Tenant System with Complete Data Isolation

---

## 📋 EXECUTIVE SUMMARY

Phase 16 implements a robust multi-tenancy architecture that enables LogiAccounting Pro to serve multiple organizations from a single deployment while ensuring complete data isolation, customizable configurations, and scalable resource management. This architecture supports SaaS deployment models with tenant-specific customizations.

### Business Value

| Benefit | Impact |
|---------|--------|
| **Cost Efficiency** | Single deployment serves multiple customers |
| **Scalability** | Add tenants without infrastructure changes |
| **Data Isolation** | Complete separation between organizations |
| **Customization** | Per-tenant configurations and branding |
| **Compliance** | Meet data residency requirements |
| **Resource Management** | Fair usage and billing per tenant |

### Multi-Tenancy Models Supported

| Model | Description | Use Case |
|-------|-------------|----------|
| **Shared Database** | Single DB with tenant_id column | Small-Medium tenants |
| **Shared Schema** | Separate schemas per tenant | Medium tenants |
| **Dedicated Database** | Separate DB per tenant | Enterprise/Compliance |
| **Hybrid** | Mix based on tenant tier | Multi-tier SaaS |

---

## 🏗️ ARCHITECTURE OVERVIEW

### Multi-Tenancy Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      MULTI-TENANCY ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────────┘

                           REQUEST FLOW
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│     ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐           │
│     │Tenant A │    │Tenant B │    │Tenant C │    │Tenant D │           │
│     │ Users   │    │ Users   │    │ Users   │    │ Users   │           │
│     └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘           │
│          │              │              │              │                  │
│          └──────────────┴──────────────┴──────────────┘                  │
│                                │                                         │
│                                ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                     LOAD BALANCER / CDN                          │    │
│  │              (Custom domains per tenant)                         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                │                                         │
│                                ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    TENANT RESOLUTION LAYER                       │    │
│  │  • Domain-based:    acme.logiaccounting.com → tenant_acme       │    │
│  │  • Subdomain-based: acme.app.logiaccounting.com → tenant_acme   │    │
│  │  • Header-based:    X-Tenant-ID: tenant_acme                     │    │
│  │  • JWT-based:       token.organization_id → tenant_acme          │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                │                                         │
└────────────────────────────────┼─────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    TENANT CONTEXT MIDDLEWARE                      │   │
│  │  • Set current tenant in request context                         │   │
│  │  • Apply tenant-specific configuration                           │   │
│  │  • Enforce tenant boundaries                                     │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                │                                         │
│                                ▼                                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │  Tenant    │  │  Feature   │  │   Rate     │  │  Resource  │        │
│  │  Config    │  │  Flags     │  │  Limiter   │  │  Quotas    │        │
│  │  Service   │  │  Service   │  │  Service   │  │  Service   │        │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    TENANT-AWARE ORM LAYER                         │   │
│  │  • Automatic tenant_id filtering on all queries                  │   │
│  │  • Prevent cross-tenant data access                              │   │
│  │  • Automatic tenant_id injection on inserts                      │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│                    DATA ISOLATION STRATEGIES                             │
│                                                                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │ SHARED DB      │  │ SCHEMA PER     │  │ DATABASE PER   │            │
│  │                │  │ TENANT         │  │ TENANT         │            │
│  │ ┌────────────┐ │  │ ┌────────────┐ │  │ ┌────────────┐ │            │
│  │ │ tenant_id  │ │  │ │ schema_a   │ │  │ │  db_acme   │ │            │
│  │ │ column     │ │  │ │ schema_b   │ │  │ │  db_corp   │ │            │
│  │ │ filtering  │ │  │ │ schema_c   │ │  │ │  db_mega   │ │            │
│  │ └────────────┘ │  │ └────────────┘ │  │ └────────────┘ │            │
│  │                │  │                │  │                │            │
│  │ Standard/Pro   │  │ Business       │  │ Enterprise     │            │
│  └────────────────┘  └────────────────┘  └────────────────┘            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Tenant Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        TENANT LIFECYCLE                                  │
└─────────────────────────────────────────────────────────────────────────┘

  1. PROVISIONING              2. CONFIGURATION           3. OPERATION
  ══════════════               ═══════════════            ═══════════

  ┌──────────────┐             ┌──────────────┐          ┌──────────────┐
  │  Tenant      │             │   Apply      │          │   Active     │
  │  Signup      │────────────▶│   Settings   │─────────▶│   Usage      │
  │              │             │   & Branding │          │              │
  └──────────────┘             └──────────────┘          └──────────────┘
         │                            │                         │
         ▼                            ▼                         ▼
  ┌──────────────┐             ┌──────────────┐          ┌──────────────┐
  │  Create      │             │   Setup      │          │   Monitor    │
  │  Database    │             │   Feature    │          │   Usage &    │
  │  Resources   │             │   Flags      │          │   Quotas     │
  └──────────────┘             └──────────────┘          └──────────────┘
         │                            │                         │
         ▼                            ▼                         ▼
  ┌──────────────┐             ┌──────────────┐          ┌──────────────┐
  │  Initialize  │             │   Configure  │          │   Billing    │
  │  Seed Data   │             │   Integra-   │          │   & Usage    │
  │              │             │   tions      │          │   Reports    │
  └──────────────┘             └──────────────┘          └──────────────┘


  4. SCALING                   5. MIGRATION               6. OFFBOARDING
  ══════════                   ═══════════                ═════════════

  ┌──────────────┐             ┌──────────────┐          ┌──────────────┐
  │  Upgrade     │             │   Export     │          │   Suspend    │
  │  Tier        │             │   Data       │          │   Account    │
  │              │             │              │          │              │
  └──────────────┘             └──────────────┘          └──────────────┘
         │                            │                         │
         ▼                            ▼                         ▼
  ┌──────────────┐             ┌──────────────┐          ┌──────────────┐
  │  Increase    │             │   Data       │          │   Data       │
  │  Resources   │             │   Portabi-   │          │   Retention  │
  │  & Limits    │             │   lity       │          │   Period     │
  └──────────────┘             └──────────────┘          └──────────────┘
         │                            │                         │
         ▼                            ▼                         ▼
  ┌──────────────┐             ┌──────────────┐          ┌──────────────┐
  │  Dedicated   │             │   Move to    │          │   Purge      │
  │  Resources   │             │   New        │          │   Data       │
  │  (Optional)  │             │   Region     │          │              │
  └──────────────┘             └──────────────┘          └──────────────┘
```

---

## 📁 PROJECT STRUCTURE

```
backend/app/
├── tenancy/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── tenant.py               # Core tenant model
│   │   ├── tenant_settings.py      # Tenant configuration
│   │   ├── tenant_domain.py        # Custom domains
│   │   ├── tenant_subscription.py  # Subscription/billing
│   │   ├── tenant_quota.py         # Resource quotas
│   │   ├── tenant_feature.py       # Feature flags
│   │   └── tenant_invitation.py    # User invitations
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── tenant_context.py       # Thread-local tenant context
│   │   ├── tenant_resolver.py      # Resolve tenant from request
│   │   ├── tenant_middleware.py    # Flask middleware
│   │   ├── tenant_aware_model.py   # Base model with tenant_id
│   │   └── query_filter.py         # Automatic query filtering
│   │
│   ├── isolation/
│   │   ├── __init__.py
│   │   ├── shared_database.py      # Shared DB strategy
│   │   ├── schema_per_tenant.py    # Schema isolation
│   │   ├── database_per_tenant.py  # Full DB isolation
│   │   └── connection_manager.py   # Dynamic connections
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── tenant_service.py       # Tenant CRUD operations
│   │   ├── provisioning_service.py # Tenant setup/teardown
│   │   ├── quota_service.py        # Quota management
│   │   ├── feature_service.py      # Feature flag management
│   │   ├── billing_service.py      # Usage & billing
│   │   └── migration_service.py    # Tenant data migration
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── tenants.py              # Tenant management (admin)
│   │   ├── settings.py             # Tenant settings
│   │   ├── subscriptions.py        # Subscription management
│   │   └── invitations.py          # User invitations
│   │
│   └── tasks/
│       ├── __init__.py
│       ├── provisioning_tasks.py   # Async provisioning
│       ├── cleanup_tasks.py        # Data cleanup
│       └── usage_tasks.py          # Usage calculation

frontend/src/
├── features/
│   └── tenancy/
│       ├── components/
│       │   ├── TenantSelector.jsx
│       │   ├── TenantSettings.jsx
│       │   ├── BrandingSettings.jsx
│       │   ├── SubscriptionCard.jsx
│       │   ├── UsageMetrics.jsx
│       │   ├── QuotaDisplay.jsx
│       │   ├── InviteMember.jsx
│       │   └── DomainSettings.jsx
│       │
│       ├── pages/
│       │   ├── TenantSettingsPage.jsx
│       │   ├── SubscriptionPage.jsx
│       │   ├── UsagePage.jsx
│       │   └── TeamPage.jsx
│       │
│       ├── hooks/
│       │   ├── useTenant.js
│       │   ├── useSubscription.js
│       │   └── useUsage.js
│       │
│       └── api/
│           └── tenantApi.js
```

---

## 🔧 TECHNOLOGY STACK

### Backend Dependencies

```txt
# requirements.txt additions

# Database Connection Pooling
sqlalchemy==2.0.23               # ORM with multi-tenancy support
psycopg2-binary==2.9.9           # PostgreSQL adapter
sqlalchemy-utils==0.41.1         # Database utilities

# Connection Management
databases==0.8.0                 # Async database support

# Caching
redis==5.0.1                     # Tenant config caching
cachetools==5.3.2                # In-memory caching

# Rate Limiting
slowapi==0.1.9                   # Rate limiting
limits==3.7.0                    # Rate limit algorithms

# Background Tasks
celery==5.3.4                    # Async provisioning

# DNS/Domain
dnspython==2.4.2                 # DNS verification

# Billing (optional)
stripe==7.10.0                   # Stripe integration
```

### Frontend Dependencies

```json
{
  "dependencies": {
    "@tanstack/react-query": "^5.17.0",
    "recharts": "^2.10.0",
    "react-hook-form": "^7.49.0"
  }
}
```

---

## 📊 DATABASE SCHEMA

```sql
-- Tenants (Core)
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Identification
    slug VARCHAR(100) NOT NULL UNIQUE,  -- URL-safe identifier
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    
    -- Contact
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    
    -- Address
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(2),  -- ISO country code
    
    -- Tax Information
    tax_id VARCHAR(50),
    vat_number VARCHAR(50),
    
    -- Status
    status VARCHAR(50) DEFAULT 'active',
    -- 'pending', 'active', 'suspended', 'cancelled', 'deleted'
    
    suspended_at TIMESTAMP,
    suspended_reason TEXT,
    
    -- Isolation Strategy
    isolation_level VARCHAR(50) DEFAULT 'shared_database',
    -- 'shared_database', 'schema', 'database'
    
    database_name VARCHAR(100),  -- For dedicated DB
    schema_name VARCHAR(100),    -- For schema isolation
    
    -- Tier
    tier VARCHAR(50) DEFAULT 'standard',
    -- 'free', 'standard', 'professional', 'business', 'enterprise'
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    
    -- Owner (first admin user)
    owner_id UUID,
    
    INDEX idx_tenants_slug (slug),
    INDEX idx_tenants_status (status)
);

-- Tenant Domains
CREATE TABLE tenant_domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Domain
    domain VARCHAR(255) NOT NULL UNIQUE,
    domain_type VARCHAR(50) DEFAULT 'subdomain',
    -- 'subdomain' (acme.logiaccounting.com)
    -- 'custom' (app.acme.com)
    
    -- Verification
    is_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(100),
    verified_at TIMESTAMP,
    
    -- SSL
    ssl_enabled BOOLEAN DEFAULT TRUE,
    ssl_certificate_id VARCHAR(255),
    
    -- Status
    is_primary BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_tenant_domains_domain (domain),
    INDEX idx_tenant_domains_tenant (tenant_id)
);

-- Tenant Settings
CREATE TABLE tenant_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Branding
    logo_url TEXT,
    logo_dark_url TEXT,
    favicon_url TEXT,
    primary_color VARCHAR(7) DEFAULT '#2563eb',
    secondary_color VARCHAR(7) DEFAULT '#1e40af',
    
    -- Locale
    default_language VARCHAR(10) DEFAULT 'en',
    default_timezone VARCHAR(50) DEFAULT 'UTC',
    default_currency VARCHAR(3) DEFAULT 'USD',
    date_format VARCHAR(20) DEFAULT 'YYYY-MM-DD',
    number_format VARCHAR(20) DEFAULT '1,234.56',
    
    -- Features
    features_enabled JSONB DEFAULT '{}',
    modules_enabled TEXT[] DEFAULT '{}',
    
    -- Security
    password_policy JSONB DEFAULT '{}',
    session_timeout_minutes INTEGER DEFAULT 60,
    mfa_required BOOLEAN DEFAULT FALSE,
    ip_whitelist TEXT[],
    
    -- Email
    email_from_name VARCHAR(255),
    email_from_address VARCHAR(255),
    email_reply_to VARCHAR(255),
    
    -- Notifications
    notification_settings JSONB DEFAULT '{}',
    
    -- Custom
    custom_settings JSONB DEFAULT '{}',
    
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(tenant_id)
);

-- Tenant Subscriptions
CREATE TABLE tenant_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Plan
    plan_id VARCHAR(100) NOT NULL,
    plan_name VARCHAR(255) NOT NULL,
    
    -- Billing
    billing_cycle VARCHAR(20) DEFAULT 'monthly',
    -- 'monthly', 'quarterly', 'annual'
    
    price_amount DECIMAL(10, 2) NOT NULL,
    price_currency VARCHAR(3) DEFAULT 'USD',
    
    -- Status
    status VARCHAR(50) DEFAULT 'active',
    -- 'trial', 'active', 'past_due', 'cancelled', 'expired'
    
    -- Dates
    trial_ends_at TIMESTAMP,
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    cancelled_at TIMESTAMP,
    
    -- Payment
    payment_method_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    
    -- Auto-renewal
    auto_renew BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_subscriptions_tenant (tenant_id),
    INDEX idx_subscriptions_status (status)
);

-- Tenant Quotas
CREATE TABLE tenant_quotas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Resource Limits
    max_users INTEGER DEFAULT 5,
    max_storage_mb INTEGER DEFAULT 1024,  -- 1GB
    max_api_calls_per_month INTEGER DEFAULT 10000,
    max_invoices_per_month INTEGER DEFAULT 100,
    max_products INTEGER DEFAULT 500,
    max_projects INTEGER DEFAULT 50,
    max_integrations INTEGER DEFAULT 3,
    
    -- Current Usage
    current_users INTEGER DEFAULT 0,
    current_storage_mb DECIMAL(10, 2) DEFAULT 0,
    current_api_calls INTEGER DEFAULT 0,
    current_invoices INTEGER DEFAULT 0,
    current_products INTEGER DEFAULT 0,
    current_projects INTEGER DEFAULT 0,
    current_integrations INTEGER DEFAULT 0,
    
    -- Usage Reset
    usage_reset_day INTEGER DEFAULT 1,  -- Day of month
    last_reset_at TIMESTAMP,
    
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(tenant_id)
);

-- Tenant Feature Flags
CREATE TABLE tenant_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    feature_key VARCHAR(100) NOT NULL,
    is_enabled BOOLEAN DEFAULT FALSE,
    
    -- Override settings
    config JSONB DEFAULT '{}',
    
    -- Validity
    enabled_at TIMESTAMP,
    expires_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(tenant_id, feature_key),
    INDEX idx_features_tenant (tenant_id)
);

-- Tenant Invitations
CREATE TABLE tenant_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Invitation
    email VARCHAR(255) NOT NULL,
    role VARCHAR(100) NOT NULL,
    
    -- Token
    token VARCHAR(255) NOT NULL UNIQUE,
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending',
    -- 'pending', 'accepted', 'expired', 'cancelled'
    
    -- Dates
    expires_at TIMESTAMP NOT NULL,
    accepted_at TIMESTAMP,
    
    -- Inviter
    invited_by UUID NOT NULL REFERENCES users(id),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_invitations_tenant (tenant_id),
    INDEX idx_invitations_token (token),
    INDEX idx_invitations_email (email)
);

-- Tenant Usage Logs (for billing)
CREATE TABLE tenant_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Metrics
    metric_type VARCHAR(100) NOT NULL,
    -- 'api_calls', 'storage', 'users', 'invoices', 'exports', etc.
    
    metric_value DECIMAL(15, 2) NOT NULL,
    metric_unit VARCHAR(50),  -- 'count', 'mb', 'gb', 'hours'
    
    -- Aggregation
    aggregation_type VARCHAR(20) DEFAULT 'sum',
    -- 'sum', 'max', 'avg', 'count'
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_usage_tenant_period (tenant_id, period_start, period_end),
    INDEX idx_usage_metric (metric_type)
);

-- Subscription Plans (Global)
CREATE TABLE subscription_plans (
    id VARCHAR(100) PRIMARY KEY,
    
    -- Plan Info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Pricing
    price_monthly DECIMAL(10, 2),
    price_annual DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Features
    tier VARCHAR(50) NOT NULL,
    -- 'free', 'standard', 'professional', 'business', 'enterprise'
    
    -- Limits
    max_users INTEGER,
    max_storage_mb INTEGER,
    max_api_calls INTEGER,
    max_invoices INTEGER,
    max_products INTEGER,
    max_projects INTEGER,
    max_integrations INTEGER,
    
    -- Features included
    features JSONB DEFAULT '{}',
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_public BOOLEAN DEFAULT TRUE,  -- Visible in pricing page
    
    -- Order
    display_order INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed default plans
INSERT INTO subscription_plans (id, name, tier, price_monthly, price_annual, max_users, max_storage_mb, max_api_calls, max_invoices, max_products, max_projects, max_integrations, features) VALUES
('free', 'Free', 'free', 0, 0, 2, 100, 1000, 10, 50, 5, 1, '{"basic_invoicing": true}'),
('standard', 'Standard', 'standard', 29, 290, 5, 1024, 10000, 100, 500, 50, 3, '{"basic_invoicing": true, "inventory": true, "reports": true}'),
('professional', 'Professional', 'professional', 79, 790, 15, 5120, 50000, 500, 2000, 200, 10, '{"basic_invoicing": true, "inventory": true, "reports": true, "projects": true, "api_access": true}'),
('business', 'Business', 'business', 199, 1990, 50, 20480, 200000, 2000, 10000, 1000, 25, '{"basic_invoicing": true, "inventory": true, "reports": true, "projects": true, "api_access": true, "audit": true, "sso": true}'),
('enterprise', 'Enterprise', 'enterprise', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '{"all": true}');
```

---

## 🎯 FEATURE SPECIFICATIONS

### 16.1 Tenant Resolution

| Method | Example | Priority |
|--------|---------|----------|
| **Custom Domain** | `app.acme.com` → tenant_acme | 1 |
| **Subdomain** | `acme.logiaccounting.com` → tenant_acme | 2 |
| **Header** | `X-Tenant-ID: tenant_acme` | 3 |
| **JWT Claim** | `token.tenant_id` | 4 |

### 16.2 Data Isolation Levels

| Level | Description | Best For |
|-------|-------------|----------|
| **Shared DB** | Row-level isolation via tenant_id | Standard/Pro tiers |
| **Schema** | Separate PostgreSQL schema | Business tier |
| **Database** | Dedicated database | Enterprise tier |

### 16.3 Resource Quotas

| Resource | Free | Standard | Professional | Business | Enterprise |
|----------|------|----------|--------------|----------|------------|
| Users | 2 | 5 | 15 | 50 | Unlimited |
| Storage | 100MB | 1GB | 5GB | 20GB | Unlimited |
| API Calls/mo | 1K | 10K | 50K | 200K | Unlimited |
| Invoices/mo | 10 | 100 | 500 | 2000 | Unlimited |
| Integrations | 1 | 3 | 10 | 25 | Unlimited |

### 16.4 Feature Flags

| Feature | Free | Standard | Pro | Business | Enterprise |
|---------|------|----------|-----|----------|------------|
| Basic Invoicing | ✅ | ✅ | ✅ | ✅ | ✅ |
| Inventory | ❌ | ✅ | ✅ | ✅ | ✅ |
| Reports | ❌ | ✅ | ✅ | ✅ | ✅ |
| Projects | ❌ | ❌ | ✅ | ✅ | ✅ |
| API Access | ❌ | ❌ | ✅ | ✅ | ✅ |
| Audit Trail | ❌ | ❌ | ❌ | ✅ | ✅ |
| SSO/SAML | ❌ | ❌ | ❌ | ✅ | ✅ |
| Custom Domain | ❌ | ❌ | ❌ | ✅ | ✅ |
| Dedicated DB | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## 🔗 API ENDPOINTS

### Tenant Management (Platform Admin)

```
GET    /api/v1/admin/tenants                   # List all tenants
POST   /api/v1/admin/tenants                   # Create tenant
GET    /api/v1/admin/tenants/:id               # Get tenant
PUT    /api/v1/admin/tenants/:id               # Update tenant
DELETE /api/v1/admin/tenants/:id               # Delete tenant
POST   /api/v1/admin/tenants/:id/suspend       # Suspend tenant
POST   /api/v1/admin/tenants/:id/activate      # Activate tenant
```

### Tenant Settings (Tenant Admin)

```
GET    /api/v1/tenant/settings                 # Get settings
PUT    /api/v1/tenant/settings                 # Update settings
PUT    /api/v1/tenant/settings/branding        # Update branding
PUT    /api/v1/tenant/settings/security        # Update security
PUT    /api/v1/tenant/settings/notifications   # Update notifications
```

### Domains

```
GET    /api/v1/tenant/domains                  # List domains
POST   /api/v1/tenant/domains                  # Add domain
DELETE /api/v1/tenant/domains/:id              # Remove domain
POST   /api/v1/tenant/domains/:id/verify       # Verify domain
POST   /api/v1/tenant/domains/:id/set-primary  # Set as primary
```

### Subscription

```
GET    /api/v1/tenant/subscription             # Get subscription
PUT    /api/v1/tenant/subscription             # Update subscription
POST   /api/v1/tenant/subscription/upgrade     # Upgrade plan
POST   /api/v1/tenant/subscription/downgrade   # Downgrade plan
POST   /api/v1/tenant/subscription/cancel      # Cancel subscription
GET    /api/v1/tenant/subscription/invoices    # Billing history
```

### Quotas & Usage

```
GET    /api/v1/tenant/quotas                   # Get quotas
GET    /api/v1/tenant/usage                    # Get current usage
GET    /api/v1/tenant/usage/history            # Usage history
```

### Features

```
GET    /api/v1/tenant/features                 # Get enabled features
GET    /api/v1/tenant/features/:key            # Check specific feature
```

### Team/Invitations

```
GET    /api/v1/tenant/team                     # List team members
POST   /api/v1/tenant/invitations              # Send invitation
GET    /api/v1/tenant/invitations              # List invitations
DELETE /api/v1/tenant/invitations/:id          # Cancel invitation
POST   /api/v1/invitations/:token/accept       # Accept invitation (public)
```

### Plans (Public)

```
GET    /api/v1/plans                           # List available plans
GET    /api/v1/plans/:id                       # Get plan details
```

---

## ⏱️ IMPLEMENTATION TIMELINE

| Week | Tasks | Hours |
|------|-------|-------|
| **Week 1** | Database schema, Tenant models | 12h |
| **Week 2** | Tenant context, Middleware, Resolver | 12h |
| **Week 3** | Tenant-aware base model, Query filtering | 10h |
| **Week 4** | Shared database isolation strategy | 10h |
| **Week 5** | Schema per tenant strategy | 12h |
| **Week 6** | Provisioning service, Tenant setup | 10h |
| **Week 7** | Quota service, Usage tracking | 10h |
| **Week 8** | Feature flags service | 8h |
| **Week 9** | Subscription & billing integration | 12h |
| **Week 10** | Domain management, SSL | 10h |
| **Week 11** | Frontend: Settings, Subscription | 12h |
| **Week 12** | Frontend: Usage, Team, Testing | 12h |

**Total: ~130 hours (12 weeks)**

---

## ✅ FEATURE CHECKLIST

| # | Feature | Priority | Status |
|---|---------|----------|--------|
| 16.1 | Database schema & models | P0 | 🔲 |
| 16.2 | Tenant context (thread-local) | P0 | 🔲 |
| 16.3 | Tenant resolver | P0 | 🔲 |
| 16.4 | Tenant middleware | P0 | 🔲 |
| 16.5 | Tenant-aware base model | P0 | 🔲 |
| 16.6 | Automatic query filtering | P0 | 🔲 |
| 16.7 | Shared database strategy | P0 | 🔲 |
| 16.8 | Schema per tenant strategy | P1 | 🔲 |
| 16.9 | Provisioning service | P0 | 🔲 |
| 16.10 | Quota service | P0 | 🔲 |
| 16.11 | Feature flags service | P0 | 🔲 |
| 16.12 | Subscription service | P1 | 🔲 |
| 16.13 | Billing integration (Stripe) | P1 | 🔲 |
| 16.14 | Domain management | P1 | 🔲 |
| 16.15 | Team invitations | P0 | 🔲 |
| 16.16 | Usage tracking | P1 | 🔲 |
| 16.17 | Frontend: Tenant settings | P0 | 🔲 |
| 16.18 | Frontend: Subscription | P1 | 🔲 |
| 16.19 | Frontend: Usage dashboard | P1 | 🔲 |
| 16.20 | Frontend: Team management | P0 | 🔲 |
| 16.21 | Tenant admin panel | P2 | 🔲 |
| 16.22 | Data export/migration | P2 | 🔲 |

---

*Phase 16 Plan - LogiAccounting Pro*
*Multi-Tenancy Architecture*
