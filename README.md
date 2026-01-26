# LogiAccounting Pro

<div align="center">

![LogiAccounting Pro](https://img.shields.io/badge/LogiAccounting-Pro-667eea?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTMgM2gxOHYxOEgzeiIvPjxwYXRoIGQ9Ik0zIDloMTgiLz48cGF0aCBkPSJNOSAyMVYzIi8+PC9zdmc+)
![Version](https://img.shields.io/badge/version-2.0.0-blue?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18+-61dafb?style=for-the-badge&logo=react&logoColor=black)

**Enterprise-grade Logistics & Accounting Platform**

[Live Demo](https://logiaccounting-pro.onrender.com) · [Documentation](#documentation) · [API Reference](#api-reference) · [Contributing](#contributing)

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Security](#security)
- [Testing](#testing)
- [Documentation](#documentation)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**LogiAccounting Pro** is a comprehensive enterprise platform that combines logistics management with accounting capabilities. Built for businesses that need to track inventory, manage projects, handle payments, and maintain financial records in one integrated system.

### Why LogiAccounting Pro?

- **Unified Platform**: Manage inventory, transactions, payments, and projects in one place
- **Role-Based Access**: Granular permissions for admins, clients, and suppliers
- **Real-Time Updates**: WebSocket-powered live notifications and dashboard updates
- **Multi-Currency**: Support for 11+ currencies with automatic conversion
- **Compliance Ready**: Advanced audit trail for SOX, GDPR, and financial regulations
- **Extensible**: Custom fields system to adapt to any business need

### Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@logiaccounting.com` | `admin123` |
| Client | `client@example.com` | `client123` |
| Supplier | `supplier@example.com` | `supplier123` |

---

## Features

### 🏢 Core Business Modules

<details>
<summary><strong>Inventory Management</strong></summary>

- Real-time stock tracking with min/max thresholds
- SKU management and barcode support
- Multi-location warehouse support
- Automatic low stock alerts
- Stock movement history
- Batch and serial number tracking
- Inventory valuation (FIFO, LIFO, Average)

</details>

<details>
<summary><strong>Transaction Management</strong></summary>

- Income and expense tracking
- Category-based organization
- Project-linked transactions
- Invoice number management
- Recurring transactions with flexible schedules
- Bulk import/export capabilities
- Transaction attachments and notes

</details>

<details>
<summary><strong>Payment Processing</strong></summary>

- Accounts receivable and payable
- Payment aging reports
- Automatic due date reminders
- Partial payment support
- Payment reconciliation
- Multi-currency payments
- Payment scheduling

</details>

<details>
<summary><strong>Project Management</strong></summary>

- Budget tracking and forecasting
- Material allocation
- Timeline management
- Progress monitoring
- Cost analysis
- Resource utilization reports
- Milestone tracking

</details>

### 🔐 Security & Authentication

| Feature | Description |
|---------|-------------|
| **JWT Authentication** | Secure token-based auth with refresh tokens |
| **Multi-Factor Authentication** | TOTP, SMS, Email verification with backup codes |
| **OAuth 2.0 / SSO** | Google, Microsoft, GitHub integration with PKCE |
| **Role-Based Access Control** | 9 system roles with granular permissions and policies |
| **Session Management** | Device tracking, concurrent limits, remote logout |
| **Field-Level Encryption** | AES-256-GCM with key rotation and encrypted fields |
| **Security Headers** | HSTS, CSP, X-Frame-Options middleware |
| **Rate Limiting** | Sliding window algorithm with per-endpoint rules |
| **IP Filtering** | Allowlist/blocklist with geographic filtering |
| **Input Sanitization** | SQL injection, XSS, command injection detection |
| **Audit Logging** | Immutable audit trail with compliance reporting |

### 📊 Dashboards & Analytics

- **Custom Dashboard Builder**: Drag-and-drop widget placement
- **15+ Widget Types**: KPIs, charts, tables, gauges, alerts
- **Real-Time Updates**: WebSocket-powered live data
- **Preset Templates**: Financial, Operations, Executive dashboards
- **Export & Sharing**: Dashboard sharing between users
- **Advanced Analytics**: Cohort analysis, trend detection, forecasting

### 🌐 Multi-Language & Accessibility

- **Internationalization**: English and Spanish (extensible)
- **Dark Mode**: System-aware theme with manual toggle
- **PWA Support**: Installable on mobile and desktop
- **Keyboard Shortcuts**: Power user navigation (Cmd/Ctrl+K command palette)
- **Responsive Design**: Mobile-first approach

### 🔔 Notifications & Collaboration

- **Real-Time Notifications**: WebSocket push notifications
- **Notification Center**: Centralized alert management
- **Email Notifications**: Configurable email alerts
- **Team Collaboration**: Comments, @mentions, task assignments
- **Activity Feed**: Entity-level activity tracking

### 📅 Planning & Scheduling

- **Calendar Integration**: Month, week, day, agenda views
- **Payment Due Dates**: Automatic calendar events
- **Project Deadlines**: Visual deadline tracking
- **Recurring Events**: Support for repeating events
- **Scheduled Reports**: Automated report generation and delivery

### 🧾 Financial Compliance

- **Tax Management**: Multiple tax rates, compound taxes, exemptions
- **Tax Reports**: Period-based tax liability calculations
- **Bank Reconciliation**: Statement import and auto-matching
- **Budget Management**: Category and project-level budgets
- **Approval Workflows**: Multi-level approval chains

### 🔧 Customization & Integration

- **Custom Fields**: Extend any entity without code changes
- **API Keys**: Secure programmatic access
- **Webhooks**: Event-driven integrations
- **Data Import Wizard**: CSV/Excel import with validation
- **Export Options**: PDF, Excel, CSV exports

### 🏪 Self-Service Portals

- **Client Portal**: View projects, invoices, payments, documents
- **Supplier Portal**: Track orders, payments, product catalog
- **Scoped Access**: Data isolation per portal user

---

## Tech Stack

### Backend

| Technology | Purpose |
|------------|---------|
| **Python 3.11+** | Runtime environment |
| **FastAPI** | High-performance async API framework |
| **Pydantic** | Data validation and serialization |
| **PyJWT** | JWT token management |
| **PyOTP** | Two-factor authentication |
| **Uvicorn** | ASGI server |
| **WebSockets** | Real-time communication |

### Frontend

| Technology | Purpose |
|------------|---------|
| **React 18** | UI framework with hooks |
| **Vite** | Build tool and dev server |
| **React Router 6** | Client-side routing |
| **Axios** | HTTP client |
| **Chart.js** | Data visualization |
| **React Grid Layout** | Dashboard builder |
| **i18next** | Internationalization |

### Infrastructure

| Technology | Purpose |
|------------|---------|
| **Render** | Cloud hosting platform |
| **GitHub Actions** | CI/CD pipelines |
| **Docker** | Containerization (optional) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Web App    │  │  Client PWA  │  │ Supplier PWA │          │
│  │   (React)    │  │   Portal     │  │    Portal    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼─────────────────┼─────────────────┼───────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API GATEWAY                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    FastAPI Application                    │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐ │  │
│  │  │  Auth   │ │  CORS   │ │  Rate   │ │ Audit Middleware│ │  │
│  │  │Middleware│ │Middleware│ │ Limiter │ │                 │ │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                       SERVICE LAYER                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Material │ │Transaction│ │ Payment  │ │ Project  │          │
│  │ Service  │ │ Service   │ │ Service  │ │ Service  │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │  Audit   │ │   Tax    │ │ Calendar │ │ Forecast │          │
│  │ Service  │ │ Service  │ │ Service  │ │ Service  │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  In-Memory Data Store                     │  │
│  │   (Production: Replace with PostgreSQL/MongoDB)          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Action → React Component → API Call → FastAPI Route → Service → Data Store
                    ↑                                              │
                    └──────────── Response ────────────────────────┘
```

### WebSocket Architecture

```
┌──────────┐     ┌─────────────┐     ┌──────────────────┐
│  Client  │────▶│  WebSocket  │────▶│  Notification    │
│  Browser │◀────│  Manager    │◀────│  Service         │
└──────────┘     └─────────────┘     └──────────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Event Types:   │
              │  • transaction  │
              │  • payment      │
              │  • inventory    │
              │  • approval     │
              └─────────────────┘
```

---

## Getting Started

### Prerequisites

- **Node.js** 18+ and npm 9+
- **Python** 3.11+
- **Git**

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/Federicojaviermartino/logiaccounting-pro.git
cd logiaccounting-pro
```

2. **Set up the backend**

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

3. **Set up the frontend**

```bash
cd frontend
npm install
```

4. **Configure environment variables**

```bash
# Backend (.env)
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Frontend (.env)
VITE_API_URL=http://localhost:8000
```

5. **Start the development servers**

```bash
# Terminal 1 - Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

6. **Access the application**

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Project Structure

```
logiaccounting-pro/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application entry
│   │   ├── config.py               # Configuration management
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── store.py            # Data store singleton
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # Authentication endpoints
│   │   │   ├── materials.py        # Inventory management
│   │   │   ├── transactions.py     # Transaction CRUD
│   │   │   ├── payments.py         # Payment management
│   │   │   ├── projects.py         # Project management
│   │   │   ├── categories.py       # Category management
│   │   │   ├── locations.py        # Location management
│   │   │   ├── dashboard.py        # Dashboard data
│   │   │   ├── reports.py          # Report generation
│   │   │   ├── notifications.py    # Notification center
│   │   │   ├── settings.py         # User settings
│   │   │   ├── activity.py         # Activity logging
│   │   │   ├── export.py           # Data export
│   │   │   ├── ai_features.py      # AI-powered features
│   │   │   ├── approval.py         # Approval workflows
│   │   │   ├── recurring.py        # Recurring transactions
│   │   │   ├── budgets.py          # Budget management
│   │   │   ├── documents.py        # Document management
│   │   │   ├── api_keys.py         # API key management
│   │   │   ├── webhooks.py         # Webhook configuration
│   │   │   ├── assistant.py        # AI assistant
│   │   │   ├── dashboards.py       # Custom dashboards
│   │   │   ├── websocket.py        # WebSocket endpoint
│   │   │   ├── reconciliation.py   # Bank reconciliation
│   │   │   ├── client_portal.py    # Client portal API
│   │   │   ├── supplier_portal.py  # Supplier portal API
│   │   │   ├── scheduled_reports.py# Scheduled reports
│   │   │   ├── currencies.py       # Multi-currency
│   │   │   ├── audit.py            # Audit trail
│   │   │   ├── data_import.py      # Data import wizard
│   │   │   ├── comments.py         # Team comments
│   │   │   ├── tasks.py            # Task management
│   │   │   ├── taxes.py            # Tax management
│   │   │   ├── custom_fields.py    # Custom fields
│   │   │   └── calendar.py         # Calendar events
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── notification_service.py
│   │   │   ├── export_service.py
│   │   │   ├── ai_service.py
│   │   │   ├── approval_service.py
│   │   │   ├── recurring_service.py
│   │   │   ├── budget_service.py
│   │   │   ├── document_service.py
│   │   │   ├── api_key_service.py
│   │   │   ├── webhook_service.py
│   │   │   ├── assistant_service.py
│   │   │   ├── dashboard_service.py
│   │   │   ├── websocket_manager.py
│   │   │   ├── reconciliation_service.py
│   │   │   ├── report_scheduler.py
│   │   │   ├── currency_service.py
│   │   │   ├── audit_service.py
│   │   │   ├── import_service.py
│   │   │   ├── collaboration_service.py
│   │   │   ├── tax_service.py
│   │   │   ├── custom_fields_service.py
│   │   │   └── calendar_service.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── auth.py             # Auth utilities
│   └── requirements.txt
├── frontend/
│   ├── public/
│   │   ├── manifest.json           # PWA manifest
│   │   └── sw.js                   # Service worker
│   ├── src/
│   │   ├── main.jsx               # React entry point
│   │   ├── App.jsx                # Main application
│   │   ├── index.css              # Global styles
│   │   ├── contexts/
│   │   │   ├── AuthContext.jsx    # Authentication state
│   │   │   ├── ThemeContext.jsx   # Theme management
│   │   │   ├── LanguageContext.jsx# i18n context
│   │   │   └── WebSocketContext.jsx# WebSocket connection
│   │   ├── services/
│   │   │   └── api.js             # API client
│   │   ├── components/
│   │   │   ├── Layout.jsx         # Main layout
│   │   │   ├── NotificationBell.jsx
│   │   │   ├── ToastContainer.jsx
│   │   │   ├── CommandPalette.jsx
│   │   │   ├── HelpCenter.jsx
│   │   │   ├── CommentSection.jsx
│   │   │   ├── CustomFieldRenderer.jsx
│   │   │   └── ...
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Materials.jsx
│   │   │   ├── Transactions.jsx
│   │   │   ├── Payments.jsx
│   │   │   ├── Projects.jsx
│   │   │   ├── Categories.jsx
│   │   │   ├── Reports.jsx
│   │   │   ├── Settings.jsx
│   │   │   ├── NotificationCenter.jsx
│   │   │   ├── ActivityLog.jsx
│   │   │   ├── TwoFactorSetup.jsx
│   │   │   ├── ReportBuilder.jsx
│   │   │   ├── OnboardingWizard.jsx
│   │   │   ├── BackupRestore.jsx
│   │   │   ├── WebhookConfig.jsx
│   │   │   ├── AIAssistant.jsx
│   │   │   ├── ApprovalWorkflows.jsx
│   │   │   ├── RecurringTransactions.jsx
│   │   │   ├── BudgetManagement.jsx
│   │   │   ├── DocumentManager.jsx
│   │   │   ├── APIKeyManager.jsx
│   │   │   ├── DashboardBuilder.jsx
│   │   │   ├── BankReconciliation.jsx
│   │   │   ├── ClientDashboard.jsx
│   │   │   ├── SupplierDashboard.jsx
│   │   │   ├── ScheduledReports.jsx
│   │   │   ├── CurrencySettings.jsx
│   │   │   ├── AuditTrail.jsx
│   │   │   ├── DataImport.jsx
│   │   │   ├── TeamTasks.jsx
│   │   │   ├── TaxManagement.jsx
│   │   │   ├── CustomFieldsConfig.jsx
│   │   │   └── Calendar.jsx
│   │   ├── hooks/
│   │   │   ├── useKeyboardShortcuts.js
│   │   │   └── useCustomFields.js
│   │   └── i18n/
│   │       ├── en.json
│   │       └── es.json
│   ├── package.json
│   └── vite.config.js
├── .gitignore
├── README.md
└── render.yaml                    # Render deployment config
```

---

## API Reference

### Base URL

```
Production: https://logiaccounting-pro.onrender.com/api/v1
Development: http://localhost:8000/api/v1
```

### Authentication

All protected endpoints require a Bearer token:

```http
Authorization: Bearer <access_token>
```

### Core Endpoints

<details>
<summary><strong>Authentication</strong></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | User login |
| POST | `/auth/register` | User registration |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Get current user |
| POST | `/auth/2fa/setup` | Setup 2FA |
| POST | `/auth/2fa/verify` | Verify 2FA code |

</details>

<details>
<summary><strong>Materials (Inventory)</strong></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/materials` | List all materials |
| POST | `/materials` | Create material |
| GET | `/materials/{id}` | Get material |
| PUT | `/materials/{id}` | Update material |
| DELETE | `/materials/{id}` | Delete material |
| PUT | `/materials/{id}/stock` | Update stock |
| GET | `/materials/low-stock` | Get low stock items |

</details>

<details>
<summary><strong>Transactions</strong></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/transactions` | List transactions |
| POST | `/transactions` | Create transaction |
| GET | `/transactions/{id}` | Get transaction |
| PUT | `/transactions/{id}` | Update transaction |
| DELETE | `/transactions/{id}` | Delete transaction |
| POST | `/transactions/bulk` | Bulk operations |

</details>

<details>
<summary><strong>Payments</strong></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/payments` | List payments |
| POST | `/payments` | Create payment |
| GET | `/payments/{id}` | Get payment |
| PUT | `/payments/{id}` | Update payment |
| DELETE | `/payments/{id}` | Delete payment |
| GET | `/payments/overdue` | Get overdue payments |

</details>

<details>
<summary><strong>Projects</strong></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/projects` | List projects |
| POST | `/projects` | Create project |
| GET | `/projects/{id}` | Get project |
| PUT | `/projects/{id}` | Update project |
| DELETE | `/projects/{id}` | Delete project |
| GET | `/projects/{id}/summary` | Get project summary |

</details>

<details>
<summary><strong>Reports & Export</strong></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/reports/summary` | Financial summary |
| GET | `/reports/monthly` | Monthly report |
| POST | `/export/{format}` | Export data |
| GET | `/report-builder/templates` | Report templates |
| POST | `/report-builder/generate` | Generate custom report |

</details>

<details>
<summary><strong>Audit & Compliance</strong></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/audit` | Search audit logs |
| GET | `/audit/statistics` | Audit statistics |
| GET | `/audit/anomalies` | Detect anomalies |
| GET | `/audit/entity/{type}/{id}` | Entity history |
| GET | `/audit/export` | Export audit logs |

</details>

### WebSocket

Connect to receive real-time updates:

```javascript
const ws = new WebSocket('wss://logiaccounting-pro.onrender.com/ws?token=<access_token>');

ws.onmessage = (event) => {
  const notification = JSON.parse(event.data);
  // Handle notification
};
```

### Rate Limiting

| Tier | Requests | Window |
|------|----------|--------|
| Standard | 100 | 1 minute |
| API Key | 1000 | 1 minute |

---

## Configuration

### Environment Variables

#### Backend

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key | Required |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | `30` |
| `CORS_ORIGINS` | Allowed origins | `*` |

#### Frontend

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` |

### Feature Flags

Configure in `backend/app/config.py`:

```python
FEATURES = {
    "2FA_ENABLED": True,
    "AI_FEATURES_ENABLED": True,
    "WEBSOCKET_ENABLED": True,
    "MULTI_CURRENCY": True,
    "CUSTOM_FIELDS": True
}
```

---

## Deployment

### Render (Recommended)

1. Fork this repository
2. Create a new Web Service on Render
3. Connect your GitHub repository
4. Configure:
   - **Build Command**: `cd frontend && npm install && npm run build && cd ../backend && pip install -r requirements.txt`
   - **Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables
6. Deploy

### Docker

```bash
# Build
docker build -t logiaccounting-pro .

# Run
docker run -p 8000:8000 -e SECRET_KEY=your-secret logiaccounting-pro
```

### Manual Deployment

```bash
# Build frontend
cd frontend
npm run build

# Copy build to backend static
cp -r dist ../backend/static

# Start production server
cd ../backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## Security

### Authentication Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Login   │────▶│  Verify  │────▶│  Issue   │
│  Request │     │  2FA     │     │  JWT     │
└──────────┘     └──────────┘     └──────────┘
                                       │
                                       ▼
                              ┌──────────────┐
                              │ Access Token │
                              │ (30 min)     │
                              │              │
                              │Refresh Token │
                              │ (7 days)     │
                              └──────────────┘
```

### Security Best Practices

- ✅ JWT tokens with short expiry
- ✅ TOTP-based two-factor authentication
- ✅ Password hashing with bcrypt
- ✅ Role-based access control
- ✅ CORS configuration
- ✅ Input validation with Pydantic
- ✅ SQL injection prevention
- ✅ XSS protection
- ✅ CSRF protection
- ✅ Audit logging

### Reporting Vulnerabilities

Please report security vulnerabilities to: security@example.com

---

## Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v --cov=app
```

### Frontend Tests

```bash
cd frontend
npm test
npm run test:coverage
```

### E2E Tests

```bash
npm run test:e2e
```

---

## Documentation

- [User Guide](docs/user-guide.md)
- [Admin Guide](docs/admin-guide.md)
- [API Documentation](https://logiaccounting-pro.onrender.com/docs)
- [Architecture Decision Records](docs/adr/)

---

## Roadmap

### Completed ✅

- [x] Phase 1: Core MVP with CRUD operations
- [x] Phase 2: Testing, Notifications, Export
- [x] Phase 3: i18n, PWA, Dark Mode, Bulk Operations
- [x] Phase 4: 2FA, Report Builder, Webhooks, Command Palette
- [x] Phase 5: AI Assistant, Approvals, Recurring, Budgets
- [x] Phase 6: Dashboard Builder, WebSocket, Portals, Multi-Currency
- [x] Phase 7: Audit Trail, Import, Collaboration, Tax, Custom Fields, Calendar
- [x] Phase 8-31: Enterprise Features, AI/ML, CRM, Workflows, Mobile, Integrations
- [x] Phase 32: Advanced Security (MFA, OAuth 2.0, RBAC, Encryption, Audit)
- [x] Phase 33: Full Accounting Module (Chart of Accounts, Journal Entries, Financial Statements)
- [x] Phase 34: Inventory & Warehouse Management (Products, Warehouses, Stock, Movements, Counting, Reorder)
- [x] Phase 35: Purchase Orders & Procurement (Suppliers, Purchase Orders, Goods Receiving, Supplier Invoices)
- [x] Phase 36: Sales Orders & Customer Management (Customer Master, Sales Orders, Order Fulfillment, Customer Invoices)
- [x] Phase 37: Banking & Cash Management (Bank Accounts, Transactions, Reconciliation, Payments, Cash Flow Forecasting)

---

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Code Style

- **Backend**: PEP 8, Black formatter
- **Frontend**: ESLint, Prettier

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://reactjs.org/) - UI library
- [Chart.js](https://www.chartjs.org/) - Data visualization
- [Render](https://render.com/) - Cloud hosting

---

<div align="center">

**Built with ❤️ for the Modern Enterprise**

[⬆ Back to Top](#logiaccounting-pro)

</div>
