# Budgeting Module Integration Guide

## 1. Register Routes

Add to your main router file (e.g., `frontend/src/router.jsx` or `frontend/src/App.jsx`):

```javascript
import { budgetingRoutes } from './features/budgeting';

// In your route configuration:
const routes = [
  // ... existing routes
  ...budgetingRoutes,
];
```

## 2. Add Navigation Link

Add to your sidebar/navigation component:

```jsx
<NavLink to="/budgeting" icon={<CalculatorIcon />}>
  Budgeting
</NavLink>
```

Or with sub-items:

```jsx
<NavGroup title="Finance" icon={<CurrencyIcon />}>
  <NavLink to="/budgeting">Budgets</NavLink>
  <NavLink to="/budgeting/new">New Budget</NavLink>
</NavGroup>
```

## 3. Add Permissions (if using RBAC)

Add these permissions to your roles:

```javascript
const budgetingPermissions = [
  'budgets.view',
  'budgets.create',
  'budgets.edit',
  'budgets.delete',
  'budgets.approve',
];
```

## 4. Backend Router Registration

Add to `backend/app/main.py`:

```python
from app.budgeting.routes import router as budgeting_router

app.include_router(budgeting_router, prefix="/api/v1")
```

## 5. Run Migration

```bash
cd backend
alembic upgrade head
```

## 6. Test Endpoints

```bash
# List budgets
curl http://localhost:8000/api/v1/budgeting/budgets

# Create budget
curl -X POST http://localhost:8000/api/v1/budgeting/budgets \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Budget", "fiscal_year": 2025, "start_date": "2025-01-01", "end_date": "2025-12-31"}'
```
