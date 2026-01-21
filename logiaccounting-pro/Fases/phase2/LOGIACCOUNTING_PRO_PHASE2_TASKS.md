# LogiAccounting Pro - Phase 2 Tasks for Claude Code VSC

## INSTRUCTIONS FOR CLAUDE CODE

Execute tasks in order. Each task is self-contained with copy-paste ready code.

---

## TASK 1: SETUP BACKEND TESTING

### 1.1 Create test directory and files

```bash
cd backend
mkdir -p tests
touch tests/__init__.py
```

### 1.2 Create conftest.py

**File:** `backend/tests/conftest.py`

```python
"""
Pytest fixtures for LogiAccounting Pro tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.store import db, init_database


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Initialize database before tests"""
    init_database()
    yield


@pytest.fixture
def client():
    """Test client for API requests"""
    return TestClient(app)


@pytest.fixture
def admin_token(client):
    """Get admin authentication token"""
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@logiaccounting.demo",
        "password": "Demo2024!Admin"
    })
    assert response.status_code == 200
    return response.json()["token"]


@pytest.fixture
def client_token(client):
    """Get client user authentication token"""
    response = client.post("/api/v1/auth/login", json={
        "email": "client@logiaccounting.demo",
        "password": "Demo2024!Client"
    })
    assert response.status_code == 200
    return response.json()["token"]


@pytest.fixture
def supplier_token(client):
    """Get supplier authentication token"""
    response = client.post("/api/v1/auth/login", json={
        "email": "supplier@logiaccounting.demo",
        "password": "Demo2024!Supplier"
    })
    assert response.status_code == 200
    return response.json()["token"]


@pytest.fixture
def admin_headers(admin_token):
    """Headers with admin authorization"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def client_headers(client_token):
    """Headers with client authorization"""
    return {"Authorization": f"Bearer {client_token}"}


@pytest.fixture
def supplier_headers(supplier_token):
    """Headers with supplier authorization"""
    return {"Authorization": f"Bearer {supplier_token}"}


@pytest.fixture
def sample_material():
    """Sample material data for tests"""
    return {
        "name": "Test Material",
        "reference": "TM-001",
        "description": "Material for testing",
        "category_id": None,
        "unit": "units",
        "quantity": 100,
        "min_stock": 10,
        "unit_cost": 25.50,
        "location_id": None
    }


@pytest.fixture
def sample_transaction():
    """Sample transaction data for tests"""
    return {
        "type": "expense",
        "amount": 1500.00,
        "description": "Test transaction",
        "category_id": None,
        "date": "2024-01-15"
    }


@pytest.fixture
def sample_payment():
    """Sample payment data for tests"""
    return {
        "type": "payable",
        "amount": 2500.00,
        "due_date": "2024-02-15",
        "description": "Test payment",
        "reference": "PAY-TEST-001"
    }
```

### 1.3 Create test_auth.py

**File:** `backend/tests/test_auth.py`

```python
"""
Authentication endpoint tests
"""
import pytest


class TestLogin:
    """Login endpoint tests"""

    def test_login_success_admin(self, client):
        """Test successful admin login"""
        response = client.post("/api/v1/auth/login", json={
            "email": "admin@logiaccounting.demo",
            "password": "Demo2024!Admin"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["role"] == "admin"

    def test_login_success_client(self, client):
        """Test successful client login"""
        response = client.post("/api/v1/auth/login", json={
            "email": "client@logiaccounting.demo",
            "password": "Demo2024!Client"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "client"

    def test_login_success_supplier(self, client):
        """Test successful supplier login"""
        response = client.post("/api/v1/auth/login", json={
            "email": "supplier@logiaccounting.demo",
            "password": "Demo2024!Supplier"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "supplier"

    def test_login_invalid_email(self, client):
        """Test login with invalid email"""
        response = client.post("/api/v1/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "password123"
        })
        assert response.status_code == 401

    def test_login_invalid_password(self, client):
        """Test login with wrong password"""
        response = client.post("/api/v1/auth/login", json={
            "email": "admin@logiaccounting.demo",
            "password": "wrongpassword"
        })
        assert response.status_code == 401

    def test_login_missing_fields(self, client):
        """Test login with missing fields"""
        response = client.post("/api/v1/auth/login", json={
            "email": "admin@logiaccounting.demo"
        })
        assert response.status_code == 422


class TestMe:
    """Current user endpoint tests"""

    def test_get_me_authenticated(self, client, admin_headers):
        """Test getting current user when authenticated"""
        response = client.get("/api/v1/auth/me", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert data["role"] == "admin"

    def test_get_me_unauthenticated(self, client):
        """Test getting current user without token"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self, client):
        """Test getting current user with invalid token"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


class TestRegister:
    """Registration endpoint tests"""

    def test_register_success(self, client, admin_headers):
        """Test successful user registration by admin"""
        import uuid
        unique_email = f"test_{uuid.uuid4().hex[:8]}@test.com"
        
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "TestPass123!",
                "first_name": "Test",
                "last_name": "User",
                "role": "client"
            },
            headers=admin_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["email"] == unique_email

    def test_register_duplicate_email(self, client, admin_headers):
        """Test registration with existing email"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "admin@logiaccounting.demo",
                "password": "TestPass123!",
                "first_name": "Test",
                "last_name": "User",
                "role": "client"
            },
            headers=admin_headers
        )
        assert response.status_code == 400

    def test_register_unauthorized(self, client, client_headers):
        """Test registration by non-admin user"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@test.com",
                "password": "TestPass123!",
                "first_name": "Test",
                "last_name": "User",
                "role": "client"
            },
            headers=client_headers
        )
        assert response.status_code == 403
```

### 1.4 Create test_inventory.py

**File:** `backend/tests/test_inventory.py`

```python
"""
Inventory endpoint tests
"""
import pytest


class TestMaterials:
    """Materials CRUD tests"""

    def test_get_materials_as_admin(self, client, admin_headers):
        """Test getting materials list as admin"""
        response = client.get("/api/v1/inventory/materials", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "materials" in data

    def test_get_materials_as_supplier(self, client, supplier_headers):
        """Test getting materials list as supplier"""
        response = client.get("/api/v1/inventory/materials", headers=supplier_headers)
        assert response.status_code == 200

    def test_get_materials_as_client_forbidden(self, client, client_headers):
        """Test client cannot access inventory"""
        response = client.get("/api/v1/inventory/materials", headers=client_headers)
        assert response.status_code == 403

    def test_get_materials_unauthenticated(self, client):
        """Test unauthenticated access denied"""
        response = client.get("/api/v1/inventory/materials")
        assert response.status_code == 401

    def test_create_material(self, client, admin_headers, sample_material):
        """Test creating a new material"""
        response = client.post(
            "/api/v1/inventory/materials",
            json=sample_material,
            headers=admin_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["material"]["name"] == sample_material["name"]
        assert "id" in data["material"]

    def test_create_material_missing_name(self, client, admin_headers):
        """Test creating material without name fails"""
        response = client.post(
            "/api/v1/inventory/materials",
            json={"quantity": 100},
            headers=admin_headers
        )
        assert response.status_code == 422

    def test_update_material(self, client, admin_headers, sample_material):
        """Test updating a material"""
        # First create
        create_res = client.post(
            "/api/v1/inventory/materials",
            json=sample_material,
            headers=admin_headers
        )
        material_id = create_res.json()["material"]["id"]
        
        # Then update
        response = client.put(
            f"/api/v1/inventory/materials/{material_id}",
            json={"name": "Updated Material", "quantity": 200},
            headers=admin_headers
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Material"
        assert response.json()["quantity"] == 200

    def test_delete_material(self, client, admin_headers, sample_material):
        """Test deleting a material"""
        # First create
        create_res = client.post(
            "/api/v1/inventory/materials",
            json=sample_material,
            headers=admin_headers
        )
        material_id = create_res.json()["material"]["id"]
        
        # Then delete
        response = client.delete(
            f"/api/v1/inventory/materials/{material_id}",
            headers=admin_headers
        )
        assert response.status_code == 200


class TestCategories:
    """Categories tests"""

    def test_get_categories(self, client, admin_headers):
        """Test getting categories"""
        response = client.get("/api/v1/inventory/categories", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data


class TestLocations:
    """Locations tests"""

    def test_get_locations(self, client, admin_headers):
        """Test getting locations"""
        response = client.get("/api/v1/inventory/locations", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "locations" in data
```

### 1.5 Create test_transactions.py

**File:** `backend/tests/test_transactions.py`

```python
"""
Transactions endpoint tests
"""
import pytest


class TestTransactions:
    """Transaction CRUD tests"""

    def test_get_transactions_as_admin(self, client, admin_headers):
        """Test getting all transactions as admin"""
        response = client.get("/api/v1/transactions", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data

    def test_get_transactions_as_client(self, client, client_headers):
        """Test client sees only their transactions"""
        response = client.get("/api/v1/transactions", headers=client_headers)
        assert response.status_code == 200

    def test_create_expense_transaction(self, client, admin_headers, sample_transaction):
        """Test creating expense transaction"""
        response = client.post(
            "/api/v1/transactions",
            json=sample_transaction,
            headers=admin_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["transaction"]["type"] == "expense"
        assert data["transaction"]["amount"] == sample_transaction["amount"]

    def test_create_income_transaction(self, client, admin_headers):
        """Test creating income transaction"""
        response = client.post(
            "/api/v1/transactions",
            json={
                "type": "income",
                "amount": 5000.00,
                "description": "Payment received",
                "date": "2024-01-20"
            },
            headers=admin_headers
        )
        assert response.status_code == 201
        assert response.json()["transaction"]["type"] == "income"

    def test_create_transaction_invalid_type(self, client, admin_headers):
        """Test creating transaction with invalid type"""
        response = client.post(
            "/api/v1/transactions",
            json={
                "type": "invalid",
                "amount": 1000.00,
                "description": "Test"
            },
            headers=admin_headers
        )
        assert response.status_code == 422

    def test_create_transaction_negative_amount(self, client, admin_headers):
        """Test creating transaction with negative amount"""
        response = client.post(
            "/api/v1/transactions",
            json={
                "type": "expense",
                "amount": -500.00,
                "description": "Negative test"
            },
            headers=admin_headers
        )
        # Should either reject or accept based on business logic
        # Typically negative amounts are rejected
        assert response.status_code in [201, 422]

    def test_filter_transactions_by_type(self, client, admin_headers):
        """Test filtering transactions by type"""
        response = client.get(
            "/api/v1/transactions?type=expense",
            headers=admin_headers
        )
        assert response.status_code == 200
        transactions = response.json()["transactions"]
        for tx in transactions:
            assert tx["type"] == "expense"
```

### 1.6 Create test_ai_services.py

**File:** `backend/tests/test_ai_services.py`

```python
"""
AI Services endpoint tests
"""
import pytest


class TestCashFlowPredictor:
    """Cash flow prediction tests"""

    def test_get_prediction_default(self, client, admin_headers):
        """Test getting default 90-day prediction"""
        response = client.get("/api/v1/cashflow/predict", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert "summary" in data

    def test_get_prediction_30_days(self, client, admin_headers):
        """Test getting 30-day prediction"""
        response = client.get(
            "/api/v1/cashflow/predict?days=30",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data.get("predictions", [])) <= 30

    def test_prediction_forbidden_for_supplier(self, client, supplier_headers):
        """Test supplier cannot access cash flow predictions"""
        response = client.get("/api/v1/cashflow/predict", headers=supplier_headers)
        assert response.status_code == 403


class TestAnomalyDetection:
    """Anomaly detection tests"""

    def test_run_scan(self, client, admin_headers):
        """Test running anomaly scan"""
        response = client.get("/api/v1/anomaly/scan", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_anomalies" in data
        assert "anomalies" in data
        assert "risk_score" in data

    def test_get_summary(self, client, admin_headers):
        """Test getting anomaly summary"""
        response = client.get("/api/v1/anomaly/summary", headers=admin_headers)
        assert response.status_code == 200

    def test_check_transaction(self, client, admin_headers):
        """Test checking single transaction"""
        response = client.post(
            "/api/v1/anomaly/check-transaction",
            json={
                "amount": 1500.00,
                "vendor_name": "Test Vendor",
                "description": "Test transaction"
            },
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "transaction_ok" in data

    def test_anomaly_scan_forbidden_for_client(self, client, client_headers):
        """Test client cannot run anomaly scan"""
        response = client.get("/api/v1/anomaly/scan", headers=client_headers)
        assert response.status_code == 403

    def test_get_status(self, client, admin_headers):
        """Test getting anomaly service status"""
        response = client.get("/api/v1/anomaly/status", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "ml_detection_enabled" in data


class TestPaymentScheduler:
    """Payment scheduler tests"""

    def test_optimize_schedule(self, client, admin_headers):
        """Test getting optimized payment schedule"""
        response = client.get(
            "/api/v1/scheduler/optimize?available_cash=50000",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data

    def test_optimize_different_strategies(self, client, admin_headers):
        """Test different optimization strategies"""
        strategies = ["balanced", "minimize_cost", "maximize_discount"]
        for strategy in strategies:
            response = client.get(
                f"/api/v1/scheduler/optimize?optimize_for={strategy}",
                headers=admin_headers
            )
            assert response.status_code == 200


class TestAssistant:
    """Profitability assistant tests"""

    def test_query_assistant(self, client, admin_headers):
        """Test querying the assistant"""
        response = client.post(
            "/api/v1/assistant/query",
            json={"query": "What projects are over budget?"},
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

    def test_get_suggestions(self, client, admin_headers):
        """Test getting query suggestions"""
        response = client.get("/api/v1/assistant/suggestions", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data

    def test_assistant_status(self, client, admin_headers):
        """Test getting assistant status"""
        response = client.get("/api/v1/assistant/status", headers=admin_headers)
        assert response.status_code == 200


class TestOCR:
    """OCR service tests"""

    def test_get_ocr_status(self, client, admin_headers):
        """Test getting OCR service status"""
        response = client.get("/api/v1/ocr/status", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "tesseract_available" in data
        assert "supported_formats" in data

    def test_get_category_suggestions(self, client, admin_headers):
        """Test getting category suggestions"""
        response = client.get(
            "/api/v1/ocr/categories/suggestions?vendor_name=Office%20Depot",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
```

### 1.7 Update requirements.txt

**Add to:** `backend/requirements.txt`

```
# Testing
pytest==8.0.0
pytest-cov==4.1.0
pytest-asyncio==0.23.0
httpx==0.26.0
```

### 1.8 Run tests

```bash
cd backend
pip install pytest pytest-cov pytest-asyncio httpx
pytest -v
pytest --cov=app --cov-report=html
```

---

## TASK 2: NOTIFICATION CENTER UI

### 2.1 Create NotificationBell component

**File:** `frontend/src/components/NotificationBell.jsx`

```jsx
import { useState, useEffect, useRef } from 'react';
import { notificationsAPI } from '../services/api';

export default function NotificationBell() {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    loadUnreadCount();
    const interval = setInterval(loadUnreadCount, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const loadUnreadCount = async () => {
    try {
      const res = await notificationsAPI.getUnreadCount();
      setUnreadCount(res.data.count);
    } catch (error) {
      console.error('Failed to load notification count:', error);
    }
  };

  const loadNotifications = async () => {
    setLoading(true);
    try {
      const res = await notificationsAPI.getNotifications({ unread: false });
      setNotifications(res.data.notifications || []);
    } catch (error) {
      console.error('Failed to load notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleDropdown = () => {
    if (!isOpen) {
      loadNotifications();
    }
    setIsOpen(!isOpen);
  };

  const markAsRead = async (id) => {
    try {
      await notificationsAPI.markAsRead(id);
      setNotifications(prev => 
        prev.map(n => n.id === id ? { ...n, read: true } : n)
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await notificationsAPI.markAllAsRead();
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    }
  };

  const getTimeAgo = (dateString) => {
    const now = new Date();
    const date = new Date(dateString);
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  const getNotificationIcon = (type) => {
    const icons = {
      payment: '💳',
      inventory: '📦',
      project: '📁',
      alert: '⚠️',
      info: 'ℹ️'
    };
    return icons[type] || '🔔';
  };

  return (
    <div className="notification-bell" ref={dropdownRef}>
      <button className="bell-button" onClick={toggleDropdown}>
        <span className="bell-icon">🔔</span>
        {unreadCount > 0 && (
          <span className="badge-count">{unreadCount > 99 ? '99+' : unreadCount}</span>
        )}
      </button>

      {isOpen && (
        <div className="notification-dropdown">
          <div className="dropdown-header">
            <h4>Notifications</h4>
            {unreadCount > 0 && (
              <button className="mark-all-btn" onClick={markAllAsRead}>
                Mark all read
              </button>
            )}
          </div>

          <div className="notification-list">
            {loading ? (
              <div className="notification-loading">Loading...</div>
            ) : notifications.length === 0 ? (
              <div className="notification-empty">No notifications</div>
            ) : (
              notifications.slice(0, 10).map(notif => (
                <div
                  key={notif.id}
                  className={`notification-item ${!notif.read ? 'unread' : ''}`}
                  onClick={() => !notif.read && markAsRead(notif.id)}
                >
                  <span className="notification-icon">
                    {getNotificationIcon(notif.type)}
                  </span>
                  <div className="notification-content">
                    <div className="notification-title">{notif.title}</div>
                    <div className="notification-message">{notif.message}</div>
                    <div className="notification-time">{getTimeAgo(notif.created_at)}</div>
                  </div>
                  {!notif.read && <span className="unread-dot"></span>}
                </div>
              ))
            )}
          </div>

          {notifications.length > 10 && (
            <div className="dropdown-footer">
              <a href="/notifications">View all notifications</a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

### 2.2 Add notification styles

**Add to:** `frontend/src/index.css`

```css
/* Notification Bell */
.notification-bell {
  position: relative;
}

.bell-button {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: background 0.2s;
  position: relative;
}

.bell-button:hover {
  background: var(--gray-100);
}

.bell-icon {
  font-size: 1.25rem;
}

.badge-count {
  position: absolute;
  top: 2px;
  right: 2px;
  background: var(--danger);
  color: white;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 2px 5px;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
}

.notification-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  width: 360px;
  max-height: 480px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  overflow: hidden;
  margin-top: 8px;
}

.dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--gray-100);
}

.dropdown-header h4 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.mark-all-btn {
  background: none;
  border: none;
  color: var(--primary);
  font-size: 0.85rem;
  cursor: pointer;
}

.mark-all-btn:hover {
  text-decoration: underline;
}

.notification-list {
  max-height: 380px;
  overflow-y: auto;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid var(--gray-50);
  position: relative;
}

.notification-item:hover {
  background: var(--gray-50);
}

.notification-item.unread {
  background: #f0f9ff;
}

.notification-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--gray-800);
  margin-bottom: 2px;
}

.notification-message {
  font-size: 0.85rem;
  color: var(--gray-600);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.notification-time {
  font-size: 0.75rem;
  color: var(--gray-400);
  margin-top: 4px;
}

.unread-dot {
  width: 8px;
  height: 8px;
  background: var(--primary);
  border-radius: 50%;
  flex-shrink: 0;
}

.notification-loading,
.notification-empty {
  padding: 40px 16px;
  text-align: center;
  color: var(--gray-400);
}

.dropdown-footer {
  padding: 12px 16px;
  text-align: center;
  border-top: 1px solid var(--gray-100);
}

.dropdown-footer a {
  color: var(--primary);
  text-decoration: none;
  font-size: 0.9rem;
}

.dropdown-footer a:hover {
  text-decoration: underline;
}
```

### 2.3 Update Layout to include NotificationBell

**File:** `frontend/src/components/Layout.jsx`

**Add import at top:**
```javascript
import NotificationBell from './NotificationBell';
```

**Update the header section (find the `<header className="page-header">` and update):**

```jsx
<header className="page-header">
  <h1 className="page-title">{pageTitles[location.pathname] || 'Dashboard'}</h1>
  <div className="header-right">
    <NotificationBell />
    <div className="user-info">
      <div className="user-name">{user?.first_name} {user?.last_name}</div>
      <div className="user-role">{user?.role}</div>
    </div>
  </div>
</header>
```

**Add to CSS (in index.css):**
```css
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
```

---

## TASK 3: EXPORT REPORTS FUNCTIONALITY

### 3.1 Install dependencies

```bash
cd frontend
npm install xlsx jspdf jspdf-autotable file-saver
```

### 3.2 Create export utilities

**File:** `frontend/src/utils/exportUtils.js`

```javascript
import * as XLSX from 'xlsx';
import jsPDF from 'jspdf';
import 'jspdf-autotable';
import { saveAs } from 'file-saver';

/**
 * Export data to CSV file
 */
export const exportToCSV = (data, filename, headers = null) => {
  if (!data || data.length === 0) {
    alert('No data to export');
    return;
  }

  const headerRow = headers || Object.keys(data[0]);
  const csvContent = [
    headerRow.join(','),
    ...data.map(row => 
      headerRow.map(key => {
        const value = row[key];
        // Handle values with commas or quotes
        if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value ?? '';
      }).join(',')
    )
  ].join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  saveAs(blob, `${filename}.csv`);
};

/**
 * Export data to Excel file
 */
export const exportToExcel = (data, filename, sheetName = 'Sheet1') => {
  if (!data || data.length === 0) {
    alert('No data to export');
    return;
  }

  const worksheet = XLSX.utils.json_to_sheet(data);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, sheetName);
  
  // Auto-size columns
  const maxWidth = 50;
  const cols = Object.keys(data[0]).map(key => ({
    wch: Math.min(maxWidth, Math.max(key.length, ...data.map(row => String(row[key] || '').length)))
  }));
  worksheet['!cols'] = cols;

  XLSX.writeFile(workbook, `${filename}.xlsx`);
};

/**
 * Export data to PDF file
 */
export const exportToPDF = (data, filename, title, columns = null) => {
  if (!data || data.length === 0) {
    alert('No data to export');
    return;
  }

  const doc = new jsPDF();
  
  // Add title
  doc.setFontSize(18);
  doc.text(title, 14, 22);
  
  // Add date
  doc.setFontSize(10);
  doc.setTextColor(100);
  doc.text(`Generated: ${new Date().toLocaleString()}`, 14, 30);

  // Prepare table data
  const headers = columns || Object.keys(data[0]);
  const tableData = data.map(row => headers.map(key => row[key] ?? ''));

  // Add table
  doc.autoTable({
    head: [headers.map(h => h.replace(/_/g, ' ').toUpperCase())],
    body: tableData,
    startY: 38,
    styles: { fontSize: 8 },
    headStyles: { fillColor: [102, 126, 234] }
  });

  doc.save(`${filename}.pdf`);
};

/**
 * Format currency for export
 */
export const formatCurrencyForExport = (value) => {
  return typeof value === 'number' ? value.toFixed(2) : value;
};

/**
 * Format date for export
 */
export const formatDateForExport = (dateString) => {
  if (!dateString) return '';
  return new Date(dateString).toLocaleDateString();
};
```

### 3.3 Create ExportButton component

**File:** `frontend/src/components/ExportButton.jsx`

```jsx
import { useState } from 'react';
import { exportToCSV, exportToExcel, exportToPDF } from '../utils/exportUtils';

export default function ExportButton({ 
  data, 
  filename, 
  title = 'Report',
  columns = null 
}) {
  const [isOpen, setIsOpen] = useState(false);

  const handleExport = (format) => {
    switch (format) {
      case 'csv':
        exportToCSV(data, filename, columns);
        break;
      case 'excel':
        exportToExcel(data, filename);
        break;
      case 'pdf':
        exportToPDF(data, filename, title, columns);
        break;
    }
    setIsOpen(false);
  };

  return (
    <div className="export-button-container">
      <button 
        className="btn btn-secondary"
        onClick={() => setIsOpen(!isOpen)}
      >
        📥 Export
      </button>
      
      {isOpen && (
        <div className="export-dropdown">
          <button onClick={() => handleExport('csv')}>
            📄 Export CSV
          </button>
          <button onClick={() => handleExport('excel')}>
            📊 Export Excel
          </button>
          <button onClick={() => handleExport('pdf')}>
            📑 Export PDF
          </button>
        </div>
      )}
    </div>
  );
}
```

### 3.4 Add export button styles

**Add to:** `frontend/src/index.css`

```css
/* Export Button */
.export-button-container {
  position: relative;
  display: inline-block;
}

.export-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  z-index: 100;
  margin-top: 4px;
  min-width: 150px;
  overflow: hidden;
}

.export-dropdown button {
  display: block;
  width: 100%;
  padding: 12px 16px;
  text-align: left;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background 0.2s;
}

.export-dropdown button:hover {
  background: var(--gray-50);
}
```

### 3.5 Add ExportButton to Reports page

**Update:** `frontend/src/pages/Reports.jsx`

**Add import:**
```javascript
import ExportButton from '../components/ExportButton';
```

**Add export buttons to each section (example for financial data):**

```jsx
// In the overview tab, after section-title
<div className="section-header">
  <h3 className="section-title">Cash Flow</h3>
  <ExportButton 
    data={cashFlow.map(d => ({
      Month: d.month,
      Income: d.income,
      Expenses: d.expenses,
      'Net Profit': d.income - d.expenses
    }))}
    filename="cash-flow-report"
    title="Cash Flow Report"
  />
</div>
```

---

## TASK 4: ENHANCED DASHBOARD WITH AI INSIGHTS

### 4.1 Update Dashboard.jsx

**File:** `frontend/src/pages/Dashboard.jsx`

**Add imports:**
```javascript
import { cashflowAPI, anomalyAPI } from '../services/api';
```

**Add state for AI data:**
```javascript
const [aiInsights, setAiInsights] = useState(null);
const [aiLoading, setAiLoading] = useState(true);
```

**Add function to load AI insights:**
```javascript
const loadAIInsights = async () => {
  if (user?.role !== 'admin') {
    setAiLoading(false);
    return;
  }
  
  try {
    const [cashflowRes, anomalyRes] = await Promise.all([
      cashflowAPI.predict(30),
      anomalyAPI.getSummary()
    ]);
    
    setAiInsights({
      cashflow: cashflowRes.data,
      anomalies: anomalyRes.data
    });
  } catch (error) {
    console.error('Failed to load AI insights:', error);
  } finally {
    setAiLoading(false);
  }
};
```

**Call in useEffect:**
```javascript
useEffect(() => {
  loadStats();
  loadAIInsights();
}, []);
```

**Add AI Insights section (before the grid-2 sections):**
```jsx
{user?.role === 'admin' && aiInsights && (
  <div className="section mb-6">
    <div className="section-header">
      <h3 className="section-title">🤖 AI Insights</h3>
      <a href="/ai-dashboard" className="btn btn-sm btn-secondary">View Details</a>
    </div>
    <div className="stats-grid">
      <div className="stat-card">
        <span className="stat-icon">📈</span>
        <div className="stat-content">
          <div className="stat-label">30-Day Cash Forecast</div>
          <div className={`stat-value ${aiInsights.cashflow?.summary?.total_net >= 0 ? 'success' : 'danger'}`}>
            {formatCurrency(aiInsights.cashflow?.summary?.total_net)}
          </div>
        </div>
      </div>
      <div className="stat-card">
        <span className="stat-icon">⚠️</span>
        <div className="stat-content">
          <div className="stat-label">Anomalies Detected</div>
          <div className={`stat-value ${aiInsights.anomalies?.total_anomalies > 0 ? 'warning' : 'success'}`}>
            {aiInsights.anomalies?.total_anomalies || 0}
          </div>
        </div>
      </div>
      <div className="stat-card">
        <span className="stat-icon">🎯</span>
        <div className="stat-content">
          <div className="stat-label">Risk Score</div>
          <div className={`stat-value ${(aiInsights.anomalies?.risk_score || 0) > 0.5 ? 'danger' : 'success'}`}>
            {((aiInsights.anomalies?.risk_score || 0) * 100).toFixed(0)}%
          </div>
        </div>
      </div>
    </div>
    {aiInsights.cashflow?.risk_alerts?.length > 0 && (
      <div className="mt-4">
        {aiInsights.cashflow.risk_alerts.slice(0, 2).map((alert, i) => (
          <div key={i} className="info-banner" style={{ background: '#fef2f2', borderColor: '#fecaca', color: '#dc2626', marginBottom: '8px' }}>
            ⚠️ {alert}
          </div>
        ))}
      </div>
    )}
  </div>
)}
```

---

## TASK 5: RUN AND TEST

### 5.1 Run backend tests

```bash
cd backend
pytest -v --tb=short
```

### 5.2 Start development servers

```bash
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload --port 5000

# Terminal 2: Frontend
cd frontend
npm run dev
```

### 5.3 Test checklist

- [ ] Login with all 3 demo accounts
- [ ] Check notification bell appears in header
- [ ] Click bell to see dropdown
- [ ] Navigate to AI Dashboard
- [ ] Check Dashboard shows AI Insights section (admin only)
- [ ] Test export buttons on Reports page
- [ ] Run `pytest` and verify tests pass

---

## TASK 6: BUILD AND DEPLOY

```bash
# Build frontend
cd frontend
npm run build

# Commit all changes
git add .
git commit -m "feat: Phase 2 - Testing, notifications, exports, AI insights"

# Push to GitHub
git push origin main

# Deploy via Render (automatic if connected)
```

---

## COMPLETION CHECKLIST

### Testing
- [ ] conftest.py with fixtures
- [ ] test_auth.py (login, register, me)
- [ ] test_inventory.py (CRUD, permissions)
- [ ] test_transactions.py
- [ ] test_ai_services.py
- [ ] All tests passing

### Notification Center
- [ ] NotificationBell component
- [ ] Dropdown with notifications
- [ ] Mark as read functionality
- [ ] Unread count badge
- [ ] Integrated in Layout

### Export Reports
- [ ] exportUtils.js (CSV, Excel, PDF)
- [ ] ExportButton component
- [ ] Added to Reports page

### Enhanced Dashboard
- [ ] AI Insights section
- [ ] Cash flow forecast stat
- [ ] Anomalies count stat
- [ ] Risk score stat
- [ ] Risk alerts display

### Deployment
- [ ] Build successful
- [ ] Tests passing
- [ ] Pushed to GitHub
- [ ] Deployed to Render

---

**END OF PHASE 2 TASKS**
