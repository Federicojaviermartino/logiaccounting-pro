# LogiAccounting Pro - Phase 14: External Integrations Hub

## Enterprise Integration Platform for ERP, CRM, Accounting & More

---

## 📋 EXECUTIVE SUMMARY

Phase 14 transforms LogiAccounting Pro into a connected enterprise platform by implementing a comprehensive integrations hub. This enables seamless data synchronization with ERPs, CRMs, accounting software, e-commerce platforms, banking systems, and shipping carriers.

### Business Value

| Benefit | Impact |
|---------|--------|
| **Data Unification** | Single source of truth across all systems |
| **Automation** | Eliminate manual data entry between platforms |
| **Real-time Sync** | Up-to-date information across all systems |
| **Reduced Errors** | Automated data transfer eliminates human mistakes |
| **Time Savings** | 60% reduction in manual reconciliation |
| **Scalability** | Connect any system via standardized APIs |

### Supported Integrations

| Category | Platforms |
|----------|-----------|
| **ERP Systems** | SAP Business One, Oracle NetSuite, Microsoft Dynamics 365 |
| **CRM** | Salesforce, HubSpot, Zoho CRM, Pipedrive |
| **Accounting** | QuickBooks Online, Xero, Sage, FreshBooks |
| **E-commerce** | Shopify, WooCommerce, Magento, BigCommerce |
| **Banking** | Plaid, Open Banking (PSD2), Stripe |
| **Shipping** | FedEx, UPS, DHL, USPS |
| **Payments** | Stripe, PayPal, Square |
| **Communication** | Slack, Microsoft Teams, Email (SMTP) |

---

## 🏗️ ARCHITECTURE OVERVIEW

### Integration Platform Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    EXTERNAL INTEGRATIONS HUB                             │
└─────────────────────────────────────────────────────────────────────────┘

                              LOGIACCOUNTING PRO
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │   Invoices   │  │  Inventory   │  │   Projects   │  │  Customers   ││
│  │   Module     │  │   Module     │  │   Module     │  │   Module     ││
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘│
│         │                 │                 │                 │         │
│         └─────────────────┴─────────────────┴─────────────────┘         │
│                                   │                                      │
│                                   ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    INTEGRATION ENGINE                              │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │  │
│  │  │   Sync      │  │   Event     │  │   Queue     │                │  │
│  │  │   Manager   │  │   Bus       │  │   Manager   │                │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                   │                                      │
└───────────────────────────────────┼──────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        CONNECTOR LAYER                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │    ERP      │  │    CRM      │  │ Accounting  │  │ E-commerce  │    │
│  │ Connectors  │  │ Connectors  │  │ Connectors  │  │ Connectors  │    │
│  │             │  │             │  │             │  │             │    │
│  │ • SAP       │  │ • Salesforce│  │ • QuickBooks│  │ • Shopify   │    │
│  │ • NetSuite  │  │ • HubSpot   │  │ • Xero      │  │ • WooComm   │    │
│  │ • Dynamics  │  │ • Zoho      │  │ • Sage      │  │ • Magento   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Banking   │  │  Shipping   │  │  Payments   │  │   Comms     │    │
│  │ Connectors  │  │ Connectors  │  │ Connectors  │  │ Connectors  │    │
│  │             │  │             │  │             │  │             │    │
│  │ • Plaid     │  │ • FedEx     │  │ • Stripe    │  │ • Slack     │    │
│  │ • OpenBank  │  │ • UPS       │  │ • PayPal    │  │ • Teams     │    │
│  │             │  │ • DHL       │  │ • Square    │  │ • Email     │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SYSTEMS                                    │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │   SAP   │  │Salesforce│  │QuickBooks│  │ Shopify │  │  Plaid  │      │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data Synchronization Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SYNC FLOW ARCHITECTURE                                │
└─────────────────────────────────────────────────────────────────────────┘

  OUTBOUND SYNC (LogiAccounting → External)
  ──────────────────────────────────────────

  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
  │  Entity  │────▶│  Event   │────▶│  Queue   │────▶│  Sync    │
  │  Change  │     │  Trigger │     │  Worker  │     │  Execute │
  └──────────┘     └──────────┘     └──────────┘     └──────────┘
                                                           │
                                                           ▼
                                                    ┌──────────┐
                                                    │ External │
                                                    │  System  │
                                                    └──────────┘


  INBOUND SYNC (External → LogiAccounting)
  ──────────────────────────────────────────

  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
  │ Webhook  │────▶│ Validate │────▶│ Transform│────▶│  Upsert  │
  │ Receive  │     │ Payload  │     │  Data    │     │  Entity  │
  └──────────┘     └──────────┘     └──────────┘     └──────────┘
       │
       │           ┌──────────┐     ┌──────────┐     ┌──────────┐
       └──────────▶│  Poll    │────▶│  Delta   │────▶│  Merge   │
                   │  Changes │     │  Detect  │     │  Data    │
                   └──────────┘     └──────────┘     └──────────┘


  CONFLICT RESOLUTION
  ──────────────────────

  ┌──────────────────────────────────────────────────────────────┐
  │                                                               │
  │  Strategy Options:                                            │
  │  • LAST_WRITE_WINS - Most recent change wins                 │
  │  • SOURCE_PRIORITY - Designated system wins                  │
  │  • MANUAL_REVIEW   - Flag for human decision                 │
  │  • MERGE_FIELDS    - Combine non-conflicting fields          │
  │                                                               │
  └──────────────────────────────────────────────────────────────┘
```

---

## 📁 PROJECT STRUCTURE

```
backend/app/
├── integrations/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── integration.py           # Integration connection model
│   │   ├── sync_config.py           # Sync configuration
│   │   ├── sync_log.py              # Sync history/logs
│   │   ├── field_mapping.py         # Field mappings
│   │   └── webhook.py               # Webhook registrations
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── base_connector.py        # Abstract connector class
│   │   ├── oauth_manager.py         # OAuth token management
│   │   ├── sync_engine.py           # Synchronization engine
│   │   ├── event_bus.py             # Internal event bus
│   │   ├── queue_manager.py         # Job queue management
│   │   ├── transformer.py           # Data transformation
│   │   └── conflict_resolver.py     # Conflict resolution
│   │
│   ├── connectors/
│   │   ├── __init__.py
│   │   │
│   │   ├── erp/
│   │   │   ├── __init__.py
│   │   │   ├── sap_connector.py
│   │   │   ├── netsuite_connector.py
│   │   │   └── dynamics_connector.py
│   │   │
│   │   ├── crm/
│   │   │   ├── __init__.py
│   │   │   ├── salesforce_connector.py
│   │   │   ├── hubspot_connector.py
│   │   │   └── zoho_connector.py
│   │   │
│   │   ├── accounting/
│   │   │   ├── __init__.py
│   │   │   ├── quickbooks_connector.py
│   │   │   ├── xero_connector.py
│   │   │   └── sage_connector.py
│   │   │
│   │   ├── ecommerce/
│   │   │   ├── __init__.py
│   │   │   ├── shopify_connector.py
│   │   │   ├── woocommerce_connector.py
│   │   │   └── magento_connector.py
│   │   │
│   │   ├── banking/
│   │   │   ├── __init__.py
│   │   │   ├── plaid_connector.py
│   │   │   └── openbanking_connector.py
│   │   │
│   │   ├── shipping/
│   │   │   ├── __init__.py
│   │   │   ├── fedex_connector.py
│   │   │   ├── ups_connector.py
│   │   │   └── dhl_connector.py
│   │   │
│   │   └── payments/
│   │       ├── __init__.py
│   │       ├── stripe_connector.py
│   │       └── paypal_connector.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── integration_service.py   # Integration management
│   │   ├── sync_service.py          # Sync operations
│   │   ├── mapping_service.py       # Field mapping service
│   │   └── webhook_service.py       # Webhook handling
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── integrations.py          # Integration CRUD
│   │   ├── sync.py                  # Sync endpoints
│   │   ├── webhooks.py              # Webhook endpoints
│   │   └── oauth_callback.py        # OAuth callbacks
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── integration_schemas.py
│   │   ├── sync_schemas.py
│   │   └── mapping_schemas.py
│   │
│   └── tasks/
│       ├── __init__.py
│       ├── sync_tasks.py            # Celery sync tasks
│       └── polling_tasks.py         # Polling tasks

frontend/src/
├── features/
│   └── integrations/
│       ├── components/
│       │   ├── IntegrationCard.jsx
│       │   ├── IntegrationSetup.jsx
│       │   ├── OAuthConnectButton.jsx
│       │   ├── FieldMapper.jsx
│       │   ├── SyncConfig.jsx
│       │   ├── SyncHistory.jsx
│       │   └── WebhookConfig.jsx
│       │
│       ├── pages/
│       │   ├── IntegrationsPage.jsx
│       │   ├── IntegrationDetailPage.jsx
│       │   └── IntegrationSetupPage.jsx
│       │
│       ├── hooks/
│       │   ├── useIntegrations.js
│       │   ├── useSync.js
│       │   └── useOAuth.js
│       │
│       └── api/
│           └── integrationsApi.js
```

---

## 🔧 TECHNOLOGY STACK

### Backend Dependencies

```txt
# requirements.txt additions

# HTTP Client
httpx==0.26.0                    # Async HTTP client
aiohttp==3.9.1                   # Async HTTP for webhooks

# OAuth
authlib==1.3.0                   # OAuth client
oauthlib==3.2.2                  # OAuth utilities

# API Clients (Official SDKs)
salesforce-bulk==2.2.0           # Salesforce
hubspot-api-client==8.1.0        # HubSpot
quickbooks-python==0.4.0         # QuickBooks (intuit-oauth)
xero-python==4.0.0               # Xero
plaid-python==14.0.0             # Plaid
stripe==7.8.0                    # Stripe
shopify-api==12.3.0              # Shopify
fedex==2.5.1                     # FedEx (unofficial)

# Data Transformation
jsonpath-ng==1.6.0               # JSONPath for field mapping
pydantic==2.5.0                  # Data validation

# Rate Limiting
ratelimit==2.2.1                 # Rate limiting decorator

# Encryption
cryptography==42.0.0             # Token encryption
```

### Frontend Dependencies

```json
{
  "dependencies": {
    "react-flow-renderer": "^10.3.17",
    "@tanstack/react-query": "^5.17.0"
  }
}
```

---

## 📊 DATABASE SCHEMA

```sql
-- Integration Connections
CREATE TABLE integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    
    -- Integration Type
    provider VARCHAR(50) NOT NULL,
    -- 'salesforce', 'hubspot', 'quickbooks', 'xero', 'shopify', etc.
    category VARCHAR(50) NOT NULL,
    -- 'erp', 'crm', 'accounting', 'ecommerce', 'banking', 'shipping', 'payments'
    
    -- Display
    name VARCHAR(255) NOT NULL,
    description TEXT,
    icon_url TEXT,
    
    -- Connection Status
    status VARCHAR(20) DEFAULT 'disconnected',
    -- 'disconnected', 'connecting', 'connected', 'error', 'expired'
    
    -- OAuth Credentials (encrypted)
    oauth_access_token_encrypted TEXT,
    oauth_refresh_token_encrypted TEXT,
    oauth_token_expires_at TIMESTAMP,
    oauth_scope TEXT,
    
    -- API Credentials (encrypted) - for API key auth
    api_key_encrypted TEXT,
    api_secret_encrypted TEXT,
    
    -- Provider-specific config
    config JSONB DEFAULT '{}',
    -- e.g., {"instance_url": "...", "company_id": "...", "realm_id": "..."}
    
    -- Sync Settings
    sync_enabled BOOLEAN DEFAULT FALSE,
    sync_direction VARCHAR(20) DEFAULT 'bidirectional',
    -- 'inbound', 'outbound', 'bidirectional'
    sync_frequency_minutes INTEGER DEFAULT 60,
    last_sync_at TIMESTAMP,
    next_sync_at TIMESTAMP,
    
    -- Error Tracking
    last_error TEXT,
    last_error_at TIMESTAMP,
    error_count INTEGER DEFAULT 0,
    
    -- Metadata
    connected_by UUID REFERENCES users(id),
    connected_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(organization_id, provider)
);

-- Sync Configurations
CREATE TABLE sync_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    
    -- Entity Mapping
    local_entity VARCHAR(100) NOT NULL,
    -- 'customer', 'invoice', 'product', 'order', 'transaction', etc.
    remote_entity VARCHAR(100) NOT NULL,
    -- Provider's entity name
    
    -- Sync Settings
    sync_enabled BOOLEAN DEFAULT TRUE,
    sync_direction VARCHAR(20) DEFAULT 'bidirectional',
    
    -- Filters
    sync_filter JSONB DEFAULT '{}',
    -- e.g., {"status": "active", "created_after": "2024-01-01"}
    
    -- Conflict Resolution
    conflict_resolution VARCHAR(50) DEFAULT 'last_write_wins',
    -- 'last_write_wins', 'source_priority', 'manual_review', 'merge'
    priority_source VARCHAR(20) DEFAULT 'local',
    -- 'local', 'remote'
    
    -- Timestamps
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(integration_id, local_entity, remote_entity)
);

-- Field Mappings
CREATE TABLE field_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sync_config_id UUID NOT NULL REFERENCES sync_configs(id) ON DELETE CASCADE,
    
    -- Field Definition
    local_field VARCHAR(255) NOT NULL,
    remote_field VARCHAR(255) NOT NULL,
    
    -- Transformation
    transform_type VARCHAR(50) DEFAULT 'direct',
    -- 'direct', 'format', 'lookup', 'compute', 'constant'
    transform_config JSONB DEFAULT '{}',
    -- e.g., {"format": "YYYY-MM-DD"}, {"lookup_table": "status_map"}
    
    -- Direction
    direction VARCHAR(20) DEFAULT 'bidirectional',
    -- 'inbound', 'outbound', 'bidirectional'
    
    -- Required
    is_required BOOLEAN DEFAULT FALSE,
    default_value TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(sync_config_id, local_field, remote_field)
);

-- Sync Logs
CREATE TABLE sync_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    sync_config_id UUID REFERENCES sync_configs(id) ON DELETE SET NULL,
    
    -- Sync Info
    sync_type VARCHAR(20) NOT NULL,
    -- 'full', 'incremental', 'manual', 'webhook'
    direction VARCHAR(20) NOT NULL,
    -- 'inbound', 'outbound'
    
    -- Status
    status VARCHAR(20) NOT NULL,
    -- 'pending', 'running', 'completed', 'failed', 'partial'
    
    -- Statistics
    records_processed INTEGER DEFAULT 0,
    records_created INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    records_skipped INTEGER DEFAULT 0,
    
    -- Errors
    errors JSONB DEFAULT '[]',
    
    -- Timing
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    
    -- Metadata
    triggered_by VARCHAR(50),
    -- 'schedule', 'webhook', 'manual', 'system'
    triggered_by_user_id UUID REFERENCES users(id),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_sync_logs_integration (integration_id),
    INDEX idx_sync_logs_created (created_at)
);

-- Sync Records (individual record tracking)
CREATE TABLE sync_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    sync_config_id UUID NOT NULL REFERENCES sync_configs(id) ON DELETE CASCADE,
    
    -- Record IDs
    local_id UUID NOT NULL,
    remote_id VARCHAR(255) NOT NULL,
    
    -- Sync State
    local_hash VARCHAR(64),      -- Hash of local record
    remote_hash VARCHAR(64),     -- Hash of remote record
    
    -- Timestamps
    local_updated_at TIMESTAMP,
    remote_updated_at TIMESTAMP,
    last_synced_at TIMESTAMP,
    
    -- Status
    sync_status VARCHAR(20) DEFAULT 'synced',
    -- 'synced', 'pending_outbound', 'pending_inbound', 'conflict', 'error'
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(sync_config_id, local_id),
    UNIQUE(sync_config_id, remote_id),
    INDEX idx_sync_records_status (sync_status)
);

-- Webhooks
CREATE TABLE integration_webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    
    -- Webhook Config
    event_type VARCHAR(100) NOT NULL,
    -- e.g., 'customer.created', 'invoice.updated', 'order.fulfilled'
    
    -- Endpoint
    endpoint_url TEXT NOT NULL,
    secret_hash VARCHAR(255),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Provider webhook ID (if registered with provider)
    provider_webhook_id VARCHAR(255),
    
    -- Statistics
    total_received INTEGER DEFAULT 0,
    total_processed INTEGER DEFAULT 0,
    total_failed INTEGER DEFAULT 0,
    last_received_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(integration_id, event_type)
);

-- Webhook Events (received webhooks log)
CREATE TABLE webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    webhook_id UUID NOT NULL REFERENCES integration_webhooks(id) ON DELETE CASCADE,
    
    -- Event Data
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    headers JSONB DEFAULT '{}',
    
    -- Processing
    status VARCHAR(20) DEFAULT 'pending',
    -- 'pending', 'processing', 'processed', 'failed', 'ignored'
    
    processed_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_webhook_events_status (status),
    INDEX idx_webhook_events_received (received_at)
);

-- OAuth States (for OAuth flow)
CREATE TABLE oauth_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    state VARCHAR(64) NOT NULL UNIQUE,
    
    organization_id UUID NOT NULL REFERENCES organizations(id),
    provider VARCHAR(50) NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    
    redirect_uri TEXT,
    additional_data JSONB DEFAULT '{}',
    
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_oauth_states_state (state)
);
```

---

## 🎯 FEATURE SPECIFICATIONS

### 14.1 Integration Management

| Feature | Description |
|---------|-------------|
| **Connection Setup** | OAuth or API key based authentication |
| **Health Monitoring** | Connection status, error tracking |
| **Token Refresh** | Automatic OAuth token refresh |
| **Configuration UI** | User-friendly setup wizard |
| **Test Connection** | Validate credentials before saving |

### 14.2 Sync Engine

| Feature | Description |
|---------|-------------|
| **Bidirectional Sync** | Two-way data synchronization |
| **Incremental Sync** | Only sync changed records |
| **Full Sync** | Complete data refresh option |
| **Scheduled Sync** | Configurable sync frequency |
| **Manual Sync** | On-demand sync trigger |
| **Delta Detection** | Hash-based change detection |

### 14.3 Field Mapping

| Feature | Description |
|---------|-------------|
| **Visual Mapper** | Drag-and-drop field mapping UI |
| **Transformations** | Format, lookup, compute values |
| **Default Values** | Fallback for missing data |
| **Required Fields** | Validation for mandatory fields |
| **Custom Fields** | Support for custom/extended fields |

### 14.4 Conflict Resolution

| Strategy | Description |
|----------|-------------|
| **Last Write Wins** | Most recent change takes priority |
| **Source Priority** | Designated system always wins |
| **Manual Review** | Flag for human decision |
| **Field Merge** | Combine non-conflicting changes |

### 14.5 Webhooks

| Feature | Description |
|---------|-------------|
| **Event Subscription** | Subscribe to provider events |
| **Signature Verification** | Validate webhook authenticity |
| **Retry Logic** | Automatic retry on failure |
| **Event Logging** | Complete webhook audit trail |

---

## 🔗 CONNECTOR SPECIFICATIONS

### ERP Connectors

| Provider | Auth | Entities | Sync Support |
|----------|------|----------|--------------|
| **SAP Business One** | OAuth 2.0 | Customers, Products, Orders, Invoices | Bidirectional |
| **Oracle NetSuite** | Token-Based | All SuiteScript entities | Bidirectional |
| **Microsoft Dynamics 365** | OAuth 2.0 | Accounts, Products, Orders | Bidirectional |

### CRM Connectors

| Provider | Auth | Entities | Sync Support |
|----------|------|----------|--------------|
| **Salesforce** | OAuth 2.0 | Leads, Contacts, Accounts, Opportunities | Bidirectional |
| **HubSpot** | OAuth 2.0 | Contacts, Companies, Deals | Bidirectional |
| **Zoho CRM** | OAuth 2.0 | Leads, Contacts, Accounts, Deals | Bidirectional |

### Accounting Connectors

| Provider | Auth | Entities | Sync Support |
|----------|------|----------|--------------|
| **QuickBooks Online** | OAuth 2.0 | Customers, Invoices, Payments, Items | Bidirectional |
| **Xero** | OAuth 2.0 | Contacts, Invoices, Payments, Items | Bidirectional |
| **Sage** | OAuth 2.0 | Customers, Invoices, Products | Bidirectional |

### E-commerce Connectors

| Provider | Auth | Entities | Sync Support |
|----------|------|----------|--------------|
| **Shopify** | OAuth 2.0 | Products, Orders, Customers, Inventory | Bidirectional |
| **WooCommerce** | API Key | Products, Orders, Customers | Bidirectional |
| **Magento** | OAuth 1.0a | Products, Orders, Customers | Bidirectional |

### Banking Connectors

| Provider | Auth | Entities | Sync Support |
|----------|------|----------|--------------|
| **Plaid** | API Key | Accounts, Transactions | Inbound Only |
| **Open Banking (PSD2)** | OAuth 2.0 | Accounts, Transactions | Inbound Only |

### Shipping Connectors

| Provider | Auth | Entities | Operations |
|----------|------|----------|------------|
| **FedEx** | OAuth 2.0 | Shipments, Tracking | Create, Track |
| **UPS** | OAuth 2.0 | Shipments, Tracking | Create, Track |
| **DHL** | API Key | Shipments, Tracking | Create, Track |

---

## 📋 FEATURE CHECKLIST

| # | Feature | Priority | Hours |
|---|---------|----------|-------|
| 14.1 | Database schema & models | P0 | 6h |
| 14.2 | Base connector framework | P0 | 8h |
| 14.3 | OAuth manager | P0 | 6h |
| 14.4 | Sync engine core | P0 | 12h |
| 14.5 | Event bus & queue | P0 | 6h |
| 14.6 | Data transformer | P1 | 6h |
| 14.7 | Conflict resolver | P1 | 4h |
| 14.8 | QuickBooks connector | P0 | 10h |
| 14.9 | Xero connector | P1 | 8h |
| 14.10 | Salesforce connector | P1 | 10h |
| 14.11 | HubSpot connector | P1 | 8h |
| 14.12 | Shopify connector | P1 | 10h |
| 14.13 | Stripe connector | P0 | 6h |
| 14.14 | Plaid connector | P1 | 8h |
| 14.15 | Webhook service | P0 | 6h |
| 14.16 | Integration routes | P0 | 6h |
| 14.17 | Sync tasks (Celery) | P0 | 6h |
| 14.18 | Frontend: Integration list | P0 | 6h |
| 14.19 | Frontend: Setup wizard | P0 | 8h |
| 14.20 | Frontend: Field mapper | P1 | 8h |
| 14.21 | Frontend: Sync dashboard | P1 | 6h |

**Total: ~154 hours**

---

## 🔗 API ENDPOINTS

### Integrations

```
GET    /api/v1/integrations                    # List available integrations
GET    /api/v1/integrations/connected          # List connected integrations
POST   /api/v1/integrations/:provider/connect  # Initiate OAuth connection
DELETE /api/v1/integrations/:id                # Disconnect integration
GET    /api/v1/integrations/:id                # Get integration details
PUT    /api/v1/integrations/:id                # Update integration config
POST   /api/v1/integrations/:id/test           # Test connection
```

### OAuth

```
GET    /api/v1/oauth/:provider/authorize       # Get OAuth authorize URL
GET    /api/v1/oauth/:provider/callback        # OAuth callback handler
POST   /api/v1/oauth/:provider/refresh         # Refresh OAuth token
```

### Sync

```
POST   /api/v1/integrations/:id/sync           # Trigger manual sync
GET    /api/v1/integrations/:id/sync/status    # Get sync status
GET    /api/v1/integrations/:id/sync/history   # Get sync history
POST   /api/v1/integrations/:id/sync/config    # Configure sync
GET    /api/v1/integrations/:id/sync/config    # Get sync config
```

### Field Mapping

```
GET    /api/v1/integrations/:id/mappings       # List field mappings
POST   /api/v1/integrations/:id/mappings       # Create mapping
PUT    /api/v1/integrations/:id/mappings/:mid  # Update mapping
DELETE /api/v1/integrations/:id/mappings/:mid  # Delete mapping
GET    /api/v1/integrations/:id/fields/local   # Get local fields
GET    /api/v1/integrations/:id/fields/remote  # Get remote fields
```

### Webhooks

```
POST   /api/v1/webhooks/:provider              # Receive webhook
GET    /api/v1/integrations/:id/webhooks       # List webhooks
POST   /api/v1/integrations/:id/webhooks       # Register webhook
DELETE /api/v1/integrations/:id/webhooks/:wid  # Delete webhook
```

---

*Phase 14 Plan - LogiAccounting Pro*
*External Integrations Hub*
