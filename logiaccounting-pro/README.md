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

### AI-Powered Features
- **Smart Invoice OCR**: Extract data from invoices using Tesseract + AI
- **Cash Flow Predictor**: 30-60-90 day predictions using Prophet ML
- **Profitability Assistant**: NLP chatbot for financial queries
- **Anomaly Detection**: Fraud prevention and duplicate detection
- **Payment Scheduler**: Optimized payment scheduling

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

- **Frontend**: React 18, Vite, Chart.js, Axios
- **Backend**: FastAPI, Pydantic, PyJWT, bcrypt
- **Database**: In-memory (PostgreSQL ready)

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
│   │   └── utils/            # Auth utilities
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── contexts/         # Auth context
│   │   └── services/         # API client
│   └── package.json
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

## License

MIT License
