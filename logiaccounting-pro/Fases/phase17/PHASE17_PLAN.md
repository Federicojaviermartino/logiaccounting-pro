# LogiAccounting Pro - Phase 17: API Gateway & Webhooks

## Enterprise API Platform with Developer Tools

---

## 📋 EXECUTIVE SUMMARY

Phase 17 implements a comprehensive API Gateway and Webhooks system that transforms LogiAccounting Pro into a developer-friendly platform. This includes API key management, rate limiting, request/response logging, webhook subscriptions for real-time event notifications, and complete OpenAPI documentation.

### Business Value

| Benefit | Impact |
|---------|--------|
| **Integration Ecosystem** | Enable third-party integrations |
| **Developer Experience** | Complete API documentation & SDKs |
| **Real-time Events** | Webhook notifications for automation |
| **Security** | API keys, rate limiting, IP filtering |
| **Monetization** | Usage-based API billing |
| **Compliance** | Complete audit trail of API access |

### Key Capabilities

| Feature | Description |
|---------|-------------|
| **API Keys** | Multiple keys per tenant with scopes |
| **Rate Limiting** | Tiered limits with burst allowance |
| **Webhooks** | Subscribe to 50+ event types |
| **API Versioning** | Support multiple API versions |
| **Request Logging** | Complete request/response audit |
| **Developer Portal** | Interactive API documentation |

---

## 🏗️ ARCHITECTURE OVERVIEW

### API Gateway Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        API GATEWAY ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────────┘

                           EXTERNAL CLIENTS
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │  Mobile App  │  │  Web Client  │  │  Third-Party │                  │
│  │              │  │              │  │  Integration │                  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │
│         │                 │                 │                           │
│         └─────────────────┴─────────────────┘                           │
│                           │                                              │
│                    API Request                                           │
│                    + API Key                                             │
│                           │                                              │
└───────────────────────────┼──────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY LAYER                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    REQUEST PIPELINE                              │   │
│  │                                                                   │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────┐│   │
│  │  │  SSL    │─▶│  Auth   │─▶│  Rate   │─▶│  IP     │─▶│ Request││   │
│  │  │ Termina │  │ (API    │  │  Limit  │  │  Filter │  │ Logging││   │
│  │  │  tion   │  │  Key)   │  │         │  │         │  │        ││   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └────────┘│   │
│  │                                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                            │                                             │
│                            ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    ROUTING & VERSIONING                          │   │
│  │                                                                   │   │
│  │  /api/v1/*  ──────────────────────────────▶  API v1 Handler     │   │
│  │  /api/v2/*  ──────────────────────────────▶  API v2 Handler     │   │
│  │                                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└───────────────────────────┼──────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       APPLICATION LAYER                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │  Invoices   │  │  Inventory  │  │  Projects   │  │  Payments   │   │
│  │    API      │  │    API      │  │    API      │  │    API      │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │
│         │                │                │                │            │
│         └────────────────┴────────────────┴────────────────┘            │
│                                   │                                      │
│                            ┌──────▼──────┐                              │
│                            │   EVENT     │                              │
│                            │   EMITTER   │                              │
│                            └──────┬──────┘                              │
│                                   │                                      │
└───────────────────────────────────┼──────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       WEBHOOK DELIVERY SYSTEM                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    EVENT PROCESSOR                               │   │
│  │                                                                   │   │
│  │  Event ──▶ Match Subscriptions ──▶ Build Payload ──▶ Queue      │   │
│  │                                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                            │                                             │
│                            ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    DELIVERY QUEUE (Redis)                        │   │
│  │                                                                   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │   │
│  │  │ Pending │  │ Retry   │  │ Retry   │  │  Dead   │            │   │
│  │  │  Queue  │  │ Queue 1 │  │ Queue 2 │  │ Letter  │            │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘            │   │
│  │                                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                            │                                             │
│                            ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    DELIVERY WORKERS                              │   │
│  │                                                                   │   │
│  │  Worker 1 ─┬─▶ HTTP POST ─▶ Customer Endpoint                   │   │
│  │  Worker 2 ─┤                                                     │   │
│  │  Worker 3 ─┤  ┌──────────────────────────────┐                  │   │
│  │  Worker N ─┘  │ Retry Policy:                │                  │   │
│  │               │ • Attempt 1: Immediate       │                  │   │
│  │               │ • Attempt 2: 1 min           │                  │   │
│  │               │ • Attempt 3: 5 min           │                  │   │
│  │               │ • Attempt 4: 30 min          │                  │   │
│  │               │ • Attempt 5: 2 hours         │                  │   │
│  │               └──────────────────────────────┘                  │   │
│  │                                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Webhook Event Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        WEBHOOK EVENT FLOW                                │
└─────────────────────────────────────────────────────────────────────────┘

  1. EVENT TRIGGER              2. SUBSCRIPTION MATCH         3. PAYLOAD BUILD
  ═══════════════               ══════════════════           ═══════════════

  ┌──────────────┐             ┌──────────────┐            ┌──────────────┐
  │   Invoice    │             │    Find      │            │   Serialize  │
  │   Created    │────────────▶│  Matching    │───────────▶│    Event     │
  │              │             │ Subscribers  │            │    Data      │
  └──────────────┘             └──────────────┘            └──────────────┘
                                     │
                                     ▼
                              ┌──────────────┐
                              │ Tenant A: ✓  │
                              │ Tenant B: ✗  │
                              │ Tenant C: ✓  │
                              └──────────────┘


  4. SIGNATURE                  5. QUEUE                     6. DELIVERY
  ═══════════                   ═════                        ═════════

  ┌──────────────┐             ┌──────────────┐            ┌──────────────┐
  │  Generate    │             │   Add to     │            │   HTTP       │
  │   HMAC       │────────────▶│   Redis      │───────────▶│    POST      │
  │  Signature   │             │   Queue      │            │              │
  └──────────────┘             └──────────────┘            └──────────────┘
        │                                                         │
        ▼                                                         ▼
  X-Webhook-Signature:                               ┌──────────────────┐
  sha256=abc123...                                   │ Success (2xx)    │
                                                     │ └─▶ Log success  │
                                                     │                  │
                                                     │ Failure (4xx/5xx)│
                                                     │ └─▶ Retry queue  │
                                                     └──────────────────┘
```

---

## 📁 PROJECT STRUCTURE

```
backend/app/
├── gateway/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── api_key.py              # API key model
│   │   ├── api_request_log.py      # Request logging
│   │   ├── rate_limit.py           # Rate limit config
│   │   └── ip_whitelist.py         # IP restrictions
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── api_key_auth.py         # API key authentication
│   │   ├── rate_limiter.py         # Rate limiting middleware
│   │   ├── request_logger.py       # Request/response logging
│   │   ├── ip_filter.py            # IP whitelist/blacklist
│   │   └── api_versioning.py       # Version routing
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── api_key_service.py      # API key management
│   │   ├── rate_limit_service.py   # Rate limit management
│   │   └── usage_service.py        # API usage tracking
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── api_keys.py             # API key endpoints
│   │   └── usage.py                # Usage statistics
│   │
│   └── middleware/
│       ├── __init__.py
│       └── gateway_middleware.py   # Combined middleware

├── webhooks/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── webhook_endpoint.py     # Webhook subscriptions
│   │   ├── webhook_event.py        # Event types
│   │   ├── webhook_delivery.py     # Delivery attempts
│   │   └── webhook_log.py          # Delivery logs
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── event_emitter.py        # Event emission
│   │   ├── event_types.py          # Event definitions
│   │   ├── payload_builder.py      # Build webhook payloads
│   │   ├── signature.py            # HMAC signature
│   │   └── delivery_manager.py     # Delivery orchestration
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── webhook_service.py      # Webhook CRUD
│   │   ├── subscription_service.py # Subscription management
│   │   └── delivery_service.py     # Delivery handling
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── webhooks.py             # Webhook management
│   │   └── events.py               # Event types listing
│   │
│   └── tasks/
│       ├── __init__.py
│       ├── delivery_tasks.py       # Celery delivery tasks
│       ├── retry_tasks.py          # Retry failed deliveries
│       └── cleanup_tasks.py        # Log cleanup

├── docs/
│   ├── __init__.py
│   ├── openapi/
│   │   ├── __init__.py
│   │   ├── generator.py            # OpenAPI spec generator
│   │   └── schemas.py              # Schema definitions
│   │
│   └── routes/
│       └── docs.py                 # Documentation endpoints

frontend/src/
├── features/
│   └── api/
│       ├── components/
│       │   ├── ApiKeyCard.jsx
│       │   ├── ApiKeyModal.jsx
│       │   ├── UsageChart.jsx
│       │   ├── WebhookCard.jsx
│       │   ├── WebhookModal.jsx
│       │   ├── EventSelector.jsx
│       │   ├── DeliveryLog.jsx
│       │   └── EndpointTester.jsx
│       │
│       ├── pages/
│       │   ├── ApiKeysPage.jsx
│       │   ├── WebhooksPage.jsx
│       │   ├── ApiUsagePage.jsx
│       │   └── ApiDocsPage.jsx
│       │
│       ├── hooks/
│       │   ├── useApiKeys.js
│       │   ├── useWebhooks.js
│       │   └── useApiUsage.js
│       │
│       └── api/
│           └── gatewayApi.js
```

---

## 🔧 TECHNOLOGY STACK

### Backend Dependencies

```txt
# requirements.txt additions

# Rate Limiting
flask-limiter==3.5.0             # Rate limiting
limits==3.7.0                    # Rate limit algorithms
redis==5.0.1                     # Rate limit storage

# API Documentation
flasgger==0.9.7.1                # OpenAPI/Swagger
apispec==6.3.0                   # Spec generation
marshmallow==3.20.1              # Schema serialization

# Webhooks
requests==2.31.0                 # HTTP client for delivery
tenacity==8.2.3                  # Retry logic
httpx==0.26.0                    # Async HTTP client

# Background Tasks
celery==5.3.4                    # Async delivery
celery-redbeat==2.1.1            # Scheduled tasks

# Security
cryptography==41.0.7             # HMAC signatures
python-jose==3.3.0               # JWT handling

# Monitoring
prometheus-client==0.19.0        # Metrics
```

### Frontend Dependencies

```json
{
  "dependencies": {
    "@tanstack/react-query": "^5.17.0",
    "recharts": "^2.10.0",
    "prismjs": "^1.29.0",
    "react-syntax-highlighter": "^15.5.0",
    "swagger-ui-react": "^5.11.0"
  }
}
```

---

## 📊 DATABASE SCHEMA

```sql
-- API Keys
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Key Info
    name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Key Value (hashed for storage)
    key_prefix VARCHAR(10) NOT NULL,  -- First 8 chars for display
    key_hash VARCHAR(255) NOT NULL,   -- SHA-256 hash
    
    -- Scopes/Permissions
    scopes TEXT[] NOT NULL DEFAULT '{}',
    -- ['invoices:read', 'invoices:write', 'inventory:read', 'reports:read']
    
    -- Environment
    environment VARCHAR(20) DEFAULT 'production',
    -- 'production', 'sandbox', 'development'
    
    -- Rate Limits (override tenant defaults)
    rate_limit_per_minute INTEGER,
    rate_limit_per_hour INTEGER,
    rate_limit_per_day INTEGER,
    
    -- IP Restrictions
    allowed_ips TEXT[],  -- NULL means no restrictions
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Usage
    last_used_at TIMESTAMP,
    total_requests BIGINT DEFAULT 0,
    
    -- Expiration
    expires_at TIMESTAMP,
    
    -- Metadata
    created_by UUID REFERENCES users(id),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_api_keys_tenant (tenant_id),
    INDEX idx_api_keys_prefix (key_prefix),
    INDEX idx_api_keys_active (is_active, tenant_id)
);

-- API Request Logs
CREATE TABLE api_request_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    api_key_id UUID REFERENCES api_keys(id),
    
    -- Request Info
    method VARCHAR(10) NOT NULL,
    path VARCHAR(500) NOT NULL,
    query_params JSONB,
    
    -- Headers (selected)
    user_agent TEXT,
    content_type VARCHAR(100),
    
    -- Client
    client_ip VARCHAR(45) NOT NULL,
    
    -- Response
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER NOT NULL,
    
    -- Size
    request_size INTEGER,
    response_size INTEGER,
    
    -- Error (if any)
    error_code VARCHAR(50),
    error_message TEXT,
    
    -- API Version
    api_version VARCHAR(10),
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_request_logs_tenant_time (tenant_id, created_at DESC),
    INDEX idx_request_logs_key (api_key_id, created_at DESC),
    INDEX idx_request_logs_status (status_code, created_at DESC)
) PARTITION BY RANGE (created_at);

-- Create partitions (monthly)
CREATE TABLE api_request_logs_2024_01 PARTITION OF api_request_logs
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Rate Limit Configuration
CREATE TABLE rate_limit_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Scope
    scope_type VARCHAR(20) NOT NULL,  -- 'global', 'tenant', 'api_key'
    scope_id UUID,  -- tenant_id or api_key_id (null for global)
    
    -- Limits
    requests_per_second INTEGER,
    requests_per_minute INTEGER,
    requests_per_hour INTEGER,
    requests_per_day INTEGER,
    
    -- Burst
    burst_size INTEGER DEFAULT 10,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(scope_type, scope_id)
);

-- Webhook Endpoints
CREATE TABLE webhook_endpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Endpoint Info
    name VARCHAR(100) NOT NULL,
    description TEXT,
    url VARCHAR(2048) NOT NULL,
    
    -- Authentication
    secret VARCHAR(255) NOT NULL,  -- For HMAC signature
    
    -- Events (subscribed event types)
    events TEXT[] NOT NULL,
    -- ['invoice.created', 'invoice.paid', 'payment.received', '*']
    
    -- Headers (custom headers to include)
    custom_headers JSONB DEFAULT '{}',
    
    -- Settings
    content_type VARCHAR(50) DEFAULT 'application/json',
    timeout_seconds INTEGER DEFAULT 30,
    
    -- Retry Policy
    max_retries INTEGER DEFAULT 5,
    retry_delay_seconds INTEGER DEFAULT 60,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Health
    last_success_at TIMESTAMP,
    last_failure_at TIMESTAMP,
    consecutive_failures INTEGER DEFAULT 0,
    
    -- Auto-disable after N failures
    failure_threshold INTEGER DEFAULT 10,
    disabled_at TIMESTAMP,
    disabled_reason TEXT,
    
    -- Metadata
    created_by UUID REFERENCES users(id),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_webhooks_tenant (tenant_id),
    INDEX idx_webhooks_active (is_active, tenant_id)
);

-- Webhook Event Types (System defined)
CREATE TABLE webhook_event_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Event Info
    event_type VARCHAR(100) NOT NULL UNIQUE,
    -- 'invoice.created', 'invoice.updated', 'payment.received'
    
    category VARCHAR(50) NOT NULL,
    -- 'invoices', 'payments', 'inventory', 'projects', 'users'
    
    name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Payload Schema (JSON Schema)
    payload_schema JSONB NOT NULL,
    
    -- Sample Payload
    sample_payload JSONB,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- API Version introduced
    api_version VARCHAR(10) DEFAULT 'v1',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_event_types_category (category)
);

-- Webhook Deliveries
CREATE TABLE webhook_deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    endpoint_id UUID NOT NULL REFERENCES webhook_endpoints(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL,
    
    -- Event
    event_type VARCHAR(100) NOT NULL,
    event_id UUID NOT NULL,  -- Reference to source event
    
    -- Payload
    payload JSONB NOT NULL,
    
    -- Delivery Status
    status VARCHAR(20) DEFAULT 'pending',
    -- 'pending', 'delivering', 'delivered', 'failed', 'cancelled'
    
    -- Attempts
    attempt_count INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 5,
    next_retry_at TIMESTAMP,
    
    -- Response
    response_status INTEGER,
    response_body TEXT,
    response_headers JSONB,
    response_time_ms INTEGER,
    
    -- Error
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMP,
    
    INDEX idx_deliveries_endpoint (endpoint_id, created_at DESC),
    INDEX idx_deliveries_status (status, next_retry_at),
    INDEX idx_deliveries_tenant (tenant_id, created_at DESC)
);

-- Webhook Delivery Attempts (detailed log)
CREATE TABLE webhook_delivery_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    delivery_id UUID NOT NULL REFERENCES webhook_deliveries(id) ON DELETE CASCADE,
    
    -- Attempt
    attempt_number INTEGER NOT NULL,
    
    -- Request
    request_url VARCHAR(2048) NOT NULL,
    request_headers JSONB NOT NULL,
    request_body TEXT NOT NULL,
    
    -- Response
    response_status INTEGER,
    response_headers JSONB,
    response_body TEXT,
    response_time_ms INTEGER,
    
    -- Error
    error_type VARCHAR(50),  -- 'timeout', 'connection_error', 'ssl_error'
    error_message TEXT,
    
    -- Timestamps
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    
    INDEX idx_attempts_delivery (delivery_id)
);

-- IP Whitelist/Blacklist
CREATE TABLE ip_access_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    api_key_id UUID REFERENCES api_keys(id) ON DELETE CASCADE,
    
    -- Rule
    ip_address VARCHAR(45) NOT NULL,  -- IPv4 or IPv6
    cidr_mask INTEGER,  -- For IP ranges
    
    -- Type
    rule_type VARCHAR(10) NOT NULL,  -- 'allow', 'deny'
    
    -- Scope
    scope VARCHAR(20) DEFAULT 'all',
    -- 'all', 'api_key', 'tenant'
    
    -- Metadata
    description TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    
    INDEX idx_ip_rules_tenant (tenant_id),
    INDEX idx_ip_rules_key (api_key_id)
);

-- Insert default event types
INSERT INTO webhook_event_types (event_type, category, name, description, payload_schema, sample_payload) VALUES
-- Invoices
('invoice.created', 'invoices', 'Invoice Created', 'Triggered when a new invoice is created', 
 '{"type":"object","properties":{"id":{"type":"string"},"number":{"type":"string"},"total":{"type":"number"}}}',
 '{"id":"inv_123","number":"INV-001","total":1500.00,"customer_id":"cust_456"}'),

('invoice.updated', 'invoices', 'Invoice Updated', 'Triggered when an invoice is modified', 
 '{"type":"object","properties":{"id":{"type":"string"},"changes":{"type":"object"}}}',
 '{"id":"inv_123","changes":{"status":"sent","sent_at":"2024-01-15T10:00:00Z"}}'),

('invoice.sent', 'invoices', 'Invoice Sent', 'Triggered when an invoice is sent to customer', 
 '{"type":"object","properties":{"id":{"type":"string"},"sent_to":{"type":"string"}}}',
 '{"id":"inv_123","sent_to":"customer@example.com","sent_at":"2024-01-15T10:00:00Z"}'),

('invoice.paid', 'invoices', 'Invoice Paid', 'Triggered when an invoice is marked as paid', 
 '{"type":"object","properties":{"id":{"type":"string"},"paid_amount":{"type":"number"}}}',
 '{"id":"inv_123","paid_amount":1500.00,"paid_at":"2024-01-20T14:30:00Z","payment_method":"bank_transfer"}'),

('invoice.overdue', 'invoices', 'Invoice Overdue', 'Triggered when an invoice becomes overdue', 
 '{"type":"object","properties":{"id":{"type":"string"},"days_overdue":{"type":"integer"}}}',
 '{"id":"inv_123","days_overdue":15,"amount_due":1500.00}'),

-- Payments
('payment.received', 'payments', 'Payment Received', 'Triggered when a payment is received', 
 '{"type":"object","properties":{"id":{"type":"string"},"amount":{"type":"number"}}}',
 '{"id":"pay_789","amount":1500.00,"invoice_id":"inv_123","method":"credit_card"}'),

('payment.refunded', 'payments', 'Payment Refunded', 'Triggered when a payment is refunded', 
 '{"type":"object","properties":{"id":{"type":"string"},"refund_amount":{"type":"number"}}}',
 '{"id":"pay_789","refund_amount":500.00,"reason":"partial_refund"}'),

-- Inventory
('product.created', 'inventory', 'Product Created', 'Triggered when a new product is created', 
 '{"type":"object","properties":{"id":{"type":"string"},"sku":{"type":"string"}}}',
 '{"id":"prod_101","sku":"WIDGET-001","name":"Widget Pro","price":29.99}'),

('product.updated', 'inventory', 'Product Updated', 'Triggered when a product is modified', 
 '{"type":"object","properties":{"id":{"type":"string"},"changes":{"type":"object"}}}',
 '{"id":"prod_101","changes":{"price":34.99,"stock_quantity":150}}'),

('stock.low', 'inventory', 'Low Stock Alert', 'Triggered when stock falls below threshold', 
 '{"type":"object","properties":{"product_id":{"type":"string"},"current_stock":{"type":"integer"}}}',
 '{"product_id":"prod_101","sku":"WIDGET-001","current_stock":5,"threshold":10}'),

('stock.out', 'inventory', 'Out of Stock', 'Triggered when a product is out of stock', 
 '{"type":"object","properties":{"product_id":{"type":"string"}}}',
 '{"product_id":"prod_101","sku":"WIDGET-001","last_stock_at":"2024-01-10T09:00:00Z"}'),

-- Projects
('project.created', 'projects', 'Project Created', 'Triggered when a new project is created', 
 '{"type":"object","properties":{"id":{"type":"string"},"name":{"type":"string"}}}',
 '{"id":"proj_202","name":"Website Redesign","client_id":"cust_456","budget":50000}'),

('project.status_changed', 'projects', 'Project Status Changed', 'Triggered when project status changes', 
 '{"type":"object","properties":{"id":{"type":"string"},"old_status":{"type":"string"},"new_status":{"type":"string"}}}',
 '{"id":"proj_202","old_status":"in_progress","new_status":"completed"}'),

('project.milestone_completed', 'projects', 'Milestone Completed', 'Triggered when a milestone is completed', 
 '{"type":"object","properties":{"project_id":{"type":"string"},"milestone_id":{"type":"string"}}}',
 '{"project_id":"proj_202","milestone_id":"ms_303","name":"Design Phase","completed_at":"2024-01-25T16:00:00Z"}'),

-- Customers
('customer.created', 'customers', 'Customer Created', 'Triggered when a new customer is created', 
 '{"type":"object","properties":{"id":{"type":"string"},"email":{"type":"string"}}}',
 '{"id":"cust_456","email":"john@example.com","name":"John Doe","company":"Acme Inc"}'),

('customer.updated', 'customers', 'Customer Updated', 'Triggered when customer info is modified', 
 '{"type":"object","properties":{"id":{"type":"string"},"changes":{"type":"object"}}}',
 '{"id":"cust_456","changes":{"phone":"+1234567890","address":"123 Main St"}}'),

-- Documents
('document.uploaded', 'documents', 'Document Uploaded', 'Triggered when a document is uploaded', 
 '{"type":"object","properties":{"id":{"type":"string"},"filename":{"type":"string"}}}',
 '{"id":"doc_505","filename":"contract.pdf","size_bytes":1048576,"mime_type":"application/pdf"}'),

('document.processed', 'documents', 'Document Processed', 'Triggered when OCR/processing completes', 
 '{"type":"object","properties":{"id":{"type":"string"},"extracted_data":{"type":"object"}}}',
 '{"id":"doc_505","extracted_data":{"vendor":"Supplier Co","amount":2500.00,"date":"2024-01-15"}}');
```

---

## 🎯 FEATURE SPECIFICATIONS

### 17.1 API Key Scopes

| Scope | Description | Endpoints |
|-------|-------------|-----------|
| `invoices:read` | View invoices | GET /invoices/* |
| `invoices:write` | Create/update invoices | POST/PUT/DELETE /invoices/* |
| `inventory:read` | View products/stock | GET /inventory/* |
| `inventory:write` | Manage inventory | POST/PUT/DELETE /inventory/* |
| `customers:read` | View customers | GET /customers/* |
| `customers:write` | Manage customers | POST/PUT/DELETE /customers/* |
| `projects:read` | View projects | GET /projects/* |
| `projects:write` | Manage projects | POST/PUT/DELETE /projects/* |
| `payments:read` | View payments | GET /payments/* |
| `payments:write` | Process payments | POST /payments/* |
| `reports:read` | Generate reports | GET /reports/* |
| `webhooks:manage` | Manage webhooks | /webhooks/* |
| `*` | Full access | All endpoints |

### 17.2 Rate Limits by Plan

| Plan | Per Minute | Per Hour | Per Day | Burst |
|------|------------|----------|---------|-------|
| **Free** | 30 | 500 | 5,000 | 5 |
| **Standard** | 100 | 2,000 | 20,000 | 10 |
| **Professional** | 300 | 10,000 | 100,000 | 20 |
| **Business** | 1,000 | 50,000 | 500,000 | 50 |
| **Enterprise** | Custom | Custom | Custom | Custom |

### 17.3 Webhook Event Categories

| Category | Events |
|----------|--------|
| **Invoices** | created, updated, sent, paid, overdue, voided |
| **Payments** | received, refunded, failed |
| **Inventory** | product.created, product.updated, stock.low, stock.out |
| **Projects** | created, updated, status_changed, milestone_completed |
| **Customers** | created, updated, deleted |
| **Documents** | uploaded, processed, signed |
| **Users** | invited, joined, removed |

### 17.4 Webhook Delivery

| Feature | Value |
|---------|-------|
| **Timeout** | 30 seconds |
| **Max Retries** | 5 attempts |
| **Retry Schedule** | 1m, 5m, 30m, 2h, 24h |
| **Signature** | HMAC-SHA256 |
| **Content-Type** | application/json |

---

## 🔗 API ENDPOINTS

### API Keys

```
GET    /api/v1/api-keys                        # List API keys
POST   /api/v1/api-keys                        # Create API key
GET    /api/v1/api-keys/:id                    # Get API key
PUT    /api/v1/api-keys/:id                    # Update API key
DELETE /api/v1/api-keys/:id                    # Delete API key
POST   /api/v1/api-keys/:id/regenerate         # Regenerate key
POST   /api/v1/api-keys/:id/revoke             # Revoke key
GET    /api/v1/api-keys/:id/usage              # Get key usage stats
```

### Webhooks

```
GET    /api/v1/webhooks                        # List webhooks
POST   /api/v1/webhooks                        # Create webhook
GET    /api/v1/webhooks/:id                    # Get webhook
PUT    /api/v1/webhooks/:id                    # Update webhook
DELETE /api/v1/webhooks/:id                    # Delete webhook
POST   /api/v1/webhooks/:id/test               # Send test event
GET    /api/v1/webhooks/:id/deliveries         # List deliveries
POST   /api/v1/webhooks/:id/deliveries/:did/retry  # Retry delivery

GET    /api/v1/webhook-events                  # List event types
GET    /api/v1/webhook-events/:type            # Get event details
```

### API Usage

```
GET    /api/v1/api/usage                       # Get usage summary
GET    /api/v1/api/usage/breakdown             # Get detailed breakdown
GET    /api/v1/api/usage/by-key                # Usage per API key
GET    /api/v1/api/usage/by-endpoint           # Usage per endpoint
GET    /api/v1/api/logs                        # Request logs
```

### Documentation

```
GET    /api/v1/docs                            # Interactive docs (Swagger UI)
GET    /api/v1/docs/openapi.json               # OpenAPI spec
GET    /api/v1/docs/openapi.yaml               # OpenAPI spec (YAML)
```

---

## ⏱️ IMPLEMENTATION TIMELINE

| Week | Tasks | Hours |
|------|-------|-------|
| **Week 1** | Database schema, API Key model | 10h |
| **Week 2** | API Key authentication, Rate limiter | 12h |
| **Week 3** | Request logging, IP filtering | 10h |
| **Week 4** | Webhook models, Event types | 10h |
| **Week 5** | Event emitter, Payload builder | 10h |
| **Week 6** | Webhook delivery, Retry logic | 12h |
| **Week 7** | Celery tasks, Queue management | 10h |
| **Week 8** | OpenAPI documentation generator | 10h |
| **Week 9** | Frontend: API Keys page | 10h |
| **Week 10** | Frontend: Webhooks page | 10h |
| **Week 11** | Frontend: Usage dashboard, Docs | 10h |
| **Week 12** | Testing, Performance tuning | 10h |

**Total: ~124 hours (12 weeks)**

---

## ✅ FEATURE CHECKLIST

| # | Feature | Priority | Status |
|---|---------|----------|--------|
| 17.1 | Database schema & models | P0 | 🔲 |
| 17.2 | API Key model & service | P0 | 🔲 |
| 17.3 | API Key authentication | P0 | 🔲 |
| 17.4 | Rate limiter (Redis) | P0 | 🔲 |
| 17.5 | Request/response logging | P1 | 🔲 |
| 17.6 | IP whitelist/blacklist | P1 | 🔲 |
| 17.7 | Webhook endpoint model | P0 | 🔲 |
| 17.8 | Event types definition | P0 | 🔲 |
| 17.9 | Event emitter | P0 | 🔲 |
| 17.10 | Payload builder | P0 | 🔲 |
| 17.11 | HMAC signature | P0 | 🔲 |
| 17.12 | Webhook delivery service | P0 | 🔲 |
| 17.13 | Celery delivery tasks | P0 | 🔲 |
| 17.14 | Retry logic | P0 | 🔲 |
| 17.15 | Delivery logging | P1 | 🔲 |
| 17.16 | OpenAPI generator | P1 | 🔲 |
| 17.17 | API versioning | P1 | 🔲 |
| 17.18 | Frontend: API Keys | P0 | 🔲 |
| 17.19 | Frontend: Webhooks | P0 | 🔲 |
| 17.20 | Frontend: Usage stats | P1 | 🔲 |
| 17.21 | Frontend: API Docs | P1 | 🔲 |
| 17.22 | Webhook test endpoint | P1 | 🔲 |

---

*Phase 17 Plan - LogiAccounting Pro*
*API Gateway & Webhooks*
