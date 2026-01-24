# LogiAccounting Pro

Enterprise logistics and accounting platform with multi-role support for administrators, clients, and suppliers.

## Features

### Core Modules

#### Logistics Module
- **Inventory Management**: Track materials, quantities, locations, and costs
- **Stock Movements**: Record entries and exits with project association
- **Low Stock Alerts**: Automatic alerts when materials fall below minimum thresholds

#### Accounting Module
- **Transaction Tracking**: Record income and expenses with categories
- **Payment Management**: Track payables and receivables with due dates
- **Cash Flow Reports**: Visualize financial performance over time

### CRM & Sales Pipeline (Phase 25)

#### Lead Management
- **Lead Capture**: Multi-source lead tracking (website, referral, campaign, cold call)
- **BANT Scoring**: Automatic lead scoring based on Budget, Authority, Need, Timeline
- **Lead Rating**: Hot, warm, cold classification based on engagement
- **Lead Conversion**: One-click conversion to contact and opportunity
- **Bulk Import**: CSV/Excel lead import with validation
- **Source Analytics**: Lead source performance metrics

#### Contact Management
- **Contact 360 View**: Complete view with activities, deals, history
- **Contact Roles**: Decision maker, influencer, champion classification
- **Communication Preferences**: Do not call, do not email flags
- **Contact Merge**: Deduplicate contacts with merge tool
- **Contact Import/Export**: Bulk operations with CSV

#### Company/Account Management
- **Health Scoring**: Automatic account health calculation
- **Company Hierarchy**: Parent/subsidiary relationships
- **Industry Classification**: 17 industry categories
- **Client Linking**: Link CRM companies to accounting clients
- **At-Risk Detection**: Identify accounts needing attention
- **Top Accounts**: Revenue-based account ranking

#### Sales Pipeline
- **Kanban Board**: Drag-and-drop deal management
- **Multiple Pipelines**: Custom pipelines per team/product
- **Stage Configuration**: Customizable stages with probabilities
- **Win/Loss Tracking**: Outcome tracking with reasons
- **Pipeline Statistics**: Value, velocity, conversion metrics
- **Stage Automation**: Auto-update probability on stage change

#### Opportunity Management
- **Deal Tracking**: Amount, probability, expected close date
- **Win/Lose Actions**: Capture win/loss reasons and competitors
- **Deal Reopen**: Reopen closed deals for new attempts
- **Forecast View**: Pipeline and weighted revenue forecast
- **Win/Loss Analysis**: Competitor and reason analysis

#### Activity Management
- **Activity Types**: Calls, emails, meetings, tasks, notes
- **Call Logging**: Outcome tracking with duration
- **Email Tracking**: Open and click tracking
- **Meeting Scheduling**: Calendar integration
- **Task Management**: Due dates, priorities, overdue alerts
- **Activity Statistics**: Team activity metrics

#### Email Templates
- **Merge Fields**: Contact, company, opportunity, sender variables
- **Template Categories**: Prospecting, follow-up, proposals
- **Template Rendering**: Variable substitution preview
- **Usage Tracking**: Template performance metrics

#### Quote Management
- **Quote Builder**: Line items with quantities and discounts
- **Approval Workflow**: Submit, approve, reject flow
- **Quote to Invoice**: Convert accepted quotes to invoices
- **Quote Expiration**: Automatic expiry tracking
- **Customer Portal**: Public quote viewing and acceptance
- **E-Signature**: Customer signature capture

### Advanced Reporting & Business Intelligence (Phase 24)

#### Visual Report Designer
- **Drag-and-Drop Builder**: @dnd-kit powered canvas with grid snapping
- **Component Library**: Charts, KPIs, tables, text, images, shapes
- **Multi-Select**: Select and manipulate multiple components
- **Zoom Controls**: 25%-200% zoom with keyboard shortcuts
- **Undo/Redo**: 50-state history with Ctrl+Z/Ctrl+Y support
- **Real-Time Preview**: Live data binding preview

#### Chart Components
- **Line Charts**: Time series with multiple datasets, area fills
- **Bar Charts**: Vertical/horizontal, stacked, grouped
- **Pie Charts**: Pie and donut variants with labels
- **KPI Cards**: Big numbers, trends, sparklines, target progress
- **Data Tables**: Sortable, filterable, paginated with CSV export
- **Pivot Tables**: Interactive aggregation with sum, avg, count, min, max

#### Semantic Layer (Metrics Catalog)
- **12 System Metrics**: Revenue, expenses, profit margin, invoice count, etc.
- **Custom Metrics**: User-defined metrics with formulas
- **Metric Certification**: Organization-wide certified metrics
- **Formula Engine**: Calculated metrics with dependencies
- **Category Organization**: Financial, operational, inventory, projects

#### Report Scheduling
- **Cron Expressions**: Flexible scheduling (daily, weekly, monthly)
- **Multiple Formats**: PDF, Excel, CSV, HTML, PowerPoint export
- **Email Distribution**: Template-based emails with attachments
- **Execution History**: Full audit trail with retry capability
- **Status Monitoring**: Running, completed, failed states

#### Data Sources & Filtering
- **Internal Tables**: Invoices, payments, projects, inventory, clients, vendors
- **Field Browser**: Browse and select fields with aggregations
- **Filter Builder**: Complex AND/OR filter groups
- **Parameter Support**: Runtime parameters for dynamic reports

### Mobile Application & PWA (Phase 23)

#### Progressive Web App (PWA)
- **Service Worker**: Workbox-powered caching with background sync
- **Offline Support**: Full offline functionality with IndexedDB storage
- **Install Prompt**: Native app-like installation on desktop and mobile
- **Push Notifications**: Web Push API with notification actions
- **App Manifest**: Shortcuts, share target, protocol handlers, file handlers

#### React Native Mobile App
- **Expo Framework**: Cross-platform iOS and Android support
- **Tab Navigation**: Dashboard, Invoices, Scanner, Inventory, Settings
- **Biometric Authentication**: Face ID and Fingerprint login
- **Barcode Scanner**: Product barcode and QR code scanning
- **Document Scanner**: Receipt and invoice capture with OCR
- **SQLite Database**: Local offline data storage
- **Bidirectional Sync**: Conflict resolution with merge strategies

#### Mobile Features
- **Dashboard**: KPI cards, quick actions, recent invoices
- **Invoice Management**: Create, view, search, filter invoices
- **Inventory Tracking**: Stock levels, low stock alerts, barcode lookup
- **Settings**: Profile, biometric toggle, sync status, notifications

#### Backend Mobile API
- **Sync Endpoints**: Pull/push changes with conflict detection
- **Push Service**: Expo notifications with channel support
- **Mobile Dashboard**: Optimized KPI and activity endpoints
- **Global Search**: Cross-entity search for mobile

### Integration Hub (Phase 29)

#### Core Integration Framework
- **Base Integration Class**: Abstract base for all providers with connect/disconnect/test methods
- **Integration Registry**: Singleton registry for provider discovery and instantiation
- **Connection Manager**: Encrypted credential storage using Fernet (AES-256)
- **Webhook Service**: Outbound webhook delivery with HMAC signatures and retry logic
- **Sync Service**: Bidirectional data synchronization with conflict resolution

#### Payment Providers
- **Stripe Integration**: Payment intents, customers, invoices, refunds, webhook handling
- **PayPal Integration**: Orders, captures, invoices, payouts, webhook verification

#### Accounting Platforms
- **QuickBooks Online**: OAuth 2.0 auth, customers, invoices, payments, bidirectional sync
- **Xero**: OAuth 2.0 auth, contacts, invoices, payments, field mapping

#### Automation & Communication
- **Zapier Integration**: 7 triggers (invoice, payment, customer events) + 5 actions
- **Slack Integration**: OAuth 2.0 auth, messaging, slash commands (/invoice, /customer, /project)

### Advanced Workflow Engine v2 (Phase 26)

#### CRM Workflow Integration
- **CRM Event Triggers**: Lead created/converted, deal stage changes, deal won/lost, quote events
- **CRM Actions**: Create leads, deals, activities; assign owners; update scores; convert leads
- **Threshold Triggers**: Metric-based triggers for overdue invoices, unassigned leads, pipeline value
- **CRM Conditions**: Complex condition evaluation with nested AND/OR rules

#### Sub-Workflows & Error Handling
- **Sub-Workflow Node**: Call workflows from other workflows as reusable components
- **Recursion Prevention**: Circular reference detection with max depth limits
- **Try-Catch Blocks**: Error handling with try, catch, finally steps
- **Retry Policies**: Configurable retry with fixed, exponential, linear backoff
- **Fallback Actions**: Execute alternative actions on failure
- **Circuit Breaker**: Prevent cascading failures with circuit breaker pattern

#### Workflow Versioning
- **Version History**: Track all workflow changes with snapshots
- **Version Comparison**: Compare changes between versions
- **Rollback Capability**: Restore previous workflow versions

#### AI-Powered Features
- **Workflow Suggestions**: AI-powered workflow recommendations
- **Natural Language to Workflow**: Describe workflow in plain English, AI builds it
- **Workflow Explanation**: AI generates human-readable workflow descriptions
- **AI Actions**: Text generation, data extraction, classification, sentiment analysis

#### Template Marketplace
- **Built-in Templates**: Invoice reminders, lead assignment, deal notifications
- **Template Categories**: Financial, CRM, operations, notifications, integrations
- **Template Installation**: One-click install with customization
- **Template Publishing**: Share custom workflows as templates
- **Template Rating**: Community ratings and install counts

#### Live Execution Monitor
- **Real-Time Updates**: WebSocket-based live execution tracking
- **Execution Timeline**: Step-by-step execution visualization
- **Step Inspector**: View input/output data for each step
- **Cancel/Retry**: Cancel running executions, retry failed ones
- **Dashboard Analytics**: Success rates, execution counts, top workflows

### Advanced Workflow Automation (Phase 22)

#### Visual Workflow Designer
- **Drag-and-Drop Editor**: React Flow-based visual workflow builder
- **Node Types**: Trigger, Action, Condition, Parallel, Delay, End nodes
- **Auto Layout**: Automatic node arrangement using dagre algorithm
- **Undo/Redo**: Full history management with keyboard shortcuts
- **Validation**: Real-time workflow validation with error highlighting

#### Trigger System
- **Entity Events**: Invoice, payment, project, inventory entity triggers
- **Scheduled Triggers**: Cron-based scheduling with timezone support
- **Manual Triggers**: User-initiated workflows with parameters
- **Webhook Triggers**: External system integration

#### Action Executors
- **Email Actions**: Template-based emails with variable interpolation
- **Notification Actions**: In-app and push notifications
- **Webhook Actions**: HTTP calls to external APIs with retry logic
- **Entity Actions**: Create, update, delete entities automatically
- **Approval Actions**: Multi-step approval workflows
- **Delay Actions**: Timed delays with duration configuration
- **Script Actions**: Sandboxed Python script execution

#### Business Rules Engine
- **Condition Evaluation**: Complex AND/OR condition groups
- **Expression Language**: 22+ built-in functions (UPPER, LOWER, DATE_ADD, etc.)
- **Variable Interpolation**: Dynamic values from context
- **Rule Prioritization**: Execution order based on priority
- **Rule Testing**: Test rules before activation

#### Execution Monitoring
- **Real-Time Status**: Pending, running, waiting, completed, failed states
- **Execution History**: Full audit trail of workflow runs
- **Step-by-Step Logs**: Detailed logging for each workflow step
- **Retry Failed**: One-click retry for failed executions
- **Cancel Running**: Graceful cancellation of running workflows
- **Statistics Dashboard**: Success rate, execution count, performance metrics

#### Workflow Templates
- **Built-in Templates**: Invoice approval, payment reminder, low stock alert, project progress
- **Custom Templates**: Save and reuse workflow configurations
- **Version Control**: Track workflow versions with rollback capability

### Internationalization & Localization (Phase 21)

#### Multi-Language Support
- **11 Languages**: English, Spanish, German, French, Italian, Portuguese, Dutch, Polish, Japanese, Chinese, Arabic
- **Translation Service**: Namespace-based translations with interpolation and pluralization
- **CLDR Pluralization**: Correct plural forms for all supported languages
- **RTL Support**: Full right-to-left support for Arabic and Hebrew
- **Dynamic Loading**: Load translations on demand for optimal performance

#### Multi-Currency System
- **24 Currencies**: USD, EUR, GBP, JPY, CHF, CAD, AUD, CNY, and more
- **Real-Time Exchange Rates**: ECB and OpenExchangeRates integration
- **Currency Conversion**: Automatic conversion with rate caching
- **Locale-Aware Formatting**: Symbol position, decimal separators per locale

#### Regional Tax Engine
- **EU VAT**: All 27 EU member states with standard and reduced rates
- **US Sales Tax**: All 50 states plus DC with local tax support
- **VAT Validation**: Format validation and VIES online verification
- **Tax Categories**: Automatic rate selection based on product category
- **B2B Support**: Reverse charge for intra-EU transactions

#### Date/Time & Number Formatting
- **Locale-Specific Formats**: Date, time, and number formatting per locale
- **Timezone Support**: 15+ common timezones with conversion utilities
- **Relative Time**: "2 hours ago" in all supported languages
- **Compact Numbers**: 1.5K, 2.3M formatting

#### Localized Documents
- **Invoice Templates**: Multi-language invoice generation
- **Address Formatting**: Country-specific address formats
- **RTL Layout**: Proper layout for RTL languages

### Performance & Scalability (Phase 20)

#### Multi-Layer Caching
- **Redis Cluster**: High-availability caching with Sentinel support
- **L1/L2 Cache**: Local memory cache with Redis distributed cache
- **Cache Decorators**: `@cached` and `@invalidate_cache` for automatic caching
- **Tag-Based Invalidation**: Group related cache entries for bulk invalidation
- **Cache Warmup**: Preload frequently accessed data on startup

#### Database Optimization
- **Connection Pooling**: Configurable pool sizes with overflow support
- **Read Replicas**: Automatic query routing to replicas for read scaling
- **Materialized Views**: Pre-computed analytics for dashboard performance
- **Table Partitioning**: Time and tenant-based partitioning for large tables
- **Query Optimizer**: Index recommendations and slow query detection

#### Observability Stack
- **Prometheus Metrics**: Request latency, cache hit rates, DB query performance
- **OpenTelemetry Tracing**: Distributed tracing across services
- **Structured Logging**: JSON logging with correlation IDs
- **Grafana Dashboards**: Real-time performance visualization

#### Kubernetes Deployment
- **Auto-Scaling**: HPA based on CPU, memory, and custom metrics
- **Rolling Updates**: Zero-downtime deployments
- **Health Probes**: Liveness, readiness, and startup probes
- **Graceful Shutdown**: Connection draining before termination
- **Network Policies**: Secure pod-to-pod communication

### AI-Powered Features (Phase 19)

#### Advanced AI Infrastructure
- **LLM Integration**: Unified client supporting Anthropic Claude and OpenAI GPT
- **Model Tiers**: Fast, Balanced, and Powerful options for different use cases
- **Usage Tracking**: Token consumption, costs, and latency monitoring

#### Smart Invoice OCR
- **Document Processing**: Tesseract OCR for images and PDFs
- **LLM-Enhanced Extraction**: AI-powered field extraction with schema hints
- **Auto-Categorization**: 13 expense categories with confidence scores
- **GL Account Suggestions**: Automatic account mapping
- **Validation Workflow**: Review, correct, and approve extracted data

#### Cash Flow Predictor
- **Prophet ML Model**: Time-series forecasting with seasonal patterns
- **Fallback Statistical Model**: Z-score based when Prophet unavailable
- **Risk Assessment**: Balance predictions with risk factors
- **Actionable Insights**: Recommendations based on forecasted trends
- **Configurable Horizons**: 30, 60, 90 day predictions

#### Profitability Assistant
- **NLP Chatbot**: Natural language queries about financial data
- **Business Tools Integration**: Revenue, expenses, profitability metrics
- **Conversation History**: Multi-turn conversations with context
- **Quick Actions**: Pre-built queries for common questions
- **Feedback System**: Thumbs up/down for response quality

#### Payment Optimizer
- **Early Discount Detection**: Identify discount opportunities with ROI
- **Batch Payment Suggestions**: Combine payments to same vendor
- **Timing Optimization**: Align payments with expected inflows
- **Priority Payments**: Flag critical vendor relationships
- **Savings Tracking**: Monitor realized vs potential savings

#### Anomaly Detection
- **Statistical Analysis**: Z-score based unusual amount detection
- **Frequency Monitoring**: Detect unusual transaction volumes
- **Timing Alerts**: Flag transactions outside business hours
- **Duplicate Detection**: Identify potential duplicate entries
- **Custom Rules Engine**: Configurable detection rules
- **Resolution Workflow**: Resolve, dismiss, or investigate anomalies

### Enterprise Features

#### Multi-Tenancy (Phase 16)
- Tenant isolation with separate data stores
- Subscription management and quota tracking
- Team management with role-based access

#### API Gateway & Webhooks (Phase 17)
- **API Key Management**
  - Scoped access control (invoices:read, payments:write, etc.)
  - Per-key rate limiting (minute/hour/day)
  - IP whitelist restrictions
  - Key regeneration and revocation
  - Usage statistics tracking
- **Webhook System**
  - 30+ event types (invoices, payments, inventory, projects, etc.)
  - HMAC-SHA256 signature verification
  - Automatic retry with exponential backoff
  - Delivery tracking and manual retry
  - Secret rotation

#### Real-Time Collaboration (Phase 18)
- **User Presence System**
  - Live online/away/busy status indicators
  - Automatic away detection after 5 minutes
  - Per-tenant user presence tracking
- **Collaboration Rooms**
  - Entity-based rooms (invoices, projects, etc.)
  - See who's viewing/editing the same document
  - Real-time user count per entity
- **Cursor Tracking**
  - Live cursor position synchronization
  - User-specific cursor colors
  - Document-level cursor visibility
- **Notification Center**
  - Real-time notification delivery via WebSocket
  - Priority levels (urgent, high, normal, low)
  - Mark read/unread, delete notifications
  - Unread count badge
- **Activity Feed**
  - Real-time activity stream
  - Entity-specific activity filtering
  - Action icons (created, updated, deleted, completed)

#### External Integrations (Phase 14)
- QuickBooks, Xero, Salesforce, HubSpot
- Shopify, Stripe, Plaid connections
- OAuth 2.0 authentication flow

#### Audit & Compliance (Phase 15)
- Comprehensive audit trail
- Compliance framework for SOX, GDPR, HIPAA
- Security alerts and monitoring

### Multi-Role System
| Role | Access |
|------|--------|
| Admin | Full access, user management, reports |
| Client | Projects, payments, transactions |
| Supplier | Inventory, movements, payments |

### Cross-Role Notifications
When payments are marked as paid, all relevant parties (admin, client, supplier) receive automatic notifications.

## Tech Stack

- **Frontend**: React 18, Vite, Chart.js, Axios, Socket.IO Client, React Flow, Zustand, @dnd-kit, lucide-react
- **Backend**: FastAPI, Pydantic, PyJWT, bcrypt, Socket.IO
- **CRM**: Lead scoring, pipeline management, activity tracking, quote workflow
- **Real-Time**: Socket.IO with Redis adapter for horizontal scaling
- **Workflow Engine**: Event-driven automation with rule evaluation
- **BI & Reporting**: Chart.js visualizations, semantic metrics layer, cron scheduling
- **Database**: PostgreSQL with read replicas, connection pooling
- **Caching**: Redis Cluster with Sentinel for high availability
- **Observability**: Prometheus, Grafana, Jaeger, OpenTelemetry
- **Infrastructure**: Docker, Kubernetes, Nginx Ingress

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- npm or yarn

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 5000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Access the Application
- Frontend: http://localhost:5173
- API: http://localhost:5000
- API Docs: http://localhost:5000/docs

## Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@logiaccounting.demo | Demo2024!Admin |
| Client | client@logiaccounting.demo | Demo2024!Client |
| Supplier | supplier@logiaccounting.demo | Demo2024!Supplier |

## Deployment to Render

1. Fork this repository
2. Connect to Render
3. Use the `render.yaml` blueprint
4. Deploy

The application will automatically build the frontend and serve it through FastAPI.

## Project Structure

```
logiaccounting-pro/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app entry
│   │   ├── routes/           # API endpoints
│   │   ├── models/           # Data stores
│   │   ├── schemas/          # Pydantic models
│   │   ├── realtime/         # WebSocket collaboration
│   │   │   ├── server.py     # Socket.IO server
│   │   │   ├── managers/     # Connection, presence, rooms
│   │   │   ├── handlers/     # Event handlers
│   │   │   ├── services/     # Notification, activity
│   │   │   └── routes/       # REST endpoints
│   │   ├── ai/               # Advanced AI Features (Phase 19)
│   │   │   ├── config.py     # AI configuration
│   │   │   ├── models/       # AI data models
│   │   │   ├── services/     # AI services
│   │   │   │   ├── llm_client.py   # LLM integration
│   │   │   │   ├── cashflow/       # Cash flow predictor
│   │   │   │   ├── invoice/        # Invoice OCR
│   │   │   │   ├── assistant/      # Chat assistant
│   │   │   │   ├── payments/       # Payment optimizer
│   │   │   │   └── anomaly/        # Anomaly detection
│   │   │   └── routes/       # AI API endpoints
│   │   ├── workflows/        # Workflow Automation (Phase 22)
│   │   │   ├── config.py     # Workflow configuration
│   │   │   ├── models/       # Workflow, execution, rule models
│   │   │   ├── engine/       # Workflow engine core and executor
│   │   │   ├── triggers/     # Event, schedule, manual triggers
│   │   │   ├── actions/      # Email, webhook, entity, approval actions
│   │   │   ├── rules/        # Expression evaluator and functions
│   │   │   ├── routes/       # API endpoints
│   │   │   └── integration.py # Entity event hooks
│   │   ├── services/
│   │   │   ├── bi/           # Business Intelligence (Phase 24)
│   │   │   │   ├── scheduler_service.py  # Report scheduling
│   │   │   │   └── metrics_service.py    # Semantic metrics layer
│   │   │   └── crm/          # CRM Services (Phase 25)
│   │   │       ├── lead_service.py       # Lead management
│   │   │       ├── contact_service.py    # Contact management
│   │   │       ├── company_service.py    # Company management
│   │   │       ├── opportunity_service.py # Deal management
│   │   │       ├── pipeline_service.py   # Pipeline config
│   │   │       ├── activity_service.py   # Activity tracking
│   │   │       ├── email_template_service.py
│   │   │       └── quote_service.py      # Quote workflow
│   │   ├── i18n/             # Internationalization (Phase 21)
│   │   │   ├── config.py     # Languages, currencies, namespaces
│   │   │   ├── core/         # Context, locale, middleware
│   │   │   ├── translation/  # Service, loader, interpolation, pluralization
│   │   │   ├── currency/     # Config, exchange, converter, formatter
│   │   │   ├── tax/          # EU VAT, US Sales Tax, validation
│   │   │   ├── datetime/     # Formatters, numbers, timezone
│   │   │   ├── templates/    # Localized document templates
│   │   │   └── api/          # i18n API routes
│   │   ├── performance/      # Performance & Scalability (Phase 20)
│   │   │   ├── caching/      # Multi-layer caching
│   │   │   │   ├── redis_client.py   # Redis connection
│   │   │   │   ├── cache_manager.py  # L1/L2 cache manager
│   │   │   │   ├── decorators.py     # @cached, @invalidate_cache
│   │   │   │   ├── invalidation.py   # Event-driven invalidation
│   │   │   │   └── warmup.py         # Cache warmup service
│   │   │   ├── database/     # Database optimization
│   │   │   │   ├── connection_pool.py # Read/write splitting
│   │   │   │   ├── read_replica.py   # Query routing
│   │   │   │   ├── materialized_views.py # Analytics views
│   │   │   │   ├── partitioning.py   # Table partitioning
│   │   │   │   └── query_optimizer.py # Index recommendations
│   │   │   ├── monitoring/   # Observability
│   │   │   │   ├── metrics.py        # Prometheus metrics
│   │   │   │   ├── tracing.py        # OpenTelemetry
│   │   │   │   └── logging_config.py # Structured logging
│   │   │   ├── scaling/      # Auto-scaling support
│   │   │   │   ├── health_check.py   # K8s probes
│   │   │   │   └── graceful_shutdown.py # Connection draining
│   │   │   └── routes/       # Health endpoints
│   │   └── utils/            # Auth utilities
│   ├── Dockerfile            # Multi-stage build
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── contexts/         # Auth context
│   │   ├── features/
│   │   │   ├── realtime/     # Real-time collaboration
│   │   │   │   ├── context/  # RealtimeContext
│   │   │   │   ├── hooks/    # usePresence, useRoom, etc.
│   │   │   │   └── components/ # UI components
│   │   │   ├── ai/           # AI Features (Phase 19)
│   │   │   │   ├── CashFlowForecast.jsx
│   │   │   │   ├── InvoiceScanner.jsx
│   │   │   │   ├── AIChatAssistant.jsx
│   │   │   │   ├── PaymentOptimizer.jsx
│   │   │   │   ├── AnomalyDashboard.jsx
│   │   │   │   └── AIUsageStats.jsx
│   │   │   ├── workflows/    # Workflow Automation (Phase 22)
│   │   │   │   ├── api/      # API layer
│   │   │   │   ├── stores/   # Zustand stores
│   │   │   │   ├── hooks/    # React hooks
│   │   │   │   ├── constants/ # Node types, triggers, actions
│   │   │   │   ├── components/
│   │   │   │   │   └── nodes/ # React Flow node components
│   │   │   │   └── pages/    # List, editor, executions pages
│   │   │   ├── bi/           # Business Intelligence (Phase 24)
│   │   │   │   ├── context/  # ReportDesignerContext
│   │   │   │   └── components/
│   │   │   └── crm/          # CRM Module (Phase 25)
│   │   │       ├── components/
│   │   │       │   ├── PipelineBoard.jsx # Kanban board
│   │   │       │   ├── StageColumn.jsx   # Pipeline stage
│   │   │       │   ├── DealCard.jsx      # Draggable deal card
│   │   │       │   ├── DealModal.jsx     # Deal create/edit
│   │   │       │   ├── LeadConversion.jsx # Lead wizard
│   │   │       │   └── CRMSidebar.jsx    # Navigation
│   │   │       ├── pages/
│   │   │       │   └── CRMDashboard.jsx  # Sales dashboard
│   │   │       ├── CRMLayout.jsx         # Module layout
│   │   │       └── routes.jsx            # CRM routing
│   │   │           ├── DataSourcePanel.jsx
│   │   │           ├── FieldsPanel.jsx
│   │   │           ├── FilterBuilder.jsx
│   │   │           ├── ReportCanvas.jsx
│   │   │           ├── ReportComponent.jsx
│   │   │           ├── ComponentPalette.jsx
│   │   │           ├── PropertyPanel.jsx
│   │   │           ├── ReportPreview.jsx
│   │   │           └── charts/     # Chart components library
│   │   ├── i18n/             # Internationalization (Phase 21)
│   │   │   ├── config.js     # Language and currency configuration
│   │   │   ├── LocaleContext.jsx  # React context provider
│   │   │   ├── translations/ # EN, ES, DE, FR translations
│   │   │   ├── hooks/        # useFormatters, useLocale
│   │   │   └── components/   # LanguageSelector, FormattedNumber, RTLProvider
│   │   ├── lib/
│   │   │   └── performance/  # Frontend Performance (Phase 20)
│   │   │       ├── cache.ts          # API caching
│   │   │       ├── optimization.ts   # Debounce, throttle, memoize
│   │   │       ├── virtualization.ts # Virtual scrolling
│   │   │       ├── lazy-loading.ts   # Component lazy loading
│   │   │       └── metrics.ts        # Web Vitals tracking
│   │   ├── pwa/              # PWA Features (Phase 23)
│   │   │   ├── registerSW.js # Service Worker registration
│   │   │   ├── useInstallPrompt.js # Install prompt hook
│   │   │   ├── storage/      # IndexedDB layer
│   │   │   ├── sync/         # Offline sync queue
│   │   │   ├── notifications/ # Push notification service
│   │   │   ├── hooks/        # useSync, useOffline
│   │   │   └── components/   # Install banner, network status
│   │   └── services/         # API client
│   ├── workbox-config.js     # Workbox PWA configuration
│   └── package.json
├── mobile/                    # React Native App (Phase 23)
│   ├── app.json              # Expo configuration
│   ├── src/
│   │   ├── app/              # Expo Router screens
│   │   │   ├── (auth)/       # Auth stack (login, register)
│   │   │   └── (tabs)/       # Tab navigator (dashboard, invoices, etc.)
│   │   ├── components/       # Reusable UI components
│   │   │   └── ui/           # KPICard, Button, Badge, Card
│   │   ├── services/         # API client, auth, invoices
│   │   ├── store/            # Zustand auth store
│   │   ├── storage/          # SQLite database
│   │   ├── sync/             # Sync engine, conflict resolver
│   │   ├── scanner/          # Barcode and document scanners
│   │   └── notifications/    # Push notification service
│   └── package.json
├── k8s/                      # Kubernetes manifests (Phase 20)
│   ├── namespace.yaml        # Namespace definition
│   ├── configmap.yaml        # Configuration
│   ├── deployment.yaml       # API and worker deployments
│   ├── service.yaml          # Service definitions
│   ├── hpa.yaml              # Horizontal Pod Autoscaler
│   ├── ingress.yaml          # Ingress configuration
│   ├── pdb.yaml              # Pod Disruption Budget
│   ├── rbac.yaml             # Service accounts and roles
│   └── network-policy.yaml   # Network security
├── infrastructure/           # Infrastructure configs
│   ├── prometheus/           # Prometheus configuration
│   └── grafana/              # Grafana provisioning
├── docker-compose.yml        # Local development stack
├── skills/                   # Agent Skills
├── AGENTS.md                 # AI agent instructions
├── render.yaml               # Render deployment
└── README.md
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `GET /api/v1/auth/me` - Current user info

### Inventory
- `GET /api/v1/inventory/materials` - List materials
- `POST /api/v1/inventory/materials` - Create material
- `PUT /api/v1/inventory/materials/{id}` - Update material

### Projects
- `GET /api/v1/projects` - List projects
- `POST /api/v1/projects` - Create project

### Transactions
- `GET /api/v1/transactions` - List transactions
- `POST /api/v1/transactions` - Create transaction

### Payments
- `GET /api/v1/payments` - List payments
- `PUT /api/v1/payments/{id}/pay` - Mark as paid

### Reports
- `GET /api/v1/reports/dashboard` - Dashboard stats
- `GET /api/v1/reports/cash-flow` - Cash flow data

### API Keys (Phase 17)
- `GET /api/v1/api-keys` - List API keys
- `POST /api/v1/api-keys` - Create API key with scopes
- `GET /api/v1/api-keys/scopes` - Available scopes
- `POST /api/v1/api-keys/{id}/regenerate` - Regenerate key
- `POST /api/v1/api-keys/{id}/revoke` - Revoke key
- `GET /api/v1/api-keys/{id}/usage` - Usage statistics

### Webhooks (Phase 17)
- `GET /api/v1/webhooks` - List webhooks
- `POST /api/v1/webhooks` - Create webhook
- `GET /api/v1/webhooks/events` - Available event types
- `POST /api/v1/webhooks/{id}/test` - Send test event
- `POST /api/v1/webhooks/{id}/rotate-secret` - Rotate signing secret
- `GET /api/v1/webhooks/{id}/deliveries` - Delivery history
- `POST /api/v1/webhooks/{id}/deliveries/{delivery_id}/retry` - Retry delivery
- `GET /api/v1/webhooks/{id}/stats` - Delivery statistics

### Real-Time Presence (Phase 18)
- `GET /api/v1/presence/online` - Get online users
- `POST /api/v1/presence/status` - Update presence status
- `GET /api/v1/presence/{user_id}` - Get user presence

### Real-Time Notifications (Phase 18)
- `GET /api/v1/notifications` - Get notifications
- `GET /api/v1/notifications/unread-count` - Get unread count
- `POST /api/v1/notifications/{id}/read` - Mark as read
- `POST /api/v1/notifications/read-all` - Mark all as read
- `DELETE /api/v1/notifications/{id}` - Delete notification

### Activity Feed (Phase 18)
- `GET /api/v1/activity` - Get activity feed
- `GET /api/v1/activity/entity/{type}/{id}` - Get entity activities

### WebSocket Events (Phase 18)
Connect via Socket.IO to `/socket.io` with JWT token:
- `presence:update` - User presence changed
- `room:user_joined` / `room:user_left` - Room membership
- `cursor:moved` - Cursor position updates
- `notification:new` - New notification
- `activity` - New activity logged

### AI Cash Flow (Phase 19)
- `POST /api/v1/ai/cashflow/forecast` - Generate forecast
- `GET /api/v1/ai/cashflow/forecast/{id}` - Get forecast
- `GET /api/v1/ai/cashflow/forecasts` - List forecasts
- `GET /api/v1/ai/cashflow/summary` - Get summary

### AI Invoice OCR (Phase 19)
- `POST /api/v1/ai/invoice/scan` - Scan invoice
- `GET /api/v1/ai/invoice/scans` - List scans
- `GET /api/v1/ai/invoice/scans/{id}` - Get scan
- `PUT /api/v1/ai/invoice/scans/{id}/correct` - Submit corrections
- `POST /api/v1/ai/invoice/scans/{id}/approve` - Approve scan
- `GET /api/v1/ai/invoice/categories` - Get categories

### AI Assistant (Phase 19)
- `POST /api/v1/ai/assistant/chat` - Send message
- `GET /api/v1/ai/assistant/conversations` - List conversations
- `GET /api/v1/ai/assistant/conversations/{id}` - Get conversation
- `POST /api/v1/ai/assistant/conversations/{id}/archive` - Archive
- `POST /api/v1/ai/assistant/messages/{id}/feedback` - Submit feedback
- `GET /api/v1/ai/assistant/capabilities` - Get capabilities

### AI Payment Optimizer (Phase 19)
- `POST /api/v1/ai/payments/optimize` - Analyze invoices
- `GET /api/v1/ai/payments/recommendations` - List recommendations
- `GET /api/v1/ai/payments/recommendations/{id}` - Get recommendation
- `POST /api/v1/ai/payments/recommendations/{id}/accept` - Accept
- `POST /api/v1/ai/payments/recommendations/{id}/reject` - Reject
- `GET /api/v1/ai/payments/calendar` - Payment calendar
- `GET /api/v1/ai/payments/savings` - Savings summary

### AI Anomaly Detection (Phase 19)
- `POST /api/v1/ai/anomaly/detect` - Detect anomalies
- `GET /api/v1/ai/anomaly/anomalies` - List anomalies
- `GET /api/v1/ai/anomaly/anomalies/{id}` - Get anomaly
- `POST /api/v1/ai/anomaly/anomalies/{id}/resolve` - Resolve
- `POST /api/v1/ai/anomaly/anomalies/{id}/dismiss` - Dismiss
- `GET /api/v1/ai/anomaly/stats` - Get statistics
- `GET /api/v1/ai/anomaly/rules` - Get detection rules
- `POST /api/v1/ai/anomaly/rules/{id}/enable` - Enable rule
- `POST /api/v1/ai/anomaly/rules/{id}/disable` - Disable rule

### AI Usage & Config (Phase 19)
- `GET /api/v1/ai/usage` - Get usage stats
- `GET /api/v1/ai/usage/by-feature` - Usage by feature
- `GET /api/v1/ai/usage/costs` - Usage costs
- `GET /api/v1/ai/config` - Get AI configuration
- `GET /api/v1/ai/health` - Check AI services health

### Workflow Automation (Phase 22)
- `GET /api/v1/workflows` - List workflows
- `POST /api/v1/workflows` - Create workflow
- `GET /api/v1/workflows/{id}` - Get workflow
- `PUT /api/v1/workflows/{id}` - Update workflow
- `DELETE /api/v1/workflows/{id}` - Delete workflow
- `POST /api/v1/workflows/{id}/activate` - Activate workflow
- `POST /api/v1/workflows/{id}/pause` - Pause workflow
- `POST /api/v1/workflows/{id}/trigger` - Manually trigger workflow
- `POST /api/v1/workflows/{id}/test` - Test workflow with sample data
- `GET /api/v1/workflows/{id}/versions` - Get version history
- `POST /api/v1/workflows/{id}/rollback/{version}` - Rollback to version

### Workflow Executions (Phase 22)
- `GET /api/v1/executions` - List executions
- `GET /api/v1/executions/{id}` - Get execution details
- `GET /api/v1/executions/{id}/steps` - Get execution steps
- `GET /api/v1/executions/{id}/logs` - Get execution logs
- `POST /api/v1/executions/{id}/cancel` - Cancel running execution
- `POST /api/v1/executions/{id}/retry` - Retry failed execution
- `GET /api/v1/executions/stats` - Get execution statistics

### Business Rules (Phase 22)
- `GET /api/v1/rules` - List rules
- `POST /api/v1/rules` - Create rule
- `GET /api/v1/rules/{id}` - Get rule
- `PUT /api/v1/rules/{id}` - Update rule
- `DELETE /api/v1/rules/{id}` - Delete rule
- `POST /api/v1/rules/{id}/activate` - Activate rule
- `POST /api/v1/rules/{id}/pause` - Pause rule
- `POST /api/v1/rules/{id}/test` - Test rule with sample data
- `POST /api/v1/rules/evaluate` - Evaluate rules for entity

### Internationalization (Phase 21)
- `GET /api/v1/i18n/languages` - List supported languages
- `GET /api/v1/i18n/languages/{code}` - Get language details
- `GET /api/v1/i18n/translations/{language}/{namespace}` - Get translations
- `GET /api/v1/i18n/currencies` - List supported currencies
- `GET /api/v1/i18n/currencies/{code}` - Get currency details
- `GET /api/v1/i18n/exchange-rate` - Get exchange rate
- `POST /api/v1/i18n/convert` - Convert currency amount
- `GET /api/v1/i18n/tax/eu-vat-rates` - Get EU VAT rates
- `GET /api/v1/i18n/tax/us-sales-tax-rates` - Get US sales tax rates
- `POST /api/v1/i18n/tax/calculate/eu-vat` - Calculate EU VAT
- `POST /api/v1/i18n/tax/calculate/us-sales` - Calculate US sales tax
- `POST /api/v1/i18n/tax/validate-vat` - Validate VAT number
- `GET /api/v1/i18n/timezones` - Get common timezones

### Mobile Sync (Phase 23)
- `GET /api/v1/sync/{entity_type}` - Get changes since timestamp
- `POST /api/v1/sync/{entity_type}/push` - Push local changes
- `POST /api/v1/sync/resolve-conflict` - Resolve sync conflict
- `GET /api/v1/sync/status` - Get sync status

### Push Notifications (Phase 23)
- `POST /api/v1/push/register` - Register device for push
- `POST /api/v1/push/unregister` - Unregister device
- `GET /api/v1/push/devices` - List registered devices
- `POST /api/v1/push/send` - Send notification
- `POST /api/v1/push/test` - Send test notification
- `GET /api/v1/push/settings` - Get notification settings
- `PATCH /api/v1/push/settings` - Update notification settings

### Mobile Dashboard (Phase 23)
- `GET /api/v1/mobile/dashboard` - Get optimized dashboard data
- `GET /api/v1/mobile/kpis` - Get key performance indicators
- `GET /api/v1/mobile/invoices/recent` - Get recent invoices
- `GET /api/v1/mobile/inventory/alerts` - Get inventory alerts
- `GET /api/v1/mobile/activity` - Get recent activity feed
- `GET /api/v1/mobile/search` - Global search

### BI Reports (Phase 24)
- `GET /api/v1/reports` - List reports with pagination
- `POST /api/v1/reports` - Create new report
- `GET /api/v1/reports/{id}` - Get report details
- `PUT /api/v1/reports/{id}` - Update report
- `DELETE /api/v1/reports/{id}` - Delete report
- `POST /api/v1/reports/{id}/execute` - Execute report
- `GET /api/v1/reports/{id}/export/{format}` - Export report (pdf, xlsx, csv, html, pptx)
- `POST /api/v1/reports/{id}/favorite` - Toggle favorite
- `GET /api/v1/reports/user/favorites` - Get user favorites
- `GET /api/v1/reports/user/recent` - Get recent reports
- `GET /api/v1/reports/categories` - Get report categories

### Report Scheduling (Phase 24)
- `GET /api/v1/reports/{id}/schedules` - List report schedules
- `POST /api/v1/reports/{id}/schedules` - Create schedule
- `PUT /api/v1/reports/{id}/schedules/{schedule_id}` - Update schedule
- `DELETE /api/v1/reports/{id}/schedules/{schedule_id}` - Delete schedule
- `POST /api/v1/reports/{id}/schedules/{schedule_id}/run` - Run schedule now

### Metrics Catalog (Phase 24)
- `GET /api/v1/reports/metrics` - List metrics
- `POST /api/v1/reports/metrics` - Create custom metric
- `GET /api/v1/reports/metrics/{id}` - Get metric details
- `PUT /api/v1/reports/metrics/{id}` - Update metric
- `DELETE /api/v1/reports/metrics/{id}` - Delete metric
- `POST /api/v1/reports/metrics/{id}/calculate` - Calculate metric value
- `GET /api/v1/reports/metrics/categories` - Get metric categories

### CRM Leads (Phase 25)
- `GET /api/v1/crm/leads` - List leads with filters
- `POST /api/v1/crm/leads` - Create lead
- `GET /api/v1/crm/leads/{id}` - Get lead details
- `PUT /api/v1/crm/leads/{id}` - Update lead
- `DELETE /api/v1/crm/leads/{id}` - Delete lead
- `POST /api/v1/crm/leads/{id}/convert` - Convert to contact/opportunity
- `POST /api/v1/crm/leads/{id}/assign` - Assign to user
- `PUT /api/v1/crm/leads/{id}/status` - Change status
- `POST /api/v1/crm/leads/bulk-assign` - Bulk assign leads
- `POST /api/v1/crm/leads/import` - Import leads
- `GET /api/v1/crm/leads/sources/stats` - Source statistics

### CRM Contacts (Phase 25)
- `GET /api/v1/crm/contacts` - List contacts
- `POST /api/v1/crm/contacts` - Create contact
- `GET /api/v1/crm/contacts/{id}` - Get contact
- `GET /api/v1/crm/contacts/{id}/360` - Get 360 view
- `PUT /api/v1/crm/contacts/{id}` - Update contact
- `DELETE /api/v1/crm/contacts/{id}` - Delete contact
- `POST /api/v1/crm/contacts/merge` - Merge contacts
- `PUT /api/v1/crm/contacts/{id}/preferences` - Update preferences
- `GET /api/v1/crm/contacts/export` - Export to CSV

### CRM Companies (Phase 25)
- `GET /api/v1/crm/companies` - List companies
- `POST /api/v1/crm/companies` - Create company
- `GET /api/v1/crm/companies/{id}` - Get company
- `GET /api/v1/crm/companies/{id}/summary` - Get summary
- `PUT /api/v1/crm/companies/{id}` - Update company
- `DELETE /api/v1/crm/companies/{id}` - Delete company
- `POST /api/v1/crm/companies/{id}/parent` - Set parent
- `GET /api/v1/crm/companies/{id}/subsidiaries` - Get subsidiaries
- `POST /api/v1/crm/companies/{id}/link-client` - Link to client
- `GET /api/v1/crm/companies/top` - Top accounts
- `GET /api/v1/crm/companies/at-risk` - At-risk accounts

### CRM Opportunities (Phase 25)
- `GET /api/v1/crm/opportunities` - List opportunities
- `POST /api/v1/crm/opportunities` - Create opportunity
- `GET /api/v1/crm/opportunities/{id}` - Get opportunity
- `PUT /api/v1/crm/opportunities/{id}` - Update opportunity
- `DELETE /api/v1/crm/opportunities/{id}` - Delete opportunity
- `POST /api/v1/crm/opportunities/{id}/move` - Move to stage
- `POST /api/v1/crm/opportunities/{id}/win` - Mark as won
- `POST /api/v1/crm/opportunities/{id}/lose` - Mark as lost
- `POST /api/v1/crm/opportunities/{id}/reopen` - Reopen deal
- `GET /api/v1/crm/opportunities/board` - Get Kanban board
- `GET /api/v1/crm/opportunities/forecast` - Get forecast
- `GET /api/v1/crm/opportunities/win-loss` - Win/loss analysis
- `GET /api/v1/crm/opportunities/pipelines` - List pipelines
- `POST /api/v1/crm/opportunities/pipelines` - Create pipeline

### CRM Activities (Phase 25)
- `GET /api/v1/crm/activities` - List activities
- `POST /api/v1/crm/activities` - Create activity
- `GET /api/v1/crm/activities/{id}` - Get activity
- `PUT /api/v1/crm/activities/{id}` - Update activity
- `DELETE /api/v1/crm/activities/{id}` - Delete activity
- `POST /api/v1/crm/activities/{id}/complete` - Complete activity
- `POST /api/v1/crm/activities/{id}/cancel` - Cancel activity
- `POST /api/v1/crm/activities/{id}/reschedule` - Reschedule
- `POST /api/v1/crm/activities/log-call` - Log call
- `POST /api/v1/crm/activities/log-email` - Log email
- `POST /api/v1/crm/activities/schedule-meeting` - Schedule meeting
- `POST /api/v1/crm/activities/create-task` - Create task
- `GET /api/v1/crm/activities/upcoming` - Upcoming activities
- `GET /api/v1/crm/activities/overdue` - Overdue tasks
- `GET /api/v1/crm/activities/stats` - Activity statistics

### CRM Quotes (Phase 25)
- `GET /api/v1/crm/quotes` - List quotes
- `POST /api/v1/crm/quotes` - Create quote
- `GET /api/v1/crm/quotes/{id}` - Get quote
- `PUT /api/v1/crm/quotes/{id}` - Update quote
- `DELETE /api/v1/crm/quotes/{id}` - Delete quote
- `POST /api/v1/crm/quotes/{id}/duplicate` - Duplicate quote
- `POST /api/v1/crm/quotes/{id}/items` - Add line item
- `PUT /api/v1/crm/quotes/{id}/items/{item_id}` - Update item
- `DELETE /api/v1/crm/quotes/{id}/items/{item_id}` - Remove item
- `POST /api/v1/crm/quotes/{id}/submit` - Submit for approval
- `POST /api/v1/crm/quotes/{id}/approve` - Approve quote
- `POST /api/v1/crm/quotes/{id}/reject` - Reject quote
- `POST /api/v1/crm/quotes/{id}/send` - Send to customer
- `POST /api/v1/crm/quotes/{id}/accept` - Accept (customer)
- `POST /api/v1/crm/quotes/{id}/decline` - Decline (customer)
- `POST /api/v1/crm/quotes/{id}/convert` - Convert to invoice
- `GET /api/v1/crm/quotes/public/{id}` - Public quote view

### Health & Metrics (Phase 20)
- `GET /health` - Full health check with all components
- `GET /health/live` - Kubernetes liveness probe
- `GET /health/ready` - Kubernetes readiness probe
- `GET /health/startup` - Startup status for debugging
- `GET /metrics` - Prometheus metrics endpoint

## Docker Compose (Local Development)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

Services included:
- API server (port 8000)
- Celery worker
- PostgreSQL primary and replica (ports 5432, 5433)
- Redis (port 6379)
- Prometheus (port 9090)
- Grafana (port 3001)
- Jaeger (port 16686)

## Kubernetes Deployment

```bash
# Create namespace and deploy
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/

# Check deployment status
kubectl -n logiaccounting get pods

# View HPA status
kubectl -n logiaccounting get hpa

# Port forward for local testing
kubectl -n logiaccounting port-forward svc/logiaccounting-api 8000:80
```

## Roadmap

### Completed Phases

| Phase | Name | Status |
|-------|------|--------|
| 1-7 | Core Platform | Completed |
| 8 | Supplier Module | Completed |
| 9 | Client Module | Completed |
| 10 | Project Management | Completed |
| 11 | Invoice System | Completed |
| 12 | Payment Processing | Completed |
| 13 | Dashboard & Analytics | Completed |
| 14 | External Integrations | Completed |
| 15 | Audit & Compliance | Completed |
| 16 | Multi-Tenancy | Completed |
| 17 | API Gateway & Webhooks | Completed |
| 18 | Real-Time Collaboration | Completed |
| 19 | AI-Powered Features | Completed |
| 20 | Performance & Scalability | Completed |
| 21 | Internationalization | Completed |
| 22 | Workflow Automation | Completed |
| 23 | Mobile App & PWA | Completed |
| 24 | Advanced BI & Reporting | Completed |
| 25 | CRM & Sales Pipeline | Completed |
| 26 | Advanced Workflow Engine v2 | Completed |
| 27 | Customer Portal v2 | Completed |
| 28 | Mobile API & PWA | Completed |
| 29 | Integration Hub | Completed |

### Upcoming Phases

| Phase | Name | Description |
|-------|------|-------------|
| 30 | AI Sales Assistant | Deal coaching, email suggestions |
| 31 | Advanced Analytics v2 | Predictive insights, ML models |

## License

MIT License
