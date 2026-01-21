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
│   │   ├── realtime/         # WebSocket collaboration
│   │   │   ├── server.py     # Socket.IO server
│   │   │   ├── managers/     # Connection, presence, rooms
│   │   │   ├── handlers/     # Event handlers
│   │   │   ├── services/     # Notification, activity
│   │   │   └── routes/       # REST endpoints
│   │   └── utils/            # Auth utilities
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── contexts/         # Auth context
│   │   ├── features/
│   │   │   └── realtime/     # Real-time collaboration
│   │   │       ├── context/  # RealtimeContext
│   │   │       ├── hooks/    # usePresence, useRoom, etc.
│   │   │       └── components/ # UI components
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

## License

MIT License
