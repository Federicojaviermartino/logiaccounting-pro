# LogiAccounting Pro

Enterprise logistics and accounting platform built with FastAPI + React.

## Tech Stack

- **Backend**: FastAPI, Pydantic, PyJWT, bcrypt, uvicorn
- **Frontend**: React 18, Vite, Chart.js, Axios, React Router 6
- **Database**: In-memory stores (PostgreSQL-ready schemas)
- **Auth**: JWT tokens (24h), bcrypt password hashing, RBAC

## Build & Test

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 5000
pytest  # run tests
```

### Frontend
```bash
cd frontend
npm install
npm run dev      # development
npm run build    # production build
npm run preview  # preview production
```

## Project Structure

```
logiaccounting-pro/
├── AGENTS.md              # You are here (agent instructions)
├── README.md              # Human documentation
├── backend/
│   ├── app/
│   │   ├── main.py        # FastAPI entry, CORS, static files
│   │   ├── routes/        # API endpoints (8 modules)
│   │   ├── models/        # Data stores and schemas
│   │   ├── schemas/       # Pydantic validation
│   │   └── utils/         # Auth, helpers
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/         # React page components
│   │   ├── components/    # Shared components
│   │   ├── contexts/      # Auth context
│   │   └── services/      # API client
│   └── package.json
├── skills/                # Agent Skills (invoke with $skill-name)
│   ├── backend/           # Backend development patterns
│   ├── frontend/          # React component patterns  
│   ├── deployment/        # Render deployment guide
│   ├── testing/           # Test patterns and commands
│   └── data-analysis/     # Report generation patterns
└── .claude/
    └── agents/            # Subagent definitions
```

## API Conventions

- Base URL: `/api/v1`
- Auth header: `Authorization: Bearer <token>`
- Error format: `{ "detail": "message" }`
- Success format: `{ "data": {...}, "message": "..." }`
- Pagination: `?page=1&per_page=20`

## Role Permissions

| Role | Inventory | Projects | Transactions | Payments | Users | Reports |
|------|-----------|----------|--------------|----------|-------|---------|
| admin | CRUD | CRUD | CRUD | CRUD | CRUD | Full |
| client | - | Read own | Create own | Read own | - | Limited |
| supplier | CRUD | - | Create own | Read own | - | Limited |

## Demo Credentials

```
admin@logiaccounting.demo / Demo2024!Admin
client@logiaccounting.demo / Demo2024!Client
supplier@logiaccounting.demo / Demo2024!Supplier
```

## Code Style

- **Python**: PEP 8, type hints, docstrings for public functions
- **JavaScript**: ES6+, functional components, hooks
- **Comments**: English only, explain WHY not WHAT
- **Imports**: Group by stdlib → third-party → local

## Gotchas

1. Frontend proxy: Vite proxies `/api` to backend on port 5000
2. CORS: Backend allows localhost origins in development
3. Auth: Token stored in localStorage, auto-refresh on 401
4. Dates: ISO 8601 format, UTC timezone
5. Currency: Always store as cents/integer, format on display

## Security

- Never commit `.env` files or API keys
- Passwords hashed with bcrypt (12 rounds)
- JWT tokens expire in 24 hours
- Role checks on every protected endpoint

## When Adding Features

1. Read relevant skill first: `skills/<domain>/SKILL.md`
2. Create API endpoint in `backend/app/routes/`
3. Add Pydantic schema in `backend/app/schemas/`
4. Create React page in `frontend/src/pages/`
5. Update API service in `frontend/src/services/api.js`
6. Add route in `frontend/src/App.jsx`
7. Test with demo credentials

## Available Skills

Invoke skills with `$skill-name` or read them for guidance:

- `$backend` - FastAPI patterns, route creation, auth decorators
- `$frontend` - React components, state management, API calls
- `$deployment` - Render setup, environment variables
- `$testing` - pytest patterns, API testing with curl
- `$data-analysis` - Report queries, chart data formatting
