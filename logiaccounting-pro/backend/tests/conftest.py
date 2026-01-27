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
