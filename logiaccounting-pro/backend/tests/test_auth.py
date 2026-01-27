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
