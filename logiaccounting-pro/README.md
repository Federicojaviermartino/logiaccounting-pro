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

### Full Accounting Module (Phase 33)

#### Chart of Accounts
- **Account Types**: Asset, Liability, Equity, Revenue, Expense with normal balance rules
- **Hierarchical Structure**: Parent/child account relationships with unlimited depth
- **Account Codes**: 4-digit codes with automatic validation
- **Header Accounts**: Group accounts for subtotals without transactions
- **Multi-Currency**: Per-account currency support

#### Journal Entries
- **Double-Entry Bookkeeping**: Enforced debit/credit balance validation
- **Entry Workflow**: Draft, Pending, Approved, Posted, Reversed, Voided states
- **Entry Types**: Standard, Adjustment, Closing entries
- **Batch Operations**: Bulk approve, post, void with audit trail
- **Auto-Numbering**: Sequential entry numbers with fiscal year reset
- **Reversing Entries**: Create reversals with linked references

#### General Ledger
- **Account Ledger View**: Transaction history with running balance
- **Date Range Filtering**: Flexible period selection
- **Opening/Closing Balances**: Automatic balance calculations
- **Debit/Credit Totals**: Period summaries per account

#### Trial Balance
- **As-of-Date Reporting**: Point-in-time balance snapshots
- **Zero Balance Toggle**: Include/exclude zero balance accounts
- **Account Type Grouping**: Organized by account classification
- **Balance Validation**: Automatic debit/credit comparison

#### Financial Statements
- **Balance Sheet**: Assets = Liabilities + Equity format with comparative periods
- **Income Statement**: Revenue - Expenses = Net Income with period comparison
- **Cash Flow Statement**: Indirect method with operating, investing, financing sections
- **Export Options**: PDF, Excel, CSV with professional formatting

#### Fiscal Periods
- **Fiscal Years**: Custom year-end dates with automatic period generation
- **Monthly Periods**: 12 periods per fiscal year with open/closed status
- **Period Locking**: Prevent posting to closed periods
- **Year-End Closing**: Automated closing entries and retained earnings transfer

#### Bank Reconciliation
- **Statement Import**: CSV and OFX file support
- **Auto-Matching**: Confidence-based transaction matching algorithm
- **Match Rules**: Amount, date proximity, reference matching
- **Reconciliation Workflow**: In-progress, completed, approved states
- **Discrepancy Detection**: Highlight unmatched transactions

### Inventory & Warehouse Management (Phase 34)

#### Product Catalog
- **SKU Management**: Unique product identifiers with validation
- **Categories**: Hierarchical product categorization
- **Units of Measure**: Configurable UOM with conversion factors
- **Pricing**: List price and standard cost tracking
- **Tracking Options**: Inventory, lot, and serial number tracking

#### Multi-Warehouse System
- **Warehouse Locations**: Zones and bin-level locations with coordinates
- **Location Types**: Receiving, storage, shipping, quality control areas
- **Capacity Management**: Location capacity and utilization tracking
- **Bulk Location Creation**: Generate locations with patterns (A-01-01 format)

#### Stock Management
- **Real-Time Stock Levels**: Per-location quantity tracking
- **Lot Tracking**: Expiration dates, manufacturing dates, supplier lots
- **Serial Numbers**: Individual item tracking with status
- **Reservations**: Stock reservation for orders and projects
- **Low Stock Alerts**: Configurable minimum quantity alerts

#### Inventory Valuation
- **FIFO Method**: First-in-first-out costing
- **LIFO Method**: Last-in-first-out costing
- **Average Cost**: Weighted average cost calculation
- **Valuation Reports**: Stock value by warehouse, category, product

#### Stock Movements
- **Receipts**: Incoming inventory with cost tracking
- **Issues**: Outgoing inventory with reason codes
- **Transfers**: Inter-warehouse and inter-location transfers
- **Adjustments**: Inventory corrections with variance tracking
- **Movement Workflow**: Draft, confirmed, cancelled states

#### Physical Inventory Counting
- **Count Sessions**: Scheduled inventory counts by warehouse/category
- **Blind Counting**: Optional hide expected quantities
- **Variance Detection**: Automatic variance calculation
- **Approval Workflow**: Draft, in-progress, completed, approved states
- **Adjustment Generation**: Auto-create adjustments from approved counts

#### Reorder Management
- **Reorder Rules**: Per-product minimum stock and reorder quantity
- **Automatic Alerts**: Low stock detection and notifications
- **Purchase Requisitions**: Auto-generate requisitions when below minimum
- **Requisition Workflow**: Pending, approved, ordered, received states

### Purchase Orders & Procurement (Phase 35)

#### Supplier Management
- **Supplier Master Data**: Complete supplier profiles with tax ID, legal name, categories
- **Supplier Types**: Vendor, contractor, service provider, distributor, manufacturer
- **Contact Management**: Multiple contacts per supplier with roles and communication preferences
- **Supplier Approval**: Approval workflow for new suppliers before ordering
- **Supplier Price Lists**: Product-specific pricing with quantity breaks and validity dates
- **Lead Time Tracking**: Default and product-specific lead times

#### Purchase Orders
- **Multi-Line Orders**: Multiple products per order with descriptions and quantities
- **Auto-Numbering**: Sequential PO numbers with configurable prefix
- **Order Workflow**: Draft, pending approval, approved, sent, partial, received, cancelled states
- **Approval Workflow**: Multi-level approval with comments and audit trail
- **Expected Delivery**: Tracking expected delivery dates per line
- **Currency Support**: Multi-currency orders with exchange rates
- **Order Totals**: Automatic calculation of subtotals, taxes, discounts, and totals

#### Goods Receiving
- **Receipt from PO**: Create receipts linked to purchase orders
- **Direct Receipts**: Receive goods without prior PO
- **Partial Receiving**: Receive partial quantities with backorder tracking
- **Quality Inspection**: Quality status tracking (pending, passed, failed, on hold)
- **Lot/Serial Capture**: Record lot numbers and serial numbers on receipt
- **Location Assignment**: Assign received goods to warehouse locations
- **Variance Detection**: Quantity and price variance tracking

#### Supplier Invoices
- **Invoice Matching**: 3-way matching (PO, receipt, invoice)
- **Match Status**: Unmatched, partial, matched, exception states
- **Price Variance**: Automatic price variance calculation and alerts
- **Quantity Variance**: Detection of quantity discrepancies
- **Invoice Workflow**: Draft, pending approval, approved, posted, paid states
- **AP Aging Report**: Aging analysis by 30/60/90/120+ day buckets
- **Payment Recording**: Track payments against supplier invoices

### Advanced Security (Phase 32)

#### Multi-Factor Authentication
- **TOTP Authentication**: Time-based one-time passwords with QR code setup
- **SMS Verification**: Phone number verification with rate limiting
- **Email Verification**: Secure email-based verification codes
- **Backup Codes**: Recovery codes for account access
- **MFA Enforcement**: Per-role MFA requirements

#### OAuth 2.0 & SSO
- **OAuth Providers**: Google, Microsoft, GitHub integration
- **PKCE Support**: Proof Key for Code Exchange for mobile apps
- **Token Management**: Secure access and refresh token handling
- **Session Management**: Device tracking, concurrent session limits

#### Role-Based Access Control (RBAC)
- **System Roles**: Super Admin, Admin, Manager, Accountant, Project Manager, Client, Supplier, Read-Only, Guest
- **Permission System**: Resource and action-level permissions with scopes
- **Policy Engine**: Time-based, IP-based, and ownership policies
- **Granular Access**: Customer and team-level permission scoping

#### Encryption & Key Management
- **AES-256-GCM**: Field-level encryption for sensitive data
- **Key Rotation**: Automatic and manual key rotation with audit trail
- **Encrypted Fields**: Transparent encryption for model fields
- **Secure Key Storage**: Encrypted master key management

#### Security Audit Logging
- **Event Types**: Authentication, data access, security, system events
- **Immutable Trail**: Tamper-proof audit log with hashing
- **Search & Filter**: Advanced filtering by date, user, action, resource
- **Compliance Reports**: SOX, GDPR, HIPAA audit report generation

#### Protection Services
- **Rate Limiting**: Sliding window algorithm with per-endpoint rules
- **IP Filtering**: Allowlist/blocklist with geographic filtering
- **Input Sanitization**: SQL injection, XSS, command injection detection
- **Security Headers**: HSTS, CSP, X-Frame-Options middleware

### Workflow Automation v3 (Phase 30)

#### Core Workflow Engine
- **Async Execution**: Python asyncio-based workflow execution with state machine
- **Node Types**: Action, condition, loop, parallel, delay, sub-workflow nodes
- **Variable Resolution**: Template system with `{{variable}}` syntax and pipe functions
- **Expression Evaluation**: Built-in functions (upper, lower, currency, date, etc.)
- **Condition Builder**: Complex conditions with AND/OR groups and operators
- **Retry Logic**: Exponential backoff with configurable retry policies

#### Trigger System
- **Event Triggers**: Entity events (invoice, payment, customer, project)
- **Schedule Triggers**: Cron-based scheduling with timezone support
- **Manual Triggers**: User-initiated workflows with parameters
- **Webhook Triggers**: External system integration with HMAC verification

#### Actions Library
- **Communication**: Email, SMS, Slack, push notifications
- **Data Operations**: Create, read, update, delete records with calculations
- **Integrations**: HTTP requests, Stripe, QuickBooks, Zapier webhooks
- **Flow Control**: Delay, wait until, stop, set variable, approval gates

#### Visual Workflow Builder
- **Drag-and-Drop Canvas**: React-based visual editor with node connections
- **Node Palette**: Categorized action selection with search
- **Configuration Panel**: Dynamic forms for node-specific settings
- **Undo/Redo**: Full history management with keyboard shortcuts
- **Zoom Controls**: Canvas zoom and pan functionality

#### Execution Monitoring
- **Execution History**: Full audit trail with step-by-step details
- **Status Tracking**: Pending, running, completed, failed states
- **Error Display**: Detailed error messages with step context
- **Duration Metrics**: Per-step and total execution timing

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

### Budgeting & Financial Planning (Phase 39)

#### Budget Management
- **Budget Creation**: Annual and quarterly budgets with configurable fiscal periods
- **Budget Categories**: Income, expense, and capital expenditure categories
- **Budget Lines**: Detailed line items with monthly/quarterly/annual amounts
- **Budget Versions**: Draft, submitted, approved, and rejected workflow
- **Budget vs Actual**: Real-time comparison of budgeted vs actual amounts
- **Variance Analysis**: Automatic calculation of budget variances with thresholds

#### Financial Forecasting
- **Revenue Forecasting**: Project future revenue based on historical trends
- **Expense Projections**: Forecast expenses with growth rate assumptions
- **Cash Flow Projections**: Forward-looking cash position estimates
- **Scenario Planning**: Multiple forecast scenarios (optimistic, realistic, pessimistic)

### Payroll & HR Basic (Phase 40)

#### Employee Management
- **Employee Master Data**: Complete employee profiles with personal, tax, and bank info
- **Employment Types**: Full-time, part-time, contract, intern support
- **Employment Status**: Active, on leave, suspended, terminated tracking
- **Employee Contracts**: Compensation details, benefits, PTO accrual tracking
- **Tax Information**: W-4/W-9, federal/state filing status, allowances
- **Employee Termination**: Termination workflow with reason tracking

#### Payroll Processing
- **Payroll Runs**: Draft, calculate, approve, process payment workflow
- **Tax Calculations**: Federal income tax (simplified brackets), state tax, Social Security (6.2%), Medicare (1.45%)
- **Employer Costs**: FUTA (0.6%), SUTA (2.7%), employer SS/Medicare match
- **Overtime Calculation**: 1.5x rate for overtime hours
- **YTD Tracking**: Year-to-date earnings and tax accumulation
- **Pay Period Management**: Weekly, bi-weekly, semi-monthly, monthly periods

#### Deductions & Benefits
- **Deduction Types**: Pre-tax and post-tax deductions with calculation methods
- **Benefit Types**: Health, dental, vision, life, disability, retirement, HSA/FSA
- **Employer Match**: Configurable employer match percentages and caps
- **Employee Deduction Assignment**: Per-employee deduction tracking

#### Time Off Management
- **Time Off Types**: Vacation, sick, personal, bereavement, jury duty, parental leave
- **Request Workflow**: Submit, approve, reject, cancel workflow
- **Balance Tracking**: Accrued, used, and available balance per employee per type
- **Balance Adjustments**: Manual balance adjustments with reason tracking

### Advanced Reporting & Financial Statements (Phase 41)

#### Report Definitions & Scheduling
- **Report Types**: Balance Sheet, Income Statement, Cash Flow, Trial Balance, AR/AP Aging, Budget vs Actual, Payroll Summary, General Ledger, Custom
- **Report Formats**: PDF, Excel, CSV, JSON export support
- **Report Scheduling**: Daily, weekly, monthly, quarterly, yearly automated generation
- **Email Distribution**: Scheduled reports with configurable email recipients
- **Execution History**: Full audit trail of report generation with status tracking

#### Financial Statements
- **Balance Sheet**: Assets, liabilities, equity with current/non-current classification and prior period comparison
- **Income Statement (P&L)**: Revenue, COGS, gross profit, operating expenses, net income with margin calculations
- **Cash Flow Statement**: Indirect method with operating, investing, and financing activities
- **Trial Balance**: Account-level debit/credit balances with balance validation
- **Comparative Periods**: Prior period comparison with variance and variance percentage

#### Financial KPI Dashboard
- **Liquidity Ratios**: Current ratio, quick ratio, cash ratio with status thresholds
- **Profitability Ratios**: Gross margin, net margin, operating margin, ROA, ROE
- **Efficiency Metrics**: Days sales outstanding (DSO), days payable outstanding (DPO)
- **Leverage Ratios**: Debt ratio, debt-to-equity ratio
- **Revenue & Expense Trends**: Monthly trend charts with 6-month history
- **Working Capital Analysis**: Cash, AR, AP breakdown with net working capital

#### Report Export & Generation
- **Excel Reports**: Professional formatting with headers, borders, currency formats (openpyxl)
- **PDF Reports**: Publication-quality financial statements (ReportLab)
- **Executive Dashboard**: Interactive charts (Chart.js) with real-time KPI cards
- **Balance Sheet Page**: Interactive report with date selection, prior period comparison, export options
- **Income Statement Page**: P&L report with date range, margin percentages, export capabilities

### Audit Trail & Compliance (Phase 42)

#### Audit Logging
- **Immutable Audit Logs**: Track all system changes with user, action, resource, and timestamp
- **Field-Level Change Tracking**: Record individual field changes with old/new values
- **Entity Snapshots**: Point-in-time entity state capture for recovery
- **Action Types**: Create, read, update, delete, login, logout, export, import, approve, reject, and more
- **Severity Levels**: Low, medium, high, critical event classification
- **User Activity Tracking**: Per-user activity history with configurable periods

#### Compliance Management
- **Compliance Standards**: SOX, GDPR, HIPAA, PCI-DSS, SOC2, and custom standards
- **Compliance Rules**: Configurable rules with violation alerts and blocking
- **Retention Policies**: Data retention with archive and expiry actions
- **Compliance Violations**: Detection, tracking, and resolution workflow
- **Compliance Dashboard**: Score calculation, violation summaries, and trend analysis

#### Access Control & Monitoring
- **Access Logging**: Sensitive data access tracking with PII and financial data flags
- **Data Classification**: Internal, confidential, restricted classification levels
- **Access Reports**: Period-based access analysis with top accessor metrics
- **IP and User Agent Tracking**: Request metadata capture for forensics

#### Frontend
- **Audit Logs Viewer**: Filterable, searchable audit log table with detail modal
- **Compliance Dashboard**: Visual compliance score, violation charts, and recent violations

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
│   │   ├── security/         # Advanced Security (Phase 32)
│   │   │   ├── config.py     # Security configuration
│   │   │   ├── auth/         # Authentication modules
│   │   │   ├── rbac/         # Role-based access control
│   │   │   ├── encryption/   # Encryption services
│   │   │   ├── audit/        # Audit logging
│   │   │   ├── protection/   # Protection services
│   │   │   └── middleware/   # Security middleware
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

### Security - MFA (Phase 32)
- `POST /api/v1/security/mfa/setup` - Initialize MFA setup
- `POST /api/v1/security/mfa/verify` - Verify MFA code
- `POST /api/v1/security/mfa/disable` - Disable MFA
- `POST /api/v1/security/mfa/backup-codes` - Generate backup codes
- `GET /api/v1/security/mfa/status` - Get MFA status

### Security - Sessions (Phase 32)
- `GET /api/v1/security/sessions` - List active sessions
- `DELETE /api/v1/security/sessions/{id}` - Terminate session
- `DELETE /api/v1/security/sessions` - Terminate all other sessions
- `GET /api/v1/security/sessions/current` - Get current session

### Security - Audit (Phase 32)
- `GET /api/v1/security/audit` - Search audit logs
- `GET /api/v1/security/audit/{id}` - Get audit entry
- `GET /api/v1/security/audit/statistics` - Get audit statistics
- `GET /api/v1/security/audit/export` - Export audit logs

### Accounting - Chart of Accounts (Phase 33)
- `GET /api/v1/accounting/accounts` - List accounts with filtering
- `POST /api/v1/accounting/accounts` - Create account
- `GET /api/v1/accounting/accounts/{id}` - Get account details
- `PUT /api/v1/accounting/accounts/{id}` - Update account
- `DELETE /api/v1/accounting/accounts/{id}` - Delete account
- `GET /api/v1/accounting/accounts/tree` - Get hierarchical account tree
- `GET /api/v1/accounting/account-types` - List account types
- `POST /api/v1/accounting/accounts/{id}/toggle-active` - Toggle account status

### Accounting - Journal Entries (Phase 33)
- `GET /api/v1/accounting/journal-entries` - List entries with filters
- `POST /api/v1/accounting/journal-entries` - Create journal entry
- `GET /api/v1/accounting/journal-entries/{id}` - Get entry details
- `PUT /api/v1/accounting/journal-entries/{id}` - Update entry
- `DELETE /api/v1/accounting/journal-entries/{id}` - Delete draft entry
- `POST /api/v1/accounting/journal-entries/{id}/submit` - Submit for approval
- `POST /api/v1/accounting/journal-entries/{id}/approve` - Approve entry
- `POST /api/v1/accounting/journal-entries/{id}/reject` - Reject entry
- `POST /api/v1/accounting/journal-entries/{id}/post` - Post entry
- `POST /api/v1/accounting/journal-entries/{id}/reverse` - Reverse posted entry
- `POST /api/v1/accounting/journal-entries/{id}/void` - Void entry
- `POST /api/v1/accounting/journal-entries/batch` - Batch operations

### Accounting - Ledger & Reports (Phase 33)
- `GET /api/v1/accounting/ledger/{account_id}` - Get account ledger
- `GET /api/v1/accounting/trial-balance` - Generate trial balance
- `GET /api/v1/accounting/balance-sheet` - Generate balance sheet
- `GET /api/v1/accounting/income-statement` - Generate income statement
- `GET /api/v1/accounting/cash-flow` - Generate cash flow statement

### Accounting - Fiscal Periods (Phase 33)
- `GET /api/v1/accounting/fiscal-years` - List fiscal years
- `POST /api/v1/accounting/fiscal-years` - Create fiscal year
- `GET /api/v1/accounting/fiscal-years/{id}` - Get fiscal year
- `POST /api/v1/accounting/fiscal-years/{id}/close` - Close fiscal year
- `GET /api/v1/accounting/periods` - List fiscal periods
- `POST /api/v1/accounting/periods/{id}/close` - Close period
- `POST /api/v1/accounting/periods/{id}/reopen` - Reopen period

### Accounting - Bank Reconciliation (Phase 33)
- `GET /api/v1/accounting/bank-accounts` - List bank accounts
- `POST /api/v1/accounting/bank-accounts` - Create bank account
- `POST /api/v1/accounting/bank-accounts/{id}/import` - Import statement
- `GET /api/v1/accounting/reconciliations` - List reconciliations
- `POST /api/v1/accounting/reconciliations` - Start reconciliation
- `GET /api/v1/accounting/reconciliations/{id}` - Get reconciliation
- `POST /api/v1/accounting/reconciliations/{id}/match` - Match transactions
- `POST /api/v1/accounting/reconciliations/{id}/unmatch` - Unmatch transactions
- `POST /api/v1/accounting/reconciliations/{id}/complete` - Complete reconciliation

### Inventory - Products (Phase 34)
- `GET /api/v1/inventory/products` - List products with filtering
- `POST /api/v1/inventory/products` - Create product
- `GET /api/v1/inventory/products/{id}` - Get product details
- `PUT /api/v1/inventory/products/{id}` - Update product
- `DELETE /api/v1/inventory/products/{id}` - Deactivate product
- `GET /api/v1/inventory/products/{id}/stock` - Get product stock levels
- `GET /api/v1/inventory/categories` - List categories
- `POST /api/v1/inventory/categories` - Create category
- `GET /api/v1/inventory/uom` - List units of measure

### Inventory - Warehouses (Phase 34)
- `GET /api/v1/inventory/warehouses` - List warehouses
- `POST /api/v1/inventory/warehouses` - Create warehouse
- `GET /api/v1/inventory/warehouses/{id}` - Get warehouse details
- `GET /api/v1/inventory/warehouses/{id}/locations` - List warehouse locations
- `POST /api/v1/inventory/warehouses/{id}/locations` - Create location
- `POST /api/v1/inventory/warehouses/{id}/locations/bulk` - Bulk create locations
- `GET /api/v1/inventory/warehouses/{id}/zones` - List warehouse zones

### Inventory - Stock (Phase 34)
- `GET /api/v1/inventory/stock` - Get stock levels with filtering
- `GET /api/v1/inventory/stock/low` - Get low stock alerts
- `GET /api/v1/inventory/stock/valuation` - Get stock valuation report

### Inventory - Movements (Phase 34)
- `GET /api/v1/inventory/movements` - List stock movements
- `POST /api/v1/inventory/movements/receipt` - Create receipt
- `POST /api/v1/inventory/movements/issue` - Create issue
- `POST /api/v1/inventory/movements/transfer` - Create transfer
- `POST /api/v1/inventory/movements/adjustment` - Create adjustment
- `POST /api/v1/inventory/movements/{id}/confirm` - Confirm movement
- `POST /api/v1/inventory/movements/{id}/cancel` - Cancel movement

### Inventory - Counting (Phase 34)
- `GET /api/v1/inventory/counts` - List inventory counts
- `POST /api/v1/inventory/counts` - Create count session
- `POST /api/v1/inventory/counts/{id}/start` - Start counting
- `POST /api/v1/inventory/counts/lines/{line_id}/record` - Record count
- `POST /api/v1/inventory/counts/{id}/complete` - Complete count
- `POST /api/v1/inventory/counts/{id}/approve` - Approve count

### Inventory - Reorder (Phase 34)
- `GET /api/v1/inventory/reorder/rules` - List reorder rules
- `POST /api/v1/inventory/reorder/rules` - Create reorder rule
- `POST /api/v1/inventory/reorder/check` - Check reorder points
- `GET /api/v1/inventory/requisitions` - List purchase requisitions
- `POST /api/v1/inventory/requisitions/{id}/approve` - Approve requisition

### Purchasing - Suppliers (Phase 35)
- `GET /api/v1/purchasing/suppliers` - List suppliers with filtering
- `POST /api/v1/purchasing/suppliers` - Create supplier
- `GET /api/v1/purchasing/suppliers/{id}` - Get supplier details
- `PUT /api/v1/purchasing/suppliers/{id}` - Update supplier
- `GET /api/v1/purchasing/suppliers/summary` - Get suppliers summary
- `POST /api/v1/purchasing/suppliers/{id}/approve` - Approve supplier
- `POST /api/v1/purchasing/suppliers/{id}/contacts` - Add supplier contact
- `PUT /api/v1/purchasing/suppliers/contacts/{id}` - Update contact
- `DELETE /api/v1/purchasing/suppliers/contacts/{id}` - Delete contact
- `GET /api/v1/purchasing/suppliers/{id}/prices` - Get supplier price list
- `POST /api/v1/purchasing/suppliers/{id}/prices` - Add supplier price
- `GET /api/v1/purchasing/suppliers/products/{id}/suppliers` - Get product suppliers

### Purchasing - Purchase Orders (Phase 35)
- `GET /api/v1/purchasing/purchase-orders` - List purchase orders
- `POST /api/v1/purchasing/purchase-orders` - Create purchase order
- `GET /api/v1/purchasing/purchase-orders/{id}` - Get order details
- `PUT /api/v1/purchasing/purchase-orders/{id}` - Update order
- `GET /api/v1/purchasing/purchase-orders/dashboard` - Get PO dashboard
- `POST /api/v1/purchasing/purchase-orders/{id}/lines` - Add order line
- `PUT /api/v1/purchasing/purchase-orders/lines/{id}` - Update order line
- `DELETE /api/v1/purchasing/purchase-orders/lines/{id}` - Delete order line
- `POST /api/v1/purchasing/purchase-orders/{id}/submit` - Submit for approval
- `POST /api/v1/purchasing/purchase-orders/{id}/approve` - Approve/reject order
- `POST /api/v1/purchasing/purchase-orders/{id}/send` - Mark as sent
- `POST /api/v1/purchasing/purchase-orders/{id}/cancel` - Cancel order

### Purchasing - Goods Receipts (Phase 35)
- `GET /api/v1/purchasing/goods-receipts` - List goods receipts
- `GET /api/v1/purchasing/goods-receipts/{id}` - Get receipt details
- `POST /api/v1/purchasing/goods-receipts/from-po` - Create receipt from PO
- `POST /api/v1/purchasing/goods-receipts/direct` - Create direct receipt
- `PUT /api/v1/purchasing/goods-receipts/lines/{id}` - Update receipt line
- `POST /api/v1/purchasing/goods-receipts/{id}/post` - Post receipt
- `POST /api/v1/purchasing/goods-receipts/{id}/cancel` - Cancel receipt

### Purchasing - Supplier Invoices (Phase 35)
- `GET /api/v1/purchasing/supplier-invoices` - List supplier invoices
- `GET /api/v1/purchasing/supplier-invoices/{id}` - Get invoice details
- `POST /api/v1/purchasing/supplier-invoices` - Create invoice
- `POST /api/v1/purchasing/supplier-invoices/from-receipt` - Create from receipt
- `GET /api/v1/purchasing/supplier-invoices/aging` - Get AP aging report
- `POST /api/v1/purchasing/supplier-invoices/{id}/match` - Perform 3-way matching
- `POST /api/v1/purchasing/supplier-invoices/{id}/approve` - Approve invoice
- `POST /api/v1/purchasing/supplier-invoices/{id}/post` - Post invoice
- `POST /api/v1/purchasing/supplier-invoices/{id}/payment` - Record payment

### Fixed Assets - Categories (Phase 38)
- `GET /api/v1/fixed-assets/categories` - List asset categories
- `GET /api/v1/fixed-assets/categories/tree` - Get category hierarchy
- `POST /api/v1/fixed-assets/categories` - Create category
- `GET /api/v1/fixed-assets/categories/{id}` - Get category details
- `PUT /api/v1/fixed-assets/categories/{id}` - Update category
- `DELETE /api/v1/fixed-assets/categories/{id}` - Delete category
- `POST /api/v1/fixed-assets/categories/setup-defaults` - Setup default categories

### Fixed Assets - Asset Register (Phase 38)
- `GET /api/v1/fixed-assets/assets` - List assets with filtering
- `GET /api/v1/fixed-assets/assets/summary` - Get asset summary statistics
- `GET /api/v1/fixed-assets/assets/barcode/{barcode}` - Find asset by barcode
- `POST /api/v1/fixed-assets/assets` - Create asset
- `GET /api/v1/fixed-assets/assets/{id}` - Get asset details
- `PUT /api/v1/fixed-assets/assets/{id}` - Update asset
- `DELETE /api/v1/fixed-assets/assets/{id}` - Delete draft asset
- `POST /api/v1/fixed-assets/assets/{id}/activate` - Activate asset
- `POST /api/v1/fixed-assets/assets/{id}/suspend-depreciation` - Suspend depreciation
- `POST /api/v1/fixed-assets/assets/{id}/resume-depreciation` - Resume depreciation
- `GET /api/v1/fixed-assets/assets/{id}/schedule` - Get depreciation schedule
- `POST /api/v1/fixed-assets/assets/{id}/regenerate-schedule` - Regenerate schedule
- `POST /api/v1/fixed-assets/assets/import` - Import assets from file
- `GET /api/v1/fixed-assets/assets/export` - Export assets to Excel

### Fixed Assets - Depreciation (Phase 38)
- `GET /api/v1/fixed-assets/depreciation/runs` - List depreciation runs
- `GET /api/v1/fixed-assets/depreciation/runs/{id}` - Get run details
- `POST /api/v1/fixed-assets/depreciation/runs` - Create depreciation run
- `POST /api/v1/fixed-assets/depreciation/runs/{id}/post` - Post run to GL
- `POST /api/v1/fixed-assets/depreciation/runs/{id}/cancel` - Cancel run
- `POST /api/v1/fixed-assets/depreciation/runs/{id}/reverse` - Reverse posted run
- `GET /api/v1/fixed-assets/depreciation/entries` - List depreciation entries
- `POST /api/v1/fixed-assets/depreciation/record-units` - Record units for production method
- `GET /api/v1/fixed-assets/depreciation/preview` - Preview depreciation calculation

### Fixed Assets - Movements & Disposals (Phase 38)
- `GET /api/v1/fixed-assets/movements` - List asset movements
- `GET /api/v1/fixed-assets/movements/{id}` - Get movement details
- `POST /api/v1/fixed-assets/transfer` - Transfer asset
- `POST /api/v1/fixed-assets/revalue` - Revalue asset
- `POST /api/v1/fixed-assets/improve` - Record asset improvement
- `GET /api/v1/fixed-assets/disposals` - List disposals
- `GET /api/v1/fixed-assets/disposals/{id}` - Get disposal details
- `POST /api/v1/fixed-assets/disposals` - Create disposal
- `POST /api/v1/fixed-assets/disposals/{id}/approve` - Approve disposal
- `POST /api/v1/fixed-assets/disposals/{id}/post` - Post disposal to GL
- `POST /api/v1/fixed-assets/disposals/{id}/cancel` - Cancel disposal

### Fixed Assets - Reports (Phase 38)
- `GET /api/v1/fixed-assets/reports/asset-register` - Asset register report
- `GET /api/v1/fixed-assets/reports/depreciation-schedule` - Depreciation schedule report
- `GET /api/v1/fixed-assets/reports/depreciation-summary` - Depreciation summary report
- `GET /api/v1/fixed-assets/reports/movement-history` - Movement history report
- `GET /api/v1/fixed-assets/reports/disposal-report` - Disposal report
- `GET /api/v1/fixed-assets/reports/fully-depreciated` - Fully depreciated assets
- `GET /api/v1/fixed-assets/reports/insurance-expiry` - Insurance expiry report
- `GET /api/v1/fixed-assets/reports/warranty-expiry` - Warranty expiry report
- `GET /api/v1/fixed-assets/reports/category-summary` - Category summary report

### Payroll - Employees (Phase 40)
- `GET /api/v1/payroll/employees` - List employees with filtering and search
- `GET /api/v1/payroll/employees/{id}` - Get employee details
- `POST /api/v1/payroll/employees` - Create employee
- `PUT /api/v1/payroll/employees/{id}` - Update employee
- `PUT /api/v1/payroll/employees/{id}/tax-info` - Update tax information
- `POST /api/v1/payroll/employees/{id}/terminate` - Terminate employee
- `GET /api/v1/payroll/employees/{id}/contracts` - List employee contracts
- `POST /api/v1/payroll/employees/{id}/contracts` - Create contract
- `PUT /api/v1/payroll/employees/contracts/{id}` - Update contract

### Payroll - Payroll Runs (Phase 40)
- `GET /api/v1/payroll/payroll/periods` - List pay periods
- `POST /api/v1/payroll/payroll/periods` - Create pay period
- `GET /api/v1/payroll/payroll/runs` - List payroll runs
- `GET /api/v1/payroll/payroll/runs/{id}` - Get payroll run details
- `POST /api/v1/payroll/payroll/runs` - Create payroll run
- `POST /api/v1/payroll/payroll/runs/{id}/calculate` - Calculate payroll
- `POST /api/v1/payroll/payroll/runs/{id}/approve` - Approve payroll
- `POST /api/v1/payroll/payroll/runs/{id}/process` - Process payments

### Payroll - Deductions & Benefits (Phase 40)
- `GET /api/v1/payroll/deductions/types` - List deduction types
- `POST /api/v1/payroll/deductions/types` - Create deduction type
- `GET /api/v1/payroll/deductions/employee/{id}` - Get employee deductions
- `POST /api/v1/payroll/deductions/employee/{id}` - Assign deduction to employee
- `GET /api/v1/payroll/deductions/benefits/types` - List benefit types
- `POST /api/v1/payroll/deductions/benefits/types` - Create benefit type

### Payroll - Time Off (Phase 40)
- `GET /api/v1/payroll/time-off/requests` - List time off requests
- `POST /api/v1/payroll/time-off/requests` - Create time off request
- `GET /api/v1/payroll/time-off/requests/{id}` - Get request details
- `POST /api/v1/payroll/time-off/requests/{id}/review` - Approve/reject request
- `POST /api/v1/payroll/time-off/requests/{id}/cancel` - Cancel request
- `GET /api/v1/payroll/time-off/balances/{employee_id}` - Get time off balances
- `POST /api/v1/payroll/time-off/balances/{employee_id}/adjust` - Adjust balance

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
| 30 | Workflow Automation v3 | Completed |
| 31 | AI/ML Features | Completed |
| 32 | Advanced Security | Completed |
| 33 | Full Accounting Module | Completed |
| 34 | Inventory & Warehouse Management | Completed |
| 35 | Purchase Orders & Procurement | Completed |
| 36 | Sales Orders & Customer Management | Completed |
| 37 | Banking & Cash Management | Completed |
| 38 | Fixed Assets & Depreciation | Completed |
| 39 | Budgeting & Financial Planning | Completed |
| 40 | Payroll & HR Basic | Completed |
| 41 | Advanced Reporting & Financial Statements | Completed |
| 42 | Audit Trail & Compliance | Completed |
| 43 | Document Management | Completed |

### Document Management (Phase 43)

#### Document Storage & Organization
- **Document Upload**: File upload with SHA-256 hashing, type validation, and size limits (50MB)
- **Document Types**: Invoice, receipt, contract, purchase order, delivery note, quote, report, statement, tax document, legal, correspondence
- **Document Status**: Draft, pending, approved, rejected, archived, deleted workflow
- **Version Control**: Upload new versions with change summaries and version history tracking
- **Document Categories**: Hierarchical categories with colors, icons, and retention policies
- **Tags & Metadata**: JSONB-based tags and custom metadata fields
- **OCR Support**: Extracted text storage for document search

#### Folder Management
- **Hierarchical Folders**: Nested folder structure with materialized path
- **Folder Navigation**: Breadcrumb trail, folder tree sidebar, folder contents view
- **Folder Operations**: Create, rename, move, delete (with recursive option)
- **Document-Folder Association**: Many-to-many relationship, add/remove documents from folders
- **Folder Statistics**: Document count and total size tracking per folder

#### Document Sharing
- **User Sharing**: Share documents with specific users with permission levels (view, download, edit, full)
- **Public Share Links**: Token-based public links with expiration, max uses, and optional password protection
- **Access Logging**: Complete audit trail of document access with IP and user agent tracking
- **Share Revocation**: Revoke individual shares or share links

#### Frontend
- **Document List**: List and grid views with search, type/category filters, and pagination
- **File Browser**: Explorer-style interface with folder tree sidebar and breadcrumb navigation
- **Upload Modal**: Drag-and-drop upload with title, type, and category selection
- **New Folder Dialog**: Create folders from the file browser interface

## License

MIT License
