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

- **Frontend**: React 18, Vite, Chart.js, Axios, Socket.IO Client
- **Backend**: FastAPI, Pydantic, PyJWT, bcrypt, Socket.IO
- **Real-Time**: Socket.IO with Redis adapter for horizontal scaling
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
│   │   │   └── ai/           # AI Features (Phase 19)
│   │   │       ├── CashFlowForecast.jsx
│   │   │       ├── InvoiceScanner.jsx
│   │   │       ├── AIChatAssistant.jsx
│   │   │       ├── PaymentOptimizer.jsx
│   │   │       ├── AnomalyDashboard.jsx
│   │   │       └── AIUsageStats.jsx
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
│   │   └── services/         # API client
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

## License

MIT License
